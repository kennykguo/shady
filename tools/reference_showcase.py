"""Render the proposed five math built-ins through glslang, without changing Shady.

Run from any directory: python3 tools/reference_showcase.py
Requires the renderer's build dependencies, SPIRV-Tools, glslang, and Pillow.
"""
from pathlib import Path
from html import escape
import json
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'tests/reference-showcase'
OUT = ROOT / 'build/reference-showcase'


def run(*args):
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=True,
                          capture_output=True, text=True, timeout=60)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vertex = OUT / 'fullscreen.vert.spv'
    run('glslangValidator', '-V', SOURCES / 'fullscreen.vert', '-o', vertex)
    run('spirv-val', '--target-env', 'vulkan1.0', vertex)
    # Build an isolated copy of the existing renderer with a fullscreen vertex
    # shader. Its usual camera, renderer binary, and compiler sources stay intact.
    renderer = (ROOT / 'tools/render.cpp').read_text()
    renderer = renderer.replace('"build/mesh.vert.spv"', json.dumps(str(vertex)))
    renderer = renderer.replace('VK_CULL_MODE_BACK_BIT', 'VK_CULL_MODE_NONE')
    (OUT / 'render.cpp').write_text(renderer)
    run('c++', '-O2', '-std=c++17', '-I' + str(ROOT / 'tests/vendor'),
        OUT / 'render.cpp', '-lvulkan', '-o', OUT / 'render')
    mesh = OUT / 'fullscreen.obj'
    mesh.write_text('v -1 -1 0\nv 3 -1 0\nv -1 3 0\nf 1 2 3\n')
    rows, cards = [], []
    shaders = sorted(SOURCES.glob('*.frag'))
    for source in shaders:
        stem = source.stem
        body = source.read_text()
        calls = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', re.sub(r'//[^\n]*', '', body)))
        assert calls <= {'sin', 'cos', 'fract', 'abs', 'smoothstep', 'vec4'}, calls
        glsl = OUT / (stem + '.frag')
        glsl.write_text('#version 450\nlayout(location=0) out vec4 fragColor;\n'
                        'void main()\n' + body.replace('gl_FragColor', 'fragColor'))
        binary = glsl.with_suffix('.spv')
        run('glslangValidator', '-V', glsl, '-o', binary)
        run('spirv-val', '--target-env', 'vulkan1.0', binary)
        run('spirv-dis', binary, '-o', glsl.with_suffix('.spvasm'))
        result = run(OUT / 'render', binary, mesh, glsl.with_suffix('.png'))
        device = next(line for line in result.stdout.splitlines() if 'using device:' in line)
        rows.append({'shader': source.name, 'builtins': sorted(calls - {'vec4'}),
                     'device': device, 'spirv_bytes': binary.stat().st_size})
        title = stem[3:].replace('_', ' ').title()
        cards.append(f'<article><h2>{escape(title)}</h2><a href="{stem}.png">'
                     f'<img src="{stem}.png" alt="{escape(title)}"></a>'
                     f'<p><a href="{stem}.frag">GLSL</a> · <a href="{stem}.spvasm">SPIR-V assembly</a></p>'
                     f'<details><summary>Source</summary><pre>{escape(body)}</pre></details></article>')
        print('PASS ' + source.name + ' (reference SPIR-V validated and rendered)', flush=True)
    report = {'pipeline': 'MiniGLSL-style block + GLSL wrapper -> glslangValidator -V -> spirv-val -> Vulkan',
              'note': 'Reference previews of proposed functionality; not compiled by Shady.',
              'versions': {tool: run(tool, '--version').stdout.splitlines()[0]
                           for tool in ('glslangValidator', 'spirv-val')}, 'results': rows}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Five functions / reference previews</title>
<style>body{background:#0d121b;color:#e4eaf0;font:16px/1.5 system-ui;max-width:1300px;margin:32px auto;padding:0 24px}main{display:grid;grid-template-columns:1fr 1fr;gap:28px}h1{font-size:36px}h2{font-size:22px}img{width:100%;display:block}a{color:#8fb8e8}pre{overflow:auto;font-size:12px}summary{cursor:pointer}@media(max-width:750px){main{grid-template-columns:1fr}}</style>
<h1>Five functions. Eight shader ideas.</h1><p>sin · cos · fract · abs · smoothstep, plus arithmetic. Static 800 × 600 Vulkan renders compiled with glslang. No textures, loops, noise built-ins, or user functions. These preview proposed functionality; Shady does not yet compile these sources.</p><main>'''
                                     + ''.join(cards) + '</main></html>')
    # Two compact preview sheets; the gallery also keeps full-resolution PNGs.
    font = ImageFont.load_default(size=22)
    for page in range(2):
        sheet = Image.new('RGB', (1280, 1060), '#0d121b')
        draw = ImageDraw.Draw(sheet)
        draw.text((24, 16), 'FIVE FUNCTIONS / REFERENCE COMPILER PREVIEWS', font=font, fill='#e4eaf0')
        for i, shader in enumerate(shaders[page * 4:page * 4 + 4]):
            x, y = (i % 2) * 640 + 16, (i // 2) * 500 + 66
            image = Image.open(OUT / (shader.stem + '.png')).convert('RGB')
            assert image.size == (800, 600) and len(image.getcolors(800 * 600)) > 100
            image = image.resize((608, 456), Image.Resampling.LANCZOS)
            draw.text((x, y), shader.stem[3:].replace('_', ' ').title(), font=font, fill='#e4eaf0')
            sheet.paste(image, (x, y + 32))
        sheet.save(OUT / f'preview-{page + 1}.png')
    print('Gallery: ' + str(OUT / 'index.html'))


if __name__ == '__main__':
    main()

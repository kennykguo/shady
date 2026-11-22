"""Compile shader stress cases with both toolchains; render six on the same teapot.

Run: python3 tests/stress/generate.py && python3 tools/stress.py
Compiler and renderer sources/binaries are checked for changes before/after.
"""
from pathlib import Path
from html import escape
import hashlib
import json
import re
import subprocess
import time
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/stress'
SOURCES = OUT / 'sources'


def hashes():
    paths = sorted(p for p in (ROOT / 'src').iterdir() if p.is_file())
    paths += [ROOT / name for name in ['build/shady', 'tools/render.cpp', 'tools/mesh.vert',
                                      'build/render', 'build/mesh.vert.spv']]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run(*args, timeout=30):
    start = time.perf_counter()
    result = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True,
                            text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{Path(args[0]).name} exited {result.returncode}: {result.stderr[-2000:]}')
    return result, time.perf_counter() - start


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = hashes()
    rows, cards, device = [], [], ''
    for source in sorted(SOURCES.glob('*.frag')):
        stem = source.stem
        row = {'shader': source.name, 'lines': len(source.read_text().splitlines()),
               'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'rendered': False, 'status': 'failed', 'stages': {},
               'float_declarations': len(re.findall(r'\bfloat\s+\w+', source.read_text())),
               'if_statements': len(re.findall(r'\bif\s*\(', source.read_text()))}
        stage = 'Shady'
        try:
            asm, binary = OUT / (stem + '.spvasm'), OUT / (stem + '.spv')
            result, elapsed = run('build/shady', source, '-o', asm)
            row['stages'][stage] = elapsed
            row['compiler_stderr'] = result.stderr
            stage = 'Shady assembly/validation'
            run('spirv-as', '--target-env', 'vulkan1.0', asm, '-o', binary)
            run('spirv-val', '--target-env', 'vulkan1.0', binary)
            row['shady_spirv_bytes'] = binary.stat().st_size
            row['shady_instruction_lines'] = sum(bool(s.strip()) and not s.startswith(';')
                                                  for s in asm.read_text().splitlines())
            row['selects'] = asm.read_text().count('OpSelect ')
            ref = OUT / (stem + '-reference.frag')
            body = re.sub(r'\brsq\b', 'inversesqrt', source.read_text())
            ref.write_text('#version 450\nlayout(location=0) out vec4 fragColor;\nvoid main()\n'
                           + body.replace('gl_FragColor', 'fragColor'))
            stage = 'glslang'
            _, elapsed = run('glslangValidator', '-V', ref, '-o', ref.with_suffix('.spv'))
            row['stages'][stage] = elapsed
            run('spirv-val', '--target-env', 'vulkan1.0', ref.with_suffix('.spv'))
            run('spirv-dis', ref.with_suffix('.spv'), '-o', ref.with_suffix('.spvasm'))
            row['reference_spirv_bytes'] = ref.with_suffix('.spv').stat().st_size
            row['status'] = 'validated'
            if not stem.startswith('probe_'):
                stage = 'Vulkan render'
                for spv in [binary, ref.with_suffix('.spv')]:
                    result, elapsed = run('build/render', spv, 'tests/assets/teapot.obj',
                                          spv.with_suffix('.png'), timeout=120)
                    row['stages'][spv.stem + ' render'] = elapsed
                    device = next(s for s in result.stdout.splitlines() if 'using device:' in s)
                a, b = Image.open(binary.with_suffix('.png')).convert('RGB'), Image.open(ref.with_suffix('.png')).convert('RGB')
                diff = ImageChops.difference(a, b)
                maximum = max(high for low, high in diff.getextrema())
                histogram = diff.histogram()
                mean = sum((i % 256) * n for i, n in enumerate(histogram)) / (800 * 600 * 3)
                row.update(rendered=True, max_rgb_error=maximum, mean_rgb_error=mean,
                           status='matches reference' if maximum <= 1 else 'render differs')
                diff.point(lambda v: min(255, v * 32)).save(OUT / (stem + '-diff.png'))
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            row.update(status='failed', failed_stage=stage, error=str(error))
        rows.append(row)
        print(f"{stem}: {row['status']}" + (f" (max {row['max_rgb_error']}/255)" if row['rendered'] else ''), flush=True)
    unchanged = before == hashes()
    report = {'device': device, 'compiler_and_renderer_unchanged': unchanged,
              'note': 'Compile/validation times are one wall-clock sample, not benchmarks. Size/depth probes are not rendered.',
              'versions': {t: run(t, '--version')[0].stdout.splitlines()[0]
                           for t in ['spirv-as', 'spirv-val', 'glslangValidator']},
              'hashes': before, 'results': rows}
    (OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    assert unchanged, 'Compiler or renderer changed during stress run'
    rendered = [row for row in rows if row['rendered']]
    for row in rows:
        stem = Path(row['shader']).stem
        title = stem.replace('_', ' ')
        images = ''
        if row['rendered']:
            images = '<div class="panels">' + ''.join(
                f'<figure><a href="{stem}{suffix}.png"><img src="{stem}{suffix}.png" alt="{label}: {title}"></a><figcaption>{label}</figcaption></figure>'
                for suffix, label in [('', 'Shady'), ('-reference', 'glslang reference'), ('-diff', 'RGB difference x32')]) + '</div>'
        cards.append(f'<article><h2>{escape(title)}</h2><p>{escape(row["status"])} | {row["lines"]:,} source lines | '
                     f'{row.get("shady_instruction_lines", 0):,} Shady SPIR-V instructions | {row.get("selects", 0):,} selects</p>'
                     + (f'<p>Max RGB error: {row["max_rgb_error"]}/255; mean: {row["mean_rgb_error"]:.5f}/255.</p>' if row['rendered'] else '')
                     + images + '<p>' + ' | '.join(f'<a href="{stem}{suffix}.spvasm">{label} assembly</a>' for suffix, label in [('', 'Shady'), ('-reference', 'Reference')] if (OUT / (stem + suffix + '.spvasm')).exists()) + '</p>'
                     + f'<details><summary>Source / diagnostics</summary><pre>{escape(row.get("error", ""))}\n{escape((SOURCES / row["shader"]).read_text())}</pre></details></article>')
    (OUT / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shady / shader stress lab</title>
<style>body{background:#0d121b;color:#e4eaf0;font:16px/1.5 system-ui;margin:32px auto;padding:0 24px;max-width:1500px}a{color:#8fb8e8}h1{font-size:36px}h2{font-size:23px}p{color:#aab8c6}article{padding:22px 0;border-top:1px solid #2a3747}.panels{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}figure{margin:0}img{width:100%}figcaption{text-align:center}pre{overflow:auto;max-height:600px;padding:16px;background:#141d29}summary{cursor:pointer}@media(max-width:800px){.panels{grid-template-columns:1fr}}</style>
<h1>Pushing the existing compiler.</h1><p>Unrolled procedural shaders compiled by Shady and glslang, independently validated, then rendered on the same teapot. No compiler, vertex shader, or renderer changes. Patterns use screen coordinates on the existing mesh; the torus is a ray-marched scene inside its silhouette. RGB differences are reported, not hidden.</p><p><a href="report.json">Measurements, diagnostics, tool versions, and unchanged-file hashes</a></p>'''
                                   + ''.join(cards) + '</html>')
    font = ImageFont.load_default(size=20)
    baseline = Image.open(ROOT / 'build/tests/01_solid_white.png').convert('RGB')
    box = ImageChops.difference(baseline, Image.new('RGB', baseline.size, baseline.getpixel((0,0)))).getbbox()
    crop = (box[0]-12, box[1]-12, box[2]+12, box[3]+12)
    for page in range((len(rendered) + 2) // 3):
        sheet = Image.new('RGB', (1400, 1150), '#0d121b')
        draw = ImageDraw.Draw(sheet)
        draw.text((28, 16), 'UNCHANGED SHADY COMPILER / STRESS SHADERS ON THE TEAPOT', font=font, fill='#e4eaf0')
        draw.text((28, 50), 'Shady', font=font, fill='#9ed5c5')
        draw.text((725, 50), 'glslang reference', font=font, fill='#8fb8e8')
        for i, row in enumerate(rendered[page * 3:page * 3 + 3]):
            stem = Path(row['shader']).stem
            draw.text((28, 100+i*345), stem[3:].replace('_',' '), font=font, fill='#e4eaf0')
            for col, suffix in enumerate(['','-reference']):
                im = Image.open(OUT/(stem+suffix+'.png')).convert('RGB').crop(crop)
                im.thumbnail((640,300),Image.Resampling.LANCZOS)
                sheet.paste(im,(28+col*697+(640-im.width)//2,135+i*345))
        sheet.save(OUT/f'preview-{page+1}.png')
    print('Gallery: ' + str(OUT/'index.html'))


if __name__ == '__main__':
    main()

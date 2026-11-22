"""create a comparison gallery and four preview images after the render test."""
from pathlib import Path
from html import escape
import json
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / 'build/tests'
OUT = ROOT / 'build/comparison'
DOCS = ROOT / 'docs/images'
BG = '#0d121b'


def gallery():
    report = json.loads((TESTS / 'comparison.json').read_text())
    rows = [row for row in report['results'] if 21 <= int(row['shader'][:2]) <= 40]
    if len(rows) != 20:
        raise ValueError('Expected 20 new verified comparison shaders (21–40)')
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    # use the same crop for both compilers. keep the full images.
    solid = Image.open(TESTS / '01_solid_white.png').convert('RGB')
    bbox = ImageChops.difference(solid, Image.new('RGB', solid.size, solid.getpixel((0, 0)))).getbbox()
    if bbox is None:
        raise ValueError('Empty mesh render')
    left, top, right, bottom = bbox
    crop = (max(0, left - 12), max(0, top - 12), min(800, right + 12), min(600, bottom + 12))
    font = ImageFont.load_default(size=19)
    small = ImageFont.load_default(size=15)
    cards = []
    for page in range(4):
        sheet = Image.new('RGB', (1200, 1390), BG)
        draw = ImageDraw.Draw(sheet)
        draw.text((28, 15), f'SHADY / GLSLANG     |     SHADERS {21 + page * 5}-{25 + page * 5}', font=font, fill='#e4eaf0')
        draw.text((28, 46), 'Shady -> SPIR-V -> Vulkan', font=small, fill='#9ed5c5')
        draw.text((625, 46), 'glslang -> SPIR-V -> Vulkan', font=small, fill='#8fb8e8')
        for i, row in enumerate(rows[page * 5: page * 5 + 5]):
            stem = Path(row['shader']).stem
            title = stem.replace('_', ' ')
            draw.text((28, 84 + i * 260), title, font=font, fill='#e4eaf0')
            for col, suffix in enumerate(('', '-reference')):
                im = Image.open(TESTS / (stem + suffix + '.png')).convert('RGB').crop(crop)
                im.thumbnail((552, 215), Image.Resampling.LANCZOS)
                sheet.paste(im, (28 + col * 597 + (552 - im.width) // 2, 116 + i * 260))
            draw.text((625, 86 + i * 260), f"max RGB error: {row['max_rgb_error']}/255", font=small, fill='#93a4b6')
        sheet.save(DOCS / f'comparison-{page + 1}.png', optimize=True)
    for row in rows:
        stem = Path(row['shader']).stem
        source = escape((ROOT / 'tests/shaders' / row['shader']).read_text())
        panels = []
        for suffix, label in [('', 'Shady'), ('-reference', 'glslang reference'), ('-diff', 'Difference ×32')]:
            panels.append(f'<figure><a href="../tests/{stem}{suffix}.png"><img loading="lazy" src="../tests/{stem}{suffix}.png" alt="{label}: {stem}"></a><figcaption>{label}</figcaption></figure>')
        cards.append(f'''<article><h2>{escape(stem.replace('_', ' '))}</h2>
<p>Max RGB error {row['max_rgb_error']}/255 · {row['different_pixels']:,} differing pixels · {row['pixels_over_tolerance']:,} pixels exceed tolerance</p>
<div class="panels">{''.join(panels)}</div>
<p><a href="../tests/{stem}.spvasm">Shady assembly</a> · <a href="../tests/{stem}.spv">Shady binary</a> · <a href="../tests/{stem}-reference.frag">Reference GLSL</a> · <a href="../tests/{stem}-reference.spvasm">Reference assembly</a> · <a href="../tests/{stem}-reference.spv">Reference binary</a></p>
<details><summary>Shader source</summary><pre>{source}</pre></details></article>''')
    document = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shady / 20 shader comparisons</title>
<style>body{{background:{BG};color:#e4eaf0;font:16px/1.5 system-ui;margin:32px auto;padding:0 24px;max-width:1500px}}a{{color:#8fb8e8}}h1{{font-size:36px}}h2{{font-size:23px}}p{{color:#aab8c6}}article{{padding:22px 0;border-top:1px solid #2a3747}}.panels{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}figure{{margin:0}}img{{width:100%;background:#101720}}figcaption{{text-align:center}}pre{{overflow:auto;padding:16px;background:#141d29}}summary{{cursor:pointer}}@media(max-width:800px){{.panels{{grid-template-columns:1fr}}}}</style>
<h1>20 shaders. Two compiler paths.</h1><p>Shady → spirv-as → spirv-val → Vulkan<br>Equivalent GLSL → glslangValidator → spirv-val → Vulkan</p>
<p>Same 800 × 600 mesh, camera, vertex shader, and device. Reference adaptation adds GLSL interface declarations and renames rsq to inversesqrt. No Shady-generated code passes through glslang. RGB tolerance: 1/255; images link to full resolution. Difference images amplify RGB error by 32.</p>
<p>{escape(report['device'])} · <a href="../tests/comparison.json">Measurements and tool versions</a></p>
{''.join(cards)}</html>'''
    (OUT / 'index.html').write_text(document)
    print(f'Gallery: {OUT / "index.html"}')
    print(f'Paired contact sheets: {DOCS}/comparison-{{1,2,3,4}}.png')


if __name__ == '__main__':
    gallery()

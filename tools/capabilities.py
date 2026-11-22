"""Render the 100 generated capability shaders with unchanged Shady and glslang.

Run tests/capabilities/generate.py first. Progress is saved after each render;
rerunning reuses results only when source/compiler hashes and artifacts match.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from html import escape
import hashlib
import json
import re
import time
from PIL import Image, ImageChops, ImageDraw, ImageFont
from stress import hashes, run, ROOT

OUT = ROOT / 'build/capabilities'
SOURCES = OUT / 'sources'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_shader(item):
    row = dict(item, rendered=False, status='failed', stages={})
    source = SOURCES / row['shader']
    row['source_sha256'] = digest(source)
    stem = source.stem
    stage = 'Shady compilation'
    try:
        asm, binary = OUT / (stem + '.spvasm'), OUT / (stem + '.spv')
        result, elapsed = run('build/shady', source, '-o', asm)
        row['stages']['Shady compilation'] = elapsed
        row['compiler_stderr'] = result.stderr
        stage = 'Shady assembly/validation'
        run('spirv-as', '--target-env', 'vulkan1.0', asm, '-o', binary)
        run('spirv-val', '--target-env', 'vulkan1.0', binary)
        assembly = asm.read_text()
        row.update(shady_spirv_bytes=binary.stat().st_size,
                   instructions=sum(bool(s.strip()) and not s.startswith(';') for s in assembly.splitlines()),
                   selects=assembly.count('OpSelect '))
        ref = OUT / (stem + '-reference.frag')
        body = re.sub(r'\brsq\b', 'inversesqrt', source.read_text())
        ref.write_text('#version 450\nlayout(location=0) out vec4 fragColor;\nvoid main()\n'
                       + body.replace('gl_FragColor', 'fragColor'))
        stage = 'Reference compilation/validation'
        _, elapsed = run('glslangValidator', '-V', ref, '-o', ref.with_suffix('.spv'))
        row['stages']['Reference compilation'] = elapsed
        run('spirv-val', '--target-env', 'vulkan1.0', ref.with_suffix('.spv'))
        run('spirv-dis', ref.with_suffix('.spv'), '-o', ref.with_suffix('.spvasm'))
        row.update(status='validated', reference_spirv_bytes=ref.with_suffix('.spv').stat().st_size,
                   binary_hashes={p.name: digest(p) for p in [binary, ref.with_suffix('.spv')]})
    except Exception as error:
        row.update(status='failed', failed_stage=stage, error=str(error))
    return row


def render_shader(row):
    stem = Path(row['shader']).stem
    try:
        for suffix in ['', '-reference']:
            binary = OUT / (stem + suffix + '.spv')
            result, elapsed = run('build/render', binary, 'tests/assets/teapot.obj',
                                  binary.with_suffix('.png'), timeout=120)
            row['stages']['Shady render' if not suffix else 'Reference render'] = elapsed
            row['device'] = next(s for s in result.stdout.splitlines() if 'using device:' in s)
        a = Image.open(OUT / (stem + '.png')).convert('RGB')
        b = Image.open(OUT / (stem + '-reference.png')).convert('RGB')
        diff = ImageChops.difference(a, b)
        red, green, blue = diff.split()
        hist = ImageChops.lighter(ImageChops.lighter(red, green), blue).histogram()
        maximum = max(high for low, high in diff.getextrema())
        mean = sum((i % 256) * n for i, n in enumerate(diff.histogram())) / (800 * 600 * 3)
        row.update(rendered=True, status='match' if maximum <= 1 else 'different',
                   max_rgb_error=maximum, mean_rgb_error=mean,
                   different_pixels=480000-hist[0], pixels_over_tolerance=480000-hist[0]-hist[1])
        diff.point(lambda v: min(255, v * 32)).save(OUT / (stem + '-diff.png'))
    except Exception as error:
        row.update(status='failed', failed_stage='Vulkan rendering', error=str(error))
    return row


def gallery(report):
    rows = report['results']
    for name in ['thumbs', 'detail']:
        (OUT / name).mkdir(exist_ok=True)
    baseline = Image.open(ROOT / 'build/tests/01_solid_white.png').convert('RGB')
    box = ImageChops.difference(baseline, Image.new('RGB', baseline.size, baseline.getpixel((0,0)))).getbbox()
    crop = (box[0]-12, box[1]-12, box[2]+12, box[3]+12)
    font = ImageFont.load_default(size=18)
    small = ImageFont.load_default(size=14)
    cards = []
    style = '''body{background:#0d121b;color:#e4eaf0;font:16px/1.5 system-ui;margin:32px auto;padding:0 24px;max-width:1600px}a{color:#9fc5f4}h1{font-size:38px;line-height:1.15}h2{font-size:20px}p{color:#aab8c6}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}.card{display:block;background:#131b27;border:1px solid #2a3747;border-radius:12px;overflow:hidden;color:inherit;text-decoration:none}.card img{width:100%;display:block}.caption{padding:12px}.caption strong{display:block}.meta{font-size:13px;color:#aab8c6}.badge{color:#9ed5c5}.different{color:#f4b96d}.failed{color:#f38d8d}.panels{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}figure{margin:0}figure img{width:100%;display:block}figcaption{text-align:center}pre{overflow:auto;max-height:650px;padding:16px;background:#141d29;font-size:12px}summary{cursor:pointer}select,input,button{background:#172333;color:#e4eaf0;border:1px solid #3a4c62;padding:10px;border-radius:6px;margin:4px 8px 16px 0;font:inherit}nav{margin:12px 0 24px}[hidden]{display:none!important}@media(max-width:1000px){.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.grid,.panels{grid-template-columns:1fr}h1{font-size:30px}}'''
    for index, row in enumerate(rows):
        stem = Path(row['shader']).stem
        if row['rendered']:
            for suffix in ['', '-reference', '-diff']:
                with Image.open(OUT / (stem + suffix + '.png')) as original:
                    im = original.convert('RGB').crop(crop)
                    im.thumbnail((680,340), Image.Resampling.LANCZOS)
                    im.save(OUT / 'thumbs' / (stem + suffix + '.png'))
        else:
            im = Image.new('RGB', (640,320), '#24161c')
            ImageDraw.Draw(im).text((24,120),'Compilation/render failed - inspect diagnostics',font=font,fill='#f38d8d')
            im.save(OUT/'thumbs'/(stem+'.png'))
        status = ('exact RGB match' if row.get('max_rgb_error') == 0 else
                  'within 1/255' if row['status']=='match' else
                  f"{row.get('pixels_over_tolerance',0):,} pixels differ >1/255" if row['rendered'] else 'failed')
        cards.append(f'<a class="card" data-family="{escape(row["family"])}" data-level="{row["complexity"]}" data-status="{row["status"]}" href="detail/{stem}.html"><img loading="lazy" src="thumbs/{stem}.png" alt="{escape(row["title"])} compiled by Shady"><div class="caption"><strong>{index+1:03} / {escape(row["title"])}</strong><span class="meta">{escape(row["family"])} · {row["complexity"]}<br>{row.get("instructions",0):,} SPIR-V instructions</span><br><span class="badge {row["status"]}">{status}</span></div></a>')
        panels = ''
        if row['rendered']:
            panels = '<div class="panels">' + ''.join(f'<figure><a href="../{stem}{suffix}.png"><img src="../thumbs/{stem}{suffix}.png" alt="{label}"></a><figcaption>{label}</figcaption></figure>' for suffix,label in [('', 'Shady'),('-reference','glslang reference'),('-diff','RGB difference x32')]) + '</div>'
        links = ' | '.join(f'<a href="../{stem}{suffix}.{extension}">{label}</a>' for suffix,extension,label in [('', 'spv', 'Shady binary'),('', 'spvasm','Shady assembly'),('-reference','frag','Reference GLSL'),('-reference','spv','Reference binary'),('-reference','spvasm','Reference assembly')] if (OUT/(stem+suffix+'.'+extension)).exists())
        previous = f'<a href="{Path(rows[index-1]["shader"]).stem}.html">Previous</a> | ' if index else ''
        following = f' | <a href="{Path(rows[index+1]["shader"]).stem}.html">Next</a>' if index+1<len(rows) else ''
        document = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(row['title'])} / Shady</title><style>{style}</style><nav>{previous}<a href="../index.html">All 100 shaders</a>{following}</nav><h1>{index+1:03} / {escape(row['title'])}</h1><p>{escape(row['family'])} · {row['complexity']} complexity<br>{escape(row['feature'])}</p><p class="badge {row['status']}">{status}</p><p>{row['lines']:,} source lines | {row.get('instructions',0):,} Shady SPIR-V instructions | {row.get('selects',0):,} selects | {row.get('shady_spirv_bytes',0):,} bytes</p>{panels}<p>{links}</p><p>Image links open original 800 × 600 renders. Previews use one shared crop. Comparison measures RGB over the entire original image.</p><details><summary>Shader source</summary><p><a href="../sources/{stem}.frag">Open source file</a></p><pre>{escape((SOURCES/row['shader']).read_text())}</pre></details><pre>{escape(row.get('error','') + row.get('compiler_stderr',''))}</pre></html>'''
        (OUT/'detail'/(stem+'.html')).write_text(document)
    sheet_links = ' | '.join(f'<a href="sheet-{i+1:02}.png">{i*10+1:03}-{i*10+10:03}</a>' for i in range(10))
    families = list(dict.fromkeys(row['family'] for row in rows))
    options = ''.join(f'<option>{escape(f)}</option>' for f in families)
    matches = sum(r['status']=='match' for r in rows)
    exact = sum(r.get('max_rgb_error')==0 for r in rows)
    rendered = sum(r['rendered'] for r in rows)
    document = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>100 shaders / Shady capabilities</title><style>{style}</style><h1>One small compiler.<br>100 procedural teapots.</h1><p>20 algorithm families, five structural variations each. {rendered}/100 rendered through unchanged Shady; {matches}/100 match glslang within 1/255 RGB ({exact} exact matches).</p><p>Every thumbnail below is Shady's actual Vulkan output. Open any card for reference/difference images, source, and SPIR-V. Families vary iteration counts, geometry, or algorithms as well as palettes. The existing renderer supplies fragment coordinates and constant color, so patterns are projected in screen space; ray-marched scenes appear inside the teapot silhouette.</p><p><a href="overview.png">All 100 in one image</a> | <a href="report.json">Full measurements and unchanged compiler hashes</a></p><details><summary>Contact sheets: ten shaders per image</summary><p>{sheet_links}</p></details><input id="search" placeholder="Search shaders" aria-label="Search shaders"><select id="family" aria-label="Filter family"><option value="">All 20 families</option>{options}</select><select id="level" aria-label="Filter complexity"><option value="">All complexity levels</option><option>Medium</option><option>High</option></select><select id="status" aria-label="Filter result"><option value="">All results</option><option value="match">Matches reference</option><option value="different">Render differs</option><option value="failed">Failed</option></select><p id="count">100 shaders</p><main class="grid">{''.join(cards)}</main><script>const ids=['search','family','level','status'];function filter(){{let count=0;document.querySelectorAll('.card').forEach(card=>{{const show=card.textContent.toLowerCase().includes(document.getElementById('search').value.toLowerCase())&&['family','level','status'].every(key=>!document.getElementById(key).value||card.dataset[key]===document.getElementById(key).value);card.hidden=!show;if(show)count++;}});document.getElementById('count').textContent=count+' shaders';}}ids.forEach(id=>document.getElementById(id).addEventListener('input',filter));</script></html>'''
    (OUT/'index.html').write_text(document)
    # The overview includes every case in catalog order, including any failures.
    overview = Image.new('RGB',(3200,2110),'#0d121b')
    draw=ImageDraw.Draw(overview)
    draw.text((20,12),'100 SHADERS / ACTUAL SHADY OUTPUT / COMPILER UNCHANGED',font=font,fill='#e4eaf0')
    for index,row in enumerate(rows):
        stem=Path(row['shader']).stem
        x,y=(index%10)*320+8,(index//10)*205+46
        im=Image.open(OUT/'thumbs'/(stem+'.png')).convert('RGB');im.thumbnail((304,160),Image.Resampling.LANCZOS)
        overview.paste(im,(x+(304-im.width)//2,y))
        draw.text((x,y+161),f'{index+1:03} '+row['title'][:27],font=small,fill='#e4eaf0')
        draw.text((x,y+179),row['complexity']+' | '+row['status'],font=small,fill='#9ed5c5' if row['status']=='match' else '#f4b96d')
    overview.save(OUT/'overview.png',optimize=True)
    for page in range(10):
        sheet=Image.new('RGB',(1440,1760),'#0d121b');draw=ImageDraw.Draw(sheet)
        draw.text((24,12),f'SHADY / SHADERS {page*10+1:03}-{page*10+10:03} / COMPILER UNCHANGED',font=font,fill='#e4eaf0')
        for i,row in enumerate(rows[page*10:page*10+10]):
            stem=Path(row['shader']).stem
            x,y=(i%2)*720+20,(i//2)*340+55
            im=Image.open(OUT/'thumbs'/(stem+'.png')).convert('RGB');im.thumbnail((680,280),Image.Resampling.LANCZOS)
            sheet.paste(im,(x+(680-im.width)//2,y))
            draw.text((x,y+285),f'{page*10+i+1:03} / '+row['title'],font=font,fill='#e4eaf0')
            draw.text((x,y+310),row['family']+' | '+row['status'],font=small,fill='#9ed5c5' if row['status']=='match' else '#f4b96d')
        sheet.save(OUT/f'sheet-{page+1:02}.png',optimize=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=hashes()
    if not (OUT/'before.json').exists():
        (OUT/'before.json').write_text(json.dumps(before,indent=2)+'\n')
    frozen=json.loads((OUT/'before.json').read_text())
    assert frozen==before, 'Compiler or renderer changed since this task started'
    catalog=json.loads((OUT/'catalog.json').read_text())
    assert len(catalog)==100
    old=json.loads((OUT/'report.json').read_text()) if (OUT/'report.json').exists() else {}
    cached={row['shader']:row for row in old.get('results',[])} if old.get('hashes')==before else {}
    results={}
    def save():
        report={'compiler_and_renderer_unchanged':before==hashes(),'hashes':before,'rgb_tolerance':1,
                'resolution':[800,600],'device':next((r['device'] for r in results.values() if r.get('device')), ''),'note':'20 algorithm families with five structural variations each. No compiler changes; all iterations explicitly unrolled. Times are individual samples, not benchmarks.',
                'results':[results[row['shader']] for row in catalog if row['shader'] in results]}
        temp=OUT/'report.tmp';temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(OUT/'report.json')
        return report
    pending=[]
    for item in catalog:
        previous=cached.get(item['shader'],{})
        stem=Path(item['shader']).stem
        good=previous.get('rendered') and previous.get('source_sha256')==digest(SOURCES/item['shader'])
        good=good and all((OUT/(stem+suffix+'.png')).exists() for suffix in ['', '-reference','-diff'])
        good=good and all((OUT/name).exists() and digest(OUT/name)==value for name,value in previous.get('binary_hashes',{}).items())
        if good:results[item['shader']]=previous
        else:pending.append(item)
    print(f'{len(results)} cached; compiling {len(pending)} shaders.',flush=True)
    render_queue=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(compile_shader,item) for item in pending]):
            row=future.result();results[row['shader']]=row
            if row['status']=='validated':render_queue.append(row)
            else:print(row['shader']+': FAILED '+row.get('error',''),flush=True)
    save()
    print(f'Compilation complete. Rendering {len(render_queue)} Shady/reference pairs.',flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(render_shader,row) for row in render_queue]):
            row=future.result();results[row['shader']]=row;save()
            print(f"{sum(r['rendered'] for r in results.values()):03}/100 {row['shader']}: {row['status']}"+(f" | max {row['max_rgb_error']}/255 | {row['pixels_over_tolerance']} pixels >1" if row['rendered'] else ' '+row.get('error','')),flush=True)
    report=save()
    assert report['compiler_and_renderer_unchanged']
    report['versions']={tool:run(tool,'--version')[0].stdout.splitlines()[0] for tool in ['spirv-as','spirv-val','glslangValidator']}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    gallery(report)
    print('Gallery: '+str(OUT/'index.html'),flush=True)


if __name__=='__main__':
    main()

"""Capture 16 surface shaders on a spherical orbit, without compiler changes.

Requires a built Shady compiler, C++17/Vulkan, glslang, SPIRV-Tools and ffmpeg.
Run from anywhere: python3 tools/build_turntables.py
"""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / 'build/turntables'
DEST = ROOT / 'docs/videos'
FRAMES, FPS = 192, 24


def run(*args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, cwd=WORK, **kwargs)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for directory in [WORK/'build',WORK/'spirv',WORK/'frames',DEST]:directory.mkdir(parents=True,exist_ok=True)
    before={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'src').iterdir() if p.is_file()}
    before['build/shady']=digest(ROOT/'build/shady')
    rows=json.loads((ROOT/'examples/turntable/catalog.json').read_text())
    run('glslangValidator','-V',ROOT/'tools/turntable.vert','-o',WORK/'build/mesh.vert.spv')
    run('spirv-val','--target-env','vulkan1.0',WORK/'build/mesh.vert.spv')
    binaries=[]
    for row in rows:
        source=ROOT/'examples/turntable'/row['shader'];stem=source.stem
        assembly=WORK/'spirv'/(stem+'.spvasm');binary=assembly.with_suffix('.spv')
        run(ROOT/'build/shady',source,'-o',assembly)
        run('spirv-as','--target-env','vulkan1.0',assembly,'-o',binary)
        run('spirv-val','--target-env','vulkan1.0',binary)
        binaries.append(binary)
        row.update(source_sha256=digest(source),spirv_sha256=digest(binary),
                   instructions=sum(bool(s.strip()) and not s.startswith(';') for s in assembly.read_text().splitlines()))
    # Reuse the existing renderer in an isolated build. firstInstance selects
    # the orbit angle in the vertex shader; no fragment or compiler changes.
    renderer=(ROOT/'tools/render.cpp').read_text().split('int main(int argc, char **argv)')[0]
    renderer=renderer.replace('vkCmdDraw(commandBuffer, vertices.size(), 1, 0, 0);',
                              'vkCmdDraw(commandBuffer, vertices.size(), 1, 0, frame_index);')
    raw_writer = '''
static int write_frame(const char *path, int width, int height, int, const void *data, int) {
    const auto *rgba = static_cast<const unsigned char *>(data);
    std::vector<unsigned char> rgb(width * height * 3);
    for (int i = 0; i < width * height; i++)
        for (int c = 0; c < 3; c++) rgb[i * 3 + c] = rgba[i * 4 + c];
    std::ofstream frame(path, std::ios::binary);
    frame << "P6\\n" << width << " " << height << "\\n255\\n";
    frame.write(reinterpret_cast<const char *>(rgb.data()), rgb.size());
    return frame.good();
}
'''
    renderer = renderer.replace('class VulkanRenderer {', raw_writer + '\nclass VulkanRenderer {')
    renderer = renderer.replace('stbi_write_png(path, width, height, 4, data, width * 4)',
                                'write_frame(path, width, height, 4, data, width * 4)')
    capture='''
int main(int argc, char **argv) {
    auto vertices = load_obj(argv[1]);
    for (int material = 3; material < argc; material++) {
        auto folder = std::filesystem::path(argv[2]) / std::filesystem::path(argv[material]).stem();
        std::filesystem::create_directories(folder);
        VulkanRenderer renderer(384, 288);
        renderer.init(); renderer.upload_vertices(vertices); renderer.create_pipeline(argv[material]);
        for (frame_index = 0; frame_index < 192; frame_index++) {
            char name[24]; snprintf(name, sizeof(name), "%04u.ppm", frame_index);
            renderer.render(); renderer.save_png((folder / name).c_str());
            VK_CHECK(vkResetCommandPool(renderer.device, renderer.commandPool, 0));
        }
        std::cout << "VIDEO " << folder.filename().string() << std::endl;
    }
}
'''
    (WORK/'capture.cpp').write_text('#include <filesystem>\nstatic unsigned frame_index = 0;\n'+renderer+capture)
    run('c++','-O2','-std=c++17','-I'+str(ROOT/'tests/vendor'),WORK/'capture.cpp','-lvulkan','-o',WORK/'capture')
    with (WORK/'capture.log').open('w') as log:
        process=subprocess.Popen([str(WORK/'capture'),str(ROOT/'tests/assets/teapot.obj'),str(WORK/'frames'),*map(str,binaries)],cwd=WORK,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
        for line in process.stdout:
            log.write(line)
            if line.startswith('VIDEO '):print(line.strip(),flush=True)
        if process.wait():raise RuntimeError('Capture failed; inspect build/turntables/capture.log')
    for row in rows:
        stem=Path(row['shader']).stem
        run('ffmpeg','-hide_banner','-loglevel','error','-y','-framerate',FPS,'-i',WORK/'frames'/stem/'%04d.ppm',
            '-c:v','libx264','-crf','22','-preset','slow','-pix_fmt','yuv420p','-movflags','+faststart','-an',DEST/(stem+'.mp4'))
        run('ffmpeg','-hide_banner','-loglevel','error','-y','-i',DEST/(stem+'.mp4'),'-frames:v','1',DEST/(stem+'.jpg'))
        row.update(video=stem+'.mp4',poster=stem+'.jpg',bytes=(DEST/(stem+'.mp4')).stat().st_size)
    inputs=[]
    for row in rows:inputs.extend(['-i',DEST/row['video']])
    layout='|'.join(f'{i%8*384}_{i//8*288}' for i in range(16))
    run('ffmpeg','-hide_banner','-loglevel','error','-y',*inputs,'-filter_complex',f'xstack=inputs=16:layout={layout}',
        '-c:v','libx264','-crf','23','-preset','slow','-pix_fmt','yuv420p','-movflags','+faststart','-an',DEST/'teapots-2x8.mp4')
    run('ffmpeg','-hide_banner','-loglevel','error','-y','-i',DEST/'teapots-2x8.mp4','-frames:v','1',DEST/'teapots-2x8.jpg')
    run('ffmpeg','-hide_banner','-loglevel','error','-y','-i',DEST/'teapots-2x8.mp4','-filter_complex',
        'fps=10,scale=1536:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=3',
        '-loop','0',DEST/'teapots-2x8.gif')
    assert all(digest(ROOT/name)==value for name,value in before.items())
    manifest=dict(rows=2,columns=8,frames=FRAMES,fps=FPS,duration_seconds=FRAMES/FPS,width=384,height=288,
                  method='Shady fragment programs; object-space coordinates and camera-space mesh normals; 360-degree azimuth with gently varying elevation; Vulkan capture.',
                  compiler_unchanged=True,compiler_hashes=before,materials=rows)
    (DEST/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Wrote 16 seamless surface-material clips, grid MP4, GIF, and posters.',flush=True)


if __name__=='__main__':main()

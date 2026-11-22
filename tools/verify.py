"""validate shader binaries. compare vulkan renders with glslang if requested."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "tests"
OUT.mkdir(parents=True, exist_ok=True)


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], cwd=ROOT, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, **kwargs)


def verify(render=False):
    shaders = sorted((ROOT / "tests/shaders").glob("*.frag"))
    results = []
    device = ""
    for shader in shaders:
        asm = OUT / (shader.stem + ".spvasm")
        binary = asm.with_suffix(".spv")
        run("build/shady", shader, "-o", asm)
        run("spirv-as", "--target-env", "vulkan1.0", asm, "-o", binary)
        run("spirv-val", "--target-env", "vulkan1.0", binary)
        if render:
            from PIL import Image, ImageChops
            reference = OUT / (shader.stem + "-reference.frag")
            source = shader.read_text().replace("gl_FragColor", "fragColor")
            source = re.sub(r"\brsq\b", "inversesqrt", source)
            source = source.replace("gl_Color", "inColor").replace("gl_TexCoord", "inTexCoord")
            reference.write_text("#version 450\n"
                                 "layout(location=0) in vec4 inColor;\n"
                                 "layout(location=1) in vec4 inTexCoord;\n"
                                 "layout(location=0) out vec4 fragColor;\n"
                                 "void main()\n" + source)
            ref_binary = reference.with_suffix(".spv")
            run("glslangValidator", "-V", reference, "-o", ref_binary)
            run("spirv-val", "--target-env", "vulkan1.0", ref_binary)
            run("spirv-dis", ref_binary, "-o", reference.with_suffix(".spvasm"))
            image = asm.with_suffix(".png")
            ref_image = OUT / (shader.stem + "-reference.png")
            for spv, png in [(binary, image), (ref_binary, ref_image)]:
                result = run("build/render", spv, "tests/assets/teapot.obj", png)
                if shader == shaders[0] and spv == binary:
                    for line in result.stdout.decode().splitlines():
                        if "using device:" in line:
                            device = line
                            print(line, flush=True)
            diff = ImageChops.difference(Image.open(image).convert("RGB"),
                                        Image.open(ref_image).convert("RGB"))
            maximum = max(high for low, high in diff.getextrema())
            pixels = list(diff.get_flattened_data() if hasattr(diff, "get_flattened_data")
                          else diff.getdata())
            results.append({
                "shader": shader.name,
                "source_sha256": hashlib.sha256(shader.read_bytes()).hexdigest(),
                "max_rgb_error": maximum,
                "mean_rgb_error": sum(sum(p) for p in pixels) / (len(pixels) * 3),
                "different_pixels": sum(any(p) for p in pixels),
                "pixels_over_tolerance": sum(max(p) > 1 for p in pixels),
                "shady_spirv_bytes": binary.stat().st_size,
                "reference_spirv_bytes": ref_binary.stat().st_size,
                "passed": maximum <= 1,
            })
            diff.point(lambda v: min(255, v * 32)).save(OUT / (shader.stem + "-diff.png"))
        passed = not render or results[-1]["passed"]
        print(f"{'PASS' if passed else 'FAIL'} {shader.name}" +
              (f" (max RGB error {maximum}/255)" if render else ""), flush=True)

    if render:
        report = {
            "device": device,
            "resolution": [800, 600],
            "rgb_tolerance": 1,
            "pipelines": {
                "shady": "MiniGLSL -> Shady -> spirv-as -> spirv-val -> Vulkan -> PNG",
                "reference": "same source with GLSL interface wrapper and rsq renamed to inversesqrt -> glslangValidator -V -> spirv-val -> Vulkan -> PNG",
            },
            "versions": {tool: run(tool, "--version").stdout.decode().splitlines()[0]
                         for tool in ("spirv-as", "spirv-val", "glslangValidator")},
            "results": results,
        }
        (OUT / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
        failures = [row["shader"] for row in results if not row["passed"]]
        if failures:
            raise AssertionError(f"Render differences exceed 1/255: {', '.join(failures)}")

    # require compilation errors to stop output and return failure.
    errors = {
        "syntax": "{ gl_FragColor = ; }",
        "undefined": "{ gl_FragColor = missing; }",
        "type": "{ float x = vec4(1.0, 0.0, 0.0, 1.0); }",
        "unterminated comment": "{/* never closed",
        "trailing syntax": "{ gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); } garbage",
        "duplicate declaration": "{ float x = 0.0; float x = 1.0; }",
    }
    for function in ("sin", "cos", "fract", "abs"):
        for argument in ("", "0.5, 1.0", "1", "true", "vec2(0.0, 1.0)"):
            errors[f"{function}({argument})"] = "{ float x = " + function + "(" + argument + "); }"
    for name, source in errors.items():
        result = subprocess.run([str(ROOT / "build/shady")], input=source,
                                text=True, capture_output=True, cwd=ROOT, timeout=5)
        assert result.returncode != 0, f"{name}: accepted invalid input"
        assert not result.stdout, f"{name}: leaked output after error"
        print(f"PASS rejects {name} error")
    # check that a large scope does not fill the table and stop insertion.
    large_source = "{" + "".join(f"float v{i} = 0.0;" for i in range(350))
    large_source += "gl_FragColor = vec4(v349, 0.0, 0.0, 1.0); }"
    large = OUT / "large-scope.spvasm"
    result = run("build/shady", input=large_source.encode())
    large.write_bytes(result.stdout)
    run("spirv-as", "--target-env", "vulkan1.0", large, "-o", large.with_suffix(".spv"))
    run("spirv-val", "--target-env", "vulkan1.0", large.with_suffix(".spv"))
    print("PASS scope with 350 variables")
    print(f"{len(shaders)} shaders, {len(errors)} error cases, and large-scope regression passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()
    try:
        verify(args.render)
    except subprocess.CalledProcessError as error:
        print(error.stdout.decode(errors="replace"))
        print(error.stderr.decode(errors="replace"))
        raise SystemExit(f"Failed: {' '.join(map(str, error.cmd))}")

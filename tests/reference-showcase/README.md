# Five-function reference previews

Eight procedural fragment shaders illustrating a possible small extension:
`sin`, `cos`, `fract`, `abs`, and `smoothstep`, using scalar floats only.
Other expressions use arithmetic and a final `vec4` constructor. There are no
textures, loops, user functions, noise built-ins, or animation inputs.

These remain **reference-only previews**: Shady supports `sin`, `cos`, `fract`,
and `abs`, but these sources also require the unsupported `smoothstep` function.
They use its block-style format so they can become compiler examples later.

From the repository root:

```sh
python3 tools/reference_showcase.py
```

The script adds a GLSL 450 wrapper, compiles with glslang, validates SPIR-V, and
renders at 800 × 600 through Vulkan. It builds an isolated copy of the existing
renderer under `build/reference-showcase/`, using a fullscreen vertex shader.
It does not change compiler sources or the usual renderer/vertex shader binaries.

Open `build/reference-showcase/index.html` for images, GLSL sources, and SPIR-V
assembly. Tool versions and the rendering device are in `report.json`. The two
`preview-*.png` files show four shaders each; individual PNGs are full resolution.

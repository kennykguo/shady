# Existing-compiler stress examples

Six visual shaders and nine compile-only probes, using the current Shady
compiler without changing compiler or renderer code. All shader iterations are
written out explicitly by the generator. This does not add loop support.

```sh
make build/shady build/render build/mesh.vert.spv
python3 tests/stress/generate.py
python3 tools/stress.py
```

Open `build/stress/index.html` for Shady/reference renders, difference images,
source, assembly, and diagnostics. `report.json` records sizes, instruction
counts, tool versions, and hashes confirming the compiler/renderer were unchanged
during the run. Source and build products stay under `build/stress/` so thousands
of generated shader lines do not become project source to maintain.

The reference path adds a GLSL interface and renames `rsq` to `inversesqrt`.
Both modules are validated against Vulkan 1.0 and use the same existing teapot,
vertex shader, camera, and 800 x 600 Vulkan renderer on an RTX 3060.
Patterns use fragment coordinates projected onto the teapot. The ray-marched
object is a separate scene drawn inside the silhouette, rather than a change
to the mesh or its lighting inputs.

## Observed results

| Shader | Stress feature | Source lines | Shady SPIR-V instructions | Max RGB error |
| --- | --- | ---: | ---: | ---: |
| Warped lapis | 12 coupled domain-warp layers | 81 | 547 | 0/255 |
| Voronoi enamel | 9 neighbor samples; nearest and second-nearest tracking | 125 | 899 | 0/255 |
| Inversion filigree | 24 inversion/fold iterations with accumulated orbit traps | 206 | 1,795 | 1/255 |
| Nested inlays | 32 nested conditional scopes; 128 selects | 203 | 1,253 | 0/255 |
| Mandelbrot | 96 iterations with nested escape predicates; 483 selects | 789 | 4,849 | 249/255 at 23 pixels |
| Ray-marched torus | 256 steps, displaced distance field, six normal samples; 517 selects | 3,701 | 29,442 | 0/255 |

All six compiled, passed SPIR-V validation, and rendered. Five matched the
reference within the usual 1/255 RGB tolerance. The largest rendered Shady
module was 510,668 bytes. The original renders are retained even when they differ.

The Mandelbrot difference affected 23 of 480,000 pixels. Diagnostic copies of
both SPIR-V modules, with `NoContraction` applied to floating-point additions,
subtractions, and multiplications, produced identical RGB images. This points
to sensitivity to floating-point contraction across many iterations. These
annotations were only applied to diagnostic copies; the compiler and gallery
originals were not changed. That extra check is saved in this run's
`build/stress/mandelbrot-diagnostics.json`.

## Observed size and depth bounds

- A dependency chain of 16,384 generated float variables (plus two coordinate
  variables) compiled and validated through both toolchains. Shady emitted
  98,367 instructions in a 1,704,976-byte module. This probe was not GPU-rendered.
- An expression containing 4,096 nested `sin` calls compiled and validated
  through both toolchains. It was not GPU-rendered.
- At 8,192 nested calls, Shady stopped with `PARSER ERROR ... memory exhausted`.
  It returned failure; no compiler fix was attempted. That case does not reach
  the reference stage in the runner.

These are observed passing/failing cases, not an exact maximum supported shader
size or nesting depth. The probes are bounded experiments, and recorded compile
times are individual wall-clock samples rather than performance benchmarks.

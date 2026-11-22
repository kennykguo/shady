# 100 shader capability gallery

Twenty algorithm families, each with five structural variations. The variations
change iteration counts, geometry, view parameters, or field construction as
well as palettes. These are 100 shader programs, not 100 unrelated algorithms.
They use the current float/vector/conditional subset and scalar math built-ins.

```sh
make build/shady build/render build/mesh.vert.spv
python3 tests/capabilities/generate.py
python3 tools/capabilities.py
```

Open `build/capabilities/index.html`. It shows every Shady render and lets you
filter by family, complexity, or comparison result. Each shader's page includes
reference and amplified difference images, the actual source, SPIR-V assembly,
and binary downloads. Original renders are 800 x 600; gallery thumbnails use
one shared crop around the teapot. `overview.png` shows all 100 outputs;
`sheet-01.png` through `sheet-10.png` provide larger groups of ten.

The generator and runner live outside the compiler. All generated shader source,
SPIR-V, reports, and images stay under `build/capabilities/`. The runner snapshots
compiler/renderer source and executable hashes and checks they remain unchanged.
The first snapshot is retained in `before.json`; use a fresh output directory if
intentionally testing a different compiler version later.

Both compiler paths compile the same logic independently. The reference wrapper
adds GLSL 450 inputs/output and `main`, and renames `rsq` to `inversesqrt`.
Both outputs are validated against Vulkan 1.0, then rendered using the unchanged
teapot, vertex shader, camera, and Vulkan driver. Only the shader programs vary.

The existing vertex shader does not expose useful surface normals or UVs, so
these are patterns projected using fragment coordinates. The five ray-marched
scenes render inside the teapot silhouette. This is not a test of textured
materials, mesh lighting, or full GLSL support. Iterations are explicitly
written out by the generator; the compiler still has no loops or user functions.

A maximum RGB error of 1/255 is accepted. Larger differences remain visible and
labeled in the gallery; they are never removed or replaced with reference output.
`report.json` includes exact source hashes, binary sizes, instruction/select
counts, per-image differences, and tool versions. Execution times are individual
wall-clock samples and are not GPU or compiler benchmarks.

The runner saves progress after each render. A rerun reuses completed pairs only
when the source and compiler hashes and required image/binary artifacts match.

## Results of this run

All 100 shaders compiled, validated, and rendered through both toolchains on
an NVIDIA GeForce RTX 3060. Shady compiler and renderer hashes stayed unchanged.
The generator labels 32 examples medium complexity and 68 high complexity;
these are qualitative categories, with exact source/instruction counts shown
in each shader page. Source lengths range from 38 to 1,315 lines and Shady
modules range from 313 to 16,650 SPIR-V instructions.

79 pairs had identical RGB pixels; another 12 were within 1/255. Nine
Mandelbrot/Julia cases exceeded that tolerance at 4 to 137 pixels per image
(267 pixels across the nine pairs). These remain labeled as differences;
this run does not diagnose the cause for every differing pixel.

| Family | Examples | Within 1/255 | Instruction range |
| --- | ---: | ---: | ---: |
| Domain warping | 5 | 5 | 351–607 |
| Wave interference | 5 | 5 | 410–610 |
| Voronoi cells | 5 | 5 | 963–2,175 |
| Truchet mosaics | 5 | 5 | 343–370 |
| Gyroid sections | 5 | 5 | 456–704 |
| Organic grain | 5 | 5 | 388–468 |
| Noise terrain | 5 | 5 | 868–1,536 |
| Woven materials | 5 | 5 | 313–325 |
| Coupled fields | 5 | 5 | 888–1,768 |
| Geometric inlays | 5 | 5 | 394–478 |
| Kaleidoscope folds | 5 | 5 | 694–1,246 |
| Inversion fractals | 5 | 5 | 1,102–2,722 |
| Deep conditional inlays | 5 | 5 | 591–1,551 |
| Recursive circuitry | 5 | 5 | 1,117–1,997 |
| Mandelbrot fractals | 5 | 0 | 4,029–9,693 |
| Julia fractals | 5 | 1 | 4,025–9,689 |
| Burning ship fractals | 5 | 5 | 4,670–11,294 |
| Volume integration | 5 | 5 | 3,532–6,914 |
| Ray-marched scenes | 5 | 5 | 6,729–16,650 |
| Nonlinear orbit traps | 5 | 5 | 2,245–5,061 |

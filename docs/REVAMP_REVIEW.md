# Cleanup review and shader comparison

This review compares the existing, uncommitted cleanup with commit `22dfd09`
(`file structure change, and cleanup`). It separates that earlier work from
changes made for the 20 additional shader comparisons. The existing cleanup was
already present when this comparison task started.

## What the earlier cleanup changed

| Area | Change beyond renaming/removing course references |
| --- | --- |
| Build | One root Makefile builds the compiler, generated Flex/Bison files, renderer, and vertex shader under `build/`. Generated binaries and objects are ignored rather than checked in. Adds formatting commands and a shared clang-format style. |
| Driver | Replaces the old driver with `src/main.c`: stdin/file input, `-o`, `--ast`, and help. Parsing and semantic errors return failure and prevent code generation. The old driver could return success on errors and write `Failed to compile` into the output stream. |
| Scanner | Fixes unterminated block comments: Flex's `input()` signals EOF with zero; the old code checked stdio's EOF value and could loop forever. Resets `errno` before number parsing. |
| Parser/memory | Adds detailed parser errors and destructors for discarded tokens/AST nodes. Frees temporary list nodes and clarifies ownership of the completed AST. The grammar and overall AST design are largely retained. |
| Symbol table | Replaces the fixed 101-slot table with a growing table. This fixes insertion hangs when a scope fills up. The regression uses 350 variables. |
| Vulkan output | Changes the fragment execution mode from `OriginLowerLeft` to `OriginUpperLeft`, and flips the vertex projection's Y sign to match. |
| Built-ins | Removes legacy light/material/environment uniforms and other built-ins that the renderer did not supply. This reduces the advertised subset; old shaders using those names no longer pass semantic checking. |
| Renderer | Consolidates and hardens the existing offscreen Vulkan renderer in `tools/render.cpp`. Checks SPIR-V input, OBJ input, and PNG writing; removes the unused GLFW dependency. This is an adaptation of the existing renderer, not a new graphics engine. |
| Verification/docs | Adds `tools/verify.py`, negative cases, large-scope validation, and same-renderer comparisons against glslang. Replaces the previous collection of docs with a short README and generated diagrams/montage. Removes archived project stages, demos, and checked-in build/render output. |

This was mostly a usability, build, and correctness cleanup. It did **not** add
full GLSL, loops, textures, user-defined functions, or new shader stages.
Predicated `if/else` lowering with `OpSelect` was already present.

## Changes for this request

- Adds exactly 20 shaders, `tests/shaders/21_*.frag` through `40_*.frag`.
- Compiles the same shader logic through Shady and glslang independently.
- Validates both SPIR-V binaries and saves both assembly listings, original-size
  PNGs, amplified differences, and machine-readable RGB measurements.
- Adds `make comparison` and `tools/comparison.py` to produce a local HTML gallery
  and four paired contact sheets. These tools live outside the compiler.
- Fixes one small backend issue needed by shaders 39 and 40: `rsq` now emits
  `InverseSqrt` as the extended-instruction name. Previously it emitted `32`,
  which `spirv-as` rejected. There is no language or architecture expansion.

The compiler remains the existing scanner/parser/AST/checker/code-generator
project. Other bugs are deliberately left for future work, per the requested
small, novice-readable scope.

## Known bugs left unfixed

These were checked with small programs during this task. Acceptance by the
parser/checker does not guarantee valid SPIR-V or correct rendering.

| Feature | Reproduction / observed result |
| --- | --- |
| Integer or boolean locals | `int n = 1;` or `bool b = true;` passes Shady but emits an undefined function-pointer type; `spirv-val` rejects it. |
| `dp3` / `lit` | Both emit invalid numeric extended-instruction names (`16` / `18`); assembly fails. They also need their actual lowering checked, rather than just renaming the emitted instruction. |
| Power operator | `float x = 0.5 ^ 2.0;` passes checking but emits an invalid ID (`-1`); assembly fails. |
| `vec2` component writes | `vec2 v = vec2(0.0, 0.0); v[0] = 0.5;` uses a hard-coded vec4 load/insert path; validation fails. |
| Declarations in ordinary nested blocks | Function-local `OpVariable` instructions can appear after executable instructions; validation fails. |
| Declarations inside conditional blocks | The branch visitor skips declarations. A use of the declared variable can print an error while compilation still succeeds, silently dropping the assignment. The resulting module may validate despite rendering incorrectly. |
| Declarations interleaved with assignments | The AST separates declarations from statements, moving initializer evaluation ahead of earlier assignments. The module validates but can render the wrong value. |

For example, this statement-order case should render red, but Shady initializes
`y` before `x = 1.0` and renders black:

```glsl
{
    float x = 0.0;
    x = 1.0;
    float y = x;
    gl_FragColor = vec4(y, 0.0, 0.0, 1.0);
}
```

The reference-render comparison measured a maximum RGB error of 255/255 for
that case. This conditional-declaration case silently loses the red assignment
and measured 204/255:

```glsl
{
    vec4 c = vec4(0.0, 0.0, 0.0, 1.0);
    if (gl_FragCoord[0] > 400.0) {
        float v = 0.8;
        c = vec4(v, 0.0, 0.0, 1.0);
    }
    gl_FragColor = c;
}
```

Raw probe sources, diagnostics, and two reference-render comparisons from this
run are under `build/probes/`. That directory is disposable; the reproductions
above describe the issues independently of those artifacts. The 20 new gallery
shaders use supported paths; they are examples, not proof that these bugs are fixed.

## Reproduce and inspect

```sh
make test
make comparison
# Open build/comparison/index.html
```

The two paths are:

```text
MiniGLSL → Shady → SPIR-V assembly → spirv-as → spirv-val → Vulkan → PNG
same logic + GLSL interface → glslangValidator -V → spirv-val → Vulkan → PNG
```

The reference wrapper maps `gl_FragColor`, `gl_Color`, and `gl_TexCoord` to explicit
GLSL 450 inputs/output, adds `main`, and renames `rsq` to `inversesqrt`. Shady's
fragment output never passes through glslang. Both paths share the reference-
compiled vertex shader, teapot mesh, camera, resolution, and Vulkan driver.

The HTML gallery shows shaders 21–40. `build/tests/comparison.json` includes all
40 shaders, exact source hashes, tool versions, binary sizes, and RGB errors.
Comparisons cover all 800 × 600 pixels, including the background; the error
threshold is 1/255 per RGB channel. Alpha is not part of the comparison metric.
Contact sheets crop a common mesh bounding box for readability; original PNGs
remain available in the gallery. Results describe this fixed scene and device,
not compiler performance or arbitrary GLSL conformance.

## Results of this run

All 40 shaders (the original 20 plus the new 20) passed both compilation paths
and produced **identical RGB pixels** on the NVIDIA GeForce RTX 3060. Maximum
RGB error was **0/255 for every pair**. The six error-rejection cases, the
350-variable scope regression, and the source formatting check also passed.

The 20 added shaders therefore produced 40 new full-resolution renders. This
does not cover the intentionally unfixed cases listed above.

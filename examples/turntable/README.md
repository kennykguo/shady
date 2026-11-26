# Varied surface materials

Sixteen small, visually distinct fragment programs using Shady's existing float arithmetic, scalar
`sin`/`cos`/`fract`/`abs`, vector indexing, conditionals, and inverse square root. The collection
varies palettes, spatial structure, and material response instead of applying
the same rainbow palette to different fields. Broad gradients sit alongside
pearl sheen, copper patina, lava veins, cobalt marbling, mineral bands, geometric
panels, enamel droplets, foil, velvet rims, brushed metal, and neon contours. There
are no loops, textures, or new language features.

The orbit vertex shader passes object coordinates through `gl_TexCoord` and
encoded camera-space mesh normals through `gl_Color`. Each fragment program
colors the actual surface and calculates diffuse/specular light from its normals.
This keeps the patterns attached during rotation instead of projecting a separate
scene inside a flat silhouette. The vertex shader is compiled by glslang; every
fragment program is compiled by Shady, assembled, and validated for Vulkan 1.0.

Rebuild all clips and the README preview with:

```sh
make build/shady
python3 tools/build_turntables.py
```

The capture tool builds an isolated adaptation of the existing renderer under
`build/turntables/`. The compiler and ordinary renderer sources remain unchanged.
A full orbit contains 192 frames at 24 fps (eight seconds), with a gentle change
in elevation. Frames are lossless intermediate PPM files; FFmpeg encodes silent
H.264 MP4s with fast-start metadata and a smaller animated GIF for GitHub.

Outputs are in `docs/videos/`: sixteen individual clips/posters, the two-row,
eight-column combined MP4, its GIF preview/poster, and `manifest.json` recording
compiler/source/binary hashes and instruction counts. Raw frames stay in `build/`.

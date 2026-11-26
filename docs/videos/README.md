# Orbiting surface materials

The sixteen numbered MP4s are silent, 384 × 288, 24 fps, eight-second loops.
`teapots-2x8.mp4` combines them in two rows of eight. The GIF is the smaller,
autoplaying README preview; the JPEGs are first-frame video posters.

The sixteen clips vary both color palettes and surface structure, including
gradients, marbling, patina, enamel, patterns, and view-dependent sheen.

All fragment programs are compiled by Shady and validated for Vulkan 1.0. The
camera and object-coordinate/normal inputs come from `tools/turntable.vert`,
compiled by glslang. The original compiler and renderer are unchanged. See
`examples/turntable/README.md` for the surface mapping and rebuild command.

`manifest.json` records the shader sources, SPIR-V hashes, dimensions, timing,
and compiler hashes. The website uses the same individual MP4s with autoplay,
muted audio, looping, and inline playback.

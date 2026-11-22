{
    // Moire satin: two fine wave families create broad interference bands.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float a = sin(53.0 * x + 8.0 * sin(2.0 * y));
    float b = sin(51.0 * (0.96 * x + 0.28 * y) + 7.0 * cos(2.0 * x));
    float weave = 0.5 + 0.5 * a * b;
    float sheen = smoothstep(0.2, 0.9, weave);
    float fold = 0.5 + 0.5 * sin(3.0 * x + 2.0 * sin(2.0 * y));
    float r = 0.06 + sheen * (0.25 + 0.6 * fold);
    float g = 0.035 + sheen * (0.55 - 0.25 * fold);
    float blue = 0.12 + sheen * (0.7 - 0.35 * fold);
    gl_FragColor = vec4(r, g, blue, 1.0);
}

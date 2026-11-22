{
    // combine two sets of diagonal bands.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float a = x + y;
    float b = x - y;
    float p = (a + 0.9) * (a + 0.3) * (a - 0.3) * (a - 0.9);
    float q = (b + 0.9) * (b + 0.3) * (b - 0.3) * (b - 0.9);
    vec4 color = vec4(0.9, 0.85, 0.65, 1.0);
    if (p < 0.0) color = vec4(0.15, 0.45, 0.45, 1.0);
    if (q < 0.0) color = vec4(0.12, 0.2, 0.3, 1.0);
    gl_FragColor = color;
}

{
    // draw a narrow band along a curved path.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float curve = y - 0.65 * x * x + 0.35;
    vec4 color = vec4(0.04, 0.15, 0.2, 1.0);
    if (curve > -0.16 && curve < 0.16) color = vec4(0.95, 0.35, 0.45, 1.0);
    if (curve > -0.045 && curve < 0.045) color = vec4(1.0, 0.85, 0.6, 1.0);
    gl_FragColor = color;
}

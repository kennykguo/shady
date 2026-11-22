{
    // use a cubic polynomial to mix colors. keep the mix in range.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float t = (x * x * x - x + y) * 0.5 + 0.5;
    if (t < 0.0) t = 0.0;
    if (t > 1.0) t = 1.0;
    gl_FragColor = vec4(0.1 + 0.75 * t, 0.7 - 0.5 * t, 0.85 - 0.3 * t, 1.0);
}

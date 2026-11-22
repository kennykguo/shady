{
    // combine the light from two separate centers.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float a = 1.0 / (1.0 + 12.0 * ((x + 0.5) * (x + 0.5) + y * y));
    float b = 1.0 / (1.0 + 12.0 * ((x - 0.5) * (x - 0.5) + y * y));
    gl_FragColor = vec4(0.08 + 0.9 * a, 0.08 + 0.4 * (a + b), 0.15 + 0.8 * b, 1.0);
}

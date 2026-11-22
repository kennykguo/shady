{
    // Neon interference: nested waves, thin contours, rational glow.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float field = sin(4.5 * x + 1.4 * sin(3.0 * y)) + cos(4.5 * y + 1.4 * cos(3.0 * x));
    float d = abs(sin(3.0 * field + 1.0));
    float core = 1.0 - smoothstep(0.015, 0.08, d);
    float glow = 0.018 / (0.018 + d * d);
    float palette = field * 1.4 + 0.7 * x;
    float r = 0.01 + glow * (0.5 + 0.5 * cos(palette)) + 0.3 * core;
    float g = 0.008 + glow * (0.5 + 0.5 * cos(palette + 2.1)) + 0.3 * core;
    float b = 0.035 + glow * (0.5 + 0.5 * cos(palette + 4.2)) + 0.3 * core;
    gl_FragColor = vec4(r, g, b, 1.0);
}

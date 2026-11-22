{
    // Aurora silk: layered sine ribbons and smooth fades.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float wave = sin(3.0 * x + sin(4.0 * y)) * 0.18;
    float ribbons = sin(18.0 * x + 4.0 * sin(3.0 * x) + 3.0 * y);
    float curtain = smoothstep(0.05, 0.95, 0.5 + 0.5 * ribbons);
    float height = 1.0 / (1.0 + 18.0 * (y - wave) * (y - wave));
    float haze = 1.0 / (1.0 + 3.0 * (y - wave) * (y - wave));
    float glow = height * (0.2 + 0.8 * curtain);
    float r = 0.015 + glow * (0.25 + 0.23 * sin(2.0 * x + 1.8)) + 0.05 * haze;
    float g = 0.025 + glow * (0.6 + 0.35 * cos(2.0 * x)) + 0.09 * haze;
    float b = 0.07 + glow * (0.65 + 0.3 * sin(2.0 * x - 1.5)) + 0.16 * haze;
    gl_FragColor = vec4(r, g, b, 1.0);
}

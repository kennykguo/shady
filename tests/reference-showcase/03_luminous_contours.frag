{
    // Luminous contours: warped height field and fract isolines.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float wx = x + 0.3 * sin(2.8 * y + 0.7 * cos(3.0 * x));
    float wy = y + 0.3 * cos(2.6 * x - 0.7 * sin(3.0 * y));
    float field = 0.4 * sin(2.5 * wx) + 0.35 * cos(3.0 * wy) + 0.15 * sin(5.0 * (wx + wy));
    float band = abs(fract(field * 8.0) - 0.5);
    float lines = 1.0 - smoothstep(0.015, 0.065, band);
    float major = 1.0 - smoothstep(0.015, 0.04, abs(fract(field * 2.0) - 0.5));
    float t = 0.5 + 0.5 * sin(2.0 * field + 0.6);
    float r = 0.015 + 0.06 * t + lines * 0.12 + major * 0.5;
    float g = 0.06 + 0.2 * t + lines * 0.45 + major * 0.5;
    float b = 0.09 + 0.25 * t + lines * 0.4 + major * 0.3;
    gl_FragColor = vec4(r, g, b, 1.0);
}

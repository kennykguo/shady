{
    // Opal cells: repeating quadratic rings with a cosine color palette.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float sx = x * 3.2;
    float sy = y * 3.2;
    float cx = fract(sx) - 0.5;
    float cy = fract(sy) - 0.5;
    float d = cx * cx + cy * cy;
    float phase = 22.0 * d + 0.6 * sin(2.0 * x + 2.0 * y);
    float rim = 1.0 - smoothstep(0.015, 0.07, abs(sin(phase * 2.0)));
    float light = 0.25 + 0.75 / (1.0 + 5.0 * d);
    float r = (0.35 + 0.35 * cos(phase + 0.3) + 0.25 * rim) * light;
    float g = (0.4 + 0.35 * cos(phase + 2.4) + 0.25 * rim) * light;
    float b = (0.5 + 0.35 * cos(phase + 4.5) + 0.25 * rim) * light;
    gl_FragColor = vec4(r, g, b, 1.0);
}

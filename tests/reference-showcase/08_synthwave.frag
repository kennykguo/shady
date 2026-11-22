{
    // Synthwave: a striped sun and perspective grid, without loops or textures.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float horizon = y - 0.12;
    float sunx = x;
    float suny = y + 0.22;
    float disc = 1.0 - smoothstep(0.2, 0.21, sunx * sunx + suny * suny);
    float stripes = smoothstep(0.16, 0.23, fract((y + 0.9) * 12.0));
    float sun = disc * stripes;
    float floorMask = smoothstep(0.12, 0.14, y);
    float depth = 0.18 / (abs(horizon) + 0.025);
    float gx = abs(fract(x * depth * 2.5) - 0.5);
    float gy = abs(fract(depth * 2.0) - 0.5);
    float gridx = 1.0 - smoothstep(0.01, 0.035, gx);
    float gridy = 1.0 - smoothstep(0.01, 0.045, gy);
    float grid = (gridx + gridy - gridx * gridy) * floorMask;
    float haze = 0.025 / (0.025 + horizon * horizon);
    float r = 0.06 + 0.2 * haze + sun * 0.85 + grid * 0.6;
    float g = 0.015 + 0.06 * haze + sun * (0.35 - 0.3 * y) + grid * 0.12;
    float b = 0.12 + 0.2 * haze + sun * 0.05 + grid * 0.8;
    gl_FragColor = vec4(r, g, b, 1.0);
}

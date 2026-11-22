{
    // Prismatic rosette: symmetry from absolute values and crossed waves.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float ax = abs(x);
    float ay = abs(y);
    float radius = x * x + y * y;
    float field = sin(9.0 * ax + 3.0 * cos(5.0 * ay)) * cos(9.0 * ay + 3.0 * sin(5.0 * ax));
    float lattice = 1.0 - smoothstep(0.025, 0.1, abs(field));
    float halo = 1.0 / (1.0 + 0.9 * radius);
    float t = field * 2.0 + radius * 2.0;
    float r = (0.12 + 0.6 * (0.5 + 0.5 * cos(t)) + 0.45 * lattice) * halo;
    float g = (0.03 + 0.35 * (0.5 + 0.5 * cos(t + 2.1)) + 0.4 * lattice) * halo;
    float b = (0.15 + 0.7 * (0.5 + 0.5 * cos(t + 4.2)) + 0.35 * lattice) * halo;
    gl_FragColor = vec4(r, g, b, 1.0);
}

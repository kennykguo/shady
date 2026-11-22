{
    // Stained glass: rotated repeating diamonds and softly outlined edges.
    float x = (gl_FragCoord[0] - 400.0) / 300.0;
    float y = (gl_FragCoord[1] - 300.0) / 300.0;
    float u = (x + y) * 2.4;
    float v = (x - y) * 2.4;
    float fu = fract(u);
    float fv = fract(v);
    float edgeu = smoothstep(0.015, 0.06, fu) * (1.0 - smoothstep(0.94, 0.985, fu));
    float edgev = smoothstep(0.015, 0.06, fv) * (1.0 - smoothstep(0.94, 0.985, fv));
    float cell = sin((u - fu) * 2.7 + (v - fv) * 5.3);
    float glass = (0.7 + 0.3 * sin(8.0 * fu) * cos(7.0 * fv)) * edgeu * edgev;
    float r = 0.025 + glass * (0.5 + 0.45 * cos(cell * 4.0));
    float g = 0.025 + glass * (0.5 + 0.45 * cos(cell * 4.0 + 2.1));
    float b = 0.035 + glass * (0.5 + 0.45 * cos(cell * 4.0 + 4.2));
    gl_FragColor = vec4(r, g, b, 1.0);
}

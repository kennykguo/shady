{
    // start with a color vector. change selected components inside each band.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec4 color = vec4(0.15, 0.2, 0.3, 1.0);
    if (x > -0.4 && x < 0.4) { color[0] = 0.95; color[1] = 0.5; }
    if (y > -0.2 && y < 0.25) { color[1] = 0.8; color[2] = 0.7; }
    gl_FragColor = color;
}

{
    // multiply the color input by a color calculated from screen coordinates.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec4 tint = vec4(0.5 + x * 0.3, 0.65 + y * 0.2, 0.8 - x * 0.2, 1.0);
    gl_FragColor = gl_Color * tint;
}

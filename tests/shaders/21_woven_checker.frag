{
    // use the signs of two polynomials to select a checker pattern.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float a = (x + 0.9) * (x + 0.45) * x * (x - 0.45) * (x - 0.9);
    float b = (y + 0.9) * (y + 0.45) * y * (y - 0.45) * (y - 0.9);
    vec4 color = vec4(0.06, 0.12, 0.23, 1.0);
    if ((a > 0.0 && b < 0.0) || (a < 0.0 && b > 0.0))
        color = vec4(0.95, 0.65, 0.23, 1.0);
    gl_FragColor = color;
}

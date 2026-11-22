{
    // use a polynomial to draw a flower shape.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float r = x * x + y * y;
    float flower = r * r - 0.7 * (x * x - y * y);
    vec4 color = vec4(0.1, 0.18, 0.18, 1.0);
    if (flower < 0.09) color = vec4(0.95, 0.35, 0.6, 1.0);
    if (r < 0.035) color = vec4(1.0, 0.8, 0.35, 1.0);
    gl_FragColor = color;
}

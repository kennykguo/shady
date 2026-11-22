{
    float x = (gl_FragCoord[0] - 400.0) / 160.0;
    float y = (gl_FragCoord[1] - 300.0) / 120.0;
    gl_FragColor = vec4(0.5 + 0.5 * sin(x + cos(y)), fract(-x), abs(sin(y)), 1.0);
}

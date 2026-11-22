{
    // use absolute coordinate values to draw nested diamonds.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float ax = x;
    float ay = y;
    vec4 color = vec4(0.04, 0.12, 0.18, 1.0);
    if (x < 0.0) ax = -x;
    if (y < 0.0) ay = -y;
    if (ax + ay < 0.95) color = vec4(0.15, 0.8, 0.7, 1.0);
    if (ax + ay < 0.55) color = vec4(1.0, 0.7, 0.3, 1.0);
    gl_FragColor = color;
}

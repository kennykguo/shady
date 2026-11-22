{
    // combine squared coordinates to draw elliptical rings.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float d = x * x * 0.5 + y * y;
    vec4 color = vec4(0.04, 0.07, 0.18, 1.0);
    if ((d > 0.08 && d < 0.16) || (d > 0.32 && d < 0.44) || (d > 0.7 && d < 0.86))
        color = vec4(0.4, 0.8, 1.0, 1.0);
    gl_FragColor = color;
}

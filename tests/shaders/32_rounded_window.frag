{
    // raise coordinates to the fourth power to draw a rounded window.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float d = x * x * x * x + y * y * y * y;
    vec4 color = vec4(0.12, 0.08, 0.22, 1.0);
    if (!(d >= 0.4)) color = vec4(0.55, 0.35, 0.85, 1.0);
    if (d < 0.12) color = vec4(0.85, 0.75, 1.0, 1.0);
    gl_FragColor = color;
}

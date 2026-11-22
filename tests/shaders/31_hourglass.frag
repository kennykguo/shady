{
    // compare squared coordinates to draw an hourglass.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float d = x * x - y * y * 0.65;
    vec4 color = vec4(0.08, 0.13, 0.25, 1.0);
    if (d <= 0.05) color = vec4(0.85, 0.4, 0.2, 1.0);
    if (d <= -0.15) color = vec4(1.0, 0.8, 0.45, 1.0);
    gl_FragColor = color;
}

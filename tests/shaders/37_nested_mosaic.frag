{
    // combine conditions across three nested levels.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec4 color = vec4(0.12, 0.2, 0.3, 1.0);
    if (x < 0.0) {
        if (y < 0.0) { if (x + y < -0.6) color = vec4(0.9, 0.4, 0.2, 1.0);
            else color = vec4(1.0, 0.7, 0.3, 1.0); }
        else color = vec4(0.15, 0.65, 0.65, 1.0);
    } else {
        if (y < 0.0) color = vec4(0.6, 0.35, 0.7, 1.0);
        else { if (x + y > 0.6) color = vec4(0.25, 0.35, 0.6, 1.0);
            else color = vec4(0.65, 0.75, 0.9, 1.0); }
    }
    gl_FragColor = color;
}

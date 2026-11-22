{
    // use the coordinate product to select curved color regions.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float h = x * y;
    vec4 color = vec4(0.1, 0.15, 0.3, 1.0);
    if (h > 0.0) { color = vec4(0.65, 0.3, 0.65, 1.0);
        if (h > 0.18) color = vec4(1.0, 0.6, 0.45, 1.0);
    } else { if (h < -0.18) color = vec4(0.15, 0.65, 0.75, 1.0); }
    gl_FragColor = color;
}

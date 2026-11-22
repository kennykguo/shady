{
    // use nested conditions to select horizontal color bands.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec4 color = vec4(0.14, 0.12, 0.34, 1.0);
    if (y < -0.45) color = vec4(0.95, 0.7, 0.4, 1.0);
    else { if (y < -0.1) color = vec4(0.95, 0.4, 0.3, 1.0);
    else { if (y < 0.25) color = vec4(0.65, 0.2, 0.4, 1.0);
    else { if (y < 0.6) color = vec4(0.35, 0.16, 0.4, 1.0); } } }
    gl_FragColor = color;
}

{
    // use a different color in each quarter.
    float x = gl_FragCoord[0] / 800.0;
    float y = gl_FragCoord[1] / 600.0;
    
    vec4 color;
    color[3] = 1.0;
    
    if (x < 0.5) {
        if (y < 0.5) {
            color[0] = 1.0; color[1] = 0.0; color[2] = 0.0; // use red.
        } else {
            color[0] = 0.0; color[1] = 1.0; color[2] = 0.0; // use green.
        }
    } else {
        if (y < 0.5) {
            color[0] = 0.0; color[1] = 0.0; color[2] = 1.0; // use blue.
        } else {
            color[0] = 1.0; color[1] = 1.0; color[2] = 0.0; // use yellow.
        }
    }
    
    gl_FragColor = color;
}

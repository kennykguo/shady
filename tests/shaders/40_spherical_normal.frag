{
    // use inverse square root to make a unit vector. convert its direction to color.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec3 p = vec3(x, y, 0.65);
    float inv = rsq(x * x + y * y + 0.4225);
    vec3 n = p * vec3(inv, inv, inv);
    gl_FragColor = vec4(0.5 + 0.5 * n[0], 0.5 + 0.5 * n[1], 0.5 + 0.5 * n[2], 1.0);
}

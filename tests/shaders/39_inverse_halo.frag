{
    // use inverse square root to reduce brightness with distance.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float light = rsq(1.0 + 9.0 * (x * x + y * y));
    gl_FragColor = vec4(0.15 + 0.6 * light, 0.1 + 0.35 * light, 0.25 + 0.7 * light, 1.0);
}

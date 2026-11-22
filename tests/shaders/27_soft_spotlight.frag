{
    // reduce brightness as squared distance increases.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    float d = (x + 0.35) * (x + 0.35) + (y + 0.3) * (y + 0.3);
    float light = 1.0 / (1.0 + 5.0 * d);
    gl_FragColor = vec4(0.1 + 0.85 * light, 0.06 + 0.65 * light, 0.15 + 0.4 * light, 1.0);
}

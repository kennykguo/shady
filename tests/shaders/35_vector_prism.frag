{
    // calculate coordinates with two component vectors. combine colors with four component vectors.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec2 p = vec2(x, y);
    vec2 q = vec2(1.0, 1.0);
    vec2 uv = (p + q) * vec2(0.5, 0.5);
    vec4 c = vec4(uv[0], uv[1], 1.0 - uv[0], 1.0);
    gl_FragColor = c * vec4(0.85, 0.9, 0.7, 1.0) + vec4(0.05, 0.05, 0.1, 0.0);
}

{
    // mix three component vectors and read their components.
    float x = (gl_FragCoord[0] - 400.0) / 220.0;
    float y = (gl_FragCoord[1] - 300.0) / 160.0;
    vec3 a = vec3(0.15, 0.25, 0.65);
    vec3 b = vec3(0.65, 0.4, -0.15);
    vec3 t = vec3(0.5 + x * 0.3, 0.5 + y * 0.3, 0.5 - x * 0.3);
    vec3 c = a + b * t;
    gl_FragColor = vec4(c[0], c[1], c[2], 1.0);
}

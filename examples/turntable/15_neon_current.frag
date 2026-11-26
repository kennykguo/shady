{
    // Turquoise and hot-pink glowing flowing contours on dark blue.
    float blue = 0.0;
    float d = 0.0;
    float diffuse = 0.0;
    float field = 0.0;
    float gloss = 0.0;
    float green = 0.0;
    float inv = 0.0;
    float light = 0.0;
    float matte = 0.0;
    float nx = 0.0;
    float ny = 0.0;
    float nz = 0.0;
    float red = 0.0;
    float s = 0.0;
    float specular = 0.0;
    float t = 0.0;
    float x = 0.0;
    float y = 0.0;
    float z = 0.0;

    x = gl_TexCoord[0]; y = gl_TexCoord[1]; z = gl_TexCoord[2];
    nx = gl_Color[0] * 2.0 - 1.0; ny = gl_Color[1] * 2.0 - 1.0; nz = gl_Color[2] * 2.0 - 1.0;
    inv = rsq(nx * nx + ny * ny + nz * nz + 0.000001);
    nx = nx * inv; ny = ny * inv; nz = nz * inv;
    matte = 0.42; gloss = 0.16;
    field = sin(x * 2.5 + sin(y * 2.0)) + cos(y * 2.8 + z);
    d = abs(sin(field * 3.0));
    t = 0.006 / (0.006 + d * d);
    s = 0.5 + 0.5 * sin(field + x);
    red = 0.025 + t * (0.12 + 0.78 * s); green = 0.04 + t * (0.85 - 0.6 * s); blue = 0.13 + t * 0.8;
    diffuse = nx * -0.42 + ny * 0.68 + nz * 0.6;
    if (diffuse < 0.0) diffuse = 0.0;
    specular = nx * -0.22 + ny * 0.38 + nz * 0.9;
    if (specular < 0.0) specular = 0.0;
    specular = specular * specular; specular = specular * specular;
    specular = specular * specular; specular = specular * specular;
    light = matte + (1.0 - matte) * diffuse;
    gl_FragColor = vec4(red * light + gloss * specular,
                        green * light + gloss * specular,
                        blue * light + gloss * specular, 1.0);
}

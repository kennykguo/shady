{
    // Large angled blocks with local jewel-colored gradients.
    float blue = 0.0;
    float diffuse = 0.0;
    float gloss = 0.0;
    float green = 0.0;
    float i = 0.0;
    float inv = 0.0;
    float j = 0.0;
    float light = 0.0;
    float matte = 0.0;
    float nx = 0.0;
    float ny = 0.0;
    float nz = 0.0;
    float red = 0.0;
    float s = 0.0;
    float specular = 0.0;
    float t = 0.0;
    float u = 0.0;
    float v = 0.0;
    float x = 0.0;
    float y = 0.0;
    float z = 0.0;

    x = gl_TexCoord[0]; y = gl_TexCoord[1]; z = gl_TexCoord[2];
    nx = gl_Color[0] * 2.0 - 1.0; ny = gl_Color[1] * 2.0 - 1.0; nz = gl_Color[2] * 2.0 - 1.0;
    inv = rsq(nx * nx + ny * ny + nz * nz + 0.000001);
    nx = nx * inv; ny = ny * inv; nz = nz * inv;
    matte = 0.42; gloss = 0.16;
    u = (x + y * 0.4) * 2.0; v = (y - x * 0.4) * 2.0;
    i = u - fract(u); j = v - fract(v);
    t = fract(u); s = fract(v);
    red = 0.080000 + t * 0.670000;
    green = 0.180000 + t * -0.060000;
    blue = 0.780000 + t * -0.180000;
    if (sin(i * 7.0 + j * 11.0) > 0.0) {
    red = 0.025000 + s * 0.925000;
    green = 0.620000 + s * 0.030000;
    blue = 0.620000 + s * -0.540000;
    }
    
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

{
    vec4 atlas_output = vec4(0.0, 0.0, 0.0, 1.0);
    float atlas_px = 400.0 + 220.0 * (gl_TexCoord[0] + 0.22 * gl_TexCoord[2]);
    float atlas_py = 300.0 + 160.0 * gl_TexCoord[1];
    float atlas_nx = gl_Color[0] * 2.0 - 1.0;
    float atlas_ny = gl_Color[1] * 2.0 - 1.0;
    float atlas_nz = gl_Color[2] * 2.0 - 1.0;
    float atlas_inv = 0.0;
    float atlas_diffuse = 0.0;
    float atlas_specular = 0.0;
    float atlas_light = 0.0;

float blue = 0.0;
float field = 0.0;
float green = 0.0;
float red = 0.0;
float u = 0.0;
float v = 0.0;
float x = 0.0;
float y = 0.0;
float z = 0.0;
x = gl_TexCoord[0]; y = gl_TexCoord[1]; z = gl_TexCoord[2];
u = x + 0.3 * cos(y * 2.0 + z); v = y + 0.3 * sin(x * 2.0 - z); field = u * 1.1 + 0.75 * sin(v * 2.1);
red = 0.5 + 0.48 * cos(field * 2.4 + 2.400000);
green = 0.5 + 0.48 * cos(field * 2.4 + 4.500000);
blue = 0.5 + 0.48 * cos(field * 2.4 + 6.600000);
atlas_output = vec4(red, green, blue, 1.0);

    atlas_inv = rsq(atlas_nx * atlas_nx + atlas_ny * atlas_ny + atlas_nz * atlas_nz + 0.000001);
    atlas_nx = atlas_nx * atlas_inv;
    atlas_ny = atlas_ny * atlas_inv;
    atlas_nz = atlas_nz * atlas_inv;
    atlas_diffuse = atlas_nx * -0.42 + atlas_ny * 0.68 + atlas_nz * 0.60;
    if (atlas_diffuse < 0.0) atlas_diffuse = 0.0;
    atlas_specular = atlas_nx * -0.22 + atlas_ny * 0.38 + atlas_nz * 0.90;
    if (atlas_specular < 0.0) atlas_specular = 0.0;
    atlas_specular = atlas_specular * atlas_specular;
    atlas_specular = atlas_specular * atlas_specular;
    atlas_specular = atlas_specular * atlas_specular;
    atlas_specular = atlas_specular * atlas_specular;
    atlas_specular = atlas_specular * 0.22;
    atlas_light = 0.48 + 0.52 * atlas_diffuse;
    gl_FragColor = vec4(atlas_output[0] * atlas_light + atlas_specular + 0.018,
                        atlas_output[1] * atlas_light + atlas_specular + 0.018,
                        atlas_output[2] * atlas_light + atlas_specular + 0.018, 1.0);
}

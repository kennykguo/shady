#version 450
layout(location=0) in vec3 inPosition;
layout(location=1) in vec3 inNormal;
layout(location=0) out vec4 outColor;
layout(location=1) out vec4 outTexCoord;
void main() {
    float angle = 6.28318530718 * float(gl_InstanceIndex) / 192.0 - 0.28;
    float elevation = 0.18 + 0.08 * sin(angle);
    vec3 eye = 6.5 * vec3(cos(elevation) * sin(angle), sin(elevation), cos(elevation) * cos(angle));
    vec3 forward = normalize(-eye);
    vec3 right = normalize(cross(forward, vec3(0.0, 1.0, 0.0)));
    vec3 up = cross(right, forward);
    mat4 view = mat4(vec4(right.x, up.x, -forward.x, 0.0),
                     vec4(right.y, up.y, -forward.y, 0.0),
                     vec4(right.z, up.z, -forward.z, 0.0),
                     vec4(-dot(right, eye), -dot(up, eye), dot(forward, eye), 1.0));
    float f = 1.0 / tan(radians(48.0) * 0.5);
    mat4 projection = mat4(vec4(f / (4.0/3.0), 0.0, 0.0, 0.0),
                           vec4(0.0, -f, 0.0, 0.0),
                           vec4(0.0, 0.0, -100.0/99.95, -1.0),
                           vec4(0.0, 0.0, -5.0/99.95, 0.0));
    gl_Position = projection * view * vec4(inPosition - vec3(0.217, 1.575, 0.0), 1.0);
    outColor = vec4(normalize(mat3(view) * inNormal) * 0.5 + 0.5, 1.0);
    outTexCoord = vec4((inPosition.x - 0.217) / 2.4,
                       (inPosition.y - 1.575) / 1.4, inPosition.z / 2.0, 1.0);
}

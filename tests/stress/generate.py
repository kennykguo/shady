"""Generate shader-only stress examples. Run before tools/stress.py."""
from pathlib import Path
import math

OUT = Path(__file__).resolve().parents[2] / 'build/stress/sources'
OUT.mkdir(parents=True, exist_ok=True)


class Shader:
    def __init__(self, description):
        self.description = description
        self.declarations = [
            'float x = (gl_FragCoord[0] - 420.0) / 230.0;',
            'float y = (gl_FragCoord[1] - 165.0) / 140.0;']
        self.statements = []

    def var(self, name, value='0.0'):
        self.declarations.append(f'float {name} = {value};')

    def emit(self, text):
        self.statements.extend(text.splitlines())

    def save(self, name):
        body = self.declarations + [''] + self.statements
        (OUT / f'{name}.frag').write_text(
            '{\n    // ' + self.description + '\n' +
            '\n'.join('    ' + line for line in body) + '\n}\n')


def marble():
    s = Shader('Twelve unrolled octaves of coupled domain warping, with mineral veins.')
    for name, value in [('u', 'x'), ('v', 'y'), ('a', '0.0'), ('b', '0.0'),
                        ('vein', '0.0'), ('light', '0.0'), ('r', '0.0'), ('g', '0.0'), ('blue', '0.0')]:
        s.var(name, value)
    for i in range(12):
        weight = 0.32 / (1.0 + i * 0.35)
        s.emit(f'// Warp layer {i + 1}.\na = sin(u * 2.7 + cos(v * 2.1));\nb = cos(v * 2.5 + sin(u * 2.3));\nu = u + {weight:.6f} * a;\nv = v + {weight:.6f} * b;')
    s.emit('''vein = abs(sin(u * 14.0 + v * 5.0 + 2.0 * sin(v * 6.0)));
light = 0.035 / (0.035 + vein * vein);
r = 0.025 + 0.78 * light + 0.13 * (0.5 + 0.5 * sin(v * 3.0));
g = 0.06 + 0.57 * light + 0.13 * (0.5 + 0.5 * cos(u * 2.0));
blue = 0.12 + 0.28 * light + 0.2 * (0.5 + 0.5 * cos(u * 2.0 + v));
gl_FragColor = vec4(r, g, blue, 1.0);''')
    s.save('01_warped_lapis')


def voronoi():
    s = Shader('Nine explicit Voronoi neighbors, nearest/second-nearest tracking, enamel borders.')
    for name, value in [('sx', 'x * 4.0'), ('sy', 'y * 4.0'), ('cx', 'sx - fract(sx)'),
                        ('cy', 'sy - fract(sy)'), ('fx', 'fract(sx)'), ('fy', 'fract(sy)'),
                        ('nearest', '100.0'), ('second', '100.0'), ('hue', '0.0'), ('edge', '0.0'),
                        ('shine', '0.0'), ('r', '0.0'), ('g', '0.0'), ('b', '0.0')]:
        s.var(name, value)
    for i, (dx, dy) in enumerate(( (a,b) for a in [-1,0,1] for b in [-1,0,1])):
        s.var(f'h{i}', f'fract(sin((cx + {dx}.0) * 13.0 + (cy + {dy}.0) * 37.0) * 31.0)')
        s.var(f'px{i}', f'{dx}.0 + 0.5 + 0.4 * sin(h{i} * 6.0) - fx')
        s.var(f'py{i}', f'{dy}.0 + 0.5 + 0.4 * cos(h{i} * 5.0) - fy')
        s.var(f'd{i}', f'px{i} * px{i} + py{i} * py{i}')
        s.emit(f'''if (d{i} < nearest) {{
    second = nearest;
    nearest = d{i};
    hue = h{i};
}} else {{
    if (d{i} < second) second = d{i};
}}''')
    s.emit('''edge = second - nearest;
shine = 0.025 / (0.025 + edge * edge);
r = (0.45 + 0.4 * cos(hue * 6.0)) * (1.0 - 0.8 * shine) + 0.9 * shine;
g = (0.4 + 0.35 * cos(hue * 6.0 + 2.1)) * (1.0 - 0.8 * shine) + 0.65 * shine;
b = (0.45 + 0.4 * cos(hue * 6.0 + 4.2)) * (1.0 - 0.8 * shine) + 0.2 * shine;
gl_FragColor = vec4(r, g, b, 1.0);''')
    s.save('02_voronoi_enamel')


def kaleidoscope():
    s = Shader('Twenty-four unrolled inversion/fold iterations and accumulated orbit traps.')
    for name, value in [('u','x'), ('v','y'), ('radius','0.0'), ('trap','0.0'),
                        ('r','0.0'), ('g','0.0'), ('b','0.0')]:
        s.var(name,value)
    for i in range(24):
        s.emit(f'''// Inversion/fold iteration {i + 1}.
radius = u * u + v * v + 0.18;
u = abs(u) / radius - 0.82;
v = abs(v) / radius - 0.52;
trap = 0.003 / (0.003 + v * v);
r = r + {0.09/(1+i*.12):.6f} * trap * (0.5 + 0.5 * cos({i*.65:.6f}));
g = g + {0.07/(1+i*.12):.6f} * trap * (0.5 + 0.5 * cos({i*.65+2.1:.6f}));
b = b + {0.15/(1+i*.12):.6f} * trap * (0.5 + 0.5 * cos({i*.65+4.2:.6f}));''')
    s.emit('gl_FragColor = vec4(0.025 + r * 3.0, 0.015 + g * 3.0, 0.06 + b * 3.0, 1.0);')
    s.save('03_inversion_filigree')


def nested():
    s = Shader('Thirty-two nested conditional scopes: repeated diamond inlays and conditional vector stores.')
    s.var('u', 'x'); s.var('v', 'y');s.var('t')
    s.declarations.append('vec4 color = vec4(0.025, 0.045, 0.09, 1.0);')
    for i in range(32):
        indent='    '*i
        s.emit(indent + 'if (abs(u) + abs(v) < 1.25) {')
        s.emit(indent + f'    color = vec4({0.4+.35*math.cos(i*.5):.6f}, {0.4+.35*math.cos(i*.5+2.1):.6f}, {0.45+.35*math.cos(i*.5+4.2):.6f}, 1.0);')
        s.emit(indent + '    t = (u + v) * 0.82;\n' + indent + '    v = (v - u) * 0.82;\n' + indent + '    u = t;')
    s.emit('\n'.join('    '*i+'}' for i in reversed(range(32))))
    s.emit('gl_FragColor = color;')
    s.save('04_nested_inlays')


def mandelbrot():
    s = Shader('Ninety-six explicitly unrolled Mandelbrot iterations with nested escape predicates.')
    for name,value in [('cx','-0.745 + x * 0.06'),('cy','0.186 + y * 0.06'),('zx','0.0'),('zy','0.0'),('tmp','0.0'),('escaped','0.0'),('count','0.0'),('r','0.0'),('g','0.0'),('b','0.0')]:
        s.var(name,value)
    for i in range(96):
        s.emit(f'''// Mandelbrot iteration {i + 1}.
if (escaped < 0.5) {{
    tmp = zx * zx - zy * zy + cx;
    zy = 2.0 * zx * zy + cy;
    zx = tmp;
    count = count + 1.0;
    if (zx * zx + zy * zy > 4.0) escaped = 1.0;
}}''')
    s.emit('''r = 0.5 + 0.5 * cos(count * 0.15 + 0.4);
g = 0.5 + 0.5 * cos(count * 0.15 + 2.5);
b = 0.5 + 0.5 * cos(count * 0.15 + 4.6);
if (escaped < 0.5) { r = 0.015; g = 0.02; b = 0.04; }
gl_FragColor = vec4(r, g, b, 1.0);''')
    s.save('05_mandelbrot_96')


def distance(s, target):
    # All scratch values are declared once, outside conditional scopes.
    s.emit(f'''qx = px;
qy = 0.8 * py + 0.6 * pz;
qz = -0.6 * py + 0.8 * pz;
a = qx * qx + qy * qy;
a = a * rsq(a + 0.0001) - 0.58;
b = a * a + qz * qz;
{target} = b * rsq(b + 0.0001) - 0.16;
{target} = {target} + 0.025 * sin(px * 14.0) * sin(py * 14.0) * sin(pz * 14.0);''')


def raymarch():
    s=Shader('Two hundred fifty-six unrolled ray-march steps, displaced torus, six distance samples for normals.')
    for name,value in [('inv','rsq(x * x + y * y + 4.0)'),('dx','x * inv'),('dy','y * inv'),('dz','-2.0 * inv'),('travel','0.0'),('hit','0.0')]:s.var(name,value)
    for name in ['px','py','pz','qx','qy','qz','a','b','d','nx','ny','nz','positive','negative','baseX','baseY','baseZ','normalizer','diffuse','specular','r','g','blue']:s.var(name)
    for i in range(256):
        s.emit(f'// Ray-march step {i+1}.\npx = dx * travel;\npy = dy * travel;\npz = 2.8 + dz * travel;')
        distance(s,'d')
        s.emit('if (d < 0.0015 && travel < 6.0) hit = 1.0;\nif (hit < 0.5 && travel < 6.0) travel = travel + d * 0.8;')
    s.emit('baseX = px;\nbaseY = py;\nbaseZ = pz;')
    for coord,normal in [('px','nx'),('py','ny'),('pz','nz')]:
        base={'px':'baseX','py':'baseY','pz':'baseZ'}[coord]
        s.emit(f'{coord} = {base} + 0.002;');distance(s,'positive')
        s.emit(f'{coord} = {base} - 0.002;');distance(s,'negative')
        s.emit(f'{normal} = positive - negative;\n{coord} = {base};')
    s.emit('''normalizer = rsq(nx * nx + ny * ny + nz * nz + 0.000001);
nx = nx * normalizer;
ny = ny * normalizer;
nz = nz * normalizer;
diffuse = nx * -0.4 + ny * -0.5 + nz * 0.76;
if (diffuse < 0.0) diffuse = 0.0;
specular = nz;
if (specular < 0.0) specular = 0.0;
specular = specular * specular;
specular = specular * specular;
specular = specular * specular;
specular = specular * specular;
r = 0.025; g = 0.04; blue = 0.08;
if (hit > 0.5) {
    r = 0.12 + 0.7 * diffuse + 0.6 * specular;
    g = 0.045 + 0.25 * diffuse + 0.55 * specular;
    blue = 0.08 + 0.3 * (0.5 + 0.5 * sin(baseX * 9.0 + baseY * 7.0)) + 0.5 * specular;
}
gl_FragColor = vec4(r, g, blue, 1.0);''')
    s.save('06_raymarched_torus_256')


def scaling():
    for count in [256,1024,4096,16384]:
        s=Shader(f'Compile-size probe: {count} distinct local variables feeding the final color.')
        for i in range(count):
            value='sin(x)' if i==0 else f'sin(v{i-1} + 0.17)'
            s.var(f'v{i}',value)
        s.emit(f'gl_FragColor = vec4(0.5 + 0.5 * v{count-1}, fract(x), abs(sin(y)), 1.0);')
        s.save(f'probe_locals_{count:05}')
    for depth in [64,256,1024,4096,8192]:
        s=Shader(f'Compile-depth probe: {depth} nested sin calls in one expression.')
        s.var('wave','sin('*depth+'x'+')'*depth)
        s.emit('gl_FragColor = vec4(0.5 + 0.5 * wave, fract(x), abs(sin(y)), 1.0);')
        s.save(f'probe_expression_{depth:05}')


if __name__=='__main__':
    marble();voronoi();kaleidoscope();nested();mandelbrot();raymarch();scaling()
    print('Generated six visual examples and nine compile-only scaling probes.')

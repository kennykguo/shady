"""Generate 100 shaders across 20 algorithm families; compiler sources stay untouched."""
from pathlib import Path
import json
import math
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'build/capabilities/sources'


def num(x):
    return f'{x:.6f}'


class Shader:
    def __init__(self, family, title, variant, complexity, feature):
        self.meta = dict(family=family, title=title, variant=variant,
                         complexity=complexity, feature=feature)
        self.variables = {}
        self.lines = []
        angle = variant * 0.27
        self.emit(f'''sx = (gl_FragCoord[0] - 420.0) / 230.0;
sy = (gl_FragCoord[1] - 165.0) / 140.0;
x = sx * {num(math.cos(angle))} - sy * {num(math.sin(angle))};
y = sx * {num(math.sin(angle))} + sy * {num(math.cos(angle))};''')

    def emit(self, code):
        for name in re.findall(r'\b([A-Za-z_]\w*)\s*=(?!=)', code):
            if name != 'gl_FragColor':
                self.variables[name] = None
        self.lines.extend(code.splitlines())

    def palette(self, scale=4.0, glow=0.0):
        phase = self.meta['variant'] * 0.8
        self.emit(f'''shade = 0.65 + 0.35 / (1.0 + x * x + y * y);
red = (0.08 + 0.8 * (0.5 + 0.5 * cos(field * {num(scale)} + {num(phase)}))) * shade + {num(glow)} * light;
green = (0.06 + 0.75 * (0.5 + 0.5 * cos(field * {num(scale)} + {num(phase + 2.1)}))) * shade + {num(glow)} * light;
blue = (0.1 + 0.8 * (0.5 + 0.5 * cos(field * {num(scale)} + {num(phase + 4.2)}))) * shade + {num(glow)} * light;''')

    def save(self, index):
        self.emit('gl_FragColor = vec4(red, green, blue, 1.0);')
        stem = f'{index:03}_' + re.sub(r'[^a-z0-9]+', '_', self.meta['title'].lower()).strip('_')
        source = '{\n    // ' + self.meta['feature'] + '\n'
        source += ''.join(f'    float {name} = 0.0;\n' for name in self.variables)
        source += '\n' + '\n'.join('    ' + line for line in self.lines) + '\n}\n'
        (OUT / (stem + '.frag')).write_text(source)
        return dict(self.meta, shader=stem + '.frag', lines=len(source.splitlines()))


def noise(s, ux, uy, prefix):
    s.emit(f'''{prefix}x = {ux};
{prefix}y = {uy};
{prefix}i = {prefix}x - fract({prefix}x);
{prefix}j = {prefix}y - fract({prefix}y);
{prefix}u = fract({prefix}x);
{prefix}v = fract({prefix}y);
{prefix}u = {prefix}u * {prefix}u * (3.0 - 2.0 * {prefix}u);
{prefix}v = {prefix}v * {prefix}v * (3.0 - 2.0 * {prefix}v);
{prefix}a = fract(sin({prefix}i * 13.0 + {prefix}j * 37.0) * 31.0);
{prefix}b = fract(sin(({prefix}i + 1.0) * 13.0 + {prefix}j * 37.0) * 31.0);
{prefix}c = fract(sin({prefix}i * 13.0 + ({prefix}j + 1.0) * 37.0) * 31.0);
{prefix}d = fract(sin(({prefix}i + 1.0) * 13.0 + ({prefix}j + 1.0) * 37.0) * 31.0);
{prefix}n = ({prefix}a * (1.0 - {prefix}u) + {prefix}b * {prefix}u) * (1.0 - {prefix}v)
    + ({prefix}c * (1.0 - {prefix}u) + {prefix}d * {prefix}u) * {prefix}v;''')
    return prefix + 'n'


def warped(v):
    titles=['Lapis rivers','Copper fault lines','Jade whorls','Porcelain turbulence','Molten silver']
    count=5+v*2
    s=Shader('Domain warping',titles[v],v,'Medium' if v<2 else 'High',f'{count} coupled warp layers, nested trigonometry, fine mineral veins.')
    s.emit('u = x;\nv = y;')
    for i in range(count):
        s.emit(f'''a = sin(u * {num(2.0 + v*.2)} + cos(v * 2.3));
b = cos(v * 2.5 + sin(u * 2.1));
u = u + {num(.19/(1+i*.18))} * a;
v = v + {num(.19/(1+i*.18))} * b;''')
    s.emit(f'''vein = abs(sin(u * {num(9+v*3)} + v * 4.0 + sin(v * 6.0)));
light = 0.018 / (0.018 + vein * vein);
red = 0.025 + light * 0.8 + 0.12 * (0.5 + 0.5 * sin(v * 3.0));
green = 0.05 + light * {num(.45+v*.07)} + 0.16 * (0.5 + 0.5 * cos(u * 2.0));
blue = 0.12 + light * {num(.2+v*.15)} + 0.12 * (0.5 + 0.5 * cos(u * 2.0 + v));''')
    return s


def interference(v):
    s=Shader('Wave interference',['Neon tide','Chladni enamel','Chromatic caustics','Interference lace','Prismatic resonance'][v],v,'Medium','Eight to sixteen directional waves with nonlinear phase modulation and contour glow.')
    s.emit('field = 0.0;')
    for i in range(8+v*2):
        angle=i*2.39996
        s.emit(f'field = field + {num(1/(i+2))} * sin(x * {num(math.cos(angle)*(3+v))} + y * {num(math.sin(angle)*(3+v))} + sin(x * 1.7 - y * 2.1 + {num(i)}));')
    s.emit(f'd = abs(sin(field * {num(5+v)}));\nlight = 0.009 / (0.009 + d * d);')
    s.palette(3,.25)
    s.emit('red = red * light;\ngreen = green * light;\nblue = blue * light;')
    return s


def cellular(v):
    neighbors=1 if v<3 else 2
    s=Shader('Voronoi cells',['Gold cloisonne','Gemstone cells','Obsidian cracks','Cellular opal','Voronoi nebula'][v],v,'High',f'{(neighbors*2+1)**2} neighboring sites; nearest and second-nearest tracking; conditional material selection.')
    s.emit(f'''u = x * {num(3+v*.7)}; v = y * {num(3+v*.7)};
ix = u - fract(u); iy = v - fract(v);
fx = fract(u); fy = fract(v);
nearest = 100.0; second = 100.0; hue = 0.0;''')
    for dx in range(-neighbors,neighbors+1):
        for dy in range(-neighbors,neighbors+1):
            s.emit(f'''h = fract(sin((ix + {num(dx)}) * 13.0 + (iy + {num(dy)}) * 37.0) * 31.0);
px = {num(dx)} + 0.5 + 0.38 * sin(h * 6.0) - fx;
py = {num(dy)} + 0.5 + 0.38 * cos(h * 5.0) - fy;
d = px * px + py * py;
if (d < nearest) {{ second = nearest; nearest = d; hue = h; }}
else {{ if (d < second) second = d; }}''')
    s.emit('field = hue;\nedge = second - nearest;\nlight = 0.012 / (0.012 + edge * edge);')
    s.palette(6,.35)
    s.emit('red = red * (0.45 + 0.55 / (1.0 + nearest));\ngreen = green * (0.45 + 0.55 / (1.0 + nearest));')
    if v==2:s.emit('red = 0.02 + light * 0.9; green = 0.03 + light * 0.55; blue = 0.06 + light * 0.2;')
    return s


def truchet(v):
    s=Shader('Truchet mosaics',['Ceramic arc maze','Golden braid tiles','Circuit arcs','Ribbon crossroads','Jewel labyrinth'][v],v,'Medium','Randomized tile orientation, paired circular arcs, layered line and border masks.')
    s.emit(f'''u = x * {num(3.5+v*.65)}; v = y * {num(3.5+v*.65)};
ix = u - fract(u); iy = v - fract(v);
px = fract(u); py = fract(v);
hash = fract(sin(ix * 13.0 + iy * 37.0) * 31.0);
if (hash > 0.5) px = 1.0 - px;
a = px * px + py * py;
b = (px - 1.0) * (px - 1.0) + (py - 1.0) * (py - 1.0);
a = abs(a * rsq(a + 0.000001) - 0.5);
b = abs(b * rsq(b + 0.000001) - 0.5);
d = a; if (b < d) d = b;
light = 0.0006 / (0.0006 + d * d);
field = hash + x * 0.18 + y * 0.12;''')
    s.palette(6,.2)
    s.emit('red = 0.025 + red * light; green = 0.03 + green * light; blue = 0.05 + blue * light;')
    if v>2:s.emit('edge = 0.003 / (0.003 + (d - 0.1) * (d - 0.1)); red = red + edge * 0.25; blue = blue + edge * 0.3;')
    return s


def gyroid(v):
    s=Shader('Gyroid sections',['Gyroid jade','Liquid lattice','Iridescent membrane','Twisted gyroid','Nested membranes'][v],v,'Medium','Layered trigonometric implicit surfaces, warped coordinates, thin-shell glow.')
    s.emit('u = x; v = y; field = 0.0; light = 0.0;')
    for i in range(4+v):
        freq=3.5+i*.7
        s.emit(f'''a = sin(u * {num(freq)}) * cos(v * {num(freq)}) + sin(v * {num(freq)}) * cos({num(i*.7+v)}) + sin({num(i*.7+v)}) * cos(u * {num(freq)});
light = light + {num(.3/(1+i*.3))} * 0.02 / (0.02 + a * a);
field = field + a * {num(.3/(i+1))};
u = u + 0.05 * sin(v * 4.0); v = v + 0.05 * cos(u * 4.0);''')
    s.palette(4,.15)
    s.emit('red = red * light; green = green * light; blue = blue * light;')
    return s


def wood(v):
    s=Shader('Organic grain',['Rosewood knots','Agate cross section','Tigerwood silk','Malachite grain','Burnished burl'][v],v,'Medium','Multiscale grain perturbations, displaced growth rings, and polished highlights.')
    s.emit('grain = 0.0;')
    for i in range(7+v):
        s.emit(f'grain = grain + {num(.25/(i+1))} * sin(x * {num(2+i*1.7)} + {num(i)} * cos(y * 2.1) + y * {num(1+i*.4)});')
    s.emit(f'''u = x + 0.25 * sin(y * 3.0) + grain;
v = y * 0.55 + 0.18 * cos(x * 4.0);
rad = u * u + v * v;
field = sin(rad * {num(14+v*5)} + grain * 5.0);
light = 0.02 / (0.02 + field * field);''')
    s.palette(2,.1)
    if v in [0,2,4]:s.emit('green = green * 0.65; blue = blue * 0.35;')
    return s


def contours(v):
    s=Shader('Noise terrain',['Ocean topography','Emerald elevation','Molten contour map','Copper relief','Cloud strata'][v],v,'High','Four to eight explicitly expanded value-noise octaves, cubic interpolation, contour extraction.')
    s.emit('field = 0.0;')
    for i in range(4+v):
        freq=1.4*1.8**i
        n=noise(s,f'x * {num(freq)} + {num(i*3)}',f'y * {num(freq)}',f'n{i}')
        s.emit(f'field = field + {num(.5**(i+1))} * {n};')
    s.emit(f'd = abs(fract(field * {num(12+v*3)}) - 0.5);\nlight = 0.0005 / (0.0005 + d * d);')
    s.palette(7,.22)
    return s


def woven(v):
    s=Shader('Woven materials',['Iridescent twill','Silk herringbone','Carbon weave','Chromatic tartan','Woven gold'][v],v,'Medium','Warped crossing thread families, tile parity, conditional over-under ordering, fine fibers.')
    s.emit(f'''u = x * {num(10+v*3)} + 0.7 * sin(y * 3.0 + sin(x * 2.0));
v = y * {num(10+v*3)} + 0.7 * cos(x * 3.0 + cos(y * 2.0));
fu = fract(u); fv = fract(v);
parity = fract(((u - fu) + (v - fv)) * 0.5);
a = sin(fu * 3.141593); b = sin(fv * 3.141593);
field = a * 0.7 + b * 0.3;
if (parity > 0.25) {{ field = b * 0.7 + a * 0.3; }}
fiber = 0.75 + 0.25 * sin(u * 28.0) * cos(v * 25.0);
light = field * fiber;''')
    s.palette(3,.0)
    s.emit('red = red * light; green = green * light; blue = blue * light;')
    if v==2:s.emit('red = light * 0.45; green = light * 0.5; blue = light * 0.6;')
    return s


def coupled(v):
    count=12+v*4
    s=Shader('Coupled fields',['Coral cellular field','Electric lichen','Peacock reaction field','Oscillating enamel','Fluid circuitry'][v],v,'High',f'{count} nonlinear coupled-map iterations with spatial forcing; a visual field, not a physical reaction-diffusion simulation.')
    s.emit('u = sin(x * 2.0); v = cos(y * 2.0); field = 0.0;')
    for i in range(count):
        s.emit(f'''a = sin(u * {num(1.7+v*.06)} - v * 1.2 + x * 0.3 + {num(i*.09)});
b = cos(v * 1.8 + u * 1.1 + y * 0.3);
u = 0.65 * u + 0.35 * a;
v = 0.65 * v + 0.35 * b;
field = field + {num(.15/(i+1))} * sin((u - v) * 7.0);''')
    s.emit('d = abs(sin((u + v) * 18.0)); light = 0.006 / (0.006 + d * d); field = field + u + v;')
    s.palette(5,.3)
    return s


def geometric(v):
    s=Shader('Geometric inlays',['Art deco tessellation','Scalloped ceramic','Rounded gem tiles','Nested diamondwork','Quilted metal'][v],v,'Medium','Rotated periodic cells, quartic and Manhattan distance masks, conditional inlay layers.')
    s.emit(f'''u = (x + y * 0.35) * {num(3+v*.6)}; v = (y - x * 0.35) * {num(3+v*.6)};
px = fract(u) - 0.5; py = fract(v) - 0.5;
hash = fract(sin((u - fract(u)) * 13.0 + (v - fract(v)) * 37.0) * 31.0);
d = px * px * px * px + py * py * py * py;
field = hash + 0.3 * sin(d * 80.0); light = 0.0;''')
    for i in range(6+v):
        threshold=.055*(1-i/(7+v))
        s.emit(f'''if (d < {num(threshold)}) {{
    field = hash + {num(i*.12)};
    if (abs(px) + abs(py) < {num(.7-i*.045)}) light = {num(i*.04)};
}}''')
    s.palette(6,.6)
    return s


def folding(v):
    count=10+v*3
    s=Shader('Kaleidoscope folds',['Crystal starfold','Mirrored lotus','Gilded origami','Fractal fan','Kaleidoscope bloom'][v],v,'High',f'{count} rotating absolute-value folds with an accumulated line-distance trap.')
    s.emit('u = x; v = y; trap = 100.0; field = 0.0;')
    for i in range(count):
        s.emit(f'''u = abs(u) - {num(.65/(1+i*.08))};
v = abs(v) - {num(.35/(1+i*.1))};
t = u * 0.8 - v * 0.6;
v = u * 0.6 + v * 0.8; u = t;
d = abs(u * v);
if (d < trap) {{ trap = d; field = {num(i*.15)} + v; }}''')
    s.emit('light = 0.0001 / (0.0001 + trap * trap);')
    s.palette(5,.3)
    s.emit('red = red * (0.15 + 0.85 * light); green = green * (0.15 + 0.85 * light); blue = blue * (0.15 + 0.85 * light);')
    return s


def inversion(v):
    count=12+v*5
    s=Shader('Inversion fractals',['Amethyst filigree','Sapphire orbit lace','Inverse coral','Fractal chandelier','Inversion cathedral'][v],v,'High',f'{count} rational inversion iterations with three accumulated orbit traps.')
    s.emit('u = x; v = y; red = 0.01; green = 0.02; blue = 0.04;')
    for i in range(count):
        s.emit(f'''radius = u * u + v * v + {num(.16+v*.015)};
u = abs(u) / radius - {num(.78+v*.015)};
v = abs(v) / radius - {num(.49+v*.01)};
a = 0.002 / (0.002 + u * u); b = 0.002 / (0.002 + v * v);
red = red + {num(.14/(1+i*.15))} * b * (0.5 + 0.5 * cos({num(i*.7)}));
green = green + {num(.12/(1+i*.15))} * a * (0.5 + 0.5 * cos({num(i*.7+2.1)}));
blue = blue + {num(.2/(1+i*.15))} * (a + b) * (0.5 + 0.5 * cos({num(i*.7+4.2)}));''')
    s.emit('red = red * 2.0; green = green * 2.0; blue = blue * 2.0;')
    return s


def nested(v):
    count=12+v*6
    s=Shader('Deep conditional inlays',['Nested octagons','Recursive stained glass','Inlay mandala','Deep prism well','Thirty-six gates'][v],v,'High',f'{count} nested scopes, combining predicates and selecting repeated scalar color stores.')
    s.emit('u = x; v = y; red = 0.025; green = 0.04; blue = 0.07;')
    for i in range(count):
        indent='    '*i
        s.emit(indent+'if (abs(u) + abs(v) < 1.25) {')
        s.emit(indent+f'red = {num(.45+.4*math.cos(i*.58+v))}; green = {num(.45+.4*math.cos(i*.58+v+2.1))}; blue = {num(.45+.4*math.cos(i*.58+v+4.2))};')
        s.emit(indent+'t = (u + v) * 0.82; v = (v - u) * 0.82; u = t;')
    s.emit('\n'.join('    '*i+'}' for i in reversed(range(count))))
    return s


def circuit(v):
    s=Shader('Recursive circuitry',['Circuit metropolis','Nested logic cells','Golden microchip','Quantum traces','Recursive motherboard'][v],v,'High','Eight to sixteen hierarchical periodic cells, random orientation, gated line accumulation.')
    s.emit('u = x; v = y; light = 0.0; field = 0.0; gate = 1.0;')
    for i in range(8+v*2):
        s.emit(f'''px = fract(u * 2.0) - 0.5; py = fract(v * 2.0) - 0.5;
hash = fract(sin((u - fract(u)) * 13.0 + (v - fract(v)) * 37.0) * 31.0);
if (hash > 0.5) {{ t = px; px = py; py = t; }}
d = abs(py); if (abs(px - 0.25) < d) d = abs(px - 0.25);
light = light + gate * {num(.12/(1+i*.15))} * 0.0002 / (0.0002 + d * d);
field = field + hash * {num(.25/(i+1))};
if (abs(px) > 0.38 && abs(py) > 0.38) gate = gate * 0.35;
u = u * 1.7 + 0.23; v = v * 1.7 - 0.17;''')
    s.palette(5,.3)
    s.emit('red = 0.015 + red * light * 2.5; green = 0.02 + green * light * 2.5; blue = 0.04 + blue * light * 2.5;')
    return s


def fractal(v, kind):
    titles={
        'Mandelbrot':['Seahorse brocade','Mandelbrot coast','Spiral boundary','Mandelbrot tapestry','Deep seahorse'],
        'Julia':['Julia dragon','Julia dendrites','Julia islands','Julia rabbit','Julia frost'],
        'Burning ship':['Burning ship sails','Shipwreck silk','Burning coast','Ember harbor','Ship fractal lace']}
    count=64+v*24
    s=Shader(kind+' fractals',titles[kind][v],v,'High',f'{count} explicit complex-plane iterations, guarded updates, escape predicates, orbit coloring.')
    if kind=='Mandelbrot':
        views=[(-.745,.186,.06),(-.6,.0,.95),(-.748,.102,.025),(-.12,.75,.18),(-.7453,.1127,.003)]
        cx,cy,scale=views[v]
        s.emit(f'cx = {num(cx)} + x * {num(scale)}; cy = {num(cy)} + y * {num(scale)}; zx = 0.0; zy = 0.0;')
    elif kind=='Julia':
        constants=[(-.8,.156),(-.745,.186),(.285,.01),(-.123,.745),(-.4,.6)]
        cx,cy=constants[v]
        s.emit(f'zx = x * 1.1; zy = y * 1.1; cx = {num(cx)}; cy = {num(cy)};')
    else:
        s.emit(f'cx = -1.75 + x * {num(.05+v*.025)}; cy = -0.035 + y * {num(.04+v*.01)}; zx = 0.0; zy = 0.0;')
    s.emit('escaped = 0.0; count = 0.0; trap = 100.0;')
    for i in range(count):
        s.emit('if (escaped < 0.5) {')
        if kind=='Burning ship':s.emit('    zx = abs(zx); zy = abs(zy);')
        s.emit('''    tmp = zx * zx - zy * zy + cx;
    zy = 2.0 * zx * zy + cy; zx = tmp;
    count = count + 1.0;
    if (abs(zy) < trap) trap = abs(zy);
    if (zx * zx + zy * zy > 16.0) escaped = 1.0;
}''')
    s.emit('field = count * 0.04; light = 0.002 / (0.002 + trap * trap);')
    s.palette(4,.08)
    s.emit('if (escaped < 0.5) { red = 0.012; green = 0.02; blue = 0.04; }')
    return s


def volume(v):
    count=32+v*8
    s=Shader('Volume integration',['Nebula glass','Aurora volume','Chromatic smoke','Plasma cloud','Cosmic furnace'][v],v,'High',f'{count} explicit depth samples through an emissive trigonometric volume with front-to-back attenuation.')
    s.emit('red = 0.01; green = 0.015; blue = 0.04; transmission = 1.0;')
    for i in range(count):
        z=-1.5+3*i/count
        s.emit(f'''px = x + {num(z*.3)}; py = y + {num(z*.15)};
a = sin(px * 4.0 + sin(py * 3.0 + {num(z)})) * cos(py * 4.0 - {num(z*2)});
b = sin(px * 9.0 - {num(z*3)}) * sin(py * 7.0 + {num(z*2)});
density = abs(a + b * 0.3);
density = 0.018 / (0.018 + density * density) * {num(.1+v*.015)};
red = red + transmission * density * (0.5 + 0.5 * cos({num(z*2+v*.5)}));
green = green + transmission * density * (0.5 + 0.5 * cos({num(z*2+v*.5+2.1)}));
blue = blue + transmission * density * (0.5 + 0.5 * cos({num(z*2+v*.5+4.2)}));
transmission = transmission * (1.0 - density);''')
    return s


def sdf(s, target, variant):
    s.emit('qx = px; qy = 0.8 * py + 0.6 * pz; qz = -0.6 * py + 0.8 * pz;')
    if variant in [0,1]:
        s.emit(f'''a = qx * qx + qy * qy;
a = a * rsq(a + 0.000001) - {num(.55 if variant==0 else .48)};
b = a * a + qz * qz;
{target} = b * rsq(b + 0.000001) - {num(.16 if variant==0 else .22)};''')
        if variant==1:s.emit(f'{target} = {target} + 0.03 * sin(px * 14.0) * sin(py * 14.0) * sin(pz * 14.0);')
    elif variant==2:
        s.emit(f'''a = (px + 0.3) * (px + 0.3) + py * py + pz * pz;
b = (px - 0.3) * (px - 0.3) + py * py + pz * pz;
a = a * rsq(a + 0.000001) - 0.4;
b = b * rsq(b + 0.000001) - 0.4;
{target} = a; if (b < {target}) {target} = b;''')
    elif variant==3:
        s.emit(f'''a = abs(qx) - 0.4; b = abs(qy) - 0.4; c = abs(qz) - 0.4;
if (a < 0.0) a = 0.0; if (b < 0.0) b = 0.0; if (c < 0.0) c = 0.0;
d = a * a + b * b + c * c;
{target} = d * rsq(d + 0.000001) - 0.1;''')
    else:
        s.emit(f'''a = px * px + py * py + pz * pz;
{target} = a * rsq(a + 0.000001) - 0.6;
{target} = {target} + 0.05 * sin(px * 10.0) * sin(py * 10.0) * sin(pz * 10.0);''')


def raymarch(v):
    count=[64,96,96,128,160][v]
    s=Shader('Ray-marched scenes',['Copper torus portal','Rippled torus portal','Twin pearl portal','Rounded cube portal','Alien pearl portal'][v],v,'High',f'{count} unrolled ray-march steps, six distance samples for a normal, diffuse and specular lighting; scene inside the teapot silhouette.')
    s.emit('inv = rsq(x * x + y * y + 4.0); dx = x * inv; dy = y * inv; dz = -2.0 * inv; travel = 0.0; hit = 0.0;')
    for i in range(count):
        s.emit('px = dx * travel; py = dy * travel; pz = 2.6 + dz * travel;')
        sdf(s,'distance',v)
        s.emit('if (distance < 0.002 && travel < 6.0) hit = 1.0;\nif (hit < 0.5 && travel < 6.0) travel = travel + distance * 0.7;')
    s.emit('baseX = px; baseY = py; baseZ = pz;')
    for coordinate,base,normal in [('px','baseX','nx'),('py','baseY','ny'),('pz','baseZ','nz')]:
        s.emit(f'{coordinate} = {base} + 0.002;');sdf(s,'positive',v)
        s.emit(f'{coordinate} = {base} - 0.002;');sdf(s,'negative',v)
        s.emit(f'{normal} = positive - negative; {coordinate} = {base};')
    s.emit('''inv = rsq(nx * nx + ny * ny + nz * nz + 0.000001);
nx = nx * inv; ny = ny * inv; nz = nz * inv;
light = nx * -0.4 + ny * -0.5 + nz * 0.76;
if (light < 0.0) light = 0.0;
specular = nz; if (specular < 0.0) specular = 0.0;
specular = specular * specular; specular = specular * specular;
specular = specular * specular; specular = specular * specular;
field = baseX * 0.8 + baseY * 0.5;''')
    s.palette(4,.0)
    s.emit('red = red * (0.15 + 0.85 * light) + specular * 0.6; green = green * (0.15 + 0.85 * light) + specular * 0.6; blue = blue * (0.15 + 0.85 * light) + specular * 0.6;\nif (hit < 0.5) { red = 0.025; green = 0.04; blue = 0.08; }')
    return s


def orbits(v):
    count=24+v*8
    s=Shader('Nonlinear orbit traps',['De Jong ribbons','Clifford silk','Orbit embroidery','Attractor enamel','Strange orbit tapestry'][v],v,'High',f'{count} nonlinear two-dimensional orbit iterations with spatially varying seeds and accumulated curve traps.')
    s.emit('u = x; v = y; red = 0.015; green = 0.02; blue = 0.04;')
    for i in range(count):
        s.emit(f'''a = sin(v * {num(1.4+v*.1)}) - cos(u * 1.7);
b = sin(u * 1.6) - cos(v * {num(1.3+v*.08)});
u = a + 0.08 * x; v = b + 0.08 * y;
d = abs(u * 0.7 + v * 0.3);
light = 0.002 / (0.002 + d * d);
red = red + light * {num(.065/(1+i*.07))} * (0.5 + 0.5 * cos({num(i*.3)}));
green = green + light * {num(.075/(1+i*.07))} * (0.5 + 0.5 * cos({num(i*.3+2.1)}));
blue = blue + light * {num(.095/(1+i*.07))} * (0.5 + 0.5 * cos({num(i*.3+4.2)}));''')
    s.emit('red = red * 3.0; green = green * 3.0; blue = blue * 3.0;')
    return s


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    families=[warped,interference,cellular,truchet,gyroid,wood,contours,woven,coupled,geometric,
              folding,inversion,nested,circuit,lambda v:fractal(v,'Mandelbrot'),
              lambda v:fractal(v,'Julia'),lambda v:fractal(v,'Burning ship'),volume,raymarch,orbits]
    rows=[]
    for family in families:
        for v in range(5):
            shader=family(v)
            rows.append(shader.save(len(rows)+1))
    (OUT.parent/'catalog.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert len(rows)==100 and len({r['family'] for r in rows})==20
    print(f'Generated {len(rows)} shaders across 20 families in {OUT}')


if __name__=='__main__':
    main()

"""create diagrams and a shader preview from verified renders.

use pillow and the svg renderer. run the render test first."""
from pathlib import Path
from html import escape
import subprocess
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/images"
OUT.mkdir(parents=True, exist_ok=True)
INK = "#e4eaf0"
MUTED = "#93a4b6"
BLUE = "#8fb8e8"
GREEN = "#9ed5c5"
BG = "#0d121b"


def text(x, y, value, size=24, fill=INK, anchor="start", mono=False):
    font = "monospace" if mono else "sans-serif"
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(value)}</text>')


def box(x, y, w, h, stroke="#2a3747", fill="#141d29", radius=12):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')


def arrow(path, color=BLUE):
    return (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" '
            f'marker-end="url(#arrow)"/>')


def save_svg(name, elements):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1000" '
           'viewBox="0 0 1600 1000" role="img">'
           '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
           'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
           f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{BLUE}"/></marker></defs>'
           f'<rect width="1600" height="1000" fill="{BG}"/>'
           + "".join(elements) + '</svg>')
    path = OUT / (name + ".svg")
    path.write_text(svg)
    subprocess.run(["rsvg-convert", str(path), "-o", str(path.with_suffix(".png"))], check=True)


def pipeline():
    e = [text(90, 90, "SHADY / THE PIPELINE", 22, GREEN, mono=True),
         text(90, 166, "From source to pixels.", 58),
         text(90, 216, "A small GLSL subset, compiled to SPIR-V and rendered with Vulkan.", 26, MUTED)]
    stages = [
        (90, 310, "01", "Scan", "scanner.l", ".frag → tokens"),
        (450, 310, "02", "Parse", "parser.y · ast.c", "tokens → AST"),
        (810, 310, "03", "Check", "semantic.c · symbol.c", "names, scopes, types"),
        (1170, 310, "04", "Generate", "codegen.c", "AST → SPIR-V text"),
        (1170, 620, "05", "SPIR-V", ".spvasm", "types + constants + body"),
        (810, 620, "06", "Assemble", "spirv-as · spirv-val", "validated .spv binary"),
        (450, 620, "07", "Render", "Vulkan · GPU driver", "fragment shader + mesh"),
        (90, 620, "08", "Pixels", ".png", "800 × 600 image"),
    ]
    for x, y, number, label, file, detail in stages:
        e += [box(x, y, 300, 200), text(x+24, y+36, number, 19, GREEN, mono=True),
              text(x+24, y+82, label, 34), text(x+24, y+125, file, 19, BLUE, mono=True),
              text(x+24, y+165, detail, 20, MUTED)]
    for x in [390, 750, 1110]:
        e.append(arrow(f"M {x+8} 410 H {x+51}"))
        e.append(arrow(f"M {x+51} 720 H {x+8}"))
    e += [arrow("M 1320 518 V 610"),
          text(90, 929, "Compiler: src/", 22, MUTED, mono=True),
          text(1510, 929, "Execution: tools/render.cpp", 22, MUTED, "end", mono=True)]
    save_svg("pipeline", e)


def predication():
    e = [text(90, 90, "SHADY / IF–ELSE", 22, GREEN, mono=True),
         text(90, 166, "Assignments become selects.", 58),
         text(90, 217, "A simplified view of the threshold shader's component assignments.", 26, MUTED),
         box(560, 282, 480, 126), text(800, 331, "x > 0.5", 34, INK, "middle", True),
         text(800, 376, "OpFOrdGreaterThan → predicate", 21, BLUE, "middle", True),
         box(170, 492, 470, 120), box(960, 492, 470, 120),
         text(405, 542, "then: color[i] = 1.0", 26, INK, "middle", True),
         text(405, 583, "predicate", 21, GREEN, "middle", True),
         text(1195, 542, "else: color[i] = 0.0", 26, INK, "middle", True),
         text(1195, 583, "OpLogicalNot(predicate)", 21, GREEN, "middle", True),
         arrow("M 685 416 V 450 H 405 V 482"),
         arrow("M 915 416 V 450 H 1195 V 482"),
         arrow("M 405 620 V 679 H 680 V 718"),
         arrow("M 1195 620 V 679 H 920 V 718"),
         box(440, 728, 720, 128),
         text(800, 778, "OpSelect + OpStore", 30, BLUE, "middle", True),
         text(800, 823, "Keep the new component only when its predicate is true.", 22, MUTED, "middle"),
         text(800, 934, "Dataflow sketch. Nested conditions combine predicates with OpLogicalAnd.", 23, MUTED, "middle")]
    save_svg("predication", e)


def shader_atlas():
    names = ["15_gradient_rgb", "11_bullseye", "08_pattern_quadrants",
             "06_gradient_twocolor", "09_radial_distance", "07_pattern_stripes"]
    canvas = Image.new("RGB", (1600, 1000), BG)
    draw = ImageDraw.Draw(canvas)
    for i, name in enumerate(names):
        im = Image.open(ROOT / "build/tests" / (name + ".png")).convert("RGB")
        # crop the rendered mesh for the preview.
        backdrop = Image.new("RGB", im.size, im.getpixel((0, 0)))
        bbox = ImageChops.difference(im, backdrop).getbbox()
        if bbox is None:
            raise ValueError(f"Empty render: {name}")
        im = im.crop(bbox)
        im.thumbnail((430, 340), Image.Resampling.LANCZOS)
        col, row = i % 3, i // 3
        x, y = 40 + col * 520, 30 + row * 480
        draw.rounded_rectangle((x, y, x+480, y+440), radius=14,
                               fill=(13, 18, 27), outline=(37, 49, 64), width=2)
        # use the render background color inside each tile.
        tile = Image.new("RGB", (460, 420), backdrop.getpixel((0, 0)))
        tile.paste(im, ((460-im.width)//2, (420-im.height)//2))
        canvas.paste(tile, (x+10, y+10))
    canvas.save(OUT / "shader-atlas.png", optimize=True)


if __name__ == "__main__":
    pipeline()
    predication()
    shader_atlas()
    print(f"Wrote gallery assets to {OUT}")

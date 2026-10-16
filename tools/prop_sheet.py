"""Render props from the shared library in the ink style, laid out on a grid, one camera per page.
    blender -b --factory-startup -P tools/prop_sheet.py -- OUT_NAME [ERA] [name_or_prefix ...]
ERA defaults to modern; with no names, renders every prop valid for ERA. Writes
renders/props/<OUT_NAME>_<page>.jpg (6 x 4 props per page, labels baked in as text objects)."""
import sys, os, math, importlib, random
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
from mathutils import Vector
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
from procedural_worlds import core, scenes
from procedural_worlds import scene_composed  # noqa: F401  (loads kits/ext)
from procedural_worlds.kits import props as P
from procedural_worlds.kits.mb import MB
from procedural_worlds.kits.room import era_palette
from procedural_worlds.ink import srgb

args = sys.argv[sys.argv.index("--") + 1:]
out_name = args[0]
era = args[1] if len(args) > 1 else "modern"
wanted = args[2:]
names = sorted(n for n, p in P.PROPS.items()
               if (p["eras"] is None or era in p["eras"]) and (not wanted or any(n == w or n.startswith(w) for w in wanted)))
COLS, ROWS, CELL = 6, 4, 2.6
pages = [names[i:i + COLS * ROWS] for i in range(0, len(names), COLS * ROWS)]
out_dir = os.path.join(root, "renders", "props")
os.makedirs(out_dir, exist_ok=True)


class Sheet:
    LABEL = "Prop sheet"
    names = []

    @staticmethod
    def build(col, seed, size, detail, height, mood="DAY", **kw):
        rng = random.Random(seed)
        pal = era_palette(core.load_preset("era")[era], mood, {"grime": 1.0})
        mb = MB("PW_PropSheet")
        floor = MB("PW_PropFloor")
        W, D = COLS * CELL, ROWS * CELL
        floor.box((W / 2, D / 2, -0.05), (W + 2, D + 2, 0.1), "floor_a")
        for i, n in enumerate(Sheet.names):
            cx, cy = (i % COLS + 0.5) * CELL, (ROWS - 1 - i // COLS + 0.5) * CELL
            p = P.PROPS[n]
            if p["place"] == "wall":
                floor.box((cx, cy + 0.45, 1.2), (CELL * 0.9, 0.1, 2.4), "wall")
                P.place_prop(mb, n, cx, cy + 0.38, 1.0 if p["size"][2] < 1.0 else 0.0, 0.0, rng, era)
            elif p["place"] == "surface":
                floor.box((cx, cy, 0.4), (0.9, 0.9, 0.8), "wood2")
                P.place_prop(mb, n, cx, cy, 0.8, 0.0, rng, era)
            elif p["place"] == "hanging":
                floor.box((cx, cy, 3.0), (1.2, 0.2, 0.1), "metal2")
                P.place_prop(mb, n, cx, cy, 2.95, 0.0, rng, era)
            else:
                P.place_prop(mb, n, cx, cy, 0.0, 0.0, rng, era)
            t = bpy.data.curves.new(f"PW_Label{i}", "FONT")
            t.body = n
            t.size = 0.22
            t.align_x = "CENTER"
            to = bpy.data.objects.new(f"PW_Label{i}", t)
            to.location = (cx, cy - CELL * 0.42, 0.02)
            col.objects.link(to)
            to.data.materials.append(core.make_material("PW_LabelMat", srgb(0.1, 0.1, 0.1)))
            to["pw_line"] = 0
        mb.build(col, pal)
        fo = floor.build(col, pal)
        fo["pw_wonk"] = 0
        return {"objects": len(col.objects), "camera": {"location": (W / 2, -D * 0.55, D * 1.05),
                                                       "target": (W / 2, D * 0.48, 0.6), "lens": 30},
                "sun_dir": (55, 200), "ink": {"line_scale": 0.9}}


scenes.REGISTRY["PROP_SHEET"] = Sheet
s = bpy.context.scene
for k, page in enumerate(pages):
    Sheet.names = page
    core.generate(bpy.context, "PROP_SHEET", seed=3, mood="DAY", layers={"era": era})
    core.setup_render("BLENDER_EEVEE", res=(1600, 1000), fast=True, ink=True)
    s.render.image_settings.file_format, s.render.image_settings.quality = "JPEG", 85
    s.render.filepath = os.path.join(out_dir, f"{out_name}_{k}.jpg")
    bpy.ops.render.render(write_still=True)
    print("PROPSHEET", s.render.filepath, len(page))
print("PROPS_TOTAL", len(P.PROPS), "rendered", len(names))

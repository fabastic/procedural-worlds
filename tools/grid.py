"""Seed x mood grid in ONE Blender session (shaders compile once), plus a contact sheet.
    blender -b --factory-startup -P tools/grid.py -- SCENE_TYPE [seeds=1,7,42] [moods=DAY,GOLDEN,DUSK,NIGHT] [RES_X RES_Y]
Writes renders/grid/<scene>_<seed>_<mood>.png and renders/grid/<scene>_sheet.png (half size)."""
import sys, os, importlib, time
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
import numpy as np
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
from procedural_worlds import core
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
scene_type = args[0] if args else "COASTAL_ISLAND"
seeds = [int(x) for x in (args[1] if len(args) > 1 else "1,7,42").split(",")]
moods = (args[2] if len(args) > 2 else "DAY,GOLDEN,DUSK,NIGHT").split(",")
res = (int(args[3]), int(args[4])) if len(args) > 4 else (960, 540)
out_dir = os.path.join(root, "renders", "grid")
os.makedirs(out_dir, exist_ok=True)
s = bpy.context.scene
tiles = []
for seed in seeds:
    row = []
    for mood in moods:
        t0 = time.time()
        core.generate(bpy.context, scene_type, seed=seed, size=60, detail=120, mood=mood,
                      engine="BLENDER_EEVEE")
        core.setup_render("BLENDER_EEVEE", res=res, fast=True, ink=True)
        path = os.path.join(out_dir, f"{scene_type.lower()}_{seed}_{mood.lower()}.png")
        s.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"GRID {seed} {mood} {time.time() - t0:.1f}s {path}")
        row.append(path)
    tiles.append(row)
# contact sheet at half resolution (numpy only; Blender ships it)
w, h = res[0] // 2, res[1] // 2
sheet = np.ones((h * len(seeds), w * len(moods), 4), dtype=np.float32)
for r, row in enumerate(tiles):
    for c, path in enumerate(row):
        img = bpy.data.images.load(path)
        img.scale(w, h)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
        y0 = (len(seeds) - 1 - r) * h
        sheet[y0:y0 + h, c * w:(c + 1) * w] = px
        bpy.data.images.remove(img)
out = bpy.data.images.new("PW_sheet", sheet.shape[1], sheet.shape[0], alpha=False)
out.pixels = sheet.ravel()
sheet_path = os.path.join(out_dir, f"{scene_type.lower()}_sheet.png")
out.filepath_raw = sheet_path
out.file_format = "PNG"
out.save()
print("SHEET", sheet_path)

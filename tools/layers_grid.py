"""Render story-layer combinations through the COMPOSED generator + a labelled contact sheet.
    blender -b --factory-startup -P tools/layers_grid.py -- OUT_NAME SPEC [SPEC ...]
SPEC = setting:era:genre[:time[:weather[:state[:seed]]]]   e.g. diner:1920s-50s:noir:night
Writes renders/layers/<OUT_NAME>/<i>_<spec>.jpg and renders/layers/<OUT_NAME>_sheet.jpg (960x540 tiles)."""
import sys, os, importlib, time, json
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
args = sys.argv[sys.argv.index("--") + 1:]
name, specs = args[0], args[1:]
out_dir = os.path.join(root, "renders", "layers", name)
os.makedirs(out_dir, exist_ok=True)
cond = core.load_preset("conditions")
s = bpy.context.scene
paths = []
for i, spec in enumerate(specs):
    p = spec.split(":") + [None] * 7
    layers = {"setting": p[0], "era": p[1], "genre_mood": p[2] or "slice-of-life", "time": p[3] or "day",
              "weather": p[4] or "clear", "state": p[5] or "lived-in"}
    seed = int(p[6]) if p[6] else 7
    t0 = time.time()
    try:
        core.generate(bpy.context, "COMPOSED", seed=seed, mood=cond["time"].get(layers["time"], "DAY"), layers=layers)
    except Exception as e:
        print(f"LAYERS_FAIL {spec}: {e!r}")
        continue
    core.setup_render("BLENDER_EEVEE", res=(960, 540), fast=True, ink=True)
    ims = s.render.image_settings
    ims.file_format, ims.quality = "JPEG", 88
    path = os.path.join(out_dir, f"{i:02d}_{spec.replace(':', '_')}.jpg")
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
    paths.append((spec, path))
    print(f"LAYERS {spec} {time.time() - t0:.1f}s {len(bpy.data.collections['PW_Generated'].objects)} objs")
json.dump([sp for sp, _ in paths], open(os.path.join(out_dir, "specs.json"), "w"))
print("DONE", len(paths))

"""Headless smoke test.  Run from the repo root:
    blender -b -P tools/smoke_test.py -- [SCENE_TYPE] [SEED]
Registers the add-on from source, generates a scene, renders renders/<scene>_<seed>.png (EEVEE-fast, 960x540)."""
import sys, os, importlib
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
pw = importlib.import_module("procedural_worlds")
pw.register()
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
scene_type = args[0] if args else "COASTAL_ISLAND"
seed = int(args[1]) if len(args) > 1 else 1
from procedural_worlds import core
info = core.generate(bpy.context, scene_type, seed=seed, size=60, detail=120, mood="GOLDEN", engine="CYCLES")
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y = 960, 540
if s.render.engine == "CYCLES":
    s.cycles.samples = 24
os.makedirs(os.path.join(root, "renders"), exist_ok=True)
out = os.path.join(root, "renders", f"{scene_type.lower()}_{seed}.png")
s.render.filepath = out
bpy.ops.render.render(write_still=True)
print("OK", info, out)

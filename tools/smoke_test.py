"""Headless smoke test.  Run from the repo root:
    blender -b --factory-startup -P tools/smoke_test.py -- [SCENE_TYPE] [SEED] [MOOD] [OUT_PNG] [RES_X RES_Y]
Registers the add-on from source, generates a scene in the ink style with EEVEE, renders a still
(default renders/<scene>_<seed>.png at 960x540) and checks the generated-collection invariants."""
import sys, os, importlib, time
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):        # factory-startup cube/camera/light would pollute the render
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
scene_type = args[0] if args else "COASTAL_ISLAND"
seed = int(args[1]) if len(args) > 1 else 1
mood = args[2] if len(args) > 2 else "GOLDEN"
out = args[3] if len(args) > 3 else os.path.join(root, "renders", f"{scene_type.lower()}_{seed}.png")
res = (int(args[4]), int(args[5])) if len(args) > 5 else (960, 540)
from procedural_worlds import core
t0 = time.time()
info = core.generate(bpy.context, scene_type, seed=seed, size=60, detail=120, mood=mood,
                     engine="BLENDER_EEVEE")
core.setup_render("BLENDER_EEVEE", res=res, fast=True, ink=True)
col = bpy.data.collections[core.COLLECTION]
bad = [o.name for o in col.objects if not o.name.startswith("PW_")]
assert not bad, f"objects without PW_ prefix: {bad}"
s = bpy.context.scene
assert s.render.engine == "BLENDER_EEVEE", s.render.engine
os.makedirs(os.path.dirname(out), exist_ok=True)
s.render.filepath = out
t1 = time.time()
bpy.ops.render.render(write_still=True)
print(f"OK {info} {out} build={t1 - t0:.1f}s render={time.time() - t1:.1f}s")

"""Render a short low-res camera fly-through MP4 of a scene (lines boil on twos).
    blender -b --factory-startup -P tools/flythrough.py -- SCENE SEED MOOD [FRAMES] [RES_X RES_Y]
Writes renders/flythrough_<scene>_<seed>_<mood>.mp4"""
import sys, os, importlib, time
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
from procedural_worlds import core, anim
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
st, seed, mood = args[0], int(args[1]), args[2]
frames = int(args[3]) if len(args) > 3 else 72
res = (int(args[4]), int(args[5])) if len(args) > 5 else (640, 360)
t0 = time.time()
info = core.generate(bpy.context, st, seed=seed, size=60, detail=160, mood=mood)
core.setup_render("BLENDER_EEVEE", res=res, fast=True, ink=True)
anim.setup_flythrough(bpy.context, info, seed=seed, frames=frames)
out = os.path.join(root, "renders", f"flythrough_{st.lower()}_{seed}_{mood.lower()}.mp4")
anim.set_video_output(bpy.context.scene, out, res)
bpy.ops.render.render(animation=True)
print(f"FLY {out} {time.time() - t0:.1f}s")

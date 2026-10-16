"""Hero renders at 1920x1080 with full EEVEE samples into renders/hero/ (JPEG q92, < 2 MB to commit).
    blender -b --factory-startup -P tools/hero.py -- SCENE:SEED:MOOD [SCENE:SEED:MOOD ...]"""
import sys, os, importlib, time
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
from procedural_worlds import core
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = os.path.join(root, "renders", "hero")
os.makedirs(out_dir, exist_ok=True)
for spec in args:
    st, seed, mood = spec.split(":")
    t0 = time.time()
    core.generate(bpy.context, st, seed=int(seed), size=60, detail=160, mood=mood)
    core.setup_render("BLENDER_EEVEE", res=(1920, 1080), fast=False, ink=True)
    path = os.path.join(out_dir, f"{st.lower()}_{seed}_{mood.lower()}.jpg")
    ims = bpy.context.scene.render.image_settings
    ims.file_format, ims.quality, ims.color_mode = "JPEG", 92, "RGB"
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"HERO {spec} {time.time() - t0:.1f}s {path}")

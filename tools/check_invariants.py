"""Invariant check: determinism per seed, PW_ naming/collection, and leak-free regeneration
(objects, meshes, materials, node groups, grease pencil, lights, cameras, curves).
    blender -b --factory-startup -P tools/check_invariants.py -- [SCENE_TYPE ...]"""
import sys, os, importlib
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
pw = importlib.import_module("procedural_worlds")
pw.register()
from procedural_worlds import core, scenes
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
types = args or list(scenes.REGISTRY)


def snapshot():
    col = bpy.data.collections[core.COLLECTION]
    return sorted((o.name, tuple(round(v, 4) for v in o.location)) for o in col.objects)


def counts():
    d = bpy.data
    return {k: len(getattr(d, k)) for k in ("objects", "meshes", "materials", "node_groups", "grease_pencils",
                                           "lights", "cameras", "curves", "worlds", "images", "textures")}


ok = True
for st in types:
    for ink in (True, False, True):
        core.generate(bpy.context, st, seed=7, mood="DUSK", ink=ink)
    a, c1 = snapshot(), counts()
    core.generate(bpy.context, st, seed=7, mood="DUSK")
    b, c2 = snapshot(), counts()
    core.generate(bpy.context, st, seed=8, mood="DUSK")
    c = snapshot()
    col = bpy.data.collections[core.COLLECTION]
    bad = [o.name for o in col.objects if not o.name.startswith("PW_")]
    stray = [o.name for o in bpy.context.scene.objects if o.name.startswith("PW_") and o.name not in col.objects]
    res = dict(deterministic=a == b, seed_differs=a != c, leak_free=c1 == c2, names_ok=not bad and not stray)
    ok &= all(res.values())
    print("INVARIANTS", st, res, "" if c1 == c2 else {k: (c1[k], c2[k]) for k in c1 if c1[k] != c2[k]})
print("INVARIANTS_PASS" if ok else "INVARIANTS_FAIL")

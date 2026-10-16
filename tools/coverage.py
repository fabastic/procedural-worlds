"""Coverage harness (Blender side): every presets/settings.json entry x 3 sampled layer combos
(its sensible eras, rotating genre / time / weather) rendered through COMPOSED at 640x360 into
renders/coverage/<category>/, results in renders/coverage/results.json.
    blender -b --factory-startup -P tools/coverage.py -- [entry ...]
Then: python tools/coverage_report.py   (contact sheets + COVERAGE.md)"""
import sys, os, json, time, importlib, traceback
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
settings = core.load_preset("settings")
cond = core.load_preset("conditions")
GENRES = ["noir", "fantasy", "horror", "romance", "adventure", "sci-fi", "mystery", "war", "comedy", "slice-of-life"]
TIMES = ["day", "night", "golden", "dusk"]
WEATHER = ["clear", "rain", "fog", "clear", "snow"]
out_root = os.path.join(root, "renders", "coverage")
res_path = os.path.join(out_root, "results.json")
results = json.load(open(res_path)) if os.path.exists(res_path) and args else {}
s = bpy.context.scene
for k, (name, e) in enumerate(sorted(settings.items())):
    if args and name not in args:
        continue
    rows = []
    for i, era in enumerate((e["eras"] * 3)[:3]):
        g, t, w = GENRES[(k + i * 3) % len(GENRES)], TIMES[(k + i) % 4], WEATHER[(k + 2 * i) % 5]
        layers = {"setting": name, "era": era, "genre_mood": g, "time": t, "weather": w, "state": "lived-in"}
        rec = {"layers": layers, "ok": False}
        t0 = time.time()
        try:
            info = core.generate(bpy.context, "COMPOSED", seed=11 + i, mood=cond["time"][t], layers=layers)
            core.setup_render("BLENDER_EEVEE", res=(640, 360), fast=True, ink=True)
            s.render.image_settings.file_format, s.render.image_settings.quality = "JPEG", 85
            d = os.path.join(out_root, e.get("category", "misc"))
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, f"{name}_{i}_{era}_{g}_{t}_{w}.jpg")
            s.render.filepath = path
            bpy.ops.render.render(write_still=True)
            rec.update(ok=True, render=os.path.relpath(path, root).replace("\\", "/"), focus=sorted(info.get("focus_points", {})),
                       objects=len(bpy.data.collections["PW_Generated"].objects), seconds=round(time.time() - t0, 1))
        except Exception as ex:
            rec["error"] = repr(ex)[:300]
            traceback.print_exc()
        rows.append(rec)
        print("COVER", name, era, g, t, w, "ok" if rec["ok"] else "FAIL", rec.get("seconds"))
    results[name] = {"category": e.get("category", "misc"), "kit": e["kit"], "eras": e["eras"], "runs": rows}
os.makedirs(out_root, exist_ok=True)
json.dump(results, open(res_path, "w"), indent=1)
print("COVERAGE_DONE", sum(r["ok"] for v in results.values() for r in v["runs"]), "/", sum(len(v["runs"]) for v in results.values()))

"""Render a story.json as an animated ink comic: per beat a 2-4 s clip at 12 fps "on twos" (a new
drawing every 2nd frame: camera move + Line Art boil step together) plus a still, into
story_out/<slug>/beats/<id>/{still.jpg, clip.mp4}, and story_out/<slug>/manifest.json for the web player.
    blender -b --factory-startup -P tools/render_story.py -- story.json [--beats b01,b02] [--res 1280x720]
                                                                      [--stills-only] [--keep-frames]
Each scene is generated once; clips are encoded with Blender's sequencer (no ffmpeg needed)."""
import sys, os, json, shutil, importlib, time, re
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
from procedural_worlds import core, shots, ink

TIME_TO_MOOD = {"dawn": "GOLDEN", "day": "DAY", "golden": "GOLDEN", "dusk": "DUSK", "night": "NIGHT"}
FPS = 12


def parse_args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"story": a[0], "beats": None, "res": (1280, 720), "stills_only": False, "keep": False}
    i = 1
    while i < len(a):
        if a[i] == "--beats":
            opts["beats"] = set(a[i + 1].split(","))
            i += 1
        elif a[i] == "--res":
            w, h = a[i + 1].lower().split("x")
            opts["res"] = (int(w), int(h))
            i += 1
        elif a[i] == "--stills-only":
            opts["stills_only"] = True
        elif a[i] == "--keep-frames":
            opts["keep"] = True
        i += 1
    return opts


def set_jpeg(scene, quality=90):
    ims = scene.render.image_settings
    try:
        ims.media_type = "IMAGE"
    except (AttributeError, TypeError):
        pass
    ims.file_format, ims.quality, ims.color_mode = "JPEG", quality, "RGB"


def render_beat(scene, info, beat, seed, eye, out_dir, res, stills_only, dutch=0.0):
    shot = dict(beat["shot"])
    dur = float(shot.get("duration_s", 3.0))
    sol = shots.compute_shot(info, shot, shot.get("focus", ""), seed=seed, eye_height=eye, dutch_deg=dutch)
    ink.retarget(scene, sol["focus_distance"], sol["lens"])
    cam = scene.camera
    n = max(2, int(round(dur * FPS / 2)))          # unique drawings (on twos)
    frames_dir = os.path.join(out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    mid = n // 2
    todo = [mid] if stills_only else range(n)
    for i in todo:
        t = i / (n - 1)
        loc, tgt = shots.lerp_cam(sol, t)
        shots.apply_camera(cam, loc, tgt, sol["lens"], sol.get("roll", 0.0))
        scene.frame_set(1 + 2 * i)                 # GP noise + compositor wobble step -> line boil
        path = os.path.join(frames_dir, f"u{i:03d}.jpg")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
    shutil.copyfile(os.path.join(frames_dir, f"u{mid:03d}.jpg"), os.path.join(out_dir, "still.jpg"))
    return n


def encode_clips(jobs, res, keep):
    """jobs: [(beat_dir, n_unique)] -> beat_dir/clip.mp4 at 12 fps, each drawing held 2 frames."""
    enc = bpy.data.scenes.get("PW_Encode") or bpy.data.scenes.new("PW_Encode")
    enc.render.resolution_x, enc.render.resolution_y = res
    enc.render.resolution_percentage = 100
    enc.render.fps = FPS
    enc.view_settings.view_transform = "Standard"
    try:
        enc.sequencer_colorspace_settings.name = "sRGB"
    except Exception:
        pass
    ims = enc.render.image_settings
    ims.media_type = "VIDEO"
    ims.file_format = "FFMPEG"
    enc.render.ffmpeg.format, enc.render.ffmpeg.codec = "MPEG4", "H264"
    enc.render.ffmpeg.constant_rate_factor = "HIGH"
    enc.sequence_editor_create()
    for beat_dir, n in jobs:
        frames = os.path.join(beat_dir, "frames")
        seq = os.path.join(beat_dir, "seq")
        os.makedirs(seq, exist_ok=True)
        k = 0
        for i in range(n):
            for _ in range(2):
                shutil.copyfile(os.path.join(frames, f"u{i:03d}.jpg"), os.path.join(seq, f"{k:04d}.jpg"))
                k += 1
        sed = enc.sequence_editor
        for st in list(sed.strips):
            sed.strips.remove(st)
        st = sed.strips.new_image("clip", os.path.join(seq, "0000.jpg"), channel=1, frame_start=1)
        for j in range(1, k):
            st.elements.append(f"{j:04d}.jpg")
        enc.frame_start, enc.frame_end = 1, k
        enc.render.filepath = os.path.join(beat_dir, "clip.mp4")
        bpy.ops.render.render(animation=True, scene=enc.name)
        # Blender may append the frame range to the movie name; normalise to clip.mp4
        for f in os.listdir(beat_dir):
            if f.startswith("clip") and f.endswith(".mp4") and f != "clip.mp4":
                os.replace(os.path.join(beat_dir, f), os.path.join(beat_dir, "clip.mp4"))
        shutil.rmtree(seq, ignore_errors=True)
        if not keep:
            shutil.rmtree(frames, ignore_errors=True)


def main():
    o = parse_args()
    story = json.load(open(o["story"], encoding="utf-8"))
    slug = story["slug"]
    out = os.path.join(root, "story_out", slug)
    os.makedirs(out, exist_ok=True)
    scenes = {s["id"]: s for s in story["scenes"]}
    eye = float(story.get("protagonist", {}).get("eye_height_m", 1.62))
    manifest_path = os.path.join(out, "manifest.json")
    scene = bpy.context.scene
    jobs, done_beats = [], []
    order = []
    for b in story["beats"]:
        if b["scene_id"] not in order:
            order.append(b["scene_id"])
    t_all = time.time()
    for sid in order:
        sc = scenes[sid]
        beats = [b for b in story["beats"] if b["scene_id"] == sid and (o["beats"] is None or b["id"] in o["beats"])]
        if not beats:
            continue
        mood = TIME_TO_MOOD.get(sc["layers"].get("time", "day"), "DAY")
        info = core.generate(bpy.context, sc["generator"], seed=int(sc["seed"]), size=60, detail=160, mood=mood,
                             layers=sc["layers"])
        dutch = core.genre_grade(sc["layers"]).get("camera", {}).get("dutch_deg", 0.0)
        core.setup_render("BLENDER_EEVEE", res=o["res"], fast=True, ink=True)
        set_jpeg(scene)
        sc["focus_points_resolved"] = sorted(info.get("focus_points", {}))
        for b in beats:
            t0 = time.time()
            bdir = os.path.join(out, "beats", b["id"])
            os.makedirs(bdir, exist_ok=True)
            seed = int(sc["seed"]) * 101 + story["beats"].index(b)
            n = render_beat(scene, info, b, seed, eye, bdir, o["res"], o["stills_only"], dutch)
            if not o["stills_only"]:
                jobs.append((bdir, n))
            done_beats.append(b["id"])
            missing = "" if b["shot"].get("focus") in info.get("focus_points", {}) or b["shot"]["type"] == "establishing" \
                else f" (focus '{b['shot'].get('focus')}' missing -> establishing)"
            print(f"BEAT {b['id']} {sid} {b['shot']['type']}:{b['shot'].get('focus')} {n} drawings "
                  f"{time.time() - t0:.1f}s{missing}")
    if jobs:
        encode_clips(jobs, o["res"], o["keep"])
    # manifest for the web player (keeps previously rendered beats when re-rendering a subset)
    mbeats = []
    for b in story["beats"]:
        bdir = os.path.join(out, "beats", b["id"])
        if not os.path.exists(os.path.join(bdir, "still.jpg")):
            continue
        e = {k: b[k] for k in ("id", "scene_id", "shot", "caption", "dialogue") if k in b}
        e["still"] = f"beats/{b['id']}/still.jpg"
        if os.path.exists(os.path.join(bdir, "clip.mp4")):
            e["clip"] = f"beats/{b['id']}/clip.mp4"
        e["width"], e["height"] = o["res"]
        mbeats.append(e)
    manifest = {"slug": slug, "title": story["title"], "logline": story.get("logline", ""),
                "protagonist": story.get("protagonist", {}),
                "cover": mbeats[0]["still"] if mbeats else "",
                "scenes": [{"id": s["id"], "name": s.get("name", s["id"]), "generator": s["generator"],
                            "layers": s["layers"]} for s in story["scenes"]],
                "beats": mbeats}
    if os.path.exists(os.path.join(out, "animatic.mp4")):
        manifest["animatic"] = "animatic.mp4"
    json.dump(manifest, open(manifest_path, "w", encoding="utf-8"), indent=1)
    shutil.copyfile(o["story"], os.path.join(out, "story.json"))
    print(f"STORY {slug} {len(done_beats)} beats in {time.time() - t_all:.0f}s -> {out}")


main()

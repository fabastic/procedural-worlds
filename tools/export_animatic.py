"""Assemble a rendered story into one MP4 with Blender's sequencer (no ffmpeg): title card, every beat's
clip (or still), cross-fades inside a scene, a wipe at scene changes, caption + dialogue boxes, end card.
    blender -b --factory-startup -P tools/export_animatic.py -- story_out/<slug> [--res 1280x720]
Writes story_out/<slug>/animatic.mp4 and adds "animatic" to its manifest.json."""
import sys, os, json
import bpy

FPS = 12
XF = 4          # cross-fade frames inside a scene
WIPE = 8        # wipe frames at a scene change
FONT_CANDIDATES = [r"C:\Windows\Fonts\segoeprb.ttf", r"C:\Windows\Fonts\segoepr.ttf",
                   r"C:\Windows\Fonts\comicbd.ttf", "/usr/share/fonts/truetype/comic-neue/ComicNeue-Bold.ttf"]


def args():
    a = sys.argv[sys.argv.index("--") + 1:]
    res = (1280, 720)
    if "--res" in a:
        w, h = a[a.index("--res") + 1].lower().split("x")
        res = (int(w), int(h))
    return a[0], res


def new_effect(sed, name, kind, channel, start, end, a=None, b=None):
    """Blender 5.x renamed new_effect's arguments (length/input1/input2); support both."""
    try:
        kw = {"length": end - start}
        if a is not None:
            kw["input1"] = a
        if b is not None:
            kw["input2"] = b
        return sed.strips.new_effect(name, kind, channel, start, **kw)
    except TypeError:
        kw = {"frame_end": end}
        if a is not None:
            kw["seq1"] = a
        if b is not None:
            kw["seq2"] = b
        return sed.strips.new_effect(name, kind, channel, start, **kw)


def text(sed, font, body, ch, start, end, size, loc, box=(0.97, 0.93, 0.80, 1.0), color=(0.05, 0.04, 0.03, 1.0),
         anchor_x="LEFT", anchor_y="TOP", wrap=0.42):
    t = new_effect(sed, "txt", "TEXT", ch, start, end)
    t.text = body
    t.font_size = size * bpy.context.scene.render.resolution_x / 1280.0
    t.color = color
    for k, v in (("use_box", True), ("box_color", box), ("box_margin", 0.012), ("wrap_width", wrap),
                 ("anchor_x", anchor_x), ("anchor_y", anchor_y), ("align_x", "LEFT"), ("use_shadow", False),
                 ("use_outline", False)):
        try:
            setattr(t, k, v)
        except (AttributeError, TypeError):
            pass
    t.location = loc
    if font is not None:
        t.font = font
    t.blend_type = "ALPHA_OVER"
    return t


def main():
    d, res = args()
    d = os.path.abspath(d)
    m = json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8"))
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.fps = FPS
    s.view_settings.view_transform = "Standard"
    try:
        s.sequencer_colorspace_settings.name = "sRGB"
    except Exception:
        pass
    ims = s.render.image_settings
    ims.media_type = "VIDEO"
    ims.file_format = "FFMPEG"
    s.render.ffmpeg.format, s.render.ffmpeg.codec = "MPEG4", "H264"
    s.render.ffmpeg.constant_rate_factor = "HIGH"
    sed = s.sequence_editor_create()
    font = None
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            font = bpy.data.fonts.load(f)
            break
    paper = (0.95, 0.91, 0.82, 1.0)
    # title card
    T = 3 * FPS
    bg = new_effect(sed, "title_bg", "COLOR", 1, 1, 1 + T)
    bg.color = (0.07, 0.06, 0.055)
    text(sed, font, m["title"].upper(), 6, 1, 1 + T, 64, (0.5, 0.62), box=(0, 0, 0, 0), color=paper,
         anchor_x="CENTER", anchor_y="CENTER", wrap=0.9)
    if m.get("logline"):
        text(sed, font, m["logline"], 7, 1, 1 + T, 26, (0.5, 0.36), box=(0, 0, 0, 0), color=paper,
             anchor_x="CENTER", anchor_y="CENTER", wrap=0.7)
    prev, prev_scene, cur = bg, None, 1 + T
    ch = 2
    for b in m["beats"]:
        clip = os.path.join(d, b["clip"]) if b.get("clip") else None
        dur = int(round(float(b["shot"].get("duration_s", 3.0)) * FPS))
        trans = WIPE if prev_scene is not None and b["scene_id"] != prev_scene else XF
        start = cur - trans
        ch = 3 if ch == 2 else 2           # alternate channels so neighbours can overlap
        if clip and os.path.exists(clip):
            st = sed.strips.new_movie(b["id"], clip, ch, start)
            if st.frame_final_duration < dur:
                dur = st.frame_final_duration
            st.frame_final_end = start + max(dur, trans + 2)
        else:
            st = sed.strips.new_image(b["id"], os.path.join(d, b["still"]), ch, start)
            st.frame_final_end = start + dur
        st.blend_type = "ALPHA_OVER"
        k = res[0] / float(b.get("width", res[0]))       # fit 1280-wide media into any output size
        if abs(k - 1.0) > 1e-3:
            st.transform.scale_x = st.transform.scale_y = k
        kind = "WIPE" if trans == WIPE else "GAMMA_CROSS"
        try:
            e = new_effect(sed, f"x_{b['id']}", kind, 4, start, start + trans, prev, st)
            if kind == "WIPE":
                for k, v in (("transition_type", "IRIS"), ("blur_width", 0.25)):
                    try:
                        setattr(e, k, v)
                    except (AttributeError, TypeError):
                        pass
        except Exception as ex:  # transitions are cosmetic; never block the export
            print("TRANSITION_SKIPPED", b["id"], ex)
        end = st.frame_final_end
        if b.get("caption"):
            text(sed, font, b["caption"], 6, start + trans, end, 30, (0.03, 0.95))
        for i, dl in enumerate(b.get("dialogue", [])):
            text(sed, font, f'{dl["speaker"]}: {dl["text"]}', 7 + i, start + trans + 3, end, 30,
                 (0.97, 0.10 + 0.09 * i), box=(1, 1, 1, 1), anchor_x="RIGHT", anchor_y="BOTTOM", wrap=0.5)
        prev, prev_scene, cur = st, b["scene_id"], end
    # end card
    endc = new_effect(sed, "end_bg", "COLOR", 1, cur, cur + 2 * FPS)
    endc.color = (0.07, 0.06, 0.055)
    try:
        new_effect(sed, "x_end", "GAMMA_CROSS", 4, cur - XF, cur, prev, endc)
        endc.frame_start = cur - XF
    except Exception as ex:
        print("TRANSITION_SKIPPED end", ex)
    text(sed, font, "THE END", 6, cur, cur + 2 * FPS, 64, (0.5, 0.5), box=(0, 0, 0, 0), color=paper,
         anchor_x="CENTER", anchor_y="CENTER")
    s.frame_start, s.frame_end = 1, cur + 2 * FPS
    out = os.path.join(d, "animatic.mp4")
    s.render.filepath = out
    bpy.ops.render.render(animation=True)
    for f in os.listdir(d):
        if f.startswith("animatic") and f.endswith(".mp4") and f != "animatic.mp4":
            os.replace(os.path.join(d, f), out)
    m["animatic"] = "animatic.mp4"
    json.dump(m, open(os.path.join(d, "manifest.json"), "w", encoding="utf-8"), indent=1)
    print(f"ANIMATIC {out} {s.frame_end / FPS:.1f}s")


main()

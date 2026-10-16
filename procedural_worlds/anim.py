"""Camera fly-through: a spline (PW_CamPath) starting at the scene's composed camera and drifting in
an arc toward its target; the camera rides it with Follow Path (eased) and aims with Track To at a
slowly drifting PW_CamTarget. In ink mode the lines "boil" on twos: the Line Art noise reseeds every
2 frames and the compositor wobble is keyed to the frame, like hand-animated line work."""
import math, random
import bpy
from mathutils import Vector


def setup_flythrough(context, info, seed=1, frames=72, fps=24, push=0.3, swing=0.35):
    scene = context.scene
    col = bpy.data.collections["PW_Generated"]
    cam = scene.camera
    context.view_layer.update()
    for name in ("PW_CamPath", "PW_CamTarget"):
        o = bpy.data.objects.get(name)
        if o is not None:
            from .core import remove_object
            remove_object(o)
    start = cam.matrix_world.translation.copy()
    tgt = Vector(info.get("camera", {}).get("target", (0, 0, 0)))
    rng = random.Random(seed * 31 + 7)
    to_t = tgt - start
    d = to_t.length
    fwd = to_t.normalized()
    side = fwd.cross(Vector((0, 0, 1))).normalized() * rng.choice((-1, 1))
    pts = []
    for k in range(5):
        u = k / 4
        p = start + fwd * (d * push * u) + side * (d * swing * math.sin(u * math.pi * 0.9))
        p.z += d * 0.05 * math.sin(u * math.pi)
        pts.append(p)
    cu = bpy.data.curves.new("PW_CamPath", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q.x, q.y, q.z, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 4
    path = bpy.data.objects.new("PW_CamPath", cu)
    col.objects.link(path)
    path.hide_render = True
    path["pw_line"] = 0
    path.lineart.usage = "EXCLUDE"
    aim = bpy.data.objects.new("PW_CamTarget", None)
    col.objects.link(aim)
    aim.location = tgt
    # camera rides the path (world placement comes from the path), aims at the drifting target
    cam.constraints.clear()
    cam.location = (0, 0, 0)
    fp = cam.constraints.new("FOLLOW_PATH")
    fp.target = path
    fp.use_fixed_location = True
    fp.use_curve_follow = False
    tt = cam.constraints.new("TRACK_TO")
    tt.target = aim
    tt.track_axis, tt.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    scene.frame_start, scene.frame_end = 1, frames
    scene.render.fps = fps
    fp.offset_factor = 0.0
    fp.keyframe_insert("offset_factor", frame=1)
    fp.offset_factor = 1.0
    fp.keyframe_insert("offset_factor", frame=frames)
    aim.keyframe_insert("location", frame=1)
    aim.location = tgt + side * (d * 0.08) + Vector((0, 0, d * 0.03))
    aim.keyframe_insert("location", frame=frames)
    scene.frame_set(1)
    return {"frames": frames, "fps": fps, "path_points": len(pts)}


def set_video_output(scene, filepath, res=(640, 360)):
    """MP4/H.264 output (Blender 5.x: media_type VIDEO, then FFMPEG)."""
    r = scene.render
    r.resolution_x, r.resolution_y = res
    ims = r.image_settings
    try:
        ims.media_type = "VIDEO"
    except (AttributeError, TypeError):
        pass
    ims.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"
    r.ffmpeg.codec = "H264"
    r.ffmpeg.constant_rate_factor = "HIGH"
    r.filepath = filepath

"""Shots: (scene info, shot type, focus point) -> a deterministic camera move.

Contract: every generator returns info["focus_points"] = {name: {"pos": (x,y,z), "size": s, "view": (dx,dy,dz)}}
where `view` points from the focus toward the side it is best seen from (into the room, toward the
alley axis, out to sea) and `size` is its characteristic extent in metres. Generators build them with
focus_point()/focus_from_objects() below at the end of build().

compute_shot() returns {"start": cam, "end": cam, "lens": mm} with cam = (location, target) and keeps
the camera out of walls (ray cast from the focus back to the camera) and above the ground.
"""
import math, random
import bpy
from mathutils import Vector

SHOT_TYPES = ("establishing", "wide", "medium", "close", "POV", "low", "high", "OTS")
MOVES = ("static", "push_in", "pull_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "drift", "orbit")

# distance in units of focus size, camera height offset (units of size), lens, extra pitch target lift
SHOT_RULES = {
    "wide":   dict(dist=3.4, h=0.55, lens=24, lift=0.0),
    "medium": dict(dist=1.9, h=0.25, lens=32, lift=0.0),
    "close":  dict(dist=1.05, h=0.12, lens=45, lift=0.0),
    "high":   dict(dist=1.5, h=2.0, lens=26, lift=-0.1),
    "low":    dict(dist=1.6, h=None, lens=22, lift=0.35),
    "POV":    dict(dist=1.7, h=None, lens=26, lift=0.0),
    "OTS":    dict(dist=1.9, h=None, lens=32, lift=0.0),
}


# ----------------------------------------------------------------------------- focus points
def _world_bbox(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
            hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
    return lo, hi


def focus_point(pos, view, size):
    v = Vector(view)
    v = v.normalized() if v.length > 1e-6 else Vector((0, -1, 0))
    return {"pos": tuple(round(x, 4) for x in pos), "view": tuple(round(x, 4) for x in v), "size": round(float(size), 4)}


def focus_from_objects(objs, toward, size=None, horizontal=True, z_frac=0.55):
    """Focus at the bbox of `objs` (center x/y, z at z_frac of the height), seen from `toward`."""
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.context.view_layer.update()
    lo, hi = _world_bbox(objs)
    c = (lo + hi) / 2
    c.z = lo.z + (hi.z - lo.z) * z_frac
    v = Vector(toward) - c
    if horizontal:
        v.z = 0
    s = size if size is not None else max(0.25, max(hi - lo) * 0.9)
    return focus_point(c, v, s)


def objects_named(col, prefix):
    return sorted([o for o in col.objects if o.name == prefix or o.name.startswith(prefix + "_")
                   or (prefix.endswith("*") and o.name.startswith(prefix[:-1]))], key=lambda o: o.name)


# ----------------------------------------------------------------------------- shot solving
def _ray_free(scene, depsgraph, a, b, skip=()):
    """Distance free from a toward b (stops at the first hit not in skip)."""
    d = b - a
    L = d.length
    if L < 1e-6:
        return L
    dirn = d / L
    origin = a.copy()
    travelled = 0.0
    for _ in range(6):
        hit, loc, nrm, idx, ob, mat = scene.ray_cast(depsgraph, origin, dirn, distance=L - travelled)
        if not hit:
            return L
        if ob is not None and (ob.name in skip or ob.get("pw_line", 1) == 0 or ob.name.startswith("PW_Reflect")):
            step = (loc - origin).length + 0.02
            origin = loc + dirn * 0.02
            travelled += step
            continue
        return travelled + (loc - origin).length
    return L


def _skip(ob, skip):
    return ob is not None and (ob.name in skip or ob.name.startswith("PW_Reflect") or ob.get("pw_line", 1) == 0)


def _cast(scene, depsgraph, origin, dirn, dist, skip):
    o = origin.copy()
    for _ in range(5):
        hit, loc, nrm, idx, ob, mat = scene.ray_cast(depsgraph, o, dirn, distance=dist)
        if not hit:
            return None, None
        if _skip(ob, skip):
            o = loc + dirn * 0.02
            continue
        return loc, nrm
    return None, None


def _ground_z(scene, depsgraph, p, skip=()):
    """Floor/terrain height under p. Casts down from just above p (so interiors don't hit the
    ceiling); if p is buried under terrain (an upward-facing surface above it) returns that surface."""
    up, nrm = _cast(scene, depsgraph, p, Vector((0, 0, 1)), 60.0, skip)
    if up is not None and nrm.z > 0.3:
        return up.z
    down, _ = _cast(scene, depsgraph, p + Vector((0, 0, 0.3)), Vector((0, 0, -1)), 200.0, skip)
    return down.z if down is not None else 0.0


def _place(scene, dg, focus, cam, skip, margin=0.3, min_clear=0.6):
    """Pull the camera toward the focus until the line of sight is clear; keep it above ground."""
    f = Vector(focus["pos"])
    s = focus["size"]
    start = f + (cam - f).normalized() * min(s * 0.6, (cam - f).length * 0.5)
    free = _ray_free(scene, dg, start, cam, skip)
    want = (cam - start).length
    if free < want:
        cam = start + (cam - start).normalized() * max(free - margin, 0.05)
    gz = _ground_z(scene, dg, cam, skip)
    if cam.z < gz + min_clear:
        cam.z = gz + min_clear
    return cam


def establishing(info):
    c = info["camera"]
    tgt = Vector(c.get("target", (0, 0, 0)))
    if c.get("location") is not None:
        loc = Vector(c["location"])
    else:
        a = math.radians(c.get("angle", 35))
        d = c.get("distance", 45)
        loc = Vector((tgt.x + math.sin(a) * d, tgt.y - math.cos(a) * d, c.get("height", 12)))
    return loc, tgt, c.get("lens", 35)


def compute_shot(info, shot, focus_name, seed=0, eye_height=1.62, skip=(), dutch_deg=0.0):
    """Return {"start": (loc, tgt), "end": (loc, tgt), "lens": mm, "focus_distance": d}."""
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    typ = shot.get("type", "medium")
    move = shot.get("camera_move", "static")
    rng = random.Random(f"{seed}:{focus_name}:{typ}:{move}")
    fps = info.get("focus_points", {})
    focus = fps.get(focus_name)
    roll = math.radians(dutch_deg) * rng.choice((-1, 1)) if typ in ("low", "high", "OTS", "close", "POV") else 0.0
    if typ == "establishing" or focus is None:      # the generator's composed hero framing
        loc, tgt, lens = establishing(info)
        f = {"pos": tuple(tgt), "size": max(1.0, (loc - tgt).length / 3.0), "view": tuple((loc - tgt).normalized())}
        out = _with_move(scene, dg, f, loc, tgt, lens, move, rng, skip, place=False)
        out["roll"] = 0.0
        return out
    R = SHOT_RULES.get(typ, SHOT_RULES["medium"])
    f = Vector(focus["pos"])
    s = focus["size"]
    v = Vector(focus["view"])
    yaw = math.radians(rng.uniform(-22, 22))
    v = Vector((v.x * math.cos(yaw) - v.y * math.sin(yaw), v.x * math.sin(yaw) + v.y * math.cos(yaw), v.z))
    hv = Vector((v.x, v.y, 0)).normalized() if Vector((v.x, v.y)).length > 1e-4 else Vector((0, -1, 0))
    d = s * R["dist"]
    cam = f + hv * d
    tgt = f.copy()
    if typ in ("POV", "OTS"):
        gz = _ground_z(scene, dg, cam, skip)
        cam.z = gz + eye_height
        if typ == "OTS":
            side = Vector((-hv.y, hv.x, 0)) * rng.choice((-1, 1))
            cam += side * max(0.35, s * 0.3) + hv * 0.3
            tgt += side * (s * 0.12)
    elif typ == "low":
        gz = _ground_z(scene, dg, cam, skip)
        cam.z = gz + 0.35
        tgt.z += s * R["lift"]
    else:
        cam.z = f.z + s * R["h"]
        tgt.z += s * R["lift"]
    cam = _place(scene, dg, focus, cam, skip)
    out = _with_move(scene, dg, focus, cam, tgt, R["lens"], move, rng, skip, place=True)
    out["roll"] = roll
    return out


def _with_move(scene, dg, focus, cam, tgt, lens, move, rng, skip, place):
    d = (cam - tgt).length
    fwd = (tgt - cam).normalized()
    side = fwd.cross(Vector((0, 0, 1)))
    side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
    a_loc, a_tgt, b_loc, b_tgt = cam.copy(), tgt.copy(), cam.copy(), tgt.copy()
    k = rng.choice((-1, 1))
    if move == "push_in":
        a_loc = tgt + (cam - tgt) * 1.10
        b_loc = tgt + (cam - tgt) * 0.86
    elif move == "pull_out":
        a_loc = tgt + (cam - tgt) * 0.88
        b_loc = tgt + (cam - tgt) * 1.10
    elif move in ("pan_left", "pan_right"):
        sgn = -1 if move == "pan_left" else 1
        a_tgt = tgt - side * sgn * d * 0.06
        b_tgt = tgt + side * sgn * d * 0.06
    elif move in ("tilt_up", "tilt_down"):
        sgn = 1 if move == "tilt_up" else -1
        a_tgt = tgt - Vector((0, 0, sgn * d * 0.07))
        b_tgt = tgt + Vector((0, 0, sgn * d * 0.07))
    elif move == "drift":
        a_loc = cam - side * k * d * 0.04
        b_loc = cam + side * k * d * 0.04
    elif move == "orbit":
        for ang, which in ((-0.08, "a"), (0.08, "b")):
            r = cam - tgt
            ca, sa = math.cos(ang * k), math.sin(ang * k)
            p = tgt + Vector((r.x * ca - r.y * sa, r.x * sa + r.y * ca, r.z))
            if which == "a":
                a_loc = p
            else:
                b_loc = p
    else:  # static still breathes a little
        a_loc = cam - side * k * d * 0.012
        b_loc = cam + side * k * d * 0.012
    if place:
        a_loc = _place(scene, dg, focus, a_loc, skip)
        b_loc = _place(scene, dg, focus, b_loc, skip)
    return {"start": (a_loc, a_tgt), "end": (b_loc, b_tgt), "lens": lens,
            "focus_distance": (cam - tgt).length}


def apply_camera(cam_obj, loc, tgt, lens, roll=0.0):
    from mathutils import Quaternion
    cam_obj.constraints.clear()
    cam_obj.location = loc
    q = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y")
    if roll:
        q = q @ Quaternion((0.0, 0.0, 1.0), roll)       # dutch angle around the view axis
    cam_obj.rotation_euler = q.to_euler()
    cam_obj.data.lens = lens


def lerp_cam(shot, t):
    """Eased interpolation of the shot's move at t in [0, 1]."""
    e = t * t * (3 - 2 * t)
    (al, at), (bl, bt) = shot["start"], shot["end"]
    return al.lerp(bl, e), at.lerp(bt, e)

"""Nature asset pack, part 2: settlement + rural props, era / culture aware across the timeline.

Buildings pick a style from the era's roof + prop tags (era_style): thatch, timber gable, slate gable,
tiled hip (classical), pagoda (Japan/China), flat adobe (Egypt/Mughal-ish desert), dome (Islamic /
Mughal), western false front, norse longhouse, makeshift shack (post-apocalyptic), eco terrace house
(solarpunk), pod / hab dome (future / space). Fences, wells, carts, lamps and signposts switch with the
era family; era-signature props (obelisk, torii, stone lantern, cannon, wreck, water tower, rover...)
are registered for the era-signature settings."""
import math
from mathutils import Vector, Matrix
from .nature import (nat, NAT, STYLE, era_style, has_tag, frame, box, cyl, limb, chain, blob, rock, jag_cone, ribbon,
                     blade, branches, smooth, _xf, TAU)
from ..props import OLD, MID, NOW, FUT, in_family


def fam(era):
    return era_style(era)[0]


def is_old(era):
    return fam(era) in ("ancient", "medieval", "1700s-1800s")


def is_ancient(era):
    return fam(era) in ("ancient", "medieval")


def is_fut(era):
    return fam(era) in ("near-future", "far-future")


def poly(mb, M, pts, key):
    vs = [mb.bm.verts.new(p) for p in pts]
    mb._tag([mb.bm.faces.new(vs)], key)
    return _xf(mb, vs, M)


def faces(mb, M, verts, idx, key):
    vs = [mb.bm.verts.new(p) for p in verts]
    fs = [mb.bm.faces.new([vs[i] for i in f]) for f in idx]
    mb._tag(fs, key)
    return _xf(mb, vs, M)


# ----------------------------------------------------------------------------- roofs
def gable_roof(mb, M, w, d, z0, rise, key, oh=0.35, t=0.14, gable_key=None):
    """Two slabs along x meeting at a ridge (rise above the wall top z0); gable triangles in gable_key."""
    sl = rise / (d / 2)
    hw = d / 2 + oh
    drop = oh * sl
    L = math.hypot(hw, rise + drop)
    a = math.atan(sl)
    for sg in (-1, 1):
        box(mb, M, (0, sg * hw / 2, z0 + (rise - drop) / 2 + t / 2), (w + 2 * oh, L, t), key, rx=-sg * a)
    if gable_key:
        for sx in (-1, 1):
            poly(mb, M, [(sx * w / 2, -d / 2, z0), (sx * w / 2, d / 2, z0), (sx * w / 2, 0, z0 + rise)], gable_key)


def hip_roof(mb, M, w, d, z0, rise, key, oh=0.4, ridge=0.5, lift=0.0, sag=0.0):
    """Hip roof; lift raises the eave corners (pagoda), sag lowers the eave mid-points."""
    x, y = w / 2 + oh, d / 2 + oh
    r = max(0.05, (w - d) / 2 * ridge)
    V = [(-x, -y, z0 + lift), (0, -y, z0 - sag), (x, -y, z0 + lift), (x, 0, z0 - sag),
         (x, y, z0 + lift), (0, y, z0 - sag), (-x, y, z0 + lift), (-x, 0, z0 - sag),
         (-r, 0, z0 + rise), (r, 0, z0 + rise)]
    F = [(0, 1, 8), (1, 9, 8), (1, 2, 9), (2, 3, 9), (3, 4, 9), (4, 5, 9), (5, 8, 9), (5, 6, 8), (6, 7, 8), (7, 0, 8),
         (7, 6, 5, 4, 3, 2, 1, 0)]
    return faces(mb, M, V, F, key)


def dome(mb, M, c, r, key, rng, sq=1.0, finial="n_gold"):
    vs = mb.sphere((0, 0, 0), r, key, sub=2)
    for v in vs:
        if v.co.z < 0:
            v.co.z *= 0.05
        v.co.z *= sq
    smooth(vs)
    _xf(mb, vs, M @ Matrix.Translation(c))
    if finial:
        limb(mb, M, Vector(c) + Vector((0, 0, r * sq * 0.95)), Vector(c) + Vector((0, 0, r * sq + 0.5)), 0.06, 0.0, finial, seg=5)


# ----------------------------------------------------------------------------- buildings
def house_style(era, rural=True):
    f, roof, tags, cul = era_style(era)
    if "space" in tags:
        return "hab"
    if "makeshift" in tags or "ruined" in tags:
        return "shack"
    if "green" in tags and "futuristic" in tags:
        return "eco"
    if f in ("near-future", "far-future"):
        return "pod"
    if "western" in tags:
        return "western"
    if "norse" in tags:
        return "longhouse"
    if roof == "pagoda":
        return "pagoda"
    if roof == "dome":
        return "dome"
    if roof == "thatch":
        return "thatch"
    if roof == "tiled":
        return "tiled"
    if roof == "flat":
        if f in ("ancient", "medieval", "1700s-1800s"):
            return "adobe"
        return "gable_modern" if rural else "flat"
    if f in ("ancient", "medieval"):
        return "timber"
    if f == "1700s-1800s":
        return "gable_old"
    return "gable_modern"


def _windows(mb, M, w, d, z, rng, key="n_glowwin", frame_key="trim", n=2, side=-1, shutters=None):
    for i in range(n):
        x = -w / 2 + w * (i + 0.5) / n
        if abs(x) < 0.7 and n > 1:
            x += 0.9 * (1 if x >= 0 else -1)
        box(mb, M, (x, side * (d / 2 + 0.03), z), (0.7, 0.06, 0.8), key)
        box(mb, M, (x, side * (d / 2 + 0.06), z), (0.82, 0.03, 0.06), frame_key)
        box(mb, M, (x, side * (d / 2 + 0.06), z - 0.44), (0.9, 0.12, 0.08), frame_key)
        if shutters:
            for sx in (-1, 1):
                box(mb, M, (x + sx * 0.52, side * (d / 2 + 0.06), z), (0.3, 0.04, 0.86), shutters)


def house(mb, x, y, z, rot, rng, era, w=None, d=None, style=None):
    """A small settlement building in the era / culture's style. Front (door) faces local -y.
    Returns the local door point (world) for focus / paths."""
    style = style or house_style(era)
    M = frame(x, y, z, rot)
    w = w or rng.uniform(5.0, 7.0)
    d = d or rng.uniform(4.0, 5.0)
    door = (0.0 if rng.random() < 0.5 else rng.uniform(-w * 0.25, w * 0.25))
    if style == "longhouse":
        w, d = w * 2.0, d * 1.1
    if style in ("timber", "thatch", "longhouse"):
        h = 2.4 if style != "longhouse" else 1.6
        box(mb, M, (0, 0, h / 2), (w, d, h), "wall")
        box(mb, M, (0, 0, 0.2), (w + 0.1, d + 0.1, 0.4), "stone")
        if style == "timber":
            for k in range(5):                                         # half-timber frame
                xx = -w / 2 + w * k / 4
                box(mb, M, (xx, -d / 2 - 0.04, h / 2), (0.16, 0.06, h), "wood2")
            box(mb, M, (0, -d / 2 - 0.04, h * 0.55), (w, 0.06, 0.14), "wood2")
            for k in range(4):
                xx = -w / 2 + w * (k + 0.5) / 4
                box(mb, M, (xx, -d / 2 - 0.05, h * 0.78), (w / 4 * 1.05, 0.05, 0.12), "wood2", ry=0.55 * (1 if k % 2 else -1))
        if style == "longhouse":
            for k in range(9):
                box(mb, M, (-w / 2 + w * k / 8, -d / 2 - 0.05, h / 2), (0.14, 0.08, h), "wood2")
        box(mb, M, (door, -d / 2 - 0.04, 0.95), (0.9, 0.08, 1.9 if style != "longhouse" else 1.5), "wood2")
        _windows(mb, M, w, d, 1.45 if style != "longhouse" else 1.1, rng, n=2 if style != "longhouse" else 0, frame_key="wood2")
        rise = d * (0.75 if style != "longhouse" else 0.95)
        hip_roof(mb, M, w, d, h, rise, "n_thatch", oh=0.55, ridge=0.75)
        box(mb, M, (0, 0, h + rise + 0.05), (w * 0.75 * 0.75 + 0.3, 0.45, 0.25), "n_hay2")
        if style == "longhouse":
            for sx in (-1, 1):                                         # crossed gable horns
                for sg in (-1, 1):
                    limb(mb, M, (sx * (w / 2 * 0.75 * 0.75), 0, h + rise - 0.1), (sx * (w / 2 * 0.6), sg * 0.7, h + rise + 1.0), 0.08, 0.04, "wood2", seg=4)
        else:
            box(mb, M, (w * 0.3, d * 0.15, h + rise * 0.7), (0.6, 0.6, rise * 0.9), "stone")
    elif style in ("gable_old", "gable_modern"):
        h = 2.8 if style == "gable_old" else 2.7
        wallk = "wall" if style == "gable_old" else "wall2"
        box(mb, M, (0, 0, h / 2), (w, d, h), wallk)
        box(mb, M, (0, 0, 0.18), (w + 0.12, d + 0.12, 0.36), "stone" if style == "gable_old" else "trim")
        if style == "gable_modern":
            for k in range(int(h / 0.3)):                              # lap siding
                box(mb, M, (0, -d / 2 - 0.02, 0.4 + k * 0.3), (w, 0.03, 0.04), "trim")
        box(mb, M, (door, -d / 2 - 0.04, 1.0), (0.95, 0.08, 2.0), "accent" if style == "gable_modern" else "wood2")
        _windows(mb, M, w, d, 1.6, rng, n=2, shutters="accent" if style == "gable_old" else None)
        rise = d * 0.45
        gable_roof(mb, M, w, d, h, rise, "n_slate" if style == "gable_old" else "n_tile" if rng.random() < 0.4 else "n_slate", gable_key=wallk)
        box(mb, M, (-w * 0.3, d * 0.1, h + rise * 0.8), (0.55, 0.55, rise * 1.1), "stone" if style == "gable_old" else "n_red")
        if style == "gable_modern":                                    # porch
            box(mb, M, (door, -d / 2 - 0.9, 0.12), (2.4, 1.8, 0.24), "wood")
            for sx in (-1, 1):
                box(mb, M, (door + sx * 1.1, -d / 2 - 1.7, 1.3), (0.1, 0.1, 2.4), "n_white")
            box(mb, M, (door, -d / 2 - 0.9, 2.55), (2.6, 2.0, 0.1), "n_slate", rx=-0.12)
    elif style == "tiled":
        h = 3.0
        box(mb, M, (0, 0, h / 2), (w, d, h), "wall")
        box(mb, M, (door, -d / 2 - 0.04, 1.0), (0.95, 0.08, 2.0), "wood2")
        _windows(mb, M, w, d, 1.9, rng, n=2, shutters="accent")
        box(mb, M, (0, 0, h + 0.06), (w + 0.2, d + 0.2, 0.12), "trim")
        hip_roof(mb, M, w, d, h + 0.12, d * 0.28, "n_tile", oh=0.45, ridge=0.6)
    elif style == "pagoda":
        h = 2.6
        box(mb, M, (0, 0, 0.3), (w + 0.8, d + 0.8, 0.6), "stone")
        box(mb, M, (0, 0, 0.6 + h / 2), (w, d, h), "n_plaster")
        for k in range(5):
            xx = -w / 2 + w * k / 4
            box(mb, M, (xx, -d / 2 - 0.05, 0.6 + h / 2), (0.16, 0.12, h), "trim")
        box(mb, M, (0, -d / 2 - 0.05, 0.6 + h - 0.2), (w, 0.12, 0.2), "trim")
        for k in range(3):                                             # shoji panels
            box(mb, M, (-w * 0.25 + k * w * 0.25, -d / 2 - 0.03, 0.6 + h * 0.48), (w * 0.22, 0.04, h * 0.7), "n_glowwin" if k == 1 else "paper")
        hip_roof(mb, M, w, d, 0.6 + h, d * 0.42, "n_slate", oh=0.9, ridge=0.55, lift=0.45, sag=0.12)
        box(mb, M, (0, 0, 0.6 + h + d * 0.42 + 0.08), (w * 0.55 * 0.55 + 0.6, 0.3, 0.2), "n_slate")
    elif style in ("adobe", "flat", "western"):
        h = 2.8 if style != "western" else 3.2
        wallk = "wall" if style != "flat" else "wall2"
        box(mb, M, (0, 0, h / 2), (w, d, h), wallk)
        if style == "western":                                         # false front + boardwalk + awning
            box(mb, M, (0, -d / 2 - 0.05, h + 0.9), (w, 0.16, 1.8), "wood")
            box(mb, M, (0, -d / 2 - 0.08, h + 1.0), (w * 0.7, 0.06, 0.6), "n_white")
            box(mb, M, (0, -d / 2 - 1.1, 0.15), (w + 0.4, 2.2, 0.3), "wood2")
            box(mb, M, (0, -d / 2 - 1.1, 2.6), (w + 0.4, 2.2, 0.1), "wood2", rx=-0.1)
            for k in range(4):
                box(mb, M, (-w / 2 + w * k / 3, -d / 2 - 2.1, 1.35), (0.12, 0.12, 2.5), "wood2")
            box(mb, M, (door, -d / 2 - 0.04, 1.0), (1.2, 0.08, 2.0), "wood2")
            _windows(mb, M, w, d, 1.5, rng, n=2, frame_key="wood2")
        else:
            for sx in (-1, 1):                                         # parapet
                box(mb, M, (sx * w / 2, 0, h + 0.25), (0.25, d, 0.5), wallk)
                box(mb, M, (0, sx * d / 2, h + 0.25), (w, 0.25, 0.5), wallk)
            if style == "adobe":
                for k in range(5):                                     # vigas
                    cyl(mb, M, (-w / 2 + w * (k + 0.5) / 5, -d / 2 - 0.25, h - 0.3), 0.09, 0.6, "wood2", seg=6, axis="Y")
                box(mb, M, (door, -d / 2 - 0.04, 1.0), (0.9, 0.08, 1.9), "dark")
                box(mb, M, (door, -d / 2 - 0.05, 1.95), (1.1, 0.1, 0.12), "trim")
                for sx in (-1, 1):
                    box(mb, M, (sx * w * 0.3, -d / 2 - 0.03, 1.8), (0.5, 0.06, 0.5), "n_glowwin")
                box(mb, M, (0, 0, h + 0.05), (w - 0.3, d - 0.3, 0.1), "wall2")
            else:
                box(mb, M, (door, -d / 2 - 0.04, 1.0), (1.0, 0.08, 2.0), "accent")
                box(mb, M, (-door * 0.3 + w * 0.2, -d / 2 - 0.03, 1.6), (w * 0.4, 0.06, 1.3), "n_glowwin")
    elif style == "dome":
        h = 3.2
        box(mb, M, (0, 0, h / 2), (w, d, h), "wall")
        box(mb, M, (0, 0, h + 0.1), (w + 0.2, d + 0.2, 0.2), "trim")
        cyl(mb, M, (0, 0, h + 0.5), min(w, d) * 0.36, 0.6, "wall", seg=16)
        dome(mb, M, (0, 0, h + 0.8), min(w, d) * 0.36, "accent", rng, sq=1.1)
        box(mb, M, (door, -d / 2 - 0.05, 1.2), (1.1, 0.1, 2.4), "dark")
        box(mb, M, (door, -d / 2 - 0.07, 2.4), (1.4, 0.08, 0.3), "trim")
        _windows(mb, M, w, d, 1.8, rng, n=2, frame_key="trim")
    elif style == "shack":
        h = 2.3
        for k in range(6):                                             # patchwork walls
            xx = -w / 2 + w * (k + 0.5) / 6
            box(mb, M, (xx, 0, h / 2 + rng.uniform(-0.1, 0.1)), (w / 6 + 0.05, d, h), rng.choice(("n_rust", "metal2", "wood2", "n_tarp")),
                rz=rng.uniform(-0.03, 0.03))
        box(mb, M, (0, 0, h + 0.2), (w + 0.6, d + 0.6, 0.08), "n_rust", rx=0.12, ry=0.04)
        box(mb, M, (door, -d / 2 - 0.05, 0.95), (0.9, 0.08, 1.9), "n_tarp")
        cyl(mb, M, (w * 0.35, d * 0.2, h + 0.9), 0.15, 1.6, "metal2", seg=6)
        for k in range(3):
            cyl(mb, M, (w / 2 + 0.6, -d / 2 + k * 0.8, 0.12), 0.35, 0.24, "dark", seg=10)
    elif style == "eco":
        h = 2.8
        box(mb, M, (0, 0, h / 2), (w, d, h), "wall")
        box(mb, M, (0, -d / 2 - 0.03, h * 0.5), (w * 0.8, 0.06, h * 0.7), "n_glowwin")
        for k in range(5):
            box(mb, M, (-w * 0.4 + k * w * 0.2, -d / 2 - 0.08, h * 0.5), (0.1, 0.1, h), "wood")
        box(mb, M, (0, 0, h + 0.15), (w + 0.6, d + 0.6, 0.3), "wood")
        for k in range(6):                                             # green roof
            NAT["bush"](mb, *(M @ Vector((-w / 2 + w * (k + 0.5) / 6, rng.uniform(-d * 0.3, d * 0.3), h + 0.3))).to_tuple(), 0, rng, era, 0.7)
        for k in range(3):
            box(mb, M, (-w * 0.3 + k * w * 0.3, d * 0.45, h + 0.9), (w * 0.26, 1.2, 0.06), "n_solar", rx=-0.5)
    elif style == "pod":
        h = 3.0
        cyl(mb, M, (0, 0, h / 2), min(w, d) * 0.55, h, "wall", seg=16)
        dome(mb, M, (0, 0, h), min(w, d) * 0.55, "wall2", rng, sq=0.5, finial=None)
        box(mb, M, (0, -min(w, d) * 0.55, 1.1), (1.0, 0.3, 2.2), "dark")
        cyl(mb, M, (0, 0, h * 0.62), min(w, d) * 0.56, 0.18, "accent", seg=16)
    elif style == "hab":
        r = min(w, d) * 0.6
        cyl(mb, M, (0, 0, 0.4), r, 0.8, "metal", seg=18)
        dome(mb, M, (0, 0, 0.8), r, "wall", rng, sq=0.75, finial=None)
        for k in range(3):
            cyl(mb, M, (0, 0, 0.8 + r * 0.75 * (0.3 + k * 0.25)), r * (0.97 - k * 0.12), 0.08, "metal2", seg=18)
        box(mb, M, (0, -r - 0.8, 1.0), (1.4, 2.0, 1.8), "metal")
        cyl(mb, M, (0, -r - 1.8, 1.0), 0.6, 0.12, "accent", seg=12, axis="Y")
    return M @ Vector((door, -d / 2 - 1.2, 0))


nat("cottage", size=(7, 6, 6), rooms=("village", "settlement", "farm", "rural"))(house)


@nat("longhouse", size=(14, 6, 6), eras=OLD, rooms=("village", "norse", "settlement"))
def longhouse(mb, x, y, z, rot, rng, era):
    house(mb, x, y, z, rot, rng, era, style="longhouse")


@nat("stilt_hut", size=(5, 5, 6), rooms=("shore", "jungle", "swamp", "tropical", "military"))
def stilt_hut(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    w, d, f = 4.0, 3.4, 1.6
    for sx in (-1, 1):
        for sy in (-1, 1):
            limb(mb, M, (sx * w * 0.45, sy * d * 0.45, -0.6), (sx * w * 0.45, sy * d * 0.45, f), 0.1, 0.09, "wood2", seg=5)
    box(mb, M, (0, 0, f), (w + 0.6, d + 0.6, 0.15), "wood")
    box(mb, M, (0, 0, f + 1.1), (w, d, 2.1), "n_bamboo" if not is_fut(era) else "wall")
    box(mb, M, (0, -d / 2 - 0.04, f + 0.95), (0.8, 0.06, 1.7), "dark")
    hip_roof(mb, M, w, d, f + 2.15, 1.6, "n_thatch" if not in_family(era, "near-future", "far-future") else "n_rust", oh=0.6, ridge=0.5)
    for k in range(5):                                                 # ladder
        box(mb, M, (0, -d / 2 - 0.5 - 0.12 * k, f - 0.3 * k - 0.15), (0.7, 0.08, 0.05), "wood2")
    for sx in (-1, 1):
        limb(mb, M, (sx * 0.35, -d / 2 - 0.4, f), (sx * 0.35, -d / 2 - 1.0, -0.1), 0.04, 0.04, "wood2", seg=4)


@nat("fishing_hut", size=(4, 4, 4), rooms=("shore", "dock", "lake"))
def fishing_hut(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    w, d, h = 3.2, 2.8, 2.2
    box(mb, M, (0, 0, h / 2), (w, d, h), rng.choice(("n_red", "n_blue", "wood", "n_teal")) if not is_ancient(era) else "wood")
    for k in range(9):
        box(mb, M, (-w / 2 + w * k / 8, -d / 2 - 0.03, h / 2), (0.05, 0.04, h), "wood2")
    box(mb, M, (0.6, -d / 2 - 0.05, 0.9), (0.8, 0.06, 1.7), "dark")
    box(mb, M, (-0.8, -d / 2 - 0.05, 1.5), (0.5, 0.06, 0.45), "n_glowwin")
    gable_roof(mb, M, w, d, h, 1.1, "n_slate" if not is_ancient(era) else "n_thatch", oh=0.3, gable_key="wood")
    NAT["fishing_net"](mb, *(M @ Vector((w / 2 + 0.7, 0, 0))).to_tuple(), rot + math.pi / 2, rng, era)


# ----------------------------------------------------------------------------- fences, walls, gates
def _fence_run(mb, M, L, rng, era, kind):
    n = max(2, int(L / 2.0) + 1)
    if kind == "picket":
        for k in range(int(L / 0.18)):
            box(mb, M, (-L / 2 + k * 0.18, 0, 0.5), (0.08, 0.03, 1.0), "n_white")
            limb(mb, M, (-L / 2 + k * 0.18, 0, 1.0), (-L / 2 + k * 0.18, 0, 1.1), 0.045, 0.0, "n_white", seg=4)
        for zz in (0.3, 0.75):
            box(mb, M, (0, 0.03, zz), (L, 0.03, 0.08), "n_white")
    elif kind == "split_rail":
        for k in range(n):
            xx = -L / 2 + L * k / (n - 1)
            box(mb, M, (xx, 0, 0.55), (0.14, 0.14, 1.1), "wood2", rz=rng.uniform(-0.1, 0.1))
        for zz in (0.45, 0.85):
            limb(mb, M, (-L / 2, 0, zz), (L / 2, 0, zz + rng.uniform(-0.05, 0.05)), 0.06, 0.05, "wood", seg=5)
    elif kind == "stone":
        for k in range(int(L / 0.55)):
            for j in range(3):
                rock(mb, M, (-L / 2 + k * 0.55 + (0.27 if j % 2 else 0), rng.uniform(-0.06, 0.06), 0.15 + j * 0.28), 0.3,
                     rng.choice(("stone", "n_rock", "n_rock2")), rng, flat=0.6, sub=0, sx=1.2)
    elif kind == "barbed":
        for k in range(n):
            xx = -L / 2 + L * k / (n - 1)
            box(mb, M, (xx, 0, 0.65), (0.08, 0.08, 1.3), "wood2" if not in_family(era, "near-future", "far-future") else "metal2", rz=rng.uniform(-0.1, 0.1))
        for zz in (0.35, 0.7, 1.05):
            limb(mb, M, (-L / 2, 0, zz), (L / 2, 0, zz - 0.04), 0.012, 0.012, "metal2", seg=3)
            for k in range(int(L / 0.4)):
                box(mb, M, (-L / 2 + k * 0.4, 0, zz), (0.06, 0.06, 0.02), "metal2", rz=0.8)
    elif kind == "bamboo":
        for k in range(int(L / 0.12)):
            limb(mb, M, (-L / 2 + k * 0.12, 0, -0.05), (-L / 2 + k * 0.12, 0, 1.3 + 0.05 * math.sin(k)), 0.05, 0.05, "n_bamboo", seg=5)
        for zz in (0.4, 1.0):
            box(mb, M, (0, 0.06, zz), (L, 0.05, 0.06), "n_rope")
    elif kind == "palisade":
        for k in range(int(L / 0.3)):
            hh = rng.uniform(2.2, 2.7)
            limb(mb, M, (-L / 2 + k * 0.3, 0, -0.1), (-L / 2 + k * 0.3, 0, hh), 0.15, 0.14, "wood2", seg=5)
            limb(mb, M, (-L / 2 + k * 0.3, 0, hh), (-L / 2 + k * 0.3, 0, hh + 0.35), 0.14, 0.0, "wood2", seg=5)
    elif kind == "rail_metal":
        for k in range(n):
            box(mb, M, (-L / 2 + L * k / (n - 1), 0, 0.5), (0.06, 0.06, 1.0), "metal")
        for zz in (0.5, 0.95):
            box(mb, M, (0, 0, zz), (L, 0.04, 0.04), "accent" if in_family(era, "near-future", "far-future") else "metal")


def fence_kind(era):
    f, roof, tags, cul = era_style(era)
    if "japanese" in tags or "chinese" in tags:
        return "bamboo"
    if "norse" in tags:
        return "palisade"
    if "western" in tags or "colonial" in tags:
        return "split_rail"
    if f in ("ancient", "medieval"):
        return "stone" if "classical" in tags else "split_rail"
    if f == "1700s-1800s":
        return "stone"
    if f in ("1920s-50s",):
        return "picket" if "military" not in tags else "barbed"
    if f == "modern":
        return "barbed" if "makeshift" in tags else "picket"
    return "rail_metal"


@nat("fence", size=(4, 0.3, 1.1), rooms=("village", "farm", "rural", "garden", "outdoor"))
def fence(mb, x, y, z, rot, rng, era, L=4.0, kind=None):
    _fence_run(mb, frame(x, y, z, rot), L, rng, era, kind or fence_kind(era))


for _k in ("picket", "split_rail", "stone", "barbed", "bamboo", "palisade"):
    nat(f"fence_{_k}" if _k != "stone" else "stone_wall", size=(4, 0.4, 1.1), rooms=("village", "farm", "rural", "garden", "military"))(
        lambda mb, x, y, z, rot, rng, era, L=4.0, _k=_k: _fence_run(mb, frame(x, y, z, rot), L, rng, era, _k))


@nat("gate", size=(3.2, 0.4, 1.4), rooms=("farm", "rural", "village"))
def gate(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    metal = fam(era) in ("modern", "near-future", "far-future")
    k = "metal" if metal else "wood"
    for sx in (-1.5, 1.5):
        box(mb, M, (sx, 0, 0.75), (0.2, 0.2, 1.5), "wood2" if not metal else "metal2")
    for zz in (0.3, 0.65, 1.0, 1.3):
        box(mb, M, (0, 0, zz), (2.8, 0.06, 0.1), k)
    box(mb, M, (0, 0, 0.8), (2.95, 0.06, 0.1), k, ry=math.atan2(1.0, 2.8))
    for xx in (-1.3, 1.3):
        box(mb, M, (xx, 0, 0.8), (0.1, 0.07, 1.1), k)


# ----------------------------------------------------------------------------- water + farm
@nat("well", size=(2, 2, 2.8), rooms=("village", "farm", "rural", "outdoor"))
def well(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    f = fam(era)
    if f in ("modern", "near-future", "far-future") and not has_tag(era, "makeshift"):
        cyl(mb, M, (0, 0, 0.35), 0.55, 0.7, "stone", seg=12)
        box(mb, M, (0, 0, 0.75), (0.2, 0.2, 0.1), "metal2")
        box(mb, M, (0, 0, 1.15), (0.12, 0.12, 0.8), "accent" if f != "modern" else "n_red")
        box(mb, M, (0.25, 0, 1.45), (0.5, 0.06, 0.06), "metal2")
        box(mb, M, (-0.15, 0, 1.25), (0.3, 0.08, 0.08), "metal2", ry=-0.6)
        return
    cyl(mb, M, (0, 0, 0.45), 0.75, 0.9, "stone", seg=12)
    cyl(mb, M, (0, 0, 0.88), 0.6, 0.06, "dark", seg=12)
    jp = has_tag(era, "japanese", "chinese")
    for sx in (-0.7, 0.7):
        box(mb, M, (sx, 0, 1.4), (0.12, 0.12, 1.9), "wood2" if not jp else "trim")
    cyl(mb, M, (0, 0, 1.9), 0.09, 1.5, "wood2", seg=6, axis="X")
    limb(mb, M, (0, 0, 1.9), (0, 0, 1.1), 0.01, 0.01, "n_rope", seg=3)
    cyl(mb, M, (0, 0, 1.0), 0.13, 0.22, "wood", seg=8)
    if jp:
        hip_roof(mb, M, 1.6, 1.4, 2.4, 0.5, "n_slate", oh=0.2, lift=0.15)
    else:
        gable_roof(mb, M, 1.4, 1.4, 2.35, 0.6, "n_thatch" if is_ancient(era) else "n_tile" if has_tag(era, "classical") else "n_slate", oh=0.2)


@nat("market_well", size=(3.5, 3.5, 4), rooms=("village", "market", "settlement"))
def market_well(mb, x, y, z, rot, rng, era):
    """A town well / fountain under a little pillared roof (or a dome / pagoda in those cultures)."""
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.12), 1.8, 0.24, "stone", seg=16)
    cyl(mb, M, (0, 0, 0.6), 1.05, 0.8, "stone", seg=14)
    cyl(mb, M, (0, 0, 0.98), 0.92, 0.04, "n_water", seg=14)
    for k in range(4):
        a = k / 4 * TAU + TAU / 8
        cyl(mb, M, (math.cos(a) * 1.4, math.sin(a) * 1.4, 1.6), 0.12, 3.0, "stone", seg=8)
    st = house_style(era)
    if st == "dome":
        dome(mb, M, (0, 0, 3.1), 1.7, "accent", rng, sq=0.8)
    elif st == "pagoda":
        hip_roof(mb, M, 3.0, 3.0, 3.1, 1.1, "n_slate", oh=0.5, lift=0.4, sag=0.08, ridge=0.1)
    else:
        hip_roof(mb, M, 3.0, 3.0, 3.1, 1.3, "n_tile" if is_old(era) else "n_slate", oh=0.3, ridge=0.05)


@nat("water_trough", size=(2, 0.7, 0.6), rooms=("farm", "rural", "village", "outdoor", "western"))
def water_trough(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "wood" if is_old(era) or has_tag(era, "western") else "metal2"
    box(mb, M, (0, 0, 0.1), (1.9, 0.65, 0.2), k)
    for sy in (-1, 1):
        box(mb, M, (0, sy * 0.3, 0.35), (1.9, 0.06, 0.5), k)
    for sx in (-1, 1):
        box(mb, M, (sx * 0.92, 0, 0.35), (0.06, 0.6, 0.5), k)
    box(mb, M, (0, 0, 0.52), (1.78, 0.52, 0.04), "n_water")


@nat("hand_pump", size=(0.6, 0.6, 1.4), eras=OLD | MID, rooms=("farm", "rural", "village", "western"))
def hand_pump(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.1), (0.6, 0.6, 0.2), "stone")
    cyl(mb, M, (0, 0, 0.7), 0.09, 1.0, "metal2", seg=8)
    limb(mb, M, (0, 0, 1.0), (0.3, 0, 0.92), 0.04, 0.03, "metal2", seg=5)
    limb(mb, M, (0, 0, 1.2), (-0.55, 0, 1.45), 0.025, 0.025, "metal2", seg=4)


@nat("hay_bale", size=(1.6, 1.2, 1.3), rooms=("farm", "rural", "outdoor"))
def hay_bale(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    if fam(era) in ("modern", "near-future", "far-future"):                       # round bales, some wrapped
        for k in range(rng.randint(1, 3)):
            wrapped = rng.random() < 0.35
            cyl(mb, M, (k * 1.5, 0, 0.62), 0.62, 1.2, "n_white" if wrapped else "n_hay", seg=14, axis="Y")
            if not wrapped:
                cyl(mb, M, (k * 1.5, -0.61, 0.62), 0.5, 0.02, "n_hay2", seg=14, axis="Y")
    else:                                                                         # square bales, stacked
        for k in range(rng.randint(2, 5)):
            j = k % 3
            box(mb, M, ((j - 1) * 0.95 + (0.45 if k >= 3 else 0), rng.uniform(-0.05, 0.05), 0.22 + (k // 3) * 0.44), (0.9, 0.5, 0.44), rng.choice(("n_hay", "n_hay2")), rz=rng.uniform(-0.1, 0.1))
            box(mb, M, ((j - 1) * 0.95 + (0.45 if k >= 3 else 0), 0, 0.22 + (k // 3) * 0.44), (0.05, 0.52, 0.46), "n_rope")


@nat("haystack", size=(3, 3, 3.5), eras=OLD | MID, rooms=("farm", "rural"))
def haystack(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    limb(mb, M, (0, 0, -0.1), (0, 0, 1.6), 1.45, 1.2, "n_hay", seg=11)
    blob(mb, M, (0, 0, 1.6), 1.2, "n_hay", rng, sq=1.25, lump=0.12)
    limb(mb, M, (0, 0, 2.7), (0, 0, 3.4), 0.05, 0.03, "wood2", seg=4)
    for k in range(10):
        a = rng.uniform(0, TAU)
        blade(mb, M, (math.cos(a) * 1.45, math.sin(a) * 1.45, 0), (math.cos(a) * 1.7, math.sin(a) * 1.7, 0.3), 0.15, "n_hay2")


@nat("cart", size=(3.5, 1.8, 1.4), rooms=("farm", "rural", "village", "market", "outdoor"))
def cart(mb, x, y, z, rot, rng, era):
    """Hand cart / ox cart (old), farm trailer (mid/modern), hover sled (future)."""
    M = frame(x, y, z, rot)
    f = fam(era)
    if f in ("near-future", "far-future"):
        box(mb, M, (0, 0, 0.7), (2.4, 1.3, 0.5), "metal")
        box(mb, M, (0, 0, 0.42), (2.0, 1.0, 0.06), "accent")
        for k in range(3):
            box(mb, M, (-0.7 + k * 0.7, 0, 1.05), (0.6, 1.0, 0.4), "wood" if k % 2 else "metal2")
        return
    k = "wood" if f not in ("modern",) else "n_red"
    box(mb, M, (0, 0, 0.85), (2.4, 1.4, 0.1), k)
    for sy in (-1, 1):
        box(mb, M, (0, sy * 0.7, 1.1), (2.4, 0.08, 0.45), k)
    for sx in (-1, 1):
        box(mb, M, (sx * 1.2, 0, 1.1), (0.08, 1.4, 0.45), k)
    nwheel = 2 if f in ("ancient", "medieval", "1700s-1800s") else 4
    xs = (0.0,) if nwheel == 2 else (-0.75, 0.75)
    for xx in xs:
        for sy in (-1, 1):
            r = 0.6 if nwheel == 2 else 0.42
            cyl(mb, M, (xx, sy * 0.8, r), r, 0.1, "wood2" if nwheel == 2 else "dark", seg=12, axis="Y")
            cyl(mb, M, (xx, sy * 0.86, r), 0.1, 0.06, "metal2", seg=8, axis="Y")
            if nwheel == 2:
                for sp in range(4):
                    box(mb, M, (xx, sy * 0.8, r), (r * 1.9, 0.12, 0.06), "wood2", ry=sp * math.pi / 4)
    limb(mb, M, (1.2, -0.3, 0.85), (2.6, -0.1, 0.6), 0.05, 0.05, "wood2", seg=4)
    limb(mb, M, (1.2, 0.3, 0.85), (2.6, 0.1, 0.6), 0.05, 0.05, "wood2", seg=4)
    for i in range(rng.randint(2, 4)):
        c = (rng.uniform(-0.8, 0.8), rng.uniform(-0.4, 0.4), 1.05)
        if f in ("ancient", "medieval", "1700s-1800s"):
            blob(mb, M, c, 0.28, rng.choice(("fabric2", "n_hay")), rng, sub=1, sq=1.1)
        else:
            box(mb, M, c, (0.5, 0.4, 0.35), rng.choice(("wood", "n_hay")))


@nat("wagon_covered", size=(4.5, 2.2, 3), eras=OLD | MID, rooms=("western", "camp", "rural", "farm"))
def wagon_covered(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 1.0), (3.6, 1.6, 0.6), "wood")
    for k in range(5):                                                       # canvas hoops
        xx = -1.6 + k * 0.8
        vs = cyl(mb, M, (xx, 0, 1.3), 0.95, 0.75, "n_canvas", seg=12, axis="X")
    box(mb, M, (0, 0, 1.3), (3.4, 1.85, 0.05), "n_canvas")
    for xx in (-1.2, 1.2):
        for sy in (-1, 1):
            r = 0.55 if xx > 0 else 0.7
            cyl(mb, M, (xx, sy * 0.95, r), r, 0.1, "wood2", seg=14, axis="Y")
            for sp in range(4):
                box(mb, M, (xx, sy * 0.95, r), (r * 1.9, 0.12, 0.05), "wood2", ry=sp * math.pi / 4)
    limb(mb, M, (1.8, 0, 0.8), (3.4, 0, 0.6), 0.06, 0.05, "wood2", seg=4)


@nat("wheelbarrow", size=(1.6, 0.8, 0.8), rooms=("farm", "garden", "rural", "outdoor"))
def wheelbarrow(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    old = is_old(era)
    k = "wood" if old else rng.choice(("n_red", "n_teal", "metal"))
    box(mb, M, (0, 0, 0.55), (0.9, 0.62, 0.32), k, ry=0.12)
    cyl(mb, M, (0.62, 0, 0.25), 0.25, 0.08, "wood2" if old else "dark", seg=12, axis="Y")
    for sy in (-1, 1):
        limb(mb, M, (0.6, sy * 0.12, 0.25), (-0.85, sy * 0.3, 0.62), 0.03, 0.03, "wood2", seg=4)
        limb(mb, M, (-0.2, sy * 0.25, 0.42), (-0.25, sy * 0.25, 0.0), 0.025, 0.025, "wood2", seg=4)
    if rng.random() < 0.6:
        blob(mb, M, (0, 0, 0.72), 0.32, rng.choice(("n_soil", "n_hay", "n_leaf_aut")), rng, sub=1, sq=0.5)


@nat("scarecrow", size=(1.4, 0.5, 2.2), rooms=("farm", "rural"))
def scarecrow(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    limb(mb, M, (0, 0, -0.2), (0, 0, 1.9), 0.04, 0.04, "wood2", seg=4)
    limb(mb, M, (-0.8, 0, 1.45), (0.8, 0, 1.5), 0.035, 0.035, "wood2", seg=4)
    box(mb, M, (0, 0, 1.25), (0.5, 0.25, 0.6), rng.choice(("fabric", "n_blue", "fabric2")))
    for sx in (-1, 1):
        box(mb, M, (sx * 0.5, 0, 1.45), (0.45, 0.2, 0.2), "fabric2")
        blade(mb, M, (sx * 0.75, 0, 1.45), (sx * 0.95, 0, 1.3), 0.12, "n_hay")
    blob(mb, M, (0, 0, 1.75), 0.18, "n_canvas", rng, sub=1)
    cyl(mb, M, (0, 0, 1.9), 0.32, 0.03, "n_hay2", seg=10)
    limb(mb, M, (0, 0, 1.9), (0, 0, 2.15), 0.17, 0.12, "n_hay2", seg=8)


# ----------------------------------------------------------------------------- road furniture
@nat("signpost", size=(1.4, 0.4, 2.6), rooms=("village", "rural", "road", "outdoor"))
def signpost(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    f = fam(era)
    if f in ("modern", "1920s-50s"):
        box(mb, M, (0, 0, 1.2), (0.07, 0.07, 2.4), "metal2")
        box(mb, M, (0, -0.05, 2.1), (1.0, 0.03, 0.6), "n_teal" if f == "modern" else "n_white")
        box(mb, M, (0, -0.07, 2.1), (0.8, 0.02, 0.08), "paper")
        return
    if f in ("near-future", "far-future"):
        box(mb, M, (0, 0, 1.1), (0.16, 0.16, 2.2), "metal")
        box(mb, M, (0, -0.09, 1.8), (0.1, 0.02, 0.6), "accent")
        return
    limb(mb, M, (0, 0, -0.2), (0, 0, 2.5), 0.07, 0.06, "wood2", seg=6)
    for k, a in enumerate((0.3, -0.5, 2.6)):
        zz = 2.2 - k * 0.32
        box(mb, M, (math.cos(a) * 0.45, math.sin(a) * 0.45, zz), (0.9, 0.04, 0.2), "wood", rz=a)
        jag_cone(mb, M, (math.cos(a) * 0.95, math.sin(a) * 0.95, zz - 0.1), 0.11, 0.2, "wood", rng, seg=2, jag=0.0, droop=0.0)


@nat("milestone", size=(0.6, 0.4, 1.0), rooms=("rural", "road", "village"))
def milestone(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    if fam(era) == "ancient":
        cyl(mb, M, (0, 0, 0.75), 0.25, 1.5, "stone", seg=10)
        cyl(mb, M, (0, 0, 0.05), 0.4, 0.1, "stone", seg=10)
        return
    box(mb, M, (0, 0, 0.4), (0.5, 0.25, 0.8), "stone")
    vs = cyl(mb, M, (0, 0, 0.8), 0.25, 0.25, "stone", seg=10, axis="Y")
    box(mb, M, (0, -0.13, 0.5), (0.3, 0.02, 0.2), "n_white" if fam(era) != "medieval" else "stone")


@nat("lantern_post", size=(0.6, 0.6, 2.8), rooms=("village", "rural", "garden", "dock", "camp", "outdoor"))
def lantern_post(mb, x, y, z, rot, rng, era):
    """Torch / oil lantern / gas lamp / solar post / glow bollard by era. Emissive keys glow at night."""
    M = frame(x, y, z, rot)
    f = fam(era)
    if has_tag(era, "japanese", "chinese"):
        stone_lantern(mb, x, y, z, rot, rng, era)
        return
    if f in ("ancient", "medieval"):
        limb(mb, M, (0, 0, -0.1), (0, 0, 2.0), 0.06, 0.05, "wood2", seg=5)
        cyl(mb, M, (0, 0, 2.05), 0.12, 0.2, "metal2", seg=6, r2=0.18)
        jag_cone(mb, M, (0, 0, 2.15), 0.13, 0.35, "fire", rng, seg=4, jag=0.4, droop=0.0)
    elif f in ("1700s-1800s", "1920s-50s"):
        limb(mb, M, (0, 0, -0.1), (0, 0, 2.6), 0.06, 0.05, "wood2" if f != "1920s-50s" else "metal2", seg=6)
        limb(mb, M, (0, 0, 2.5), (0.4, 0, 2.6), 0.03, 0.03, "metal2", seg=4)
        box(mb, M, (0.4, 0, 2.35), (0.22, 0.22, 0.32), "lampshade")
        cyl(mb, M, (0.4, 0, 2.55), 0.16, 0.1, "metal2", seg=4, r2=0.02)
    elif f == "modern":
        box(mb, M, (0, 0, 1.4), (0.08, 0.08, 2.8), "metal2")
        box(mb, M, (0, 0, 2.85), (0.4, 0.3, 0.04), "n_solar")
        box(mb, M, (0, 0, 2.7), (0.18, 0.18, 0.2), "lampshade")
    else:
        cyl(mb, M, (0, 0, 0.5), 0.12, 1.0, "metal", seg=8)
        cyl(mb, M, (0, 0, 0.85), 0.125, 0.2, "accent", seg=8)


@nat("stone_lantern", size=(0.8, 0.8, 1.7), rooms=("japanese", "garden", "shrine"))
def stone_lantern(mb, x, y, z, rot, rng, era):
    """Japanese toro: base, pillar, light box (glows at night), wide cap, finial."""
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.1), 0.38, 0.2, "stone", seg=6)
    cyl(mb, M, (0, 0, 0.55), 0.12, 0.7, "stone", seg=8)
    cyl(mb, M, (0, 0, 0.95), 0.3, 0.12, "stone", seg=6)
    box(mb, M, (0, 0, 1.15), (0.36, 0.36, 0.3), "lampshade")
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(mb, M, (sx * 0.17, sy * 0.17, 1.15), (0.07, 0.07, 0.3), "stone")
    cyl(mb, M, (0, 0, 1.38), 0.46, 0.18, "stone", seg=6, r2=0.18)
    blob(mb, M, (0, 0, 1.55), 0.09, "stone", rng, sub=1, sq=1.4)


# ----------------------------------------------------------------------------- camp
@nat("tent", size=(3, 2.4, 1.8), rooms=("camp", "military", "nomad", "rural"))
def tent(mb, x, y, z, rot, rng, era, kind=None):
    M = frame(x, y, z, rot)
    f = fam(era)
    kind = kind or ("dome" if f in ("modern", "near-future", "far-future") and not has_tag(era, "military", "makeshift") else "canvas")
    if kind == "dome":
        vs = mb.sphere((0, 0, 0), 1.3, "accent" if f != "modern" else rng.choice(("n_red", "n_teal", "n_flower4", "n_blue")), sub=2)
        for v in vs:
            if v.co.z < 0:
                v.co.z = 0.0
            v.co.z *= 0.85
        smooth(vs)
        _xf(mb, vs, M)
        for a in (0.6, -0.6):
            box(mb, M, (0, 0, 0.55), (2.65, 0.04, 0.04), "dark", rz=a, ry=0.0)
        box(mb, M, (0, -1.2, 0.45), (0.7, 0.1, 0.8), "dark")
        return
    key = "n_tarp" if has_tag(era, "military") else "n_canvas"
    L, W, H = 2.8, 2.2, 1.7
    a = math.atan2(H, W / 2)
    sl = math.hypot(W / 2, H)
    for sg in (-1, 1):
        box(mb, M, (0, sg * W / 4, H / 2), (L, sl, 0.04), key, rx=-sg * a)
    poly(mb, M, [(L / 2, -W / 2, 0), (L / 2, W / 2, 0), (L / 2, 0, H)], key)
    poly(mb, M, [(-L / 2, -W / 2, 0), (-L / 2, 0, H), (-L / 2, -0.15, 0)], key)
    poly(mb, M, [(-L / 2, W / 2, 0), (-L / 2, 0.15, 0), (-L / 2, 0, H)], key)
    poly(mb, M, [(-L / 2 - 0.01, -0.15, 0), (-L / 2 - 0.01, 0, H * 0.85), (-L / 2 - 0.01, 0.15, 0)], "dark")
    for sx in (-1, 1):
        limb(mb, M, (sx * (L / 2 + 0.05), 0, 0), (sx * (L / 2 + 0.05), 0, H + 0.2), 0.03, 0.03, "wood2", seg=4)
        limb(mb, M, (sx * (L / 2 + 0.05), 0, H + 0.1), (sx * (L / 2 + 1.0), 0, 0), 0.008, 0.008, "n_rope", seg=3)


@nat("tent_canvas", size=(3, 2.4, 1.8), rooms=("camp", "military"))
def tent_canvas(mb, x, y, z, rot, rng, era):
    tent(mb, x, y, z, rot, rng, era, kind="canvas")


@nat("tent_dome", size=(2.8, 2.8, 1.2), eras=NOW | FUT, rooms=("camp",))
def tent_dome(mb, x, y, z, rot, rng, era):
    tent(mb, x, y, z, rot, rng, era, kind="dome")


@nat("yurt", size=(5, 5, 3), rooms=("camp", "nomad", "steppe"))
def yurt(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.8), 2.4, 1.6, "n_felt", seg=16)
    cyl(mb, M, (0, 0, 1.0), 2.42, 0.18, "fabric", seg=16)
    cyl(mb, M, (0, 0, 1.45), 2.42, 0.08, "fabric2", seg=16)
    cyl(mb, M, (0, 0, 2.15), 2.5, 1.1, "n_felt", seg=16, r2=0.45)
    cyl(mb, M, (0, 0, 2.75), 0.45, 0.12, "wood2", seg=10)
    for k in range(8):
        a = k / 8 * TAU
        limb(mb, M, (math.cos(a) * 2.48, math.sin(a) * 2.48, 1.62), (math.cos(a) * 0.48, math.sin(a) * 0.48, 2.68), 0.025, 0.025, "fabric", seg=3)
    box(mb, M, (0, -2.4, 0.75), (0.95, 0.15, 1.5), "accent")
    box(mb, M, (0, -2.45, 1.55), (1.15, 0.1, 0.15), "fabric")


@nat("campfire", size=(1.6, 1.6, 1.0), rooms=("camp", "nomad", "military", "beach", "cave"))
def campfire(mb, x, y, z, rot, rng, era, lit=True):
    """Stone ring + crossed logs + flame (flame keys glow). The kit adds the point light."""
    M = frame(x, y, z, rot)
    for k in range(9):
        a = k / 9 * TAU
        rock(mb, M, (math.cos(a) * 0.62, math.sin(a) * 0.62, 0.1), 0.17, rng.choice(("stone", "n_rock2")), rng, flat=0.7, sub=0)
    for k in range(4):
        a = k / 4 * TAU + 0.3
        limb(mb, M, (math.cos(a) * 0.5, math.sin(a) * 0.5, 0.08), (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.42), 0.06, 0.05, "n_charred" if k % 2 else "n_bark", seg=5)
    cyl(mb, M, (0, 0, 0.03), 0.42, 0.04, "n_charred", seg=10)
    if lit:
        jag_cone(mb, M, (0, 0, 0.1), 0.3, 0.75, "fire", rng, seg=5, jag=0.5, droop=0.0)
        jag_cone(mb, M, (0.05, 0.03, 0.12), 0.18, 0.5, "fire2", rng, seg=4, jag=0.5, droop=0.0)


@nat("firewood_pile", size=(2.2, 1.2, 1.2), rooms=("camp", "rural", "farm", "village", "outdoor"))
def firewood_pile(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for row in range(4):
        n = 6 - row
        for k in range(n):
            xx = (k - (n - 1) / 2) * 0.27
            cyl(mb, M, (xx, rng.uniform(-0.05, 0.05), 0.13 + row * 0.23), 0.12, 1.0 + rng.uniform(-0.1, 0.1), "n_bark" if (k + row) % 3 else "n_wood_end", seg=6, axis="Y")
    if not is_fut(era):
        box(mb, M, (1.1, 0, 0.25), (0.35, 0.35, 0.5), "n_wood_end")
        limb(mb, M, (1.05, 0, 0.5), (1.3, -0.1, 1.1), 0.025, 0.025, "wood2", seg=4)
        box(mb, M, (1.32, -0.11, 0.55), (0.08, 0.14, 0.18), "metal2")


@nat("drying_rack", size=(3, 1, 2), rooms=("shore", "dock", "camp", "nomad", "norse"))
def drying_rack(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for sx in (-1.3, 1.3):
        for sy in (-1, 1):
            limb(mb, M, (sx, sy * 0.4, -0.1), (sx, 0, 1.9), 0.04, 0.04, "wood2", seg=4)
    limb(mb, M, (-1.5, 0, 1.85), (1.5, 0, 1.85), 0.04, 0.04, "wood2", seg=4)
    for k in range(9):
        xx = -1.2 + k * 0.3
        box(mb, M, (xx, 0, 1.5), (0.08, 0.03, 0.6), rng.choice(("n_rock_band", "n_driftwood", "fabric2")))


# ----------------------------------------------------------------------------- water's edge
@nat("pier_section", size=(3, 6, 1.5), rooms=("dock", "shore", "lake", "river"))
def pier_section(mb, x, y, z, rot, rng, era, L=6.0, w=2.4, deck=0.9):
    """Plank deck on posts, running +y from (x, y); z = deck base level (usually the bank)."""
    M = frame(x, y, z, rot)
    metal = is_fut(era)
    for k in range(int(L / 0.32)):
        box(mb, M, (rng.uniform(-0.03, 0.03), 0.16 + k * 0.32, deck), (w, 0.28, 0.08), rng.choice(("wood", "wood", "wood2")) if not metal else "metal")
    for k in range(int(L / 2.0) + 1):
        for sx in (-1, 1):
            limb(mb, M, (sx * (w / 2 - 0.05), k * 2.0, -2.0), (sx * (w / 2 - 0.05), k * 2.0, deck + 0.5), 0.12, 0.11, "wood2", seg=6)
    if rng.random() < 0.6:
        for sx in (-1, 1):
            limb(mb, M, (sx * (w / 2 - 0.05), 0, deck + 0.5), (sx * (w / 2 - 0.05), L, deck + 0.5), 0.03, 0.03, "n_rope", seg=3)


@nat("rowboat", size=(3.4, 1.4, 0.8), rooms=("dock", "shore", "lake", "river"))
def rowboat(mb, x, y, z, rot, rng, era, key=None):
    M = frame(x, y, z, rot)
    key = key or ("wood" if is_old(era) else rng.choice(("n_teal", "n_red", "n_white", "n_blue")))
    L, W, H = 3.4, 1.3, 0.6
    V, F = [], []
    n = 7
    for i in range(n):
        t = i / (n - 1)
        xx = -L / 2 + L * t
        hw = W / 2 * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7 if t < 0.999 else 0.02
        hw = max(hw, 0.04)
        V += [(xx, -hw, H), (xx, -hw * 0.55, 0.05), (xx, hw * 0.55, 0.05), (xx, hw, H)]
    for i in range(n - 1):
        a, b = i * 4, (i + 1) * 4
        for j in range(3):
            F.append((a + j, b + j, b + j + 1, a + j + 1))
    F.append((0, 1, 2, 3))
    F.append(((n - 1) * 4 + 3, (n - 1) * 4 + 2, (n - 1) * 4 + 1, (n - 1) * 4))
    faces(mb, M, V, F, key)
    for t in (0.3, 0.62):
        box(mb, M, (-L / 2 + L * t, 0, H * 0.7), (0.25, W * 0.9, 0.05), "wood2")
    for sy in (-1, 1):
        limb(mb, M, (-0.2, sy * 0.4, H * 0.8), (1.0, sy * 0.85, 0.15), 0.025, 0.02, "wood2", seg=4)


@nat("canoe", size=(4.4, 0.9, 0.5), rooms=("lake", "river", "shore", "camp"))
def canoe(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    key = "n_bark_birch" if is_old(era) else rng.choice(("n_red", "n_flower4", "n_teal"))
    L, W, H = 4.4, 0.85, 0.42
    V, F = [], []
    n = 9
    for i in range(n):
        t = i / (n - 1)
        xx = -L / 2 + L * t
        hw = max(0.02, W / 2 * math.sin(math.pi * t) ** 0.8)
        lift = 0.18 * (abs(t - 0.5) * 2) ** 3
        V += [(xx, -hw, H + lift), (xx, -hw * 0.5, 0.04 + lift * 0.5), (xx, hw * 0.5, 0.04 + lift * 0.5), (xx, hw, H + lift)]
    for i in range(n - 1):
        a, b = i * 4, (i + 1) * 4
        for j in range(3):
            F.append((a + j, b + j, b + j + 1, a + j + 1))
    faces(mb, M, V, F, key)
    for t in (0.3, 0.7):
        box(mb, M, (-L / 2 + L * t, 0, H * 0.75), (0.1, W * 0.7, 0.04), "wood2")
    limb(mb, M, (-0.6, 0.2, H), (1.0, -0.1, H + 0.1), 0.02, 0.02, "wood2", seg=4)
    box(mb, M, (1.05, -0.1, H + 0.1), (0.4, 0.15, 0.03), "wood2")


@nat("fishing_net", size=(2.4, 0.6, 2), rooms=("dock", "shore"))
def fishing_net(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for sx in (-1.1, 1.1):
        limb(mb, M, (sx, 0, -0.1), (sx, 0, 2.0), 0.05, 0.045, "wood2", seg=5)
    limb(mb, M, (-1.2, 0, 1.95), (1.2, 0, 1.95), 0.04, 0.04, "wood2", seg=4)
    P = [Vector((-1.0 + 2.0 * u, 0.02, 1.9 - 0.9 * math.sin(math.pi * u) - 0.2)) for u in (0, 0.2, 0.4, 0.6, 0.8, 1.0)]
    for k in range(5):
        ribbon(mb, M, [p + Vector((0, 0, -0.18 * k)) for p in P], [0.03] * 6, "n_net", up=(0, 1, 0))
    for k in range(7):
        xx = -0.9 + k * 0.3
        limb(mb, M, (xx, 0.02, 1.9), (xx, 0.02, 1.9 - 0.9 * math.sin(math.pi * (xx + 1) / 2) - 0.95), 0.01, 0.01, "n_net", seg=3)
    for k in range(4):
        _xf(mb, mb.sphere((0, 0, 0), 0.08, "n_flower4", sub=1), M @ Matrix.Translation((-0.8 + k * 0.55, 0.03, 1.85)))


@nat("lobster_pots", size=(1.6, 1.2, 1.0), rooms=("dock", "shore"))
def lobster_pots(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for k in range(rng.randint(2, 4)):
        c = Vector(((k % 2) * 0.75 - 0.35, rng.uniform(-0.1, 0.1), 0.0 if k < 2 else 0.5))
        if is_old(era):
            cyl(mb, M, c + Vector((0, 0, 0.25)), 0.35, 0.5, "n_driftwood", seg=8, r2=0.25)
            cyl(mb, M, c + Vector((0, 0, 0.5)), 0.12, 0.04, "dark", seg=8)
        else:
            box(mb, M, c + Vector((0, 0, 0.22)), (0.7, 0.5, 0.44), "n_net")
            box(mb, M, c + Vector((0, 0, 0.45)), (0.72, 0.52, 0.03), rng.choice(("n_flower4", "n_red")))
    limb(mb, M, (0.5, 0.3, 0.05), (1.2, 0.6, 0.02), 0.015, 0.015, "n_rope", seg=3)
    _xf(mb, mb.sphere((0, 0, 0), 0.14, "n_red", sub=1), M @ Matrix.Translation((1.25, 0.62, 0.12)))


# ----------------------------------------------------------------------------- farm + village extras
@nat("beehive", size=(0.7, 0.7, 1.1), rooms=("farm", "garden", "rural"))
def beehive(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    if is_old(era):                                                     # straw skep on a stand
        box(mb, M, (0, 0, 0.3), (0.6, 0.6, 0.06), "wood2")
        for sx in (-0.25, 0.25):
            box(mb, M, (sx, 0, 0.14), (0.06, 0.5, 0.28), "wood2")
        for k in range(5):
            cyl(mb, M, (0, 0, 0.38 + k * 0.1), 0.3 - k * 0.045, 0.1, "n_hay" if k % 2 else "n_hay2", seg=12)
        box(mb, M, (0, -0.28, 0.38), (0.12, 0.04, 0.06), "dark")
    else:                                                               # stacked box hive
        for sx in (-0.2, 0.2):
            box(mb, M, (sx, 0, 0.15), (0.06, 0.5, 0.3), "wood2")
        for k in range(3):
            box(mb, M, (0, 0, 0.42 + k * 0.24), (0.5, 0.42, 0.22), "n_white" if k != 1 else "n_flower4")
        box(mb, M, (0, 0, 1.15), (0.58, 0.5, 0.08), "metal2")


@nat("chicken_coop", size=(2.4, 1.6, 1.8), rooms=("farm", "rural", "village"))
def chicken_coop(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for sx in (-0.9, 0.9):
        for sy in (-0.55, 0.55):
            box(mb, M, (sx, sy, 0.3), (0.08, 0.08, 0.6), "wood2")
    box(mb, M, (0, 0, 0.95), (2.0, 1.3, 0.8), rng.choice(("n_red", "wood", "n_white")) if not is_ancient(era) else "wood")
    gable_roof(mb, M, 2.0, 1.3, 1.35, 0.5, "n_slate" if not is_ancient(era) else "n_thatch", oh=0.15, gable_key="wood")
    box(mb, M, (0.4, -0.67, 0.85), (0.35, 0.04, 0.4), "dark")
    box(mb, M, (0.4, -1.1, 0.3), (0.3, 0.9, 0.04), "wood2", rx=0.6)
    box(mb, M, (-0.5, -0.67, 1.0), (0.5, 0.04, 0.3), "n_net")


@nat("windmill", size=(6, 6, 14), rooms=("landscape",))
def windmill(mb, x, y, z, rot, rng, era, s=1.0):
    """Tower mill with sails (old), metal wind pump (mid / western), white wind turbine (modern+)."""
    M = frame(x, y, z, rot, s)
    f = fam(era)
    if f in ("modern", "near-future", "far-future") and not has_tag(era, "makeshift"):
        cyl(mb, M, (0, 0, 15), 0.9, 30, "n_white", seg=12, r2=0.45)
        box(mb, M, (0, -0.4, 30.2), (1.1, 3.0, 1.1), "n_white")
        cyl(mb, M, (0, -2.0, 30.2), 0.45, 0.9, "n_white", seg=10, axis="Y")
        for k in range(3):
            a = k / 3 * TAU + 0.4
            d = Vector((math.cos(a), 0, math.sin(a)))
            ribbon(mb, M, [Vector((0, -2.3, 30.2)) + d * u * 14 for u in (0.05, 0.3, 0.7, 1.0)], [1.0, 1.1, 0.6, 0.15], "n_white", up=(0, 1, 0))
        return
    if f == "1920s-50s" or has_tag(era, "western", "makeshift"):
        for sx in (-1, 1):
            for sy in (-1, 1):
                limb(mb, M, (sx * 1.4, sy * 1.4, 0), (sx * 0.3, sy * 0.3, 10), 0.08, 0.06, "metal2" if f != "1700s-1800s" else "wood2", seg=4)
        for k in range(5):
            zz = 1.5 + k * 1.9
            r = 1.4 - (zz / 10) * 1.1
            for sg in (-1, 1):
                box(mb, M, (0, sg * r, zz), (2 * r, 0.05, 0.05), "metal2")
                box(mb, M, (sg * r, 0, zz), (0.05, 2 * r, 0.05), "metal2")
        cyl(mb, M, (0, -0.6, 10.3), 0.15, 1.6, "metal2", seg=6, axis="Y")
        for k in range(16):
            a = k / 16 * TAU
            box(mb, M, (math.cos(a) * 1.1, -1.4, 10.3 + math.sin(a) * 1.1), (1.4, 0.04, 0.32), "metal" if k % 2 else "n_rust", ry=-a)
        box(mb, M, (0, 1.2, 10.3), (0.06, 2.2, 0.9), "n_rust")
        cyl(mb, M, (2.5, 0, 0.5), 1.3, 1.0, "metal2", seg=14)
        return
    cyl(mb, M, (0, 0, 4.5), 2.6, 9.0, "wall" if f != "medieval" else "stone", seg=12, r2=1.9)
    hip_roof(mb, M, 3.6, 3.6, 9.0, 2.0, "n_thatch", oh=0.3, ridge=0.02)
    box(mb, M, (0, -2.45, 1.1), (1.0, 0.3, 2.2), "wood2")
    for zz in (4.0, 6.5):
        box(mb, M, (0, -2.2 + (zz - 4) * 0.12, zz), (0.6, 0.3, 0.8), "n_glowwin")
    hub = Vector((0, -3.2, 9.0))
    limb(mb, M, (0, -1.6, 9.0), hub, 0.25, 0.22, "wood2", seg=8)
    a0 = rng.uniform(0, 0.8)
    for k in range(4):
        a = a0 + k / 4 * TAU
        d = Vector((math.cos(a), 0, math.sin(a)))
        n = Vector((-d.z, 0, d.x))
        limb(mb, M, hub, hub + d * 7.0, 0.12, 0.08, "wood2", seg=4)
        for j in range(6):
            c = hub + d * (1.6 + j * 0.95) + n * 0.6
            box(mb, M, c, (0.9, 0.05, 0.9), "n_canvas" if j % 2 else "wood", ry=-a)


@nat("watchtower", size=(4, 4, 9), rooms=("landscape", "military", "fort"))
def watchtower(mb, x, y, z, rot, rng, era, s=1.0):
    """Timber watchtower (old), guard tower w/ searchlight (mid: camps, borders), stone tower (classical)."""
    M = frame(x, y, z, rot, s)
    f = fam(era)
    H = 7.0
    if has_tag(era, "classical", "egyptian"):
        cyl(mb, M, (0, 0, H / 2), 2.0, H, "stone", seg=10, r2=1.7)
        for k in range(10):
            a = k / 10 * TAU
            box(mb, M, (math.cos(a) * 1.75, math.sin(a) * 1.75, H + 0.35), (0.6, 0.4, 0.7), "stone", rz=a)
        box(mb, M, (0, -1.85, 1.1), (0.9, 0.3, 2.2), "dark")
        return
    mat = "wood2" if f in ("ancient", "medieval", "1700s-1800s") or has_tag(era, "military", "tropical") else "metal2"
    bamboo = has_tag(era, "tropical")
    for sx in (-1, 1):
        for sy in (-1, 1):
            limb(mb, M, (sx * 1.6, sy * 1.6, -0.2), (sx * 1.15, sy * 1.15, H), 0.13, 0.11, "n_bamboo" if bamboo else mat, seg=6)
    for zz in (2.2, 4.6):
        for sg in (-1, 1):
            r = 1.6 - zz / H * 0.45
            box(mb, M, (0, sg * r, zz), (2 * r, 0.07, 0.12), mat, ry=0.5 * sg)
            box(mb, M, (sg * r, 0, zz), (0.07, 2 * r, 0.12), mat, rx=0.5 * sg)
    box(mb, M, (0, 0, H), (3.0, 3.0, 0.15), "wood")
    for sg in (-1, 1):
        box(mb, M, (0, sg * 1.45, H + 0.55), (3.0, 0.08, 1.0), "wood")
        box(mb, M, (sg * 1.45, 0, H + 0.55), (0.08, 3.0, 1.0), "wood")
    for sx in (-1, 1):
        for sy in (-1, 1):
            limb(mb, M, (sx * 1.4, sy * 1.4, H), (sx * 1.4, sy * 1.4, H + 2.0), 0.06, 0.06, mat, seg=4)
    roofk = "n_thatch" if f in ("ancient", "medieval") or bamboo else "n_rust" if f != "1700s-1800s" else "n_slate"
    hip_roof(mb, M, 3.0, 3.0, H + 2.0, 1.4, roofk, oh=0.4, ridge=0.02)
    for k in range(int(H / 0.5)):                                    # ladder
        box(mb, M, (0, -1.8 + k * 0.03, 0.4 + k * 0.5), (0.6, 0.06, 0.05), mat)
    if f in ("1920s-50s", "modern"):
        cyl(mb, M, (1.2, -1.5, H + 1.3), 0.25, 0.4, "lampshade", seg=10, axis="Y")


@nat("water_tower", size=(4, 4, 9), eras=OLD | MID, rooms=("western", "farm", "landscape"))
def water_tower(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(mb, M, (sx * 1.3, sy * 1.3, 2.7), (0.25, 0.25, 5.4), "wood2")
    for zz in (1.8, 3.8):
        for sg in (-1, 1):
            box(mb, M, (0, sg * 1.3, zz), (2.7, 0.08, 0.14), "wood2", ry=0.6 * sg)
    box(mb, M, (0, 0, 5.45), (3.0, 3.0, 0.12), "wood2")
    cyl(mb, M, (0, 0, 6.9), 1.7, 2.8, "wood", seg=14)
    for zz in (5.9, 6.9, 7.9):
        cyl(mb, M, (0, 0, zz), 1.73, 0.07, "metal2", seg=14)
    cyl(mb, M, (0, 0, 8.65), 1.85, 0.7, "n_slate", seg=14, r2=0.1)
    limb(mb, M, (1.4, 0, 5.8), (2.4, 0, 3.6), 0.12, 0.12, "metal2", seg=6)


# ----------------------------------------------------------------------------- shrines, stones, monuments
@nat("shrine", size=(2, 2, 2.6), rooms=("shrine", "rural", "village", "garden"))
def shrine(mb, x, y, z, rot, rng, era):
    """Wayside shrine: Japanese hokora, Greek herm / altar, Christian wayside cross, Egyptian naos,
    modern memorial; offerings glow at night."""
    M = frame(x, y, z, rot)
    f, roof, tags, cul = era_style(era)
    if tags & {"japanese", "chinese"}:
        box(mb, M, (0, 0, 0.35), (1.2, 1.0, 0.7), "stone")
        box(mb, M, (0, 0, 1.05), (0.8, 0.7, 0.7), "wood")
        box(mb, M, (0, -0.36, 1.05), (0.5, 0.03, 0.5), "trim")
        hip_roof(mb, M, 0.9, 0.8, 1.4, 0.45, "n_slate", oh=0.3, lift=0.15, sag=0.04)
        for sx in (-0.45, 0.45):
            cyl(mb, M, (sx, -0.65, 0.85), 0.05, 0.3, "flame", seg=6)
        box(mb, M, (0, -0.7, 0.75), (0.5, 0.2, 0.06), "trim")
        return
    if tags & {"classical", "ancient", "egyptian"} or f == "ancient":
        box(mb, M, (0, 0, 0.5), (1.1, 0.8, 1.0), "stone" if "egyptian" not in tags else "wall")
        box(mb, M, (0, 0, 1.05), (1.3, 1.0, 0.12), "stone")
        cyl(mb, M, (0, 0, 1.2), 0.3, 0.2, "metal", seg=10, r2=0.4)
        jag_cone(mb, M, (0, 0, 1.3), 0.22, 0.45, "fire", rng, seg=4, jag=0.4, droop=0.0)
        return
    if tags & {"islamic", "mughal"}:
        box(mb, M, (0, 0, 0.8), (1.2, 1.2, 1.6), "wall")
        dome(mb, M, (0, 0, 1.6), 0.6, "accent", rng)
        box(mb, M, (0, -0.61, 0.7), (0.5, 0.04, 1.0), "dark")
        return
    if f in ("near-future", "far-future"):
        cyl(mb, M, (0, 0, 0.6), 0.45, 1.2, "metal", seg=8)
        cyl(mb, M, (0, 0, 1.4), 0.3, 0.4, "accent", seg=8)
        return
    # wayside cross / box shrine with candles
    limb(mb, M, (0, 0, -0.1), (0, 0, 1.6), 0.07, 0.07, "wood2", seg=5)
    box(mb, M, (0, 0, 1.75), (0.6, 0.4, 0.5), "wood")
    box(mb, M, (0, -0.21, 1.75), (0.35, 0.02, 0.32), "n_white")
    gable_roof(mb, M, 0.6, 0.4, 2.0, 0.25, "wood2", oh=0.12)
    for k in range(3):
        cyl(mb, M, (-0.25 + k * 0.25, -0.5, 0.06), 0.04, 0.12, "n_white", seg=6)
        cyl(mb, M, (-0.25 + k * 0.25, -0.5, 0.15), 0.012, 0.05, "flame", seg=4)
    NAT["flowers"](mb, *(M @ Vector((0.3, -0.4, 0))).to_tuple(), 0, rng, era, 0.6)


@nat("standing_stone", size=(1.4, 1.0, 3.5), rooms=("moor", "landscape", "ritual"))
def standing_stone(mb, x, y, z, rot, rng, era, s=1.0, h=None):
    M = frame(x, y, z, rot, s)
    h = h or rng.uniform(2.4, 3.8)
    vs = mb.box((0, 0, 0), (1.0, 0.6, h), "stone")
    for v in vs:
        t = (v.co.z / h + 0.5)
        v.co.x *= 1.0 - 0.25 * t + rng.uniform(-0.08, 0.08)
        v.co.y *= 1.0 - 0.2 * t + rng.uniform(-0.08, 0.08)
        v.co.z += h / 2 + rng.uniform(-0.1, 0.1) * t
    _xf(mb, vs, M @ Matrix.Rotation(rng.uniform(-0.08, 0.08), 4, "Y"))
    if rng.random() < 0.5:
        blob(mb, M, (0.2, -0.1, h * 0.25), 0.4, "n_moss", rng, sub=1, sq=0.4, smooth_=False)


@nat("rune_stone", size=(1.2, 0.6, 2.4), eras=OLD, rooms=("norse", "moor", "ritual"))
def rune_stone(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    standing_stone(mb, x, y, z, rot, rng, era, h=2.2)
    for k in range(6):                                                 # carved serpent band
        a = k / 6 * math.pi
        box(mb, M, (math.cos(a) * 0.38, -0.33, 0.6 + math.sin(a) * 1.1), (0.22, 0.03, 0.08), "n_red", ry=a + math.pi / 2)


@nat("totem", size=(1.4, 1.0, 5.5), rooms=("ritual", "camp", "nomad", "village"))
def totem(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    keys = ("n_red", "n_teal", "n_flower4", "n_white", "wood")
    zz = 0.0
    for k in range(5):
        h = rng.uniform(0.8, 1.1)
        cyl(mb, M, (0, 0, zz + h / 2), 0.42 - k * 0.02, h, "wood", seg=10)
        box(mb, M, (0, -0.4, zz + h * 0.62), (0.5, 0.08, 0.16), rng.choice(keys))
        for sx in (-0.15, 0.15):
            cyl(mb, M, (sx, -0.42, zz + h * 0.62), 0.07, 0.06, "dark", seg=8, axis="Y")
        box(mb, M, (0, -0.44, zz + h * 0.28), (0.3, 0.06, 0.08), "dark")
        zz += h
    for sx in (-1, 1):                                                 # wings near the top
        box(mb, M, (sx * 0.9, 0, zz - 0.6), (1.2, 0.12, 0.35), rng.choice(keys), ry=sx * 0.25)
    jag_cone(mb, M, (0, 0, zz), 0.4, 0.6, "n_red", rng, seg=3, jag=0.2, droop=0.0)


@nat("obelisk", size=(1.4, 1.4, 9), eras=OLD, rooms=("egyptian", "monument", "landscape"))
def obelisk(mb, x, y, z, rot, rng, era, h=9.0):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.3), (2.0, 2.0, 0.6), "stone")
    vs = mb.box((0, 0, 0), (1.0, 1.0, h), "wall2")
    for v in vs:
        t = v.co.z / h + 0.5
        v.co.x *= 1.0 - 0.38 * t
        v.co.y *= 1.0 - 0.38 * t
        v.co.z += h / 2 + 0.6
    _xf(mb, vs, M)
    limb(mb, M, (0, 0, h + 0.6), (0, 0, h + 1.2), 0.44, 0.0, "n_gold", seg=4)
    for k in range(7):                                                 # hieroglyph column
        zc = 1.6 + k * 1.0
        half = 0.5 * (1.0 - 0.38 * (zc - 0.6) / h)
        box(mb, M, (0, -half - 0.01, zc), (0.22, 0.03, 0.3 if k % 2 else 0.16), "n_ink")


@nat("column", size=(1.2, 1.2, 6), eras=OLD, rooms=("classical", "ruins", "monument", "garden"))
def column(mb, x, y, z, rot, rng, era, h=6.0, broken=False):
    M = frame(x, y, z, rot)
    eg = has_tag(era, "egyptian")
    box(mb, M, (0, 0, 0.15), (1.3, 1.3, 0.3), "stone")
    if broken:
        h = h * rng.uniform(0.3, 0.7)
    cyl(mb, M, (0, 0, 0.3 + h / 2), 0.48 if eg else 0.42, h, "wall" if not eg else "wall2", seg=12 if not eg else 10, r2=0.38)
    if not broken:
        if eg:
            cyl(mb, M, (0, 0, h + 0.6), 0.7, 0.6, "wall2", seg=10, r2=0.45)
            box(mb, M, (0, 0, h + 1.0), (1.1, 1.1, 0.25), "accent")
        else:
            cyl(mb, M, (0, 0, h + 0.4), 0.55, 0.22, "wall", seg=12, r2=0.4)
            box(mb, M, (0, 0, h + 0.6), (1.25, 1.25, 0.22), "wall")
    else:
        rock(mb, M, (1.2, 0.4, 0.4), 0.45, "wall", rng, flat=0.8)


@nat("torii", size=(5, 1, 5), rooms=("japanese", "shrine", "garden"))
def torii(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for sx in (-1.6, 1.6):
        limb(mb, M, (sx, 0, -0.1), (sx * 0.95, 0, 4.2), 0.2, 0.17, "n_vermilion", seg=10)
        cyl(mb, M, (sx, 0, 0.25), 0.26, 0.5, "n_ink", seg=10)
    box(mb, M, (0, 0, 3.5), (4.3, 0.24, 0.3), "n_vermilion")
    box(mb, M, (0, 0, 3.85), (0.25, 0.22, 0.5), "n_vermilion")
    V = [(-2.9, -0.28, 4.4), (2.9, -0.28, 4.4), (2.9, 0.28, 4.4), (-2.9, 0.28, 4.4),
         (-3.0, -0.3, 4.75), (3.0, -0.3, 4.75), (3.0, 0.3, 4.75), (-3.0, 0.3, 4.75)]
    V = [(vx, vy, vz + 0.12 * (abs(vx) / 3.0) ** 3 * 3) for vx, vy, vz in V]
    faces(mb, M, V, [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], "n_ink")
    box(mb, M, (0, 0, 4.25), (5.2, 0.32, 0.22), "n_vermilion")


@nat("koi_pond", size=(5, 4, 0.5), rooms=("japanese", "garden", "shrine"))
def koi_pond(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    pts = []
    for k in range(14):
        a = k / 14 * TAU
        r = (2.2 + 0.5 * math.sin(a * 2 + 0.6)) * rng.uniform(0.92, 1.05)
        pts.append((math.cos(a) * r * 1.2, math.sin(a) * r * 0.85, 0.04))
    poly(mb, M, pts, "n_water")
    for k, p in enumerate(pts):                                        # stone rim
        rock(mb, M, (p[0] * 1.06, p[1] * 1.08, 0.12), rng.uniform(0.25, 0.42), rng.choice(("stone", "n_rock", "n_moss")), rng, flat=0.55, sub=1)
    for k in range(6):                                                 # koi
        a = rng.uniform(0, TAU)
        c = Vector((math.cos(a) * rng.uniform(0.3, 1.6), math.sin(a) * rng.uniform(0.2, 1.1), 0.06))
        vs = mb.sphere((0, 0, 0), 0.16, rng.choice(("n_flower4", "n_vermilion", "n_white")), sub=1)
        for v in vs:
            v.co.x *= 1.9
            v.co.z *= 0.3
        _xf(mb, vs, M @ Matrix.Translation(c) @ Matrix.Rotation(rng.uniform(0, TAU), 4, "Z"))
    NAT["lily_pads"](mb, *(M @ Vector((1.0, 0.6, 0.03))).to_tuple(), 0, rng, era, 0.8)


@nat("bridge_stone", size=(10, 3.5, 4), rooms=("river", "landscape", "village"))
def bridge_stone(mb, x, y, z, rot, rng, era, span=9.0, w=3.2, deck=2.6):
    """Single arch along local x (river flows along y). Japanese cultures get a red drum bridge."""
    M = frame(x, y, z, rot)
    jp = has_tag(era, "japanese", "chinese")
    n = 14
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        x0, x1 = -span / 2 + span * t0, -span / 2 + span * t1
        if jp:
            a0, a1 = deck * 0.95 * math.sin(math.pi * t0), deck * 0.95 * math.sin(math.pi * t1)
            box(mb, M, ((x0 + x1) / 2, 0, (a0 + a1) / 2 + 0.6), (span / n * 1.05, w * 0.8, 0.12), "wood", ry=-math.atan2(a1 - a0, x1 - x0))
            for sy in (-1, 1):
                limb(mb, M, (x0, sy * w * 0.4, a0 + 0.6), (x0, sy * w * 0.4, a0 + 1.5), 0.05, 0.05, "n_vermilion", seg=5)
                limb(mb, M, (x0, sy * w * 0.4, a0 + 1.45), (x1, sy * w * 0.4, a1 + 1.45), 0.05, 0.05, "n_vermilion", seg=5)
        else:
            tm = (t0 + t1) / 2
            ya = -1.2 + (deck - 0.45 + 1.2) * math.sin(math.pi * tm) ** 0.8          # arch soffit
            box(mb, M, ((x0 + x1) / 2, 0, (ya + deck) / 2), (span / n * 1.03, w, deck - ya), "stone" if i % 2 else "wall2")
            box(mb, M, ((x0 + x1) / 2, 0, ya + 0.12), (span / n * 1.03, w + 0.12, 0.3), "n_rock2")
    if not jp:
        box(mb, M, (0, 0, deck + 0.2), (span + 2.0, w, 0.4), "stone")
        for sy in (-1, 1):
            box(mb, M, (0, sy * (w / 2 - 0.15), deck + 0.75), (span + 2.0, 0.3, 0.7), "stone")
        for sx in (-1, 1):
            box(mb, M, (sx * (span / 2 + 1.2), 0, deck / 2 - 0.5), (2.6, w + 0.4, deck + 1.0), "stone")


@nat("bridge_rope", size=(14, 2, 3), rooms=("canyon", "jungle", "mountain", "landscape"))
def bridge_rope(mb, x, y, z, rot, rng, era, span=14.0, sag=1.4):
    M = frame(x, y, z, rot)
    n = int(span / 0.45)
    for i in range(n + 1):
        t = i / n
        xx = -span / 2 + span * t
        zz = -sag * math.sin(math.pi * t)
        box(mb, M, (xx, 0, zz), (0.3, 1.3, 0.06), rng.choice(("wood", "wood2", "n_driftwood")), rz=rng.uniform(-0.06, 0.06))
    for sy in (-0.7, 0.7):
        for hz in (0.0, 1.0):
            P = [Vector((-span / 2 + span * t, sy, hz - sag * math.sin(math.pi * t) * (1 if hz == 0 else 0.75))) for t in [k / 10 for k in range(11)]]
            chain(mb, M, P, 0.03, 0.03, "n_rope", seg=4)
    for sx in (-1, 1):
        for sy in (-0.75, 0.75):
            limb(mb, M, (sx * span / 2, sy, -0.8), (sx * span / 2, sy, 1.4), 0.1, 0.09, "wood2", seg=5)


# ----------------------------------------------------------------------------- era-signature props
@nat("cannon", size=(2.4, 1.2, 1.2), eras=OLD, rooms=("pirate", "fort", "beach", "military"))
def cannon(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.35), (1.4, 0.8, 0.3), "wood2")
    for sx in (-0.5, 0.5):
        for sy in (-1, 1):
            cyl(mb, M, (sx, sy * 0.45, 0.25), 0.25, 0.1, "wood2", seg=10, axis="Y")
    limb(mb, M, (-0.8, 0, 0.7), (1.3, 0, 0.82), 0.24, 0.16, "n_ink", seg=10)
    cyl(mb, M, (1.3, 0, 0.82), 0.19, 0.12, "n_ink", seg=10, axis="X")
    for k in range(4):
        _xf(mb, mb.sphere((0, 0, 0), 0.11, "n_ink", sub=1), M @ Matrix.Translation((-1.2 + (k % 2) * 0.22, 0.5, 0.11 + (k // 2) * 0.19)))


@nat("shipwreck", size=(12, 5, 5), eras=OLD | MID, rooms=("pirate", "beach", "shore"))
def shipwreck(mb, x, y, z, rot, rng, era):
    """A half-buried broken hull on its side: ribs, planking, a snapped mast."""
    M = frame(x, y, z, rot) @ Matrix.Rotation(0.35, 4, "X")
    L = 11.0
    for k in range(12):                                                # ribs
        t = k / 11
        xx = -L / 2 + L * t
        r = 2.4 * math.sin(math.pi * (0.1 + 0.85 * t)) ** 0.6
        for sg in (-1, 1):
            P = [Vector((xx, sg * r * math.sin(a), 2.0 - r * math.cos(a) - 0.4)) for a in (0, 0.5, 1.0, 1.4)]
            chain(mb, M, P, 0.11, 0.08, "n_driftwood" if k % 3 else "wood2", seg=5)
    for j in range(5):                                                 # surviving planks on one side
        a = 0.25 + j * 0.25
        P = [Vector((-L / 2 + L * t, -2.4 * math.sin(math.pi * (0.1 + 0.85 * t)) ** 0.6 * math.sin(a), 1.6 - 2.4 * math.cos(a))) for t in (0.1, 0.3, 0.5, 0.65)]
        for i in range(len(P) - 1):
            box(mb, M, (P[i] + P[i + 1]) / 2, ((P[i + 1] - P[i]).length, 0.08, 0.28), "wood" if j % 2 else "wood2",
                rz=math.atan2((P[i + 1] - P[i]).y, (P[i + 1] - P[i]).x))
    limb(mb, M, (0.5, 0, -0.5), (1.4, 0.6, 6.0), 0.22, 0.16, "wood2", seg=8)
    limb(mb, M, (1.0, 0.3, 2.8), (-2.2, 0.0, 3.3), 0.09, 0.07, "wood2", seg=5)
    ribbon(mb, M, [Vector((1.3, 0.55, 5.6)), Vector((0.2, 0.9, 4.8)), Vector((-0.6, 0.6, 3.6))], [1.6, 1.3, 0.7], "n_canvas", up=(1, 0, 0))


@nat("treasure_chest", size=(1.0, 0.6, 0.7), eras=OLD, rooms=("pirate", "beach", "cave", "dungeon"))
def treasure_chest(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.25), (0.9, 0.55, 0.5), "wood")
    cyl(mb, M, (0, 0.05, 0.62), 0.28, 0.9, "wood", seg=8, axis="X")
    for sx in (-0.35, 0.35):
        box(mb, M, (sx, 0, 0.45), (0.06, 0.58, 0.9), "n_gold")
    box(mb, M, (0, -0.29, 0.45), (0.12, 0.04, 0.16), "n_gold")
    for k in range(5):
        cyl(mb, M, (rng.uniform(-0.6, 0.6), rng.uniform(-0.6, -0.35), 0.01), 0.05, 0.02, "n_gold", seg=8)


@nat("rover", size=(4, 2.6, 2), eras=FUT, rooms=("colony", "mars", "space"))
def rover(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 1.05), (3.2, 1.9, 0.9), "n_white")
    box(mb, M, (1.2, 0, 1.25), (0.9, 1.7, 0.6), "n_solar", ry=0.3)
    box(mb, M, (-0.4, 0, 1.6), (1.6, 1.6, 0.25), "metal2")
    for k in range(3):
        for sy in (-1, 1):
            xx = -1.2 + k * 1.2
            cyl(mb, M, (xx, sy * 1.1, 0.42), 0.42, 0.35, "dark", seg=12, axis="Y")
            cyl(mb, M, (xx, sy * 1.3, 0.42), 0.18, 0.05, "metal", seg=8, axis="Y")
    limb(mb, M, (-1.2, 0.6, 1.7), (-1.3, 0.6, 3.0), 0.03, 0.03, "metal", seg=4)
    cyl(mb, M, (-1.3, 0.6, 3.05), 0.3, 0.08, "metal", seg=10, r2=0.05)
    box(mb, M, (0.4, 0, 1.75), (0.5, 0.25, 0.06), "accent")


@nat("solar_array", size=(5, 3, 2), eras=NOW | FUT, rooms=("colony", "eco", "farm", "space"))
def solar_array(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for k in range(3):
        xx = -1.7 + k * 1.7
        limb(mb, M, (xx, 0, 0), (xx, 0, 1.0), 0.06, 0.06, "metal2", seg=5)
        box(mb, M, (xx, 0, 1.15), (1.6, 2.2, 0.06), "n_solar", rx=0.5)
        for j in range(3):
            box(mb, M, (xx, -0.75 + j * 0.75, 1.15 + 0.03), (1.62, 0.03, 0.08), "metal", rx=0.5)


@nat("antenna_mast", size=(1.2, 1.2, 8), eras=MID | NOW | FUT, rooms=("colony", "military", "space", "landscape"))
def antenna_mast(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for k in range(3):
        a = k / 3 * TAU
        limb(mb, M, (math.cos(a) * 0.5, math.sin(a) * 0.5, 0), (0, 0, 7.5), 0.04, 0.03, "metal2", seg=4)
    for zz in (2.0, 4.0, 6.0):
        cyl(mb, M, (0, 0, zz), 0.5 * (1 - zz / 7.5) + 0.05, 0.04, "metal2", seg=6)
    cyl(mb, M, (0.4, 0, 6.8), 0.6, 0.12, "n_white", seg=12, r2=0.15)
    cyl(mb, M, (0, 0, 7.6), 0.07, 0.15, "fire", seg=6)


@nat("car_wreck", size=(4.2, 1.9, 1.5), eras=MID | NOW | FUT, rooms=("wasteland", "ruins", "farm"))
def car_wreck(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot) @ Matrix.Rotation(rng.uniform(-0.08, 0.08), 4, "X")
    box(mb, M, (0, 0, 0.55), (4.0, 1.75, 0.6), "n_rust")
    box(mb, M, (-0.2, 0, 1.1), (2.0, 1.6, 0.55), rng.choice(("n_rust", "metal2", "n_teal")))
    box(mb, M, (-0.2, -0.81, 1.1), (1.7, 0.03, 0.4), "dark")
    box(mb, M, (0.82, 0, 1.08), (0.06, 1.4, 0.45), "dark", ry=0.5)
    for sx in (-1.3, 1.3):
        for sy in (-1, 1):
            if rng.random() < 0.7:
                cyl(mb, M, (sx, sy * 0.8, 0.3), 0.32, 0.22, "dark", seg=10, axis="Y")
    box(mb, M, (1.95, 0, 0.5), (0.1, 1.5, 0.25), "metal2")
    if rng.random() < 0.6:
        NAT["tall_grass"](mb, *(M @ Vector((1.6, 0.9, 0))).to_tuple(), 0, rng, era, 0.8)


@nat("oil_drum", size=(0.7, 0.7, 1.0), eras=MID | NOW | FUT, rooms=("wasteland", "dock", "military", "camp", "outdoor"))
def oil_drum(mb, x, y, z, rot, rng, era, fire=None):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.45), 0.3, 0.9, rng.choice(("n_rust", "n_blue", "n_red", "metal2")), seg=12)
    for zz in (0.3, 0.6):
        cyl(mb, M, (0, 0, zz), 0.31, 0.04, "metal2", seg=12)
    if fire or (fire is None and has_tag(era, "makeshift") and rng.random() < 0.5):
        jag_cone(mb, M, (0, 0, 0.9), 0.24, 0.55, "fire", rng, seg=4, jag=0.5, droop=0.0)


@nat("sandbags", size=(3, 1, 1), eras=MID | NOW | FUT, rooms=("military", "camp", "battlefield"))
def sandbags(mb, x, y, z, rot, rng, era, L=3.0):
    M = frame(x, y, z, rot)
    for row in range(3):
        n = int(L / 0.6)
        for k in range(n - (row % 2)):
            c = (-L / 2 + 0.3 + k * 0.6 + (0.3 if row % 2 else 0), rng.uniform(-0.03, 0.03), 0.15 + row * 0.26)
            blob(mb, M, c, 0.3, rng.choice(("n_tarp", "n_canvas", "fabric2")) if has_tag(era, "military") else rng.choice(("n_canvas", "n_hay2")), rng, sub=1, sq=0.48, sx=1.05, sy=0.7, lump=0.08)


@nat("greenhouse", size=(5, 3.5, 3), eras=MID | NOW | FUT, rooms=("farm", "garden", "eco", "colony"))
def greenhouse(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.25), (4.6, 3.0, 0.5), "stone")
    for k in range(7):
        xx = -2.25 + k * 0.75
        for sg in (-1, 1):
            limb(mb, M, (xx, sg * 1.5, 0.5), (xx, sg * 1.5, 1.8), 0.03, 0.03, "n_white", seg=4)
            limb(mb, M, (xx, sg * 1.5, 1.8), (xx, 0, 2.7), 0.03, 0.03, "n_white", seg=4)
    for sg in (-1, 1):
        box(mb, M, (0, sg * 1.49, 1.15), (4.5, 0.03, 1.3), "glass")
        box(mb, M, (0, sg * 0.75, 2.25), (4.5, 1.7, 0.03), "glass", rx=sg * 0.55)
    for k in range(5):
        NAT["bush"](mb, *(M @ Vector((-1.8 + k * 0.9, 0.5, 0.5))).to_tuple(), 0, rng, era, 0.45)


@nat("terrace_planter", size=(6, 2.5, 1.2), eras=NOW | FUT, rooms=("eco", "garden", "solarpunk"))
def terrace_planter(mb, x, y, z, rot, rng, era, L=6.0):
    """A curved wooden planter step with crops, flowers and a little solar pergola (solarpunk)."""
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.5), (L, 2.2, 1.0), "wood")
    box(mb, M, (0, 0, 1.0), (L - 0.2, 2.0, 0.06), "n_soil")
    for k in range(int(L / 0.9)):
        xx = -L / 2 + 0.45 + k * 0.9
        f = rng.random()
        if f < 0.4:
            NAT["bush"](mb, *(M @ Vector((xx, rng.uniform(-0.4, 0.4), 1.0))).to_tuple(), 0, rng, era, 0.55)
        elif f < 0.7:
            NAT["flowers_wild"](mb, *(M @ Vector((xx, rng.uniform(-0.4, 0.4), 1.0))).to_tuple(), 0, rng, era, 1.0)
        else:
            NAT["tall_grass"](mb, *(M @ Vector((xx, rng.uniform(-0.4, 0.4), 1.0))).to_tuple(), 0, rng, era, 0.9, ("n_leaf_lime", "n_leaf"))
    for sx in (-L / 2 + 0.3, L / 2 - 0.3):
        limb(mb, M, (sx, 0.9, 1.0), (sx, 0.9, 3.0), 0.05, 0.05, "wood2", seg=5)
    box(mb, M, (0, 0.6, 3.05), (L, 1.4, 0.06), "n_solar", rx=-0.3)

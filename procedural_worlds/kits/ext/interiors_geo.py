"""Geometry helpers for the interiors asset pack (kits/ext/interiors_*.py). Registers nothing.

Prop-local conventions used by every interiors prop (x right, -Y = the side facing the viewer/room):
- floor:   origin = footprint centre on the floor (z = floor height).
- surface: origin = bottom centre on the supporting surface.
- wall:    origin on the WALL FACE, body extends toward local -Y (into the room), so a feature places it at
           R.wp(side, u, z, 0.01) with R.yaw(side). size z >= 1.0 -> standing furniture (z = floor);
           size z < 1.0 -> mounted item (z = height of its centre).
- hanging: origin at the ceiling attachment point, body hangs down (-Z).
Every part is a closed solid (box / cylinder / icosphere) with non-zero extent in all three axes."""
import math
import bmesh
from mathutils import Vector, Matrix, Euler
from ..props import FAMILY


def frame(x, y, z, rot):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z")


def _R(r):
    return Euler(r).to_matrix().to_4x4() if r else Matrix()


def box(mb, M, c, s, key, r=None):
    """Box of size s centred at local c (optional Euler r about its centre)."""
    s = tuple(max(0.006, abs(v)) for v in s)
    vs = mb.box((0, 0, 0), s, key)
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)) @ _R(r), verts=vs)
    return vs


def cyl(mb, M, c, r, h, key, seg=10, r2=None, axis="Z", rr=None, sq=None):
    """Cylinder/cone (r -> r2) centred at c along axis; sq=(sx, sy, sz) stretches it (ovals)."""
    vs = mb.cyl((0, 0, 0), max(0.004, r), max(0.006, h), key, seg=seg, r2=r2, axis=axis)
    S = Matrix.Diagonal((*sq, 1.0)) if sq else Matrix()
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)) @ _R(rr) @ S, verts=vs)
    return vs


def tier(era):
    """0 ancient/medieval, 1 1700s-1800s, 2 1920s-50s, 3 modern, 4 near/far-future (any timeline key)."""
    return {"ancient": 0, "medieval": 0, "1700s-1800s": 1, "1920s-50s": 2, "modern": 3}.get(FAMILY.get(era, era), 4)


# finer sub-eras for variants inside a family (legacy keys map to their most iconic look)
SUB = {"ancient": "antiq", "classical_antiquity": "antiq", "medieval": "med", "early_high_middle_ages": "med",
       "renaissance_discovery": "ren", "enlightenment_piracy": "enl", "1700s-1800s": "vic", "victorian_industrial": "vic",
       "interwar": "inter", "1920s-50s": "cold", "cold_war": "cold", "analog_digital": "analog", "modern": "now",
       "contemporary": "now", "post_apocalyptic": "post", "near-future": "fut", "near_future": "fut", "cyberpunk": "cyber",
       "solarpunk": "solar", "far-future": "space", "space_age": "space", "far_future": "space"}


def sub(era):
    return SUB.get(era, {0: "med", 1: "vic", 2: "cold", 3: "now", 4: "fut"}[tier(era)])


def eras_of(*subs):
    """Every era key (legacy + timeline) whose sub-era is in subs."""
    return {k for k in set(FAMILY) | set(SUB) if sub(k) in subs}


ANTIQ, MEDV = eras_of("antiq"), eras_of("med")
PRE = eras_of("antiq", "med", "ren", "enl")                 # before gas/electric
VIC = eras_of("vic")
INTER, COLD = eras_of("inter"), eras_of("cold")
MIDC = INTER | COLD
ANALOG = eras_of("analog")
NOWS = eras_of("now", "post")
FUTS = eras_of("fut", "cyber", "solar", "space")
INDUSTRIAL_ON = VIC | MIDC | ANALOG | NOWS | FUTS          # plumbing, gas, printed paper...
ELECTRIC = MIDC | ANALOG | NOWS | FUTS
ALL = PRE | INDUSTRIAL_ON


def sph(mb, M, c, r, key, sq=(1.0, 1.0, 1.0), sub=1):
    vs = mb.sphere((0, 0, 0), r, key, sub=sub)
    S = Matrix.Diagonal((*sq, 1.0))
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)) @ S, verts=vs)
    return vs


def rod(mb, M, a, b, r, key, seg=6):
    """Cylinder from local point a to local point b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-4:
        return []
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    vs = mb.cyl((0, 0, 0), r, L, key, seg=seg)
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4(), verts=vs)
    return vs


def surf(M, c, r):
    """Clutter surface (world centre, half extent) from a prop-local point."""
    return (M @ Vector(c), r)


def legs4(mb, M, w, d, h, t, key, z0=0.0, inset=0.0):
    for sx in (-1, 1):
        for sy in (-1, 1):
            box(mb, M, (sx * (w / 2 - t / 2 - inset), sy * (d / 2 - t / 2 - inset), z0 + h / 2), (t, t, h), key)


def drawers(mb, M, x, y_front, z0, w, h, n, key="trim", knob="metal"):
    """n drawer fronts stacked from z0 on a face at y_front (facing -Y), with knobs."""
    dh = h / n
    for i in range(n):
        zc = z0 + dh * (i + 0.5)
        box(mb, M, (x, y_front - 0.008, zc), (w - 0.04, 0.016, dh - 0.03), key)
        box(mb, M, (x, y_front - 0.025, zc), (min(0.14, w * 0.3), 0.02, 0.025), knob)


def doors(mb, M, x, y_front, z0, w, h, n, key="trim", knob="metal"):
    """n vertical door panels side by side, centred on x, facing -Y."""
    dw = w / n
    for i in range(n):
        xc = x - w / 2 + dw * (i + 0.5)
        box(mb, M, (xc, y_front - 0.008, z0 + h / 2), (dw - 0.03, 0.016, h - 0.04), key)
        kx = xc + (dw / 2 - 0.06) * (1 if i % 2 == 0 else -1) if n > 1 else xc + dw / 2 - 0.06
        box(mb, M, (kx, y_front - 0.025, z0 + h * 0.55), (0.025, 0.02, 0.1), knob)

"""genre_fx asset pack: shared geometry helpers + the pack's own prop registry (no props here).
All helpers add to a MeshBuilder (kits/mb.py) in prop-local coordinates transformed by a matrix M,
so props stay ONE mesh per kit bucket (fast Line Art, clean GLB export). Palette keys only."""
import math
import bmesh
from mathutils import Vector, Matrix, Euler
from .. import props as P
from ... import core

FX = {}          # name -> builder fn (features call these directly, so a name clash elsewhere can't break them)
FEATURE_ONLY = ("fx_feature",)     # room tag no setting uses: big props that only features place


def _eras_with_glowing_accent():
    out = set()
    for k, v in core.load_preset("era").items():
        a = v.get("palette", {}).get("accent")
        if isinstance(a, dict) and a.get("strength", 0) > 0:
            out.add(k)
    return out


GLOW = _eras_with_glowing_accent()          # eras whose "accent" key is emissive (neon ink)
ANC = {e for e in P.OLD if P.FAMILY.get(e, e) == "ancient"}
MED = {e for e in P.OLD if P.FAMILY.get(e, e) == "medieval"}
EARLY = {e for e in P.OLD if P.FAMILY.get(e, e) == "1700s-1800s"}
PRE = P.OLD | P.MID                        # before the computer age
LATE = P.MID | P.NOW | P.FUT               # electric ages
ELEC = P.NOW | P.FUT


def glow(era):
    """Key for a lit screen / indicator: neon accent where the era glows, else the night-lit 'screen'."""
    return "accent" if era in GLOW else "screen"


def hot(era):
    """Key for something that must always glow (reactor, holo): accent in glowing eras, else fire2."""
    return "accent" if era in GLOW else "fire2"


def fxprop(name, place, size, eras=None, rooms=FEATURE_ONLY):
    def deco(fn):
        if name in P.PROPS and name not in FX:
            print(f"genre_fx: prop name '{name}' already registered elsewhere; overriding in PROPS")
        P.prop(name, place, size, eras=eras, rooms=rooms)(fn)
        FX[name] = fn
        return fn
    return deco


def put(mb, name, x, y, z, rot, rng, era):
    return FX[name](mb, x, y, z, rot, rng, era) or []


# ----------------------------------------------------------------------------- transforms
def M0(x, y, z, rot=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z")


def R(rx=0.0, ry=0.0, rz=0.0):
    return Euler((rx, ry, rz), "XYZ").to_matrix().to_4x4()


def sub(M, c, rx=0.0, ry=0.0, rz=0.0, s=1.0):
    m = M @ Matrix.Translation(Vector(c)) @ R(rx, ry, rz)
    return m @ Matrix.Scale(s, 4) if s != 1.0 else m


def _xf(mb, M, c, vs, rx, ry, rz):
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)) @ R(rx, ry, rz), verts=vs)
    return vs


# ----------------------------------------------------------------------------- primitives
def bx(mb, M, c, s, key, rx=0.0, ry=0.0, rz=0.0):
    return _xf(mb, M, c, mb.box((0, 0, 0), s, key), rx, ry, rz)


def cy(mb, M, c, r, h, key, seg=10, r2=None, rx=0.0, ry=0.0, rz=0.0):
    return _xf(mb, M, c, mb.cyl((0, 0, 0), r, h, key, seg=seg, r2=r2), rx, ry, rz)


def cyx(mb, M, c, r, h, key, seg=10, r2=None):
    """Cylinder along local X."""
    return cy(mb, M, c, r, h, key, seg, r2, ry=math.pi / 2)


def cyy(mb, M, c, r, h, key, seg=10, r2=None):
    """Cylinder along local Y."""
    return cy(mb, M, c, r, h, key, seg, r2, rx=math.pi / 2)


def sp(mb, M, c, r, key, sub=1, sc=(1, 1, 1), rx=0.0, ry=0.0, rz=0.0):
    vs = mb.sphere((0, 0, 0), r, key, sub=sub)
    for v in vs:
        v.co = Vector((v.co.x * sc[0], v.co.y * sc[1], v.co.z * sc[2]))
    return _xf(mb, M, c, vs, rx, ry, rz)


def lathe(mb, M, c, prof, key, seg=10, rx=0.0, ry=0.0, rz=0.0, sc=(1, 1)):
    """Surface of revolution about local Z from a profile [(radius, z), ...] (radius 0 = pole)."""
    bm = mb.bm
    rings = []
    for r, z in prof:
        if r <= 1e-4:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((math.cos(a) * r * sc[0], math.sin(a) * r * sc[1], z))
                          for a in (i / seg * math.tau for i in range(seg))])
    faces = []
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(seg):
            j = (i + 1) % seg
            if len(A) == 1:
                faces.append(bm.faces.new((A[0], B[j], B[i])))
            elif len(B) == 1:
                faces.append(bm.faces.new((A[i], A[j], B[0])))
            else:
                faces.append(bm.faces.new((A[i], A[j], B[j], B[i])))
    if len(rings[0]) > 1:
        faces.append(bm.faces.new(rings[0][::-1]))
    if len(rings[-1]) > 1:
        faces.append(bm.faces.new(rings[-1]))
    mb._tag(faces, key)
    return _xf(mb, M, c, [v for rr in rings for v in rr], rx, ry, rz)


def prism(mb, M, c, pts, depth, key, rx=0.0, ry=0.0, rz=0.0):
    """Polygon [(x, z), ...] in the local XZ plane extruded along Y (shields, blades, banners, arches)."""
    bm = mb.bm
    a = [bm.verts.new((u, -depth / 2, v)) for u, v in pts]
    b = [bm.verts.new((u, depth / 2, v)) for u, v in pts]
    n = len(pts)
    faces = [bm.faces.new(a), bm.faces.new(b[::-1])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    mb._tag(faces, key)
    return _xf(mb, M, c, a + b, rx, ry, rz)


def slab(mb, M, c, pts, h, key, rx=0.0, ry=0.0, rz=0.0):
    """Polygon [(x, y), ...] in the local XY plane extruded up by h (coffins, rugs, irregular tops)."""
    bm = mb.bm
    a = [bm.verts.new((u, v, 0)) for u, v in pts]
    b = [bm.verts.new((u, v, h)) for u, v in pts]
    n = len(pts)
    faces = [bm.faces.new(a), bm.faces.new(b[::-1])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((a[i], a[j], b[j], b[i])))
    mb._tag(faces, key)
    return _xf(mb, M, c, a + b, rx, ry, rz)


def ring(mb, M, c, Rr, r, key, seg=16, mseg=4, arc=math.tau, rx=0.0, ry=0.0, rz=0.0):
    """Torus (or an arc of one) in the local XY plane."""
    bm = mb.bm
    full = arc >= math.tau - 1e-6
    n = seg if full else seg + 1
    rings = []
    for i in range(n):
        a = arc * i / seg
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(((Rr + r * math.cos(b)) * ca, (Rr + r * math.cos(b)) * sa, r * math.sin(b)))
                      for b in (k / mseg * math.tau for k in range(mseg))])
    faces = []
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(mseg):
            l = (k + 1) % mseg
            faces.append(bm.faces.new((A[k], A[l], B[l], B[k])))
    if not full:
        faces += [bm.faces.new(rings[0]), bm.faces.new(rings[-1][::-1])]
    mb._tag(faces, key)
    return _xf(mb, M, c, [v for rr in rings for v in rr], rx, ry, rz)


def strut(mb, M, a, b, r, key, seg=4):
    """Beam/rod from local point a to b (square for seg<=4, round otherwise)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    if d.length < 1e-5:
        return []
    q = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    vs = mb.box((0, 0, 0), (r * 2, r * 2, d.length), key) if seg <= 4 else mb.cyl((0, 0, 0), r, d.length, key, seg=seg)
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation((a + b) / 2) @ q, verts=vs)
    return vs


def polyline(mb, M, pts, r, key, seg=4):
    for a, b in zip(pts, pts[1:]):
        strut(mb, M, a, b, r, key, seg)


def flat_grid(mb, M, x0, y0, x1, y1, nx, ny, key_fn, z=0.0, jitter=0.0, rng=None):
    """Flat tile grid (one quad per tile, key per tile) transformed by M: mosaics, floor panels."""
    bm = mb.bm
    vv = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            jx = rng.uniform(-jitter, jitter) if rng and 0 < i < nx else 0.0
            jy = rng.uniform(-jitter, jitter) if rng and 0 < j < ny else 0.0
            vv[i, j] = bm.verts.new((x0 + (x1 - x0) * i / nx + jx, y0 + (y1 - y0) * j / ny + jy, z))
    for i in range(nx):
        for j in range(ny):
            f = bm.faces.new((vv[i, j], vv[i + 1, j], vv[i + 1, j + 1], vv[i, j + 1]))
            mb._tag([f], key_fn(i, j))
    bmesh.ops.transform(bm, matrix=M, verts=list(vv.values()))


# ----------------------------------------------------------------------------- reusable parts
def arch_pts(w, h, spring=None, seg=8, pointed=False):
    """Outline of a round (or gothic pointed) arch opening/slab, base at z=0."""
    spring = h - w / 2 if spring is None else spring
    pts = [(-w / 2, 0), (w / 2, 0), (w / 2, spring)]
    for i in range(1, seg):
        a = i / seg * math.pi
        if pointed:
            t = i / seg
            x = w / 2 * math.cos(a)
            z = spring + (h - spring) * math.sin(a) ** 0.8
        else:
            x, z = w / 2 * math.cos(a), spring + (h - spring) * math.sin(a)
        pts.append((x, z))
    pts.append((-w / 2, spring))
    return pts


def flame(mb, M, c, s=1.0, key="flame"):
    """Little flame: two stacked cones (always emissive via 'flame'/'fire')."""
    cy(mb, M, (c[0], c[1], c[2] + 0.03 * s), 0.018 * s, 0.06 * s, key, seg=6, r2=0.0)


def fire(mb, M, c, s=1.0, n=3, rng=None):
    for k in range(n):
        dx = (rng.uniform(-0.1, 0.1) if rng else (k - 1) * 0.08) * s
        dy = (rng.uniform(-0.1, 0.1) if rng else 0.0) * s
        h = (0.45 - 0.08 * k) * s
        cy(mb, M, (c[0] + dx, c[1] + dy, c[2] + h / 2), (0.14 - 0.03 * k) * s, h, "fire" if k % 2 == 0 else "fire2", seg=6, r2=0.0)


def candle(mb, M, c, h=0.14, r=0.02, lit=True):
    cy(mb, M, (c[0], c[1], c[2] + h / 2), r, h, "paper", seg=8)
    if lit:
        flame(mb, M, (c[0], c[1], c[2] + h), 1.0)


def book(mb, M, c, w=0.22, d=0.16, t=0.05, key="fabric", rz=0.0, rx=0.0):
    bx(mb, M, c, (w, d, t), key, rx=rx, rz=rz)
    bx(mb, M, (c[0], c[1] - 0.004, c[2]), (w - 0.02, d, t - 0.012), "paper", rx=rx, rz=rz)


def table(mb, M, w, d, h, key="wood", leg=0.07, top=0.06):
    bx(mb, M, (0, 0, h - top / 2), (w, d, top), key)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx(mb, M, (sx * (w / 2 - leg), sy * (d / 2 - leg), (h - top) / 2), (leg, leg, h - top), key)


def barrel_shape(mb, M, c, r=0.28, h=0.8, key="wood", hoop="metal2", rx=0.0, ry=0.0):
    prof = [(0, 0), (r * 0.82, 0), (r * 0.96, h * 0.22), (r, h * 0.5), (r * 0.96, h * 0.78), (r * 0.82, h), (0, h)]
    lathe(mb, M, c, prof, key, seg=12, rx=rx, ry=ry)
    for t in (0.12, 0.88):
        rr = r * (0.88 if t < 0.2 or t > 0.8 else 1.0) + 0.012
        zc = Vector((0, 0, h * t))
        m = sub(M, c, rx, ry)
        ring(mb, m, zc, rr * 1.03, 0.012, hoop, seg=14, mseg=3)


def surface(x, y, z, r):
    return [(Vector((x, y, z)), r)]


def world(M, p):
    return M @ Vector(p)

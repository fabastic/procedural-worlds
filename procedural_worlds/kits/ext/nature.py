"""Nature asset pack, part 1: shared organic geometry helpers, the nature palette keys and the
vegetation / ground props (trees of many species and seasons, bushes, flowers, grass, rocks, logs,
snow, ice, beach litter, cave rock). Everything is low-poly MeshBuilder geometry (tapered limbs,
lumpy smooth blobs, jagged cones, ribbons) so it exports cleanly to GLB.

Registry: NAT[name] = builder(mb, x, y, z, rot, rng, era, s=1.0) (also registered in props.PROPS
under the same name, tags "nature" + biome tags). Kits in this pack call NAT directly so a later
module re-using a name cannot swap our trees out.

Context: STYLE.culture / STYLE.season are set by the nature kits for the duration of a build
(props.PROPS functions only receive the era key; see report "wanted core changes")."""
import math, random
from functools import lru_cache
import bmesh
from mathutils import Vector, Matrix, noise
from ..props import prop, PROPS, OLD, MID, NOW, FUT, in_family
from .. import room as _room
from ... import core
from ...ink import srgb

TAU = math.tau
NAT = {}


class _Style:
    culture = None       # layers.culture of the build in progress (kits set + reset it)
    season = None        # None | "autumn" | "winter" | "spring" | "dry"
    snow = False


STYLE = _Style()


@lru_cache(maxsize=256)
def _era_info(era, culture):
    key, d = core.resolve_era({"era": era, "culture": culture}, era if era else "modern")
    return d.get("family", key), d.get("roof", "gable"), frozenset(d.get("props", [])), d.get("culture")


def era_style(era):
    """(family, roof, prop tags, culture) for an era key under the current build's culture."""
    try:
        return _era_info(era, STYLE.culture)
    except Exception:
        return "modern", "gable", frozenset(), None


def has_tag(era, *tags):
    return bool(era_style(era)[2] & set(tags))


# ----------------------------------------------------------------------------- palette keys
def _s(*c):
    return srgb(*c)


NATURE_KEYS = {
    "n_bark": _s(0.36, 0.27, 0.20), "n_bark2": _s(0.46, 0.36, 0.27), "n_bark_birch": _s(0.90, 0.88, 0.82),
    "n_bark_red": _s(0.58, 0.32, 0.22), "n_bark_pale": _s(0.62, 0.56, 0.46), "n_bark_grey": _s(0.50, 0.46, 0.42),
    "n_charred": _s(0.15, 0.13, 0.12), "n_wood_end": _s(0.82, 0.68, 0.46), "n_ink": _s(0.12, 0.11, 0.10),
    "n_leaf": _s(0.34, 0.48, 0.30), "n_leaf2": _s(0.44, 0.56, 0.32), "n_leaf_dark": _s(0.22, 0.36, 0.30),
    "n_leaf_lime": _s(0.58, 0.64, 0.34), "n_leaf_aut": _s(0.84, 0.52, 0.22), "n_leaf_aut2": _s(0.72, 0.30, 0.18),
    "n_leaf_gold": _s(0.88, 0.72, 0.30), "n_leaf_dry": _s(0.64, 0.60, 0.34), "n_palm": _s(0.38, 0.54, 0.30),
    "n_blossom": _s(0.94, 0.74, 0.76), "n_blossom2": _s(0.96, 0.88, 0.86), "n_bamboo": _s(0.66, 0.68, 0.38),
    "n_bamboo2": _s(0.44, 0.48, 0.26), "n_grass": _s(0.50, 0.58, 0.32), "n_grass2": _s(0.40, 0.50, 0.28),
    "n_grass_dry": _s(0.82, 0.70, 0.42), "n_grass_dry2": _s(0.70, 0.58, 0.34), "n_stem": _s(0.36, 0.48, 0.28),
    "n_flower": _s(0.94, 0.90, 0.76), "n_flower2": _s(0.82, 0.40, 0.36), "n_flower3": _s(0.64, 0.56, 0.78),
    "n_flower4": _s(0.92, 0.78, 0.30), "n_fruit": _s(0.80, 0.30, 0.20), "n_fruit2": _s(0.72, 0.28, 0.46),
    "n_mush": _s(0.78, 0.28, 0.22), "n_mush_stem": _s(0.92, 0.88, 0.78), "n_coconut": _s(0.42, 0.30, 0.18),
    "n_rock": _s(0.60, 0.58, 0.54), "n_rock2": _s(0.47, 0.46, 0.44), "n_rock_red": _s(0.76, 0.48, 0.32),
    "n_rock_red2": _s(0.62, 0.36, 0.26), "n_rock_band": _s(0.86, 0.70, 0.50), "n_rock_dark": _s(0.24, 0.22, 0.22),
    "n_moss": _s(0.42, 0.52, 0.30), "n_snow": _s(0.95, 0.96, 0.97), "n_ice": _s(0.72, 0.86, 0.90), "n_ice2": _s(0.86, 0.94, 0.96),
    "n_sand": _s(0.90, 0.80, 0.60), "n_soil": _s(0.38, 0.29, 0.22), "n_coral": _s(0.90, 0.52, 0.45),
    "n_coral2": _s(0.92, 0.74, 0.52), "n_coral3": _s(0.74, 0.44, 0.56), "n_seaweed": _s(0.30, 0.36, 0.22),
    "n_driftwood": _s(0.74, 0.68, 0.58), "n_cactus": _s(0.42, 0.56, 0.38), "n_cactus2": _s(0.52, 0.62, 0.42),
    "n_succ": _s(0.52, 0.64, 0.58), "n_lily": _s(0.36, 0.54, 0.34), "n_reed": _s(0.62, 0.60, 0.36),
    "n_cattail": _s(0.36, 0.24, 0.16), "n_termite": _s(0.72, 0.50, 0.32), "n_tundra": _s(0.58, 0.44, 0.30),
    "n_tundra2": _s(0.50, 0.52, 0.34), "n_olive": _s(0.58, 0.62, 0.48), "n_olive2": _s(0.46, 0.52, 0.40),
    # settlement materials
    "n_hay": _s(0.88, 0.74, 0.40), "n_hay2": _s(0.76, 0.62, 0.32), "n_canvas": _s(0.88, 0.82, 0.68),
    "n_felt": _s(0.82, 0.74, 0.60), "n_rope": _s(0.72, 0.62, 0.44), "n_thatch": _s(0.74, 0.62, 0.38),
    "n_tile": _s(0.66, 0.34, 0.24), "n_slate": _s(0.36, 0.38, 0.42), "n_plaster": _s(0.92, 0.89, 0.80),
    "n_adobe": _s(0.82, 0.64, 0.46), "n_net": _s(0.48, 0.46, 0.38), "n_red": _s(0.70, 0.26, 0.20),
    "n_blue": _s(0.30, 0.44, 0.58), "n_teal": _s(0.28, 0.50, 0.48), "n_white": _s(0.92, 0.91, 0.88),
    "n_rust": _s(0.56, 0.32, 0.20), "n_steel": _s(0.62, 0.64, 0.66), "n_gold": _s(0.86, 0.68, 0.28),
    "n_vermilion": _s(0.82, 0.26, 0.16), "n_water": _s(0.30, 0.46, 0.50), "n_tarp": _s(0.36, 0.42, 0.30),
    "n_mars": _s(0.80, 0.46, 0.30), "n_solar": _s(0.18, 0.24, 0.36),
    "n_lava": {"color": _s(1.0, 0.46, 0.12), "emission": _s(1.0, 0.42, 0.10), "strength": 4.0},
    "n_crystal": {"color": _s(0.56, 0.88, 0.96), "emission": _s(0.50, 0.86, 0.96), "strength": 2.5},
    "n_ember": {"color": _s(1.0, 0.60, 0.20), "emission": _s(1.0, 0.55, 0.18), "strength": 3.0},
    "n_glowwin": {"color": _s(1.0, 0.80, 0.48), "emission": _s(1.0, 0.76, 0.42), "strength": 2.2},
    "n_neon": {"color": _s(0.40, 0.95, 0.90), "emission": _s(0.40, 0.95, 0.90), "strength": 3.0},
}


def _install_palette_defaults():
    """Additive hook: era_palette() also carries the nature keys (setdefault only, never overrides),
    so these props render with sensible colours in every kit and on the prop sheet."""
    orig = _room.era_palette
    if getattr(orig, "_pw_nature", False):
        return

    def era_palette(era_def, mood, state):
        pal = orig(era_def, mood, state)
        for k, v in NATURE_KEYS.items():
            pal.setdefault(k, v)
        if mood not in ("DUSK", "NIGHT") or state.get("lights_off"):
            pal["n_glowwin"] = srgb(0.24, 0.27, 0.29)       # unlit windows read as dark glass by day
        return pal

    era_palette._pw_nature = True
    _room.era_palette = era_palette
    from .. import terrain as _terrain, street as _street
    for mod in (_terrain, _street):
        if getattr(mod, "era_palette", None) is orig:
            mod.era_palette = era_palette


_install_palette_defaults()


# ----------------------------------------------------------------------------- geometry helpers
def frame(x, y, z, rot=0.0, s=1.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((s, s, s, 1.0))


def _xf(mb, vs, M):
    bmesh.ops.transform(mb.bm, matrix=M, verts=vs)
    return vs


def smooth(vs):
    for v in vs:
        for f in v.link_faces:
            f.smooth = True
    return vs


def box(mb, M, c, s, key, rz=0.0, rx=0.0, ry=0.0):
    vs = mb.box((0, 0, 0), s, key)
    R = Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")
    return _xf(mb, vs, M @ Matrix.Translation(c) @ R)


def cyl(mb, M, c, r, h, key, seg=10, r2=None, axis="Z"):
    vs = mb.cyl((0, 0, 0), r, h, key, seg=seg, r2=r2, axis=axis)
    return _xf(mb, vs, M @ Matrix.Translation(c))


def limb(mb, M, p0, p1, r0, r1, key, seg=6):
    """Tapered cylinder from p0 (radius r0) to p1 (radius r1), any direction."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = max(d.length, 1e-4)
    vs = mb.cyl((0, 0, 0), r0, L, key, seg=seg, r2=r1)
    q = Vector((0, 0, 1)).rotation_difference(d / L).to_matrix().to_4x4()
    return _xf(mb, vs, M @ Matrix.Translation(p0) @ q @ Matrix.Translation((0, 0, L / 2)))


def chain(mb, M, pts, r0, r1, key, seg=6):
    """Limbs along a polyline with radius lerped r0 -> r1."""
    n = len(pts) - 1
    for i in range(n):
        limb(mb, M, pts[i], pts[i + 1], r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n, key, seg)


def blob(mb, M, c, r, key, rng, sub=2, sq=1.0, lump=0.2, sx=1.0, sy=1.0, smooth_=True):
    """Lumpy, smooth-shaded canopy / bush / snow blob."""
    vs = mb.sphere((0, 0, 0), r, key, sub=sub)
    o = Vector((rng.uniform(-60, 60), rng.uniform(-60, 60), rng.uniform(-60, 60)))
    for v in vs:
        n = noise.noise(v.co * (1.5 / max(r, 1e-3)) + o)
        v.co *= 1.0 + lump * n
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sq
    if smooth_:
        smooth(vs)
    return _xf(mb, vs, M @ Matrix.Translation(c))


def rock(mb, M, c, r, key, rng, flat=0.7, sub=1, sx=1.0, sy=1.0, lump=0.32):
    """Faceted (flat-shaded) rock with a flattened base."""
    vs = mb.sphere((0, 0, 0), r, key, sub=sub)
    o = Vector((rng.uniform(-60, 60), rng.uniform(-60, 60), rng.uniform(-60, 60)))
    a = rng.uniform(0, TAU)
    R = Matrix.Rotation(a, 3, "Z")
    for v in vs:
        n = noise.noise(v.co * (1.2 / max(r, 1e-3)) + o)
        v.co *= 1.0 + lump * n
        v.co = R @ v.co
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= flat
        if v.co.z < -0.25 * r * flat:
            v.co.z = -0.25 * r * flat
    return _xf(mb, vs, M @ Matrix.Translation(c))


def jag_cone(mb, M, c, r, h, key, rng, seg=9, jag=0.3, droop=0.18):
    """Cone with a saw-tooth skirt (conifer tier, snow cap, spiky crown)."""
    bm = mb.bm
    c = Vector(c)
    n = seg * 2
    ring = []
    for i in range(n):
        a = i / n * TAU + rng.uniform(-0.06, 0.06)
        rr = r * (1.0 if i % 2 == 0 else 1.0 - jag) * rng.uniform(0.9, 1.08)
        zz = -droop * h if i % 2 == 0 else 0.0
        ring.append(bm.verts.new(c + Vector((math.cos(a) * rr, math.sin(a) * rr, zz))))
    apex = bm.verts.new(c + Vector((rng.uniform(-0.05, 0.05) * r, rng.uniform(-0.05, 0.05) * r, h)))
    mid = bm.verts.new(c + Vector((0, 0, h * 0.12)))
    faces = [bm.faces.new((ring[i], ring[(i + 1) % n], apex)) for i in range(n)]
    faces += [bm.faces.new((ring[(i + 1) % n], ring[i], mid)) for i in range(n)]
    mb._tag(faces, key)
    vs = ring + [apex, mid]
    return _xf(mb, vs, M)


def ribbon(mb, M, pts, widths, key, up=(0, 0, 1)):
    """Flat strip along pts (leaf, frond, blade of kelp); width per point."""
    bm = mb.bm
    pts = [Vector(p) for p in pts]
    n = len(pts)
    L, R = [], []
    for i, p in enumerate(pts):
        t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        side = t.cross(Vector(up))
        if side.length < 1e-5:
            side = Vector((1, 0, 0))
        side.normalize()
        w = max(widths[i], 0.004) / 2
        L.append(bm.verts.new(p - side * w))
        R.append(bm.verts.new(p + side * w))
    faces = [bm.faces.new((L[i], R[i], R[i + 1], L[i + 1])) for i in range(n - 1)]
    mb._tag(faces, key)
    return _xf(mb, L + R, M)


def blade(mb, M, base, tip, w, key):
    bm = mb.bm
    base, tip = Vector(base), Vector(tip)
    d = tip - base
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-5:
        side = Vector((1, 0, 0))
    side = side.normalized() * w / 2
    vs = [bm.verts.new(base - side), bm.verts.new(base + side), bm.verts.new(tip)]
    mb._tag([bm.faces.new(vs)], key)
    return _xf(mb, vs, M)


def branches(mb, M, rng, p, d, L, r, depth, key, tips, spread=0.6, up=0.35, kids=(2, 2, 3)):
    """Recursive bare branching; collects branch tips."""
    p, d = Vector(p), Vector(d).normalized()
    end = p + d * L
    limb(mb, M, p, end, r, r * 0.62, key, seg=5 if r > 0.07 else 4)
    if depth <= 0:
        tips.append(end)
        return
    for _ in range(rng.choice(kids)):
        nd = d + Vector((rng.uniform(-spread, spread), rng.uniform(-spread, spread), rng.uniform(-0.05, up)))
        branches(mb, M, rng, end, nd, L * rng.uniform(0.58, 0.74), r * 0.62, depth - 1, key, tips, spread, up, kids)


def on_sphere(rng, c, r, zmin=-0.2):
    while True:
        v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(zmin, 1)))
        if 0.2 < v.length <= 1.0:
            return Vector(c) + v.normalized() * r


def leaf_keys(season=None, base=("n_leaf", "n_leaf2")):
    season = season or STYLE.season
    if season == "autumn":
        return ("n_leaf_aut", "n_leaf_aut2", "n_leaf_gold")
    if season == "spring":
        return ("n_blossom", "n_leaf2", "n_blossom2")
    if season == "dry":
        return ("n_leaf_dry", "n_leaf_gold")
    return base


def is_winter(season=None):
    return (season or STYLE.season) == "winter" or STYLE.snow


def nat(name, place="floor", size=(1, 1, 1), eras=None, rooms=("nature",)):
    """Register a nature builder in NAT and (if the name is free) in props.PROPS."""
    def deco(fn):
        NAT[name] = fn

        def wrapped(mb, x, y, z, rot, rng, era, _fn=fn):
            return _fn(mb, x, y, z, rot, rng, era)
        if name not in PROPS or PROPS[name].get("_nature"):
            prop(name, place, size, eras, rooms)(wrapped)
            PROPS[name]["_nature"] = True
        else:
            prop("nat_" + name, place, size, eras, rooms)(wrapped)
        return fn
    return deco


# ----------------------------------------------------------------------------- broadleaf trees
def deciduous(mb, M, rng, trunk_h=2.6, trunk_r=0.42, limbs=(3, 4), limb_len=2.0, rise=(1.0, 2.0), crown=1.8,
              keys=None, bare=False, bark="n_bark", snow=False, crown_sq=0.78):
    keys = keys or leaf_keys()
    top = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), trunk_h))
    limb(mb, M, (0, 0, -0.2), top, trunk_r, trunk_r * 0.72, bark, seg=7)
    for k in range(4):
        a = k / 4 * TAU + rng.uniform(-0.4, 0.4)
        limb(mb, M, (math.cos(a) * trunk_r * 0.4, math.sin(a) * trunk_r * 0.4, 0.35),
             (math.cos(a) * trunk_r * 1.9, math.sin(a) * trunk_r * 1.9, -0.08), trunk_r * 0.4, trunk_r * 0.12, bark, seg=5)
    n = rng.randint(*limbs)
    ends = []
    for k in range(n):
        a = k / n * TAU + rng.uniform(-0.4, 0.4)
        end = top + Vector((math.cos(a) * limb_len, math.sin(a) * limb_len, rng.uniform(*rise)))
        limb(mb, M, top, end, trunk_r * 0.58, trunk_r * 0.26, bark, seg=6)
        ends.append(end)
        if bare:
            tips = []
            branches(mb, M, rng, end, end - top, limb_len * 0.7, trunk_r * 0.24, 2, bark, tips, spread=0.7, up=0.5)
            if snow:
                blob(mb, M, end + Vector((0, 0, trunk_r * 0.25)), trunk_r * 0.45, "n_snow", rng, sub=1, sq=0.35, lump=0.1)
    if bare:
        if snow:
            blob(mb, M, top + Vector((0, 0, trunk_r * 0.3)), trunk_r * 0.7, "n_snow", rng, sub=1, sq=0.35, lump=0.1)
        return ends
    for e in ends:
        blob(mb, M, e + Vector((0, 0, crown * 0.25)), crown * rng.uniform(0.82, 1.05), rng.choice(keys), rng, sq=crown_sq)
    blob(mb, M, top + Vector((0, 0, rise[1] + crown * 0.55)), crown * 1.12, keys[0], rng, sq=crown_sq)
    if snow:
        blob(mb, M, top + Vector((0, 0, rise[1] + crown * 1.25)), crown * 0.8, "n_snow", rng, sq=0.32, lump=0.12)
    return ends


@nat("oak", size=(7, 7, 8), rooms=("nature", "forest", "park", "farm", "garden"))
def oak(mb, x, y, z, rot, rng, era, s=1.0, season=None):
    M = frame(x, y, z, rot, s)
    w = is_winter(season)
    deciduous(mb, M, rng, keys=leaf_keys(season), bare=w, snow=STYLE.snow)


@nat("oak_autumn", size=(7, 7, 8), rooms=("nature", "forest", "park"))
def oak_autumn(mb, x, y, z, rot, rng, era, s=1.0):
    deciduous(mb, frame(x, y, z, rot, s), rng, keys=leaf_keys("autumn"))


@nat("oak_bare", size=(7, 7, 8), rooms=("nature", "forest", "park", "graveyard"))
def oak_bare(mb, x, y, z, rot, rng, era, s=1.0):
    deciduous(mb, frame(x, y, z, rot, s), rng, bare=True, snow=STYLE.snow)


@nat("birch", size=(3, 3, 9), rooms=("nature", "forest", "park"))
def birch(mb, x, y, z, rot, rng, era, s=1.0, season=None):
    M = frame(x, y, z, rot, s)
    h = rng.uniform(7.0, 9.0)
    p1 = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), h * 0.55))
    p2 = p1 + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), h * 0.45))
    limb(mb, M, (0, 0, -0.1), p1, 0.17, 0.12, "n_bark_birch", seg=7)
    limb(mb, M, p1, p2, 0.12, 0.04, "n_bark_birch", seg=6)
    for _ in range(14):                                     # the black birch dashes
        t = rng.uniform(0.04, 0.95)
        c = Vector((0, 0, -0.1)).lerp(p1, t / 0.55) if t < 0.55 else p1.lerp(p2, (t - 0.55) / 0.45)
        rr = 0.17 - 0.13 * t
        a = rng.uniform(0, TAU)
        box(mb, M, c + Vector((math.cos(a), math.sin(a), 0)) * rr * 0.92, (rr * 1.3, 0.035, rng.uniform(0.03, 0.07)), "n_ink", rz=a + math.pi / 2)
    keys = leaf_keys(season, ("n_leaf_lime", "n_leaf2"))
    if is_winter(season):
        tips = []
        for k in range(5):
            a = rng.uniform(0, TAU)
            branches(mb, M, rng, p1.lerp(p2, k / 5), (math.cos(a), math.sin(a), 1.2), 1.4, 0.05, 1, "n_bark_grey", tips)
        return
    if season == "autumn" or STYLE.season == "autumn":
        keys = ("n_leaf_gold", "n_leaf_aut")
    for k in range(rng.randint(5, 7)):
        t = rng.uniform(0.15, 1.0)
        c = p1.lerp(p2, t)
        a = rng.uniform(0, TAU)
        blob(mb, M, c + Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 0)), rng.uniform(0.8, 1.15), rng.choice(keys), rng, sq=1.35)


@nat("birch_autumn", size=(3, 3, 9), rooms=("nature", "forest", "park"))
def birch_autumn(mb, x, y, z, rot, rng, era, s=1.0):
    birch(mb, x, y, z, rot, rng, era, s, season="autumn")


@nat("willow", size=(7, 7, 6), rooms=("nature", "river", "lake", "park", "garden"))
def willow(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    top = Vector((0.5, 0, 2.3))
    limb(mb, M, (0, 0, -0.2), top, 0.55, 0.4, "n_bark", seg=7)
    for k in range(4):
        a = k / 4 * TAU + 0.3
        limb(mb, M, top, top + Vector((math.cos(a) * 1.8, math.sin(a) * 1.8, 1.7)), 0.24, 0.1, "n_bark", seg=5)
    keys = leaf_keys(None, ("n_leaf2", "n_leaf_lime"))
    if is_winter():
        keys = ("n_leaf_dry", "n_bark2")
    c = top + Vector((0, 0, 1.9))
    blob(mb, M, c, 2.6, keys[0], rng, sq=0.42)
    for k in range(4):
        a = k / 4 * TAU + 0.7
        blob(mb, M, c + Vector((math.cos(a) * 1.7, math.sin(a) * 1.7, -0.5)), 1.6, keys[-1], rng, sq=0.6)
    for i in range(46):                                     # hanging curtains
        a = i / 46 * TAU + rng.uniform(-0.05, 0.05)
        rr = rng.uniform(2.2, 2.9)
        zt = c.z - rng.uniform(0.3, 0.9)
        ln = rng.uniform(2.4, 3.8)
        p0 = Vector((c.x + math.cos(a) * rr, c.y + math.sin(a) * rr, zt))
        pm = p0 + Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, -ln * 0.5))
        k = rng.choice(keys)
        limb(mb, M, p0, pm, 0.13, 0.07, k, seg=4)
        limb(mb, M, pm, pm + Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, -ln * 0.5)), 0.07, 0.01, k, seg=4)


@nat("fruit_tree", size=(4, 4, 4.5), rooms=("nature", "orchard", "farm", "garden"))
def fruit_tree(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    if is_winter():
        deciduous(mb, M, rng, trunk_h=1.5, trunk_r=0.22, limb_len=1.2, rise=(0.6, 1.1), bare=True, snow=STYLE.snow)
        return
    keys = leaf_keys(None)
    deciduous(mb, M, rng, trunk_h=1.5, trunk_r=0.22, limb_len=1.1, rise=(0.6, 1.1), crown=1.2, keys=keys, crown_sq=0.85)
    for _ in range(16):
        c = on_sphere(rng, (0, 0, 3.0), 1.65, zmin=-0.5)
        mb_s = mb.sphere((0, 0, 0), 0.1, "n_fruit" if STYLE.season != "autumn" else "n_leaf_gold", sub=1)
        _xf(mb, mb_s, M @ Matrix.Translation(c))


@nat("blossom_tree", size=(4, 4, 4.5), rooms=("nature", "orchard", "garden", "shrine", "park"))
def blossom_tree(mb, x, y, z, rot, rng, era, s=1.0):
    deciduous(mb, frame(x, y, z, rot, s), rng, trunk_h=1.6, trunk_r=0.24, limb_len=1.4, rise=(0.5, 1.0), crown=1.3,
              keys=("n_blossom", "n_blossom2", "n_blossom"), bark="n_bark", crown_sq=0.7)


@nat("baobab", size=(6, 6, 8), rooms=("nature", "savanna"))
def baobab(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    limb(mb, M, (0, 0, -0.3), (0, 0, 2.6), 1.55, 1.3, "n_bark_pale", seg=11)
    limb(mb, M, (0, 0, 2.6), (0.1, 0, 5.0), 1.3, 0.65, "n_bark_pale", seg=11)
    top = Vector((0.1, 0, 4.9))
    dry = STYLE.season in ("dry", "winter")
    for k in range(7):
        a = k / 7 * TAU + rng.uniform(-0.3, 0.3)
        end = top + Vector((math.cos(a) * 2.1, math.sin(a) * 2.1, rng.uniform(0.6, 1.4)))
        limb(mb, M, top, end, 0.35, 0.12, "n_bark_pale", seg=5)
        tips = []
        branches(mb, M, rng, end, end - top + Vector((0, 0, 0.5)), 0.9, 0.1, 1, "n_bark_pale", tips, kids=(2, 3))
        if not dry:
            for t in tips:
                blob(mb, M, t, rng.uniform(0.45, 0.7), rng.choice(("n_leaf", "n_leaf_dry")), rng, sub=1, sq=0.6)


@nat("acacia", size=(7, 7, 6), rooms=("nature", "savanna"))
def acacia(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    fork = Vector((0.4, 0, 2.2))
    limb(mb, M, (0, 0, -0.1), fork, 0.22, 0.17, "n_bark", seg=6)
    ends = []
    for k in range(rng.randint(3, 4)):
        a = k / 3.5 * TAU + rng.uniform(-0.3, 0.3)
        e = fork + Vector((math.cos(a) * 1.9, math.sin(a) * 1.9, rng.uniform(2.0, 2.6)))
        limb(mb, M, fork, e, 0.15, 0.07, "n_bark", seg=5)
        ends.append(e)
    keys = ("n_leaf_dry", "n_leaf") if STYLE.season != "dry" else ("n_leaf_dry", "n_leaf_gold")
    for e in ends:
        blob(mb, M, e + Vector((0, 0, 0.25)), rng.uniform(2.0, 2.6), rng.choice(keys), rng, sq=0.24, lump=0.3)


@nat("dead_tree", size=(5, 5, 7), rooms=("nature", "swamp", "wasteland", "graveyard", "desert"))
def dead_tree(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    top = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 3.0))
    limb(mb, M, (0, 0, -0.2), top, 0.32, 0.22, "n_bark_grey", seg=6)
    tips = []
    for k in range(3):
        a = k / 3 * TAU + rng.uniform(-0.5, 0.5)
        branches(mb, M, rng, top, (math.cos(a), math.sin(a), 1.1), 1.8, 0.16, 2, "n_bark_grey", tips, spread=0.8)


@nat("burnt_tree", size=(2, 2, 5), rooms=("nature", "wasteland", "volcanic", "battlefield"))
def burnt_tree(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    h = rng.uniform(3.0, 5.5)
    top = Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), h))
    limb(mb, M, (0, 0, -0.2), top, 0.34, 0.16, "n_charred", seg=6)
    limb(mb, M, top, top + Vector((0.1, 0.05, 0.7)), 0.16, 0.0, "n_charred", seg=4)        # broken spike
    for k in range(rng.randint(2, 4)):
        a = rng.uniform(0, TAU)
        p = Vector((0, 0, -0.2)).lerp(top, rng.uniform(0.4, 0.9))
        limb(mb, M, p, p + Vector((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.5)), 0.1, 0.02, "n_charred", seg=4)


@nat("redwood", size=(6, 6, 30), rooms=("nature", "forest"))
def redwood(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    limb(mb, M, (0, 0, -0.4), (0, 0, 14), 1.35, 0.78, "n_bark_red", seg=11)
    limb(mb, M, (0, 0, 14), (0.2, 0, 29), 0.78, 0.12, "n_bark_red", seg=9)
    for k in range(5):
        a = k / 5 * TAU
        limb(mb, M, (math.cos(a) * 0.6, math.sin(a) * 0.6, 1.2), (math.cos(a) * 2.2, math.sin(a) * 2.2, -0.1), 0.5, 0.15, "n_bark_red", seg=5)
    for i in range(7):
        zz = 13 + i * 2.4
        r = 3.6 - i * 0.42
        jag_cone(mb, M, (0.03 * zz / 2, 0, zz), r, 3.4, "n_leaf_dark" if i % 2 else "n_leaf", rng, seg=8, jag=0.35)
        if STYLE.snow:
            jag_cone(mb, M, (0.03 * zz / 2, 0, zz + 1.2), r * 0.66, 2.3, "n_snow", rng, seg=8, jag=0.3, droop=0.1)


# ----------------------------------------------------------------------------- conifers + palms
@nat("spruce", size=(4.5, 4.5, 10), rooms=("nature", "forest", "snow", "mountain"))
def spruce(mb, x, y, z, rot, rng, era, s=1.0, snow=None):
    M = frame(x, y, z, rot, s)
    snow = STYLE.snow if snow is None else snow
    h = rng.uniform(8.0, 10.5)
    R = rng.uniform(2.0, 2.4)
    limb(mb, M, (0, 0, -0.2), (0, 0, h * 0.35), 0.26, 0.2, "n_bark", seg=6)
    n = 6
    for i in range(n):
        zz = h * (0.12 + i * 0.14)
        r = R * (1.0 - i / n * 0.82)
        ht = h * 0.27
        jag_cone(mb, M, (0, 0, zz), r, ht, "n_leaf_dark", rng, seg=9, jag=0.32)
        if snow:
            jag_cone(mb, M, (0, 0, zz + ht * 0.3), r * 0.8, ht * 0.72, "n_snow", rng, seg=9, jag=0.38, droop=0.1)


@nat("spruce_snow", size=(4.5, 4.5, 10), rooms=("nature", "forest", "snow", "mountain"))
def spruce_snow(mb, x, y, z, rot, rng, era, s=1.0):
    spruce(mb, x, y, z, rot, rng, era, s, snow=True)


@nat("pine", size=(4, 4, 9), rooms=("nature", "forest", "mountain"))
def pine(mb, x, y, z, rot, rng, era, s=1.0):
    """Scots pine: tall orange-barked trunk, flat clumps of needles up top."""
    M = frame(x, y, z, rot, s)
    h = rng.uniform(7.0, 9.0)
    p1 = Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), h * 0.6))
    p2 = p1 + Vector((rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), h * 0.4))
    limb(mb, M, (0, 0, -0.2), p1, 0.28, 0.2, "n_bark2", seg=6)
    limb(mb, M, p1, p2, 0.2, 0.08, "n_bark_red", seg=6)
    for k in range(rng.randint(4, 6)):
        t = rng.uniform(0.0, 1.0)
        c = p1.lerp(p2, t)
        a = rng.uniform(0, TAU)
        e = c + Vector((math.cos(a) * (1.4 - t * 0.7), math.sin(a) * (1.4 - t * 0.7), 0.4))
        limb(mb, M, c, e, 0.09, 0.04, "n_bark_red", seg=4)
        blob(mb, M, e + Vector((0, 0, 0.2)), rng.uniform(0.85, 1.25), rng.choice(("n_leaf_dark", "n_leaf")), rng, sub=2, sq=0.42, lump=0.3)
        if STYLE.snow:
            blob(mb, M, e + Vector((0, 0, 0.55)), 0.75, "n_snow", rng, sub=1, sq=0.3, lump=0.15)
    blob(mb, M, p2 + Vector((0, 0, 0.2)), 1.0, "n_leaf_dark", rng, sq=0.5)


@nat("pine_umbrella", size=(8, 8, 8), rooms=("nature", "mediterranean", "garden"))
def pine_umbrella(mb, x, y, z, rot, rng, era, s=1.0):
    """Stone pine: bent trunk, wide flat umbrella crown (Mediterranean / classical landscapes)."""
    M = frame(x, y, z, rot, s)
    pts = [Vector((0, 0, -0.2)), Vector((0.5, 0, 2.5)), Vector((1.4, 0.2, 4.6)), Vector((1.8, 0.2, 6.2))]
    chain(mb, M, pts, 0.32, 0.16, "n_bark2", seg=6)
    top = pts[-1]
    for k in range(3):
        a = k / 3 * TAU
        limb(mb, M, top, top + Vector((math.cos(a) * 1.4, math.sin(a) * 1.4, 0.6)), 0.14, 0.06, "n_bark2", seg=4)
    blob(mb, M, top + Vector((0, 0, 1.0)), 3.4, "n_leaf_dark", rng, sq=0.3, lump=0.25)
    blob(mb, M, top + Vector((0.8, 0.4, 1.4)), 2.2, "n_leaf", rng, sq=0.32, lump=0.25)


@nat("cypress", size=(2, 2, 9), rooms=("nature", "mediterranean", "garden", "graveyard"))
def cypress(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    limb(mb, M, (0, 0, -0.2), (0, 0, 1.0), 0.2, 0.16, "n_bark", seg=5)
    h = rng.uniform(7.0, 9.0)
    blob(mb, M, (0, 0, h * 0.5), 1.05, "n_leaf_dark", rng, sq=h / 2.0 / 1.05 * 0.95, lump=0.15)


def palm_tree(mb, M, rng, H=8.0, bend=0.25, fronds=8, coconuts=0, frond_len=3.2):
    pts = [Vector((bend * (t ** 2) * H, 0, t * H)) for t in [i / 6 for i in range(7)]]
    pts[0].z = -0.2
    for i in range(6):
        limb(mb, M, pts[i], pts[i + 1], 0.24 - i * 0.012, 0.22 - i * 0.012, "n_bark_pale" if i % 2 else "n_bark2", seg=7)
    top = pts[-1]
    blob(mb, M, top, 0.35, "n_bark2", rng, sub=1, sq=0.8)
    for k in range(fronds):
        a = k / fronds * TAU + rng.uniform(-0.15, 0.15)
        d = Vector((math.cos(a), math.sin(a), 0))
        lift = rng.uniform(0.6, 1.4)
        P = [top + d * (u * frond_len) + Vector((0, 0, lift * math.sin(u * math.pi * 0.8) - 1.9 * u * u)) for u in [j / 7 for j in range(8)]]
        W = [0.08, 0.5, 0.75, 0.8, 0.7, 0.5, 0.3, 0.02]
        ribbon(mb, M, P, [w * rng.uniform(0.85, 1.1) for w in W], "n_palm" if k % 2 else "n_leaf")
    for k in range(coconuts):
        a = k / max(coconuts, 1) * TAU
        _xf(mb, mb.sphere((0, 0, 0), 0.16, "n_coconut", sub=1), M @ Matrix.Translation(top + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, -0.35))))


@nat("palm", size=(6, 6, 9), rooms=("nature", "beach", "jungle", "tropical"))
def palm(mb, x, y, z, rot, rng, era, s=1.0):
    palm_tree(mb, frame(x, y, z, rot, s), rng, H=rng.uniform(7.5, 9.5), bend=rng.uniform(0.05, 0.15), fronds=9)


@nat("palm_coconut", size=(6, 6, 8), rooms=("nature", "beach", "tropical"))
def palm_coconut(mb, x, y, z, rot, rng, era, s=1.0):
    palm_tree(mb, frame(x, y, z, rot, s), rng, H=rng.uniform(6.5, 8.0), bend=rng.uniform(0.3, 0.45), fronds=8, coconuts=4)


@nat("palm_short", size=(4, 4, 3.5), rooms=("nature", "beach", "jungle", "tropical", "garden"))
def palm_short(mb, x, y, z, rot, rng, era, s=1.0):
    palm_tree(mb, frame(x, y, z, rot, s), rng, H=rng.uniform(1.8, 2.6), bend=0.05, fronds=11, frond_len=2.0)


@nat("bamboo_clump", size=(2.5, 2.5, 8), rooms=("nature", "bamboo", "jungle", "garden", "shrine"))
def bamboo_clump(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for i in range(rng.randint(10, 15)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.8)
        base = Vector((math.cos(a) * rr, math.sin(a) * rr, -0.1))
        lean = Vector((math.cos(a) * rng.uniform(0.05, 0.14), math.sin(a) * rng.uniform(0.05, 0.14), 1)).normalized()
        H = rng.uniform(6.0, 9.0)
        segs = 6
        r = rng.uniform(0.05, 0.08)
        prev = base
        for k in range(segs):
            nxt = base + lean * H * (k + 1) / segs + Vector((0, 0, 0)) + lean * (k * k * 0.02)
            limb(mb, M, prev, nxt, r, r * 0.95, "n_bamboo", seg=6)
            cyl(mb, M, nxt, r * 1.25, 0.05, "n_bamboo2", seg=6)
            prev = nxt
        for k in range(rng.randint(2, 4)):                    # leaf sprays near the top
            c = base + lean * H * rng.uniform(0.6, 1.0)
            b = rng.uniform(0, TAU)
            d = Vector((math.cos(b), math.sin(b), 0))
            P = [c + d * u * 1.1 + Vector((0, 0, 0.2 * math.sin(u * 3) - 0.5 * u * u)) for u in (0, 0.25, 0.5, 0.75, 1.0)]
            ribbon(mb, M, P, [0.02, 0.16, 0.2, 0.14, 0.01], "n_leaf_lime" if k % 2 else "n_leaf2")


# ----------------------------------------------------------------------------- bushes, flowers, grass
@nat("bush", size=(1.6, 1.6, 1.2), rooms=("nature", "garden", "park", "forest", "farm"))
def bush(mb, x, y, z, rot, rng, era, s=1.0, keys=None, berries=False):
    M = frame(x, y, z, rot, s)
    keys = keys or (("n_bark2", "n_leaf_dry") if is_winter() and not STYLE.snow else leaf_keys(None, ("n_leaf2", "n_leaf")))
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, TAU)
        r = rng.uniform(0.45, 0.8)
        blob(mb, M, (math.cos(a) * 0.4, math.sin(a) * 0.4, r * 0.55), r, rng.choice(keys), rng, sq=0.75)
    if STYLE.snow:
        blob(mb, M, (0, 0, 0.95), 0.6, "n_snow", rng, sub=1, sq=0.35, lump=0.12)
    if berries:
        for _ in range(12):
            _xf(mb, mb.sphere((0, 0, 0), 0.05, "n_fruit", sub=0), M @ Matrix.Translation(on_sphere(rng, (0, 0, 0.5), 0.75, zmin=0.0)))


@nat("bush_berry", size=(1.6, 1.6, 1.2), rooms=("nature", "garden", "forest"))
def bush_berry(mb, x, y, z, rot, rng, era, s=1.0):
    bush(mb, x, y, z, rot, rng, era, s, keys=("n_leaf_dark", "n_leaf"), berries=True)


@nat("bush_autumn", size=(1.6, 1.6, 1.2), rooms=("nature", "garden", "park", "forest"))
def bush_autumn(mb, x, y, z, rot, rng, era, s=1.0):
    bush(mb, x, y, z, rot, rng, era, s, keys=("n_leaf_aut", "n_leaf_aut2", "n_leaf_gold"))


@nat("hedge", size=(3.0, 1.0, 1.4), rooms=("nature", "garden", "park", "farm"))
def hedge(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    box(mb, M, (0, 0, 0.62), (3.0, 0.9, 1.24), "n_leaf_dark")
    for k in range(5):
        blob(mb, M, (-1.2 + k * 0.6, rng.uniform(-0.1, 0.1), 1.2), rng.uniform(0.38, 0.5), "n_leaf_dark" if k % 2 else "n_leaf", rng, sub=1, sq=0.45)
    if STYLE.snow:
        box(mb, M, (0, 0, 1.3), (3.05, 0.95, 0.12), "n_snow")


@nat("flowers", size=(0.8, 0.8, 0.5), rooms=("nature", "garden", "park", "meadow"))
def flowers(mb, x, y, z, rot, rng, era, s=1.0, keys=None):
    M = frame(x, y, z, rot, s)
    keys = keys or (rng.choice(("n_flower", "n_flower2", "n_flower3", "n_flower4")),)
    for i in range(rng.randint(9, 14)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.38)
        b = Vector((math.cos(a) * rr, math.sin(a) * rr, 0))
        h = rng.uniform(0.25, 0.5)
        t = b + Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), h))
        limb(mb, M, b, t, 0.012, 0.01, "n_stem", seg=3)
        jag_cone(mb, M, t - Vector((0, 0, 0.03)), rng.uniform(0.07, 0.11), 0.07, rng.choice(keys), rng, seg=5, jag=0.45, droop=0.0)
        blade(mb, M, b, b + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), h * 0.5)), 0.09, "n_grass")


@nat("flowers_wild", size=(1.0, 1.0, 0.6), rooms=("nature", "meadow", "garden", "park"))
def flowers_wild(mb, x, y, z, rot, rng, era, s=1.0):
    flowers(mb, x, y, z, rot, rng, era, s, keys=("n_flower", "n_flower2", "n_flower3", "n_flower4"))
    tall_grass(mb, x, y, z, rot, rng, era, s * 0.6, n=10)


@nat("tall_grass", size=(1.0, 1.0, 1.0), rooms=("nature", "meadow", "farm", "river", "savanna"))
def tall_grass(mb, x, y, z, rot, rng, era, s=1.0, keys=None, n=None):
    M = frame(x, y, z, rot, s)
    keys = keys or (("n_grass_dry", "n_grass_dry2") if STYLE.season in ("dry", "autumn") else ("n_grass", "n_grass2"))
    for i in range(n or rng.randint(18, 26)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.45)
        b = Vector((math.cos(a) * rr, math.sin(a) * rr, -0.02))
        h = rng.uniform(0.55, 1.1)
        t = b + Vector((math.cos(a) * h * 0.3 + rng.uniform(-0.1, 0.1), math.sin(a) * h * 0.3, h))
        blade(mb, M, b, t, rng.uniform(0.08, 0.13), rng.choice(keys))


@nat("grass_dry", size=(1.0, 1.0, 0.9), rooms=("nature", "savanna", "desert", "wasteland"))
def grass_dry(mb, x, y, z, rot, rng, era, s=1.0):
    tall_grass(mb, x, y, z, rot, rng, era, s, keys=("n_grass_dry", "n_grass_dry2", "n_leaf_gold"))


@nat("fern", size=(1.8, 1.8, 0.8), rooms=("nature", "forest", "jungle", "cave"))
def fern(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    key = "n_leaf_aut" if STYLE.season == "autumn" else "n_leaf2"
    for k in range(rng.randint(7, 9)):
        a = k / 8 * TAU + rng.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        L = rng.uniform(0.8, 1.1)
        P = [d * u * L + Vector((0, 0, 0.6 * math.sin(u * math.pi * 0.8) * L)) for u in (0, 0.2, 0.4, 0.6, 0.8, 1.0)]
        ribbon(mb, M, P, [0.04, 0.22, 0.3, 0.26, 0.16, 0.02], key if k % 3 else "n_leaf")


@nat("mushrooms", size=(0.5, 0.5, 0.3), rooms=("nature", "forest", "cave", "swamp"))
def mushrooms(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for i in range(rng.randint(3, 6)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.22)
        b = Vector((math.cos(a) * rr, math.sin(a) * rr, 0))
        h = rng.uniform(0.08, 0.24)
        r = rng.uniform(0.06, 0.14)
        limb(mb, M, b, b + Vector((0, 0, h)), r * 0.35, r * 0.3, "n_mush_stem", seg=5)
        blob(mb, M, b + Vector((0, 0, h)), r, "n_mush", rng, sub=1, sq=0.55, lump=0.1)
        for _ in range(3):
            _xf(mb, mb.sphere((0, 0, 0), r * 0.16, "n_mush_stem", sub=0), M @ Matrix.Translation(on_sphere(rng, b + Vector((0, 0, h)), r * 1.0, zmin=0.35)))


@nat("mushroom_giant", size=(3, 3, 3.5), rooms=("nature", "fantasy", "forest", "cave"))
def mushroom_giant(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    pts = [Vector((0, 0, -0.1)), Vector((0.15, 0, 1.2)), Vector((0.1, 0.1, 2.6))]
    chain(mb, M, pts, 0.36, 0.26, "n_mush_stem", seg=8)
    blob(mb, M, pts[-1], 1.5, "n_mush", rng, sq=0.45, lump=0.1)
    for _ in range(9):
        _xf(mb, mb.sphere((0, 0, 0), 0.16, "n_mush_stem", sub=1), M @ Matrix.Translation(on_sphere(rng, pts[-1], 1.45, zmin=0.25)))


@nat("reeds", size=(1.2, 1.2, 2.0), rooms=("nature", "swamp", "river", "lake"))
def reeds(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for i in range(rng.randint(14, 22)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.5)
        b = Vector((math.cos(a) * rr, math.sin(a) * rr, -0.1))
        h = rng.uniform(1.1, 2.0)
        blade(mb, M, b, b + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), h)), 0.09, rng.choice(("n_reed", "n_grass2")))
    for i in range(rng.randint(3, 6)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.4)
        b = Vector((math.cos(a) * rr, math.sin(a) * rr, 0))
        h = rng.uniform(1.2, 1.7)
        limb(mb, M, b, b + Vector((0, 0, h)), 0.012, 0.01, "n_stem", seg=3)
        cyl(mb, M, b + Vector((0, 0, h + 0.12)), 0.035, 0.24, "n_cattail", seg=6)


@nat("lily_pads", place="floor", size=(1.5, 1.5, 0.05), rooms=("nature", "lake", "swamp", "pond", "garden"))
def lily_pads(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for i in range(rng.randint(5, 9)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.7)
        c = Vector((math.cos(a) * rr, math.sin(a) * rr, 0.01))
        cyl(mb, M, c, rng.uniform(0.18, 0.36), 0.02, "n_lily", seg=11)
    for i in range(rng.randint(1, 2)):
        jag_cone(mb, M, (rng.uniform(-0.4, 0.4), rng.uniform(-0.4, 0.4), 0.02), 0.09, 0.1, rng.choice(("n_flower", "n_blossom")), rng, seg=5, jag=0.5, droop=0.0)


@nat("shrub_tundra", size=(1.4, 1.4, 0.5), rooms=("nature", "tundra", "mountain", "snow"))
def shrub_tundra(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for k in range(rng.randint(4, 7)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 0.55)
        r = rng.uniform(0.25, 0.5)
        blob(mb, M, (math.cos(a) * rr, math.sin(a) * rr, r * 0.2), r, rng.choice(("n_tundra", "n_tundra2", "n_leaf_aut2")), rng, sub=1, sq=0.42, lump=0.3)


# ----------------------------------------------------------------------------- desert plants
@nat("cactus_saguaro", size=(2, 2, 4.5), rooms=("nature", "desert", "western"))
def cactus_saguaro(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    H = rng.uniform(3.4, 4.6)
    limb(mb, M, (0, 0, -0.1), (0, 0, H), 0.32, 0.29, "n_cactus", seg=9)
    blob(mb, M, (0, 0, H), 0.29, "n_cactus", rng, sub=1, sq=1.1, lump=0.05, smooth_=False)
    for side in rng.sample((-1, 1), rng.randint(1, 2)):
        ha = rng.uniform(1.2, 2.2)
        e = Vector((side * 0.85, 0, ha + 0.2))
        limb(mb, M, (0, 0, ha), e, 0.2, 0.2, "n_cactus", seg=8)
        top = e + Vector((0, 0, rng.uniform(0.9, 1.5)))
        limb(mb, M, e, top, 0.2, 0.18, "n_cactus", seg=8)
        blob(mb, M, top, 0.18, "n_cactus", rng, sub=1, lump=0.05, smooth_=False)


@nat("cactus_barrel", size=(1, 1, 0.9), rooms=("nature", "desert", "western"))
def cactus_barrel(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    cyl(mb, M, (0, 0, 0.3), 0.42, 0.6, "n_cactus2", seg=12, r2=0.36)
    blob(mb, M, (0, 0, 0.6), 0.36, "n_cactus2", rng, sub=1, sq=0.5, lump=0.05, smooth_=False)
    for k in range(3):
        _xf(mb, mb.sphere((0, 0, 0), 0.07, "n_flower4", sub=1), M @ Matrix.Translation((math.cos(k * 2) * 0.12, math.sin(k * 2) * 0.12, 0.78)))


@nat("cactus_pear", size=(1.5, 1.5, 1.6), rooms=("nature", "desert", "mediterranean", "western"))
def cactus_pear(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)

    def pad(c, a, size, depth):
        R = Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(rng.uniform(-0.3, 0.3), 4, "Y")
        vs = mb.sphere((0, 0, 0), size, "n_cactus2", sub=1)
        for v in vs:
            v.co.x *= 0.85
            v.co.y *= 0.22
            v.co.z *= 1.15
        _xf(mb, vs, M @ Matrix.Translation(c) @ R)
        if depth > 0:
            for k in range(rng.randint(1, 2)):
                b = a + rng.uniform(-0.9, 0.9)
                pad(Vector(c) + Vector((math.cos(a) * size * rng.uniform(-0.6, 0.6), math.sin(a) * size * 0.3, size * 1.6)), b, size * 0.85, depth - 1)
        elif rng.random() < 0.7:
            _xf(mb, mb.sphere((0, 0, 0), 0.06, "n_fruit2", sub=1), M @ Matrix.Translation(Vector(c) + Vector((0, 0, size * 1.1))))
    for k in range(rng.randint(2, 3)):
        pad(Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.3)), rng.uniform(0, TAU), 0.32, 2)


@nat("succulents", size=(1.2, 1.2, 0.8), rooms=("nature", "desert", "garden", "mediterranean"))
def succulents(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for c, sc in (((0, 0, 0), 1.0), ((0.6, 0.2, 0), 0.55)):
        n = rng.randint(11, 15)
        for k in range(n):
            a = k / n * TAU + rng.uniform(-0.1, 0.1)
            L = rng.uniform(0.55, 0.8) * sc
            el = rng.uniform(0.5, 1.1)
            limb(mb, M, Vector(c) + Vector((0, 0, 0.05)), Vector(c) + Vector((math.cos(a) * L * math.cos(el), math.sin(a) * L * math.cos(el), L * math.sin(el))),
                 0.09 * sc, 0.0, "n_succ", seg=4)


# ----------------------------------------------------------------------------- rocks, wood, snow, shore
@nat("boulder", size=(2.5, 2.5, 1.6), rooms=("nature", "any_outdoor"))
def boulder(mb, x, y, z, rot, rng, era, s=1.0, key="n_rock", moss=False):
    M = frame(x, y, z, rot, s)
    r = rng.uniform(0.9, 1.4)
    rock(mb, M, (0, 0, r * 0.35), r, key, rng, flat=0.75, sx=rng.uniform(1.0, 1.4))
    if rng.random() < 0.5:
        rock(mb, M, (r * 1.1, r * 0.3, r * 0.15), r * 0.4, key, rng, flat=0.7)
    if moss:
        blob(mb, M, (0, 0, r * 0.85), r * 0.75, "n_moss", rng, sub=1, sq=0.3, lump=0.25, smooth_=False)
    if STYLE.snow:
        blob(mb, M, (0, 0, r * 0.95), r * 0.7, "n_snow", rng, sub=1, sq=0.28, lump=0.15)


@nat("boulder_mossy", size=(2.5, 2.5, 1.6), rooms=("nature", "forest", "swamp"))
def boulder_mossy(mb, x, y, z, rot, rng, era, s=1.0):
    boulder(mb, x, y, z, rot, rng, era, s, moss=True)


@nat("boulder_red", size=(2.5, 2.5, 1.6), rooms=("nature", "desert", "canyon", "mars"))
def boulder_red(mb, x, y, z, rot, rng, era, s=1.0):
    boulder(mb, x, y, z, rot, rng, era, s, key="n_rock_red")


@nat("boulder_dark", size=(2.5, 2.5, 1.6), rooms=("nature", "volcanic", "cave"))
def boulder_dark(mb, x, y, z, rot, rng, era, s=1.0):
    boulder(mb, x, y, z, rot, rng, era, s, key="n_rock_dark")


@nat("rock_outcrop", size=(5, 5, 4), rooms=("nature", "mountain", "desert", "tundra", "moor"))
def rock_outcrop(mb, x, y, z, rot, rng, era, s=1.0, keys=("n_rock", "n_rock2")):
    M = frame(x, y, z, rot, s)
    rock(mb, M, (0, 0, 1.0), 1.9, keys[0], rng, flat=1.4, sx=0.8)
    for k in range(rng.randint(3, 5)):
        a = rng.uniform(0, TAU)
        r = rng.uniform(0.6, 1.2)
        rock(mb, M, (math.cos(a) * 1.9, math.sin(a) * 1.9, r * 0.3), r, keys[k % 2], rng, flat=rng.uniform(0.6, 1.2))
    for k in range(2):
        box(mb, M, (rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), 0.15), (rng.uniform(1.0, 1.8), rng.uniform(0.6, 1.0), 0.3), keys[1], rz=rng.uniform(0, 3))


@nat("scree", size=(5, 5, 0.6), rooms=("nature", "mountain", "canyon", "tundra"))
def scree(mb, x, y, z, rot, rng, era, s=1.0, key="n_rock2"):
    M = frame(x, y, z, rot, s)
    for i in range(rng.randint(26, 38)):
        a, rr = rng.uniform(0, TAU), rng.uniform(0, 2.5) ** 0.9
        r = rng.uniform(0.08, 0.32)
        rock(mb, M, (math.cos(a) * rr, math.sin(a) * rr, r * 0.2), r, rng.choice((key, "n_rock")), rng, flat=0.6, sub=0)


@nat("log", size=(3.2, 0.8, 0.7), rooms=("nature", "forest", "camp", "river"))
def log(mb, x, y, z, rot, rng, era, s=1.0, key="n_bark"):
    M = frame(x, y, z, rot, s)
    r = rng.uniform(0.25, 0.34)
    limb(mb, M, (-1.5, 0, r), (1.5, 0, r * 0.92), r, r * 0.9, key, seg=8)
    limb(mb, M, (1.49, 0, r * 0.92), (1.53, 0, r * 0.92), r * 0.84, r * 0.84, "n_wood_end", seg=8)
    limb(mb, M, (-1.53, 0, r), (-1.49, 0, r), r * 0.94, r * 0.94, "n_wood_end", seg=8)
    for k in range(2):
        p = Vector((rng.uniform(-1.0, 1.0), 0, r * 1.6))
        limb(mb, M, p - Vector((0, 0, r * 0.5)), p + Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.2), 0.3)), 0.06, 0.03, key, seg=4)
    if rng.random() < 0.5:
        mushrooms(mb, *(M @ Vector((0.4, -r * 0.9, 0.0))).to_tuple(), rot, rng, era, s * 0.6)


@nat("stump", size=(1.2, 1.2, 0.7), rooms=("nature", "forest", "camp", "farm"))
def stump(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    h = rng.uniform(0.4, 0.7)
    limb(mb, M, (0, 0, -0.1), (0, 0, h), 0.46, 0.4, "n_bark", seg=9)
    limb(mb, M, (0, 0, h), (0, 0, h + 0.02), 0.37, 0.37, "n_wood_end", seg=9)
    for k in range(4):
        a = k / 4 * TAU + rng.uniform(-0.3, 0.3)
        limb(mb, M, (math.cos(a) * 0.2, math.sin(a) * 0.2, 0.25), (math.cos(a) * 0.85, math.sin(a) * 0.85, -0.05), 0.16, 0.05, "n_bark", seg=5)


@nat("fallen_tree", size=(8, 2.6, 2.6), rooms=("nature", "forest", "river", "swamp"))
def fallen_tree(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    limb(mb, M, (0, 0, 0.45), (7.0, 0.4, 0.32), 0.45, 0.2, "n_bark", seg=8)
    limb(mb, M, (-0.18, 0, 0.6), (0.02, 0, 0.6), 1.3, 1.25, "n_soil", seg=10)                       # root plate
    for k in range(7):
        a = k / 7 * TAU
        limb(mb, M, (-0.1, math.cos(a) * 0.6, 0.6 + math.sin(a) * 0.6), (-0.6, math.cos(a) * 1.5, 0.6 + math.sin(a) * 1.4), 0.1, 0.02, "n_bark", seg=4)
    tips = []
    for k in range(4):
        p = Vector((rng.uniform(2.5, 6.5), 0.3, 0.55))
        branches(mb, M, rng, p, (rng.uniform(-0.2, 0.6), rng.choice((-1, 1)) * rng.uniform(0.3, 1.0), rng.uniform(0.3, 1.0)), 1.4, 0.09, 1, "n_bark", tips)


@nat("driftwood", size=(3, 1.2, 0.5), rooms=("nature", "beach", "shore", "lake"))
def driftwood(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    pts = [Vector((-1.4, 0, 0.18)), Vector((-0.4, 0.25, 0.2)), Vector((0.6, 0.1, 0.16)), Vector((1.5, 0.45, 0.12))]
    chain(mb, M, pts, 0.2, 0.1, "n_driftwood", seg=6)
    tips = []
    for k in range(2):
        p = pts[k + 1]
        e = p + Vector((rng.uniform(-0.4, 0.4), rng.choice((-1, 1)) * 0.8, 0.0))
        limb(mb, M, p, e, 0.07, 0.03, "n_driftwood", seg=4)


@nat("termite_mound", size=(2, 2, 3), rooms=("nature", "savanna"))
def termite_mound(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    limb(mb, M, (0, 0, -0.1), (0, 0, 1.2), 0.95, 0.62, "n_termite", seg=9)
    limb(mb, M, (0, 0, 1.2), (0.12, 0, 2.3), 0.62, 0.28, "n_termite", seg=8)
    limb(mb, M, (0.12, 0, 2.3), (0.18, 0.05, 3.0), 0.28, 0.04, "n_termite", seg=6)
    limb(mb, M, (0.5, 0.3, 0.6), (0.7, 0.4, 1.8), 0.35, 0.05, "n_termite", seg=6)
    for k in range(4):
        a = rng.uniform(0, TAU)
        blob(mb, M, (math.cos(a) * 0.7, math.sin(a) * 0.7, rng.uniform(0.3, 1.2)), rng.uniform(0.25, 0.4), "n_termite", rng, sub=1, smooth_=False)


@nat("snowdrift", size=(4, 2, 0.8), rooms=("nature", "snow", "tundra"))
def snowdrift(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for k in range(3):
        blob(mb, M, (rng.uniform(-1.0, 1.0), rng.uniform(-0.4, 0.4), 0.0), rng.uniform(0.8, 1.2), "n_snow", rng, sq=0.32, sx=1.9, lump=0.12)


@nat("ice_chunks", size=(3, 3, 1.2), rooms=("nature", "snow", "tundra", "lake"))
def ice_chunks(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for k in range(rng.randint(5, 8)):
        sz = rng.uniform(0.4, 1.3)
        box(mb, M, (rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), sz * 0.25), (sz, sz * rng.uniform(0.6, 1.0), sz * rng.uniform(0.3, 0.6)),
            rng.choice(("n_ice", "n_ice2")), rz=rng.uniform(0, TAU), rx=rng.uniform(-0.4, 0.4), ry=rng.uniform(-0.4, 0.4))


@nat("coral", size=(1.4, 1.4, 0.8), rooms=("nature", "beach", "shore", "tropical"))
def coral(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    tips = []
    for k in range(3):
        a = rng.uniform(0, TAU)
        branches(mb, M, rng, (0.2, 0, 0), (math.cos(a) * 0.4, math.sin(a) * 0.4, 1), 0.3, 0.06, 2, "n_coral", tips, spread=0.9, kids=(2, 3))
    blob(mb, M, (-0.45, 0.2, 0.1), 0.3, "n_coral2", rng, sub=2, sq=0.7, lump=0.35)
    limb(mb, M, (0.3, 0.45, 0.3), (0.33, 0.47, 0.3), 0.32, 0.3, "n_coral3", seg=9)          # sea fan


@nat("seaweed", size=(1.8, 1.8, 0.1), rooms=("nature", "beach", "shore"))
def seaweed(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    for k in range(rng.randint(6, 10)):
        a = rng.uniform(0, TAU)
        d = Vector((math.cos(a), math.sin(a), 0))
        n = Vector((-d.y, d.x, 0))
        P = [d * u * 0.9 + n * 0.15 * math.sin(u * 7 + k) + Vector((0, 0, 0.03)) for u in (0, 0.2, 0.4, 0.6, 0.8, 1.0)]
        ribbon(mb, M, P, [0.06, 0.1, 0.12, 0.1, 0.08, 0.02], rng.choice(("n_seaweed", "n_leaf_dark")))
    for k in range(5):
        _xf(mb, mb.sphere((0, 0, 0), 0.04, "n_leaf_dry", sub=0), M @ Matrix.Translation((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 0.05)))


@nat("stalagmite", size=(1.2, 1.2, 2.5), rooms=("nature", "cave"))
def stalagmite(mb, x, y, z, rot, rng, era, s=1.0, down=False):
    M = frame(x, y, z, rot, s)
    sg = -1 if down else 1
    for k in range(rng.randint(1, 3)):
        h = rng.uniform(1.0, 2.6) / (k + 1)
        b = Vector((rng.uniform(-0.35, 0.35) * k, rng.uniform(-0.35, 0.35) * k, -0.1 * sg))
        limb(mb, M, b, b + Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), h * sg)), rng.uniform(0.25, 0.4) / (k * 0.4 + 1), 0.02, "n_rock2" if k else "n_rock", seg=7)


@nat("crystal_cluster", size=(1.4, 1.4, 1.6), rooms=("nature", "cave", "fantasy", "alien"))
def crystal_cluster(mb, x, y, z, rot, rng, era, s=1.0):
    M = frame(x, y, z, rot, s)
    rock(mb, M, (0, 0, 0.1), 0.45, "n_rock_dark", rng, flat=0.5)
    for k in range(rng.randint(5, 8)):
        a = rng.uniform(0, TAU)
        d = Vector((math.cos(a) * rng.uniform(0.2, 0.7), math.sin(a) * rng.uniform(0.2, 0.7), 1)).normalized()
        r = rng.uniform(0.09, 0.2)
        L = rng.uniform(0.5, 1.4)
        p0 = Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, 0.05))
        limb(mb, M, p0, p0 + d * L, r, r * 0.9, "n_crystal", seg=6)
        limb(mb, M, p0 + d * L, p0 + d * (L + r * 1.6), r * 0.9, 0.0, "n_crystal", seg=6)


@nat("olive_tree", size=(4, 4, 4), rooms=("nature", "orchard", "mediterranean", "garden"))
def olive_tree(mb, x, y, z, rot, rng, era, s=1.0):
    """Gnarled twin-trunk olive with silvery grey-green clumps (classical / Mediterranean groves)."""
    M = frame(x, y, z, rot, s)
    ends = []
    for k in range(rng.randint(2, 3)):
        a = k / 2.5 * TAU + rng.uniform(-0.4, 0.4)
        pts = [Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, -0.2)),
               Vector((math.cos(a) * 0.45, math.sin(a) * 0.3, 0.8)),
               Vector((math.cos(a + 0.6) * 0.3, math.sin(a + 0.6) * 0.5, 1.6)),
               Vector((math.cos(a) * 1.0, math.sin(a) * 1.0, 2.3))]
        chain(mb, M, pts, 0.24, 0.1, "n_bark_grey", seg=6)
        ends.append(pts[-1])
    for e in ends:
        for j in range(2):
            blob(mb, M, e + Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), rng.uniform(0.2, 0.7))), rng.uniform(0.8, 1.1),
                 rng.choice(("n_olive", "n_olive2")), rng, sq=0.6, lump=0.3)

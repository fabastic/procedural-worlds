"""Shared procedural prop library, tagged by era / room type / placement, plus scatter helpers.

Each prop is PROPS[name] = dict(fn, place, eras, rooms, size) where fn(mb, x, y, z, rot, rng, era) adds
geometry to a MeshBuilder using palette keys (wood, metal, fabric, accent, paper, glass, ...).
place: "floor" | "surface" | "wall" | "hanging". eras: None = any era. rooms: tags matched against a
setting's prop tags ("domestic", "kitchen", "office", "bar", "shop", "tavern", "lab", "civic", "any").
Kits call scatter_* with free regions they recorded while building features."""
import math, random
from mathutils import Vector, Matrix

OLD = {"ancient", "medieval", "1700s-1800s"}
MID = {"1920s-50s"}
NOW = {"modern"}
FUT = {"near-future", "far-future"}


def _extend_era_groups():
    """Timeline eras (presets/era.d) join the group of their legacy family, so every prop/kit
    written against OLD/MID/NOW/FUT understands them; ANCIENT/MEDIEVAL/... give finer control."""
    import json, os
    d = os.path.join(os.path.dirname(os.path.dirname(__file__)), "presets", "era.d")
    groups = {"ancient": OLD, "medieval": OLD, "1700s-1800s": OLD, "1920s-50s": MID, "modern": NOW,
              "near-future": FUT, "far-future": FUT}
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith(".json"):
            for k, v in json.load(open(os.path.join(d, f), encoding="utf-8")).items():
                if isinstance(v, dict) and v.get("family") in groups:
                    groups[v["family"]].add(k)
                    FAMILY[k] = v["family"]


FAMILY = {k: k for k in ("ancient", "medieval", "1700s-1800s", "1920s-50s", "modern", "near-future", "far-future")}
_extend_era_groups()


def in_family(era, *families):
    """True if `era` (any timeline key) belongs to one of the legacy families."""
    return FAMILY.get(era, era) in families

PROPS = {}


def prop(name, place, size, eras=None, rooms=("any",)):
    def deco(fn):
        PROPS[name] = dict(fn=fn, place=place, size=size, eras=set(eras) if eras else None, rooms=set(rooms))
        return fn
    return deco


def _rot(x, y, rot):
    return Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, "Z")


def _box(mb, M, c, s, key):
    """Box in prop-local coords (c centre, s size) transformed by M."""
    vs = mb.box((0, 0, 0), s, key)
    import bmesh
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)), verts=vs)
    return vs


def _cyl(mb, M, c, r, h, key, seg=10, r2=None):
    vs = mb.cyl((0, 0, 0), r, h, key, seg=seg, r2=r2)
    import bmesh
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)), verts=vs)
    return vs


# ----------------------------------------------------------------------------- furniture
@prop("chair", "floor", (0.5, 0.5, 0.95))
def chair(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    k = "metal" if era in FUT else "wood"
    _box(mb, M, (0, 0, 0.45), (0.44, 0.44, 0.05), k)
    for sx in (-0.19, 0.19):
        for sy in (-0.19, 0.19):
            _box(mb, M, (sx, sy, 0.22), (0.04, 0.04, 0.44), k)
    _box(mb, M, (0, 0.2, 0.72), (0.44, 0.04, 0.5), k)


@prop("stool", "floor", (0.4, 0.4, 0.75))
def stool(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    _cyl(mb, M, (0, 0, 0.72), 0.19, 0.06, "fabric" if era in MID else "wood")
    _cyl(mb, M, (0, 0, 0.36), 0.03, 0.7, "metal")
    _cyl(mb, M, (0, 0, 0.02), 0.16, 0.04, "metal")


@prop("table", "floor", (1.1, 0.8, 0.76))
def table(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    k = "metal" if era in FUT else "wood"
    _box(mb, M, (0, 0, 0.74), (1.1, 0.8, 0.05), k)
    for sx in (-0.48, 0.48):
        for sy in (-0.33, 0.33):
            _box(mb, M, (sx, sy, 0.36), (0.06, 0.06, 0.72), k)
    return [(Vector((x, y, z + 0.765)), 0.45)]          # surface for clutter


@prop("crate", "floor", (0.7, 0.7, 0.6), rooms=("storage", "outdoor", "shop", "dock", "tavern", "factory", "dungeon"))
def crate(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    s = rng.uniform(0.45, 0.75)
    _box(mb, M, (0, 0, s / 2), (s, s, s), "wood" if era not in FUT else "metal")
    _box(mb, M, (0, -s / 2 - 0.01, s / 2), (s * 0.95, 0.02, 0.08), "trim")
    if rng.random() < 0.4:
        s2 = s * rng.uniform(0.6, 0.85)
        _box(mb, M, (rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), s + s2 / 2), (s2, s2, s2), "wood")


@prop("barrel", "floor", (0.6, 0.6, 0.9), eras=OLD | MID, rooms=("storage", "tavern", "outdoor", "dock", "dungeon", "factory"))
def barrel(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    _cyl(mb, M, (0, 0, 0.45), 0.28, 0.9, "wood", seg=12)
    for zz in (0.15, 0.75):
        _cyl(mb, M, (0, 0, zz), 0.295, 0.05, "metal", seg=12)


@prop("shelf_unit", "wall", (1.0, 0.35, 1.9), rooms=("any",))
def shelf_unit(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    k = "metal" if era in FUT else "wood"
    for sx in (-0.48, 0.48):
        _box(mb, M, (sx, 0, 0.95), (0.04, 0.34, 1.9), k)
    tops = []
    for zz in (0.05, 0.5, 0.95, 1.4, 1.85):
        _box(mb, M, (0, 0, zz), (1.0, 0.34, 0.03), k)
        for i in range(rng.randint(2, 6)):           # books / jars on every shelf
            if zz > 1.8:
                break
            w = rng.uniform(0.04, 0.12)
            hh = rng.uniform(0.18, 0.36)
            px = rng.uniform(-0.42, 0.42)
            _box(mb, M, (px, -0.02, zz + hh / 2 + 0.015), (w, 0.22, hh), rng.choice(("fabric", "accent", "paper", "wood")))
    return tops


@prop("bookcase", "wall", (1.2, 0.4, 2.2), rooms=("library", "office", "domestic", "study", "wizard", "civic"))
def bookcase(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    _box(mb, M, (0, 0.18, 1.1), (1.2, 0.04, 2.2), "wood")
    for sx in (-0.58, 0.58):
        _box(mb, M, (sx, 0, 1.1), (0.04, 0.4, 2.2), "wood")
    for zz in (0.05, 0.5, 0.95, 1.4, 1.85, 2.18):
        _box(mb, M, (0, 0, zz), (1.2, 0.4, 0.04), "wood")
        if zz < 2.1:
            px = -0.54
            while px < 0.5:
                w = rng.uniform(0.03, 0.08)
                hh = rng.uniform(0.26, 0.4)
                lean = rng.random() < 0.06
                _box(mb, M, (px + w / 2, -0.02, zz + hh / 2 + 0.02), (w, 0.28, hh), rng.choice(("fabric", "accent", "paper", "trim", "wood2")))
                px += w + (0.12 if lean else 0.004)


@prop("bed", "floor", (1.1, 2.1, 0.9), rooms=("domestic", "bedroom", "hospital", "kids", "barracks"))
def bed(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    k = "metal" if era in MID | FUT else "wood"
    _box(mb, M, (0, 0, 0.3), (1.0, 2.0, 0.2), k)
    _box(mb, M, (0, 0, 0.48), (0.96, 1.96, 0.18), "paper")
    _box(mb, M, (0, 0.2, 0.6), (0.98, 1.4, 0.08), "fabric")
    _box(mb, M, (0, -0.8, 0.63), (0.6, 0.3, 0.12), "paper")
    _box(mb, M, (0, -1.0, 0.55), (1.0, 0.05, 0.9), k)
    for sx in (-0.47, 0.47):
        for sy in (-0.97, 0.97):
            _box(mb, M, (sx, sy, 0.15), (0.05, 0.05, 0.3), k)


@prop("sofa", "floor", (2.0, 0.9, 0.85), rooms=("domestic", "living", "office", "lounge"))
def sofa(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    _box(mb, M, (0, 0, 0.25), (2.0, 0.9, 0.3), "fabric")
    _box(mb, M, (0, 0.35, 0.6), (2.0, 0.2, 0.6), "fabric")
    for sx in (-0.92, 0.92):
        _box(mb, M, (sx, 0, 0.45), (0.18, 0.9, 0.4), "fabric")
    for sx in (-0.48, 0.48):
        _box(mb, M, (sx, -0.05, 0.45), (0.9, 0.7, 0.12), "fabric2")


@prop("desk", "floor", (1.4, 0.7, 0.76), rooms=("office", "civic", "police", "classroom", "lab", "study", "domestic"))
def desk(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    k = "metal" if era in FUT else "wood"
    _box(mb, M, (0, 0, 0.74), (1.4, 0.7, 0.05), k)
    _box(mb, M, (0.5, 0, 0.36), (0.38, 0.66, 0.72), k)
    _box(mb, M, (0.5, -0.335, 0.5), (0.3, 0.01, 0.12), "trim")
    _box(mb, M, (0.5, -0.335, 0.25), (0.3, 0.01, 0.12), "trim")
    for sy in (-0.3, 0.3):
        _box(mb, M, (-0.66, sy, 0.36), (0.05, 0.05, 0.72), k)
    screen(mb, x, y, z + 0.765, rot, rng, era, M=M @ Matrix.Translation((-0.15, 0.12, 0.765)))
    return [(Vector((x, y, z + 0.765)), 0.35)]


def screen(mb, x, y, z, rot, rng, era, M=None):
    """Era-appropriate desk device: typewriter / radio / CRT / flat screen / holo panel."""
    M = M or (Matrix.Translation((0, 0, z)) @ _rot(x, y, rot))
    if era in OLD:
        _box(mb, M, (0, 0, 0.03), (0.3, 0.22, 0.04), "paper")
        _cyl(mb, M, (0.2, 0.05, 0.08), 0.03, 0.14, "metal")
    elif era in MID:
        _box(mb, M, (0, 0, 0.08), (0.42, 0.32, 0.14), "metal2")
        _box(mb, M, (0, 0.12, 0.2), (0.4, 0.06, 0.14), "metal2")
        _box(mb, M, (0, 0.16, 0.32), (0.3, 0.01, 0.16), "paper")
    elif era in NOW:
        _box(mb, M, (0, 0.05, 0.25), (0.55, 0.04, 0.34), "metal2")
        _box(mb, M, (0, 0.03, 0.25), (0.5, 0.01, 0.29), "screen")
        _box(mb, M, (0, 0.05, 0.05), (0.06, 0.06, 0.1), "metal2")
        _box(mb, M, (0, -0.15, 0.01), (0.45, 0.15, 0.02), "metal2")
    else:
        _box(mb, M, (0, 0.05, 0.28), (0.6, 0.02, 0.36), "accent")
        _box(mb, M, (0, 0.05, 0.04), (0.2, 0.12, 0.06), "metal")


@prop("counter", "floor", (2.0, 0.65, 1.05), rooms=("diner", "bar", "shop", "tavern", "civic", "police", "hospital", "station"))
def counter(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    _box(mb, M, (0, 0, 0.5), (2.0, 0.6, 1.0), "wood" if era not in FUT else "wall2")
    _box(mb, M, (0, -0.04, 1.03), (2.08, 0.72, 0.06), "metal" if era in MID | FUT else "wood2")
    for i in range(4):
        _box(mb, M, (-0.75 + i * 0.5, -0.305, 0.5), (0.42, 0.01, 0.8), "trim")
    return [(Vector((x, y, z + 1.06)), 0.8)]


@prop("lamp", "surface", (0.3, 0.3, 0.5))
def lamp(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((x, y, z))
    if era in OLD:
        _cyl(mb, M, (0, 0, 0.04), 0.07, 0.08, "metal")
        _cyl(mb, M, (0, 0, 0.16), 0.025, 0.18, "paper")
        _cyl(mb, M, (0, 0, 0.27), 0.01, 0.05, "flame")
    elif era in MID:
        _cyl(mb, M, (0, 0, 0.18), 0.02, 0.36, "metal")
        _cyl(mb, M, (0, 0, 0.42), 0.16, 0.18, "fabric", r2=0.09)
    elif era in NOW:
        _cyl(mb, M, (0, 0, 0.2), 0.015, 0.4, "metal")
        _cyl(mb, M, (0, 0, 0.42), 0.1, 0.12, "metal2", r2=0.04)
    else:
        _box(mb, M, (0, 0, 0.18), (0.06, 0.06, 0.36), "accent")


@prop("bottle", "surface", (0.08, 0.08, 0.3), rooms=("any", "bar", "kitchen", "tavern", "diner", "shop", "lab"))
def bottle(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((x, y, z))
    h = rng.uniform(0.22, 0.32)
    k = rng.choice(("glass", "glass2", "accent"))
    _cyl(mb, M, (0, 0, h * 0.35), 0.04, h * 0.7, k, seg=8)
    _cyl(mb, M, (0, 0, h * 0.82), 0.015, h * 0.3, k, seg=6)


@prop("mug", "surface", (0.1, 0.1, 0.1), rooms=("any", "kitchen", "diner", "office", "domestic", "police"))
def mug(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((x, y, z))
    _cyl(mb, M, (0, 0, 0.05), 0.045, 0.1, rng.choice(("paper", "accent", "fabric")), seg=10)


@prop("plate", "surface", (0.24, 0.24, 0.03), rooms=("kitchen", "diner", "tavern", "domestic"))
def plate(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((x, y, z))
    _cyl(mb, M, (0, 0, 0.01), 0.12, 0.02, "paper", seg=14, r2=0.1)


@prop("books", "surface", (0.3, 0.22, 0.15), rooms=("any", "library", "office", "study", "domestic", "wizard", "classroom"))
def books(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot + rng.uniform(-0.3, 0.3))
    zz = 0.0
    for i in range(rng.randint(1, 4)):
        t = rng.uniform(0.03, 0.06)
        _box(mb, M, (rng.uniform(-0.02, 0.02), 0, zz + t / 2), (rng.uniform(0.2, 0.28), rng.uniform(0.15, 0.2), t),
             rng.choice(("fabric", "accent", "trim", "paper")))
        zz += t


@prop("papers", "surface", (0.3, 0.3, 0.01), rooms=("any", "office", "police", "classroom", "lab", "study", "civic"))
def papers(mb, x, y, z, rot, rng, era):
    for i in range(rng.randint(1, 3)):
        a = rot + rng.uniform(-0.6, 0.6)
        M = Matrix.Translation((0, 0, z + 0.002 * i)) @ _rot(x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.05, 0.05), a)
        _box(mb, M, (0, 0, 0.002), (0.21, 0.29, 0.004), "paper")


@prop("candle", "surface", (0.06, 0.06, 0.2), eras=OLD, rooms=("any",))
def candle(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((x, y, z))
    _cyl(mb, M, (0, 0, 0.01), 0.06, 0.02, "metal")
    h = rng.uniform(0.08, 0.18)
    _cyl(mb, M, (0, 0, 0.02 + h / 2), 0.02, h, "paper", seg=8)
    _cyl(mb, M, (0, 0, 0.04 + h), 0.008, 0.035, "flame", seg=6)


@prop("plant", "floor", (0.5, 0.5, 1.0), eras=MID | NOW | FUT, rooms=("domestic", "office", "diner", "shop", "lobby", "living"))
def plant(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((x, y, z))
    _cyl(mb, M, (0, 0, 0.18), 0.18, 0.36, "accent", r2=0.14)
    for i in range(6):
        a = i / 6 * math.tau + rng.uniform(-0.3, 0.3)
        h = rng.uniform(0.4, 0.7)
        mb.sphere((x + math.cos(a) * 0.12, y + math.sin(a) * 0.12, z + 0.36 + h * 0.6), rng.uniform(0.1, 0.16), "leaf", sub=1, squash=1.6)


@prop("frame", "wall", (0.6, 0.04, 0.5), rooms=("any",))
def frame(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    w, h = rng.uniform(0.35, 0.8), rng.uniform(0.3, 0.6)
    _box(mb, M, (0, 0, 0), (w, 0.03, h), "trim")
    _box(mb, M, (0, -0.012, 0), (w - 0.08, 0.01, h - 0.08), rng.choice(("paper", "accent", "wall2")))


@prop("clock", "wall", (0.35, 0.05, 0.35), eras=MID | NOW | {"1700s-1800s"}, rooms=("any", "diner", "civic", "classroom", "office", "station"))
def clock(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot) @ Matrix.Rotation(math.pi / 2, 4, "X")
    _cyl(mb, M, (0, 0, 0), 0.17, 0.04, "trim", seg=16)
    _cyl(mb, M, (0, 0, -0.012), 0.15, 0.02, "paper", seg=16)


@prop("sconce", "wall", (0.2, 0.15, 0.35), rooms=("any",))
def sconce(mb, x, y, z, rot, rng, era):
    """Era wall light (also where kits put point lights)."""
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    if era in OLD:
        _box(mb, M, (0, 0.05, 0), (0.08, 0.1, 0.3), "metal")
        _cyl(mb, M, (0, -0.04, 0.17), 0.012, 0.06, "flame", seg=6)
    elif era in FUT:
        _box(mb, M, (0, 0.0, 0), (0.6, 0.04, 0.06), "accent")
    else:
        _box(mb, M, (0, 0.04, 0), (0.1, 0.06, 0.12), "metal")
        _cyl(mb, M, (0, -0.06, 0.06), 0.09, 0.14, "lampshade", seg=10, r2=0.05)


@prop("rug", "floor", (2.2, 1.5, 0.02), rooms=("domestic", "living", "bedroom", "office", "study", "tavern", "wizard", "kids"))
def rug(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    _box(mb, M, (0, 0, 0.008), (rng.uniform(1.6, 2.4), rng.uniform(1.1, 1.6), 0.016), "rug")


@prop("sack", "floor", (0.5, 0.5, 0.6), eras=OLD | MID, rooms=("storage", "tavern", "shop", "dock", "outdoor", "dungeon", "farm"))
def sack(mb, x, y, z, rot, rng, era):
    mb.sphere((x, y, z + 0.28), rng.uniform(0.22, 0.3), "fabric2", sub=1, squash=1.3)


@prop("cabinet", "wall", (0.9, 0.45, 1.1), rooms=("any",))
def cabinet(mb, x, y, z, rot, rng, era):
    M = Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)
    k = "metal" if era in MID | FUT else "wood"
    _box(mb, M, (0, 0, 0.55), (0.9, 0.45, 1.1), k)
    for sx in (-0.22, 0.22):
        _box(mb, M, (sx, -0.23, 0.6), (0.38, 0.02, 0.85), "trim")
    return [(Vector((x, y, z + 1.1)), 0.35)]


# ----------------------------------------------------------------------------- selection + scatter
def candidates(place, era, rooms):
    rooms = set(rooms) | {"any"}
    return [n for n, p in PROPS.items()
            if p["place"] == place and (p["eras"] is None or era in p["eras"]) and (p["rooms"] & rooms)]


def place_prop(mb, name, x, y, z, rot, rng, era):
    out = PROPS[name]["fn"](mb, x, y, z, rot, rng, era)
    return out or []


def scatter_surfaces(mb, surfaces, era, rooms, rng, density=1.0):
    """surfaces: [(centre Vector, half_extent)] -> small props on top."""
    names = candidates("surface", era, rooms)
    if not names:
        return
    for c, r in surfaces:
        for _ in range(int(rng.uniform(1, 4) * density)):
            n = rng.choice(names)
            place_prop(mb, n, c.x + rng.uniform(-r, r) * 0.8, c.y + rng.uniform(-r, r) * 0.5, c.z, rng.uniform(0, math.tau), rng, era)


def scatter_floor(mb, region, era, rooms, rng, count, avoid, place="floor"):
    """Drop floor props in region (x0, y0, x1, y1) avoiding circles avoid=[(x, y, r)]; returns surfaces."""
    names = candidates(place, era, rooms)
    surfaces = []
    if not names:
        return surfaces
    x0, y0, x1, y1 = region
    for _ in range(count * 6):
        if count <= 0:
            break
        n = rng.choice(names)
        s = PROPS[n]["size"]
        rr = max(s[0], s[1]) * 0.6
        x, y = rng.uniform(x0 + rr, x1 - rr), rng.uniform(y0 + rr, y1 - rr)
        if any((x - ax) ** 2 + (y - ay) ** 2 < (ar + rr) ** 2 for ax, ay, ar in avoid):
            continue
        surfaces += place_prop(mb, n, x, y, 0.0, rng.uniform(0, math.tau), rng, era)
        avoid.append((x, y, rr))
        count -= 1
    return surfaces

"""Urban asset pack, part 1: geometry helpers shared by the urban props and kits, and vehicles as
props for every era (carts and carriages -> 1930s sedans -> 1950s cars -> modern hatchbacks, vans,
buses, trams -> hover cars), plus long rail / tram car bodies used by the platform and carriage kits.

Vehicle convention: long axis along local Y, FRONT at local -Y (faces the viewer at rot=0, like room
props), wheels on z=0. Palette keys only (body colours come from fabric/accent/wall2/metal/trim)."""
import math
import bmesh
from mathutils import Vector, Matrix
from ..props import prop, _box, _cyl, _rot, OLD, MID, NOW, FUT, FAMILY

ALL = OLD | MID | NOW | FUT
# finer era groups over the 15-era timeline (legacy keys kept so old stories still match)
ANC = {"ancient", "classical_antiquity"}
MED = {"medieval", "early_high_middle_ages"}
PREIND = {"1700s-1800s", "renaissance_discovery", "enlightenment_piracy"}
STEAM = {"1700s-1800s", "victorian_industrial"}
V18 = STEAM                                   # gas-lamp / steam age
INTER = {"1920s-50s", "interwar"}
COLD = {"1920s-50s", "cold_war"}
EIGHTIES = {"analog_digital"}
NOWISH = {"modern", "contemporary", "post_apocalyptic"}
NEAR = {"near-future", "near_future", "cyberpunk", "solarpunk"}
FAR = {"far-future", "space_age", "far_future"}
RAIL = STEAM | MID | NOW | FUT                # railway age onwards
BODY = ("fabric", "accent", "wall2", "metal", "trim", "fabric2")


def body_key(rng, era, choices=BODY):
    """A vehicle body colour; future eras' accent is emissive neon, so it is kept for trim only."""
    c = [k for k in choices if not (k == "accent" and era in FUT)] or ["metal"]
    return rng.choice(c)


def acc(era):
    """'accent' for big painted surfaces, swapped for fabric where accent glows (future eras)."""
    return "fabric" if era in FUT else "accent"


# ----------------------------------------------------------------------------- geometry helpers
def M_at(x, y, z, rot):
    return Matrix.Translation((0, 0, z)) @ _rot(x, y, rot)


def cylx(mb, M, c, r, h, key, seg=12, axis="X", r2=None):
    """Cylinder along a local axis (X / Y / Z) centred at c."""
    vs = mb.cyl((0, 0, 0), r, h, key, seg=seg, r2=r2, axis=axis)
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)), verts=vs)
    return vs


def rbox(mb, M, c, s, key, rx=0.0, ry=0.0, rz=0.0):
    """Box rotated about its own centre (X then Y then Z)."""
    R = Matrix.Rotation(rz, 4, "Z") @ Matrix.Rotation(ry, 4, "Y") @ Matrix.Rotation(rx, 4, "X")
    vs = mb.box((0, 0, 0), s, key)
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)) @ R, verts=vs)
    return vs


def tbox(mb, M, c, s, key, top=(1.0, 1.0), shift=(0.0, 0.0)):
    """Box whose top face is scaled by top=(sx, sy) and shifted (dx, dy): tapered cabins, roofs, plinths."""
    vs = mb.box((0, 0, 0), s, key)
    for v in vs:
        if v.co.z > 0:
            v.co.x = v.co.x * top[0] + shift[0]
            v.co.y = v.co.y * top[1] + shift[1]
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation(Vector(c)), verts=vs)
    return vs


def rod(mb, M, a, b, r, key, seg=6):
    """Cylinder between two local points (poles, braces, scaffold tubes, rigging)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    if L < 1e-5:
        return []
    vs = mb.cyl((0, 0, 0), r, L, key, seg=seg)
    q = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation((a + b) / 2) @ q, verts=vs)
    return vs


def wheel(mb, M, c, r, w, era, hub="metal"):
    """Tyre + hub (axis X). Old eras get a wooden spoked wheel."""
    if era in OLD:
        spoked(mb, M, c, r, w, "wood2")
        return
    cylx(mb, M, c, r, w, "dark", seg=14)
    cylx(mb, M, (c[0] + math.copysign(0.012, c[0] or 1), c[1], c[2]), r * 0.55, w, hub, seg=10)


def spoked(mb, M, c, r, w, key, n=10):
    """Wooden cart wheel: rim from short boxes, spokes, hub (axis X)."""
    c = Vector(c)
    for i in range(n):
        a = i / n * math.tau
        p = c + Vector((0, math.cos(a) * r * 0.93, math.sin(a) * r * 0.93))
        rbox(mb, M, p, (w, r * 2 * math.pi / n * 1.05, r * 0.14), key, rx=a + math.pi / 2)
        rbox(mb, M, c + Vector((0, math.cos(a) * r * 0.45, math.sin(a) * r * 0.45)), (w * 0.5, 0.04, r * 0.85), key,
             rx=a + math.pi / 2)
    cylx(mb, M, tuple(c), r * 0.16, w * 1.6, "metal", seg=8)


def cabin(mb, M, y, z, L, W, H, body, glass="glass", top=(0.86, 0.62), shift=0.0, band=(0.18, 0.86), pillars=1):
    """Tapered cabin with a glass band all round (side windows + windscreen + rear screen)."""
    tbox(mb, M, (0, y, z + H / 2), (W, L, H), body, top=top, shift=(0, shift))
    z0, z1 = band
    def at(f):                                   # cabin footprint at height fraction f
        return W * (1 - (1 - top[0]) * f), L * (1 - (1 - top[1]) * f), shift * f
    w0, l0, s0 = at(z0)
    w1, l1, s1 = at(z1)
    hh = (z1 - z0) * H
    vs = mb.box((0, 0, 0), (1, 1, hh), glass)
    for v in vs:                                 # glass shell 2 cm proud of the cabin
        top_ = v.co.z > 0
        w, l, s = (w1, l1, s1) if top_ else (w0, l0, s0)
        v.co.x = math.copysign(w / 2 + 0.02, v.co.x)
        v.co.y = math.copysign(l / 2 + 0.02, v.co.y) + s
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation((0, y, z + (z0 + z1) / 2 * H)), verts=vs)
    for k in range(pillars):                     # B/C pillars break the side glass
        f = (k + 1) / (pillars + 1)
        py = y - L / 2 + L * f + shift * 0.5
        mb_y = py
        rbox(mb, M, (0, mb_y, z + (z0 + z1) / 2 * H), ((w0 + w1) / 2 + 0.07, 0.09, hh + 0.02), body)


def lights(mb, M, y, z, W, front=True, era="modern", r=0.09):
    key = "lampshade" if front else "fabric"
    for sx in (-1, 1):
        if era in MID and front:
            cylx(mb, M, (sx * (W / 2 - 0.22), y, z), r, 0.08, key, seg=10, axis="Y")
        else:
            _box(mb, M, (sx * (W / 2 - 0.2), y, z), (0.3 if era in FUT else 0.22, 0.04, 0.1), key)


def car(mb, M, rng, era, style, body=None, L=4.3, W=1.76):
    """Era cars from blocks: '30s', '50s', 'hatch', 'sedan', 'taxi', 'hover'."""
    body = body or body_key(rng, era)
    if style == "30s":
        r = 0.38
        for sy in (-1.25, 1.35):
            for sx in (-0.78, 0.78):
                wheel(mb, M, (sx, sy, r), r, 0.16, "1920s-50s")
                cylx(mb, M, (sx * 0.98, sy, r + 0.08), r + 0.08, 0.3, body, seg=12, r2=None)   # fenders
        _box(mb, M, (0, 0.1, 0.62), (1.3, 3.9, 0.5), body)                  # chassis + running boards
        for sx in (-0.79, 0.79):
            _box(mb, M, (sx, 0.05, 0.42), (0.28, 2.0, 0.05), "dark")
        tbox(mb, M, (0, -1.15, 0.98), (1.0, 1.5, 0.3), body, top=(0.92, 0.98))          # long hood
        _box(mb, M, (0, -1.92, 0.85), (0.8, 0.08, 0.55), "metal")                     # grille
        cabin(mb, M, 0.6, 0.85, 2.0, 1.48, 0.95, body, top=(0.98, 0.92), band=(0.3, 0.85), pillars=1)
        _box(mb, M, (0, 0.6, 1.82), (1.5, 2.05, 0.06), "dark")                       # roof
        cylx(mb, M, (0, 1.85, 0.95), 0.3, 0.14, "dark", seg=12, axis="Y")              # spare wheel
        for sx in (-1, 1):
            cylx(mb, M, (sx * 0.55, -1.85, 1.05), 0.12, 0.12, "lampshade", seg=10, axis="Y")
        _box(mb, M, (0, -2.02, 0.5), (1.6, 0.08, 0.1), "metal")
        return
    if style == "50s":
        r = 0.36
        for sy in (-1.45, 1.45):
            for sx in (-0.82, 0.82):
                wheel(mb, M, (sx, sy, r), r, 0.22, era)
        tbox(mb, M, (0, 0, 0.72), (1.95, 5.0, 0.6), body, top=(1.0, 0.98))
        for sx in (-0.9, 0.9):                                                          # tail fins
            tbox(mb, M, (sx, 2.05, 1.08), (0.12, 0.8, 0.22), body, top=(0.6, 0.3), shift=(0, 0.2))
        _box(mb, M, (0, 0, 0.72), (1.98, 4.6, 0.05), "metal")                          # chrome strip
        cabin(mb, M, 0.25, 1.02, 2.2, 1.7, 0.58, "paper" if rng.random() < 0.5 else body, top=(0.9, 0.7), band=(0.12, 0.9))
        _box(mb, M, (0, -2.52, 0.55), (2.0, 0.1, 0.16), "metal")                       # bumpers
        _box(mb, M, (0, 2.52, 0.55), (2.0, 0.1, 0.16), "metal")
        _box(mb, M, (0, -2.51, 0.78), (1.1, 0.04, 0.2), "metal")
        lights(mb, M, -2.51, 0.82, 1.9, True, "1920s-50s", r=0.1)
        lights(mb, M, 2.51, 0.95, 1.9, False, era)
        return
    if style == "hover":
        tbox(mb, M, (0, 0, 0.75), (1.9, 4.6, 0.55), body, top=(0.94, 0.9))
        cabin(mb, M, 0.3, 1.02, 2.6, 1.7, 0.6, "glass2", glass="glass", top=(0.72, 0.5), shift=0.2, band=(0.05, 0.95), pillars=0)
        for sy in (-1.5, 1.5):                                                          # thruster pods
            for sx in (-1.0, 1.0):
                cylx(mb, M, (sx, sy, 0.45), 0.32, 0.22, "metal2", seg=14, axis="Z")
                cylx(mb, M, (sx, sy, 0.33), 0.26, 0.04, "accent", seg=14, axis="Z")
        _box(mb, M, (0, -2.31, 0.85), (1.6, 0.04, 0.08), "accent")
        _box(mb, M, (0, 2.31, 0.85), (1.6, 0.04, 0.08), "accent")
        return
    # modern-ish: hatch / sedan / taxi
    r = 0.32
    short = style == "hatch"
    L = 3.9 if short else 4.5
    for sy in (-L / 2 + 0.75, L / 2 - 0.7):
        for sx in (-0.78, 0.78):
            wheel(mb, M, (sx, sy, r), r, 0.22, era)
    tbox(mb, M, (0, 0, 0.62), (W, L, 0.56), body, top=(1.0, 0.98))
    if short:
        cabin(mb, M, 0.45, 0.9, 2.7, W * 0.98, 0.62, body, top=(0.86, 0.72), shift=0.25, band=(0.1, 0.88))
    else:
        cabin(mb, M, 0.15, 0.9, 2.5, W * 0.98, 0.58, body, top=(0.86, 0.6), band=(0.1, 0.88))
    for sx in (-1, 1):                                                                  # wheel arches
        for sy in (-L / 2 + 0.75, L / 2 - 0.7):
            _box(mb, M, (sx * (W / 2 + 0.005), sy, 0.55), (0.02, 0.85, 0.12), "dark")
    _box(mb, M, (0, -L / 2 - 0.02, 0.45), (W * 0.95, 0.08, 0.18), "metal2")
    _box(mb, M, (0, L / 2 + 0.02, 0.45), (W * 0.95, 0.08, 0.18), "metal2")
    _box(mb, M, (0, -L / 2 - 0.01, 0.62), (0.6, 0.04, 0.14), "dark")                  # grille
    lights(mb, M, -L / 2 - 0.01, 0.72, W, True, era)
    lights(mb, M, L / 2 + 0.01, 0.78, W, False, era)
    if style == "taxi":
        _box(mb, M, (0, 0.15, 1.56), (0.55, 0.22, 0.16), "lampshade")
        for sx in (-1, 1):
            for k in range(8):
                _box(mb, M, (sx * (W / 2 + 0.012), -1.2 + k * 0.3, 0.72 + (k % 2) * 0.06), (0.01, 0.15, 0.06), "dark")


# ----------------------------------------------------------------------------- vehicle props
@prop("handcart", "floor", (1.0, 1.6, 0.9), eras=ALL, rooms=("street", "market", "dock", "construction", "farm"))
def handcart(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = "wood" if era not in FUT else "metal"
    _box(mb, M, (0, 0, 0.55), (0.9, 1.2, 0.08), k)
    for sx in (-0.45, 0.45):
        _box(mb, M, (sx, 0, 0.72), (0.05, 1.2, 0.3), k)
        rod(mb, M, (sx * 0.7, 0.6, 0.6), (sx * 0.6, 1.45, 0.82), 0.025, "wood2")
    _box(mb, M, (0, -0.6, 0.72), (0.9, 0.05, 0.3), k)
    for sx in (-0.52, 0.52):
        if era in OLD:
            spoked(mb, M, (sx, -0.05, 0.42), 0.42, 0.06, "wood2", n=8)
        else:
            wheel(mb, M, (sx, -0.05, 0.3), 0.3, 0.1, era)
    for i in range(rng.randint(1, 3)):
        _box(mb, M, (rng.uniform(-0.2, 0.2), rng.uniform(-0.3, 0.3), 0.78), (0.3, 0.35, 0.3), rng.choice(("wood2", "fabric2", "paper")))


@prop("horse_cart", "floor", (1.8, 4.2, 1.6), eras=MED | PREIND | STEAM, rooms=("street", "market", "farm", "dock"))
def horse_cart(mb, x, y, z, rot, rng, era):
    """Farm cart with shafts (the horse stays off-panel)."""
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0.4, 1.0), (1.5, 2.6, 0.1), "wood")
    for sx in (-0.75, 0.75):
        _box(mb, M, (sx, 0.4, 1.25), (0.08, 2.6, 0.45), "wood")
        for k in range(5):
            _box(mb, M, (sx * 1.02, -0.6 + k * 0.5, 1.25), (0.05, 0.06, 0.5), "wood2")
    _box(mb, M, (0, 1.7, 1.25), (1.5, 0.08, 0.45), "wood")
    for sx in (-0.92, 0.92):
        spoked(mb, M, (sx, 0.6, 0.62), 0.62, 0.08, "wood2", n=12)
    cylx(mb, M, (0, 0.6, 0.62), 0.05, 1.9, "wood2", seg=6)
    for sx in (-0.45, 0.45):
        rod(mb, M, (sx, -0.8, 1.0), (sx * 0.7, -2.6, 0.75), 0.04, "wood2")
    _box(mb, M, (0, -0.85, 1.45), (1.2, 0.35, 0.08), "wood2")                       # driver bench
    for i in range(rng.randint(2, 5)):
        if rng.random() < 0.5:
            mb.sphere(M @ Vector((rng.uniform(-0.4, 0.4), rng.uniform(0, 1.3), 1.3)), 0.28, "fabric2", sub=1, squash=1.2)
        else:
            _box(mb, M, (rng.uniform(-0.4, 0.4), rng.uniform(0, 1.3), 1.3), (0.4, 0.4, 0.4), "wood2")


@prop("carriage", "floor", (2.0, 4.6, 2.6), eras=MED | PREIND | STEAM, rooms=("street", "market"))
def carriage(mb, x, y, z, rot, rng, era):
    """Enclosed coach on four spoked wheels, lamps, driver's box."""
    M = M_at(x, y, z, rot)
    body = rng.choice(("fabric", "dark", "accent", "trim"))
    tbox(mb, M, (0, 0.4, 1.0), (1.4, 2.0, 0.6), body, top=(1.05, 1.15))
    tbox(mb, M, (0, 0.4, 1.75), (1.45, 2.3, 0.9), body, top=(0.92, 0.9))
    for sx in (-1, 1):
        _box(mb, M, (sx * 0.71, 0.4, 1.85), (0.04, 0.7, 0.55), "glass")               # door window
        _box(mb, M, (sx * 0.72, 0.4, 1.35), (0.03, 0.75, 0.6), "trim")
        _box(mb, M, (sx * 0.7, -0.4, 1.85), (0.04, 0.35, 0.4), "glass")
        _box(mb, M, (sx * 0.7, 1.2, 1.85), (0.04, 0.35, 0.4), "glass")
    _box(mb, M, (0, 0.4, 2.25), (1.5, 2.4, 0.08), "trim")                           # roof + luggage rail
    for i in range(rng.randint(1, 3)):
        _box(mb, M, (rng.uniform(-0.3, 0.3), 0.2 + i * 0.5, 2.45), (0.7, 0.45, 0.3), rng.choice(("wood2", "fabric2")))
    _box(mb, M, (0, -1.15, 1.55), (1.3, 0.6, 0.12), "wood2")                        # driver's box
    _box(mb, M, (0, -0.95, 1.85), (1.3, 0.08, 0.5), "wood2")
    _box(mb, M, (0, 0.4, 0.7), (0.3, 3.4, 0.12), "wood2")                           # perch
    for sy, r in ((-0.95, 0.5), (1.35, 0.68)):
        for sx in (-0.88, 0.88):
            spoked(mb, M, (sx, sy, r), r, 0.07, "wood2", n=12)
    for sx in (-0.82, 0.82):
        _box(mb, M, (sx, -0.65, 1.95), (0.14, 0.14, 0.22), "lampshade")
    for sx in (-0.4, 0.4):
        rod(mb, M, (sx, -1.3, 0.75), (sx * 0.8, -3.0, 0.9), 0.04, "wood2")


@prop("sedan_1930s", "floor", (1.8, 4.2, 1.9), eras=INTER, rooms=("street", "parking", "garage"))
def sedan_1930s(mb, x, y, z, rot, rng, era):
    car(mb, M_at(x, y, z, rot), rng, era, "30s", body=rng.choice(("dark", "trim", "fabric", "wall2")))


@prop("car_1950s", "floor", (2.0, 5.1, 1.6), eras=COLD | {"analog_digital"}, rooms=("street", "parking", "garage"))
def car_1950s(mb, x, y, z, rot, rng, era):
    car(mb, M_at(x, y, z, rot), rng, era, "50s", body=rng.choice(("accent", "wall2", "fabric", "trim")))


@prop("hatchback", "floor", (1.8, 3.9, 1.55), eras=NOWISH | NEAR, rooms=("street", "parking", "garage"))
def hatchback(mb, x, y, z, rot, rng, era):
    car(mb, M_at(x, y, z, rot), rng, era, "hatch")


@prop("sedan", "floor", (1.8, 4.5, 1.5), eras=NOW | NEAR, rooms=("street", "parking", "garage"))
def sedan(mb, x, y, z, rot, rng, era):
    car(mb, M_at(x, y, z, rot), rng, era, "sedan")


@prop("taxi", "floor", (1.8, 4.5, 1.7), eras=MID | NOW | NEAR, rooms=("street", "parking"))
def taxi(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    if era in MID:
        car(mb, M, rng, era, "30s", body="accent")
        _box(mb, M, (0, 0.6, 1.92), (0.5, 0.2, 0.16), "lampshade")
    else:
        car(mb, M, rng, era, "taxi", body=acc(era))


@prop("hover_car", "floor", (2.2, 4.7, 1.7), eras=FUT, rooms=("street", "parking", "garage"))
def hover_car(mb, x, y, z, rot, rng, era):
    car(mb, M_at(x, y, z + 0.35, rot), rng, era, "hover", body=rng.choice(("metal", "wall2", "fabric", "trim")))


@prop("van", "floor", (2.0, 5.0, 2.3), eras=MID | NOW | FUT, rooms=("street", "parking", "garage", "construction"))
def van(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    body = body_key(rng, era, ("paper", "wall2", "metal", "accent"))
    r = 0.36
    for sy in (-1.55, 1.6):
        for sx in (-0.85, 0.85):
            wheel(mb, M, (sx, sy, r), r, 0.24, era)
    if era in MID:                                       # rounded '50s delivery van
        tbox(mb, M, (0, 0.4, 1.3), (1.9, 3.6, 1.7), body, top=(0.92, 0.95))
        tbox(mb, M, (0, -1.85, 0.85), (1.7, 1.0, 0.75), body, top=(0.9, 0.7), shift=(0, 0.15))
        cabin(mb, M, -1.25, 1.2, 0.5, 1.8, 0.7, body, top=(0.95, 0.6), shift=0.12, band=(0.15, 0.85), pillars=0)
        cylx(mb, M, (0, -2.36, 0.85), 0.3, 0.06, "metal", axis="Y")
    else:
        tbox(mb, M, (0, 0.15, 1.35), (1.95, 4.6, 1.9), body, top=(0.98, 0.94), shift=(0, 0.1))
        _box(mb, M, (0, -2.0, 1.75), (1.85, 0.62, 0.62), "glass")                    # windscreen
        for sx in (-1, 1):
            _box(mb, M, (sx * 0.985, -1.5, 1.75), (0.02, 0.7, 0.55), "glass")
            _box(mb, M, (sx * 0.985, 0.6, 1.3), (0.01, 1.6, 0.02), "dark")             # sliding door seam
        _box(mb, M, (0, -2.47, 0.55), (1.9, 0.08, 0.22), "metal2")
        lights(mb, M, -2.45, 0.9, 1.9, True, era)
    if rng.random() < 0.6:                                # painted trade sign
        for sx in (-1, 1):
            _box(mb, M, (sx * 0.99, 0.6, 1.55), (0.01, 2.0, 0.55), "signcol" if era in FUT else "accent")


@prop("delivery_truck", "floor", (2.4, 7.0, 3.2), eras=MID | NOW | FUT, rooms=("street", "construction", "dock", "parking"))
def delivery_truck(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    body = body_key(rng, era, ("fabric", "accent", "wall2", "trim"))
    box_k = rng.choice(("paper", "metal", "wall"))
    r = 0.48
    for sy in (-2.3, 1.6, 2.6):
        for sx in (-0.95, 0.95):
            wheel(mb, M, (sx, sy, r), r, 0.3, era)
    _box(mb, M, (0, 0.3, 0.75), (1.0, 6.4, 0.3), "dark")                             # chassis
    if era in MID:
        tbox(mb, M, (0, -2.85, 1.05), (1.7, 1.1, 0.75), body, top=(0.9, 0.85), shift=(0, 0.05))
        cabin(mb, M, -1.95, 0.95, 1.1, 2.0, 1.35, body, top=(0.96, 0.9), band=(0.45, 0.85), pillars=0)
    else:
        tbox(mb, M, (0, -2.45, 1.55), (2.3, 1.8, 2.0), body, top=(0.96, 0.85), shift=(0, 0.12))
        _box(mb, M, (0, -3.32, 2.0), (2.1, 0.06, 0.8), "glass")
        lights(mb, M, -3.37, 0.95, 2.2, True, era)
        _box(mb, M, (0, -3.38, 0.65), (2.3, 0.1, 0.3), "metal2")
    _box(mb, M, (0, 1.15, 2.0), (2.4, 4.6, 2.5), box_k)                              # cargo box
    _box(mb, M, (0, 3.46, 2.0), (2.2, 0.04, 2.3), "trim")
    for sx in (-1, 1):
        _box(mb, M, (sx * 1.205, 1.15, 2.2), (0.01, 3.4, 0.9), "signcol" if era in FUT else "accent")


@prop("bus", "floor", (2.6, 11.0, 3.2), eras=MID | NOW | FUT, rooms=("street", "station"))
def bus(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    body = body_key(rng, era, ("fabric", "accent", "wall2")) if era not in FUT else "metal"
    L, W = (9.5 if era in MID else 11.0), 2.5
    r = 0.5
    for sy in (-L / 2 + 2.0, L / 2 - 2.2):
        for sx in (-1.05, 1.05):
            wheel(mb, M, (sx, sy, r), r, 0.32, era)
    if era in MID:                                      # '50s bus: rounded snout, two-tone
        tbox(mb, M, (0, 0.2, 1.75), (W, L - 0.4, 2.6), body, top=(0.92, 0.97))
        tbox(mb, M, (0, -L / 2 + 0.05, 0.9), (2.1, 0.6, 0.9), body, top=(0.9, 0.6), shift=(0, 0.15))
        _box(mb, M, (0, 0.2, 1.05), (W + 0.02, L - 0.5, 0.25), "paper")
    else:
        tbox(mb, M, (0, 0, 1.7), (W, L, 2.9), body, top=(0.99, 0.99))
    lo, hi = 1.55, 2.65
    n = int(L / 1.3)
    for sx in (-1, 1):                                  # window band with mullions
        _box(mb, M, (sx * (W / 2 + 0.01), 0.3, (lo + hi) / 2), (0.02, L - 1.6, hi - lo), "glass")
        for k in range(n + 1):
            _box(mb, M, (sx * (W / 2 + 0.02), -L / 2 + 1.1 + k * (L - 1.6) / n, (lo + hi) / 2), (0.02, 0.1, hi - lo + 0.04), body)
        _box(mb, M, (sx * (W / 2 + 0.015), -L / 2 + 1.4, 1.2), (0.01, 1.0, 2.0), "dark")  # door
    _box(mb, M, (0, -L / 2 - 0.01, 2.05), (W - 0.2, 0.04, 1.3), "glass")                 # windscreen
    _box(mb, M, (0, -L / 2 - 0.02, 3.0), (W - 0.6, 0.04, 0.3), "lampshade" if era not in FUT else "accent")  # route sign
    lights(mb, M, -L / 2 - 0.02, 0.75, W, True, era)
    _box(mb, M, (0, -L / 2 - 0.05, 0.45), (W, 0.1, 0.3), "metal2")


@prop("tram", "floor", (2.6, 12.0, 3.8), eras=STEAM | MID | NOW | FUT, rooms=("street", "station"))
def tram(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    rail_car(mb, M, rng, era, 12.0 if era not in STEAM else 7.0, kind="tram")


def rail_car(mb, M, rng, era, L, kind="train", body=None):
    """Long rail/tram car body along local Y (centred), on bogies, with window band + doors."""
    W = 2.6 if kind == "tram" else 2.9
    body = body or ("wood" if era in OLD else body_key(rng, era, ("wall2", "fabric", "accent", "trim")) if era in MID | NOW else "metal")
    H = 3.3 if kind == "tram" else 3.6
    z0 = 0.45 if kind == "tram" else 0.9
    for sy in (-L / 2 + 1.6, L / 2 - 1.6):                                            # bogies
        _box(mb, M, (0, sy, z0 * 0.55), (2.0, 2.2, 0.35), "dark")
        for dy in (-0.7, 0.7):
            for sx in (-0.75, 0.75):
                cylx(mb, M, (sx, sy + dy, 0.42), 0.42, 0.12, "metal2", seg=12)
    top = (0.92, 0.99) if era in OLD | MID else (0.97, 0.995)
    tbox(mb, M, (0, 0, z0 + H / 2), (W, L, H), body, top=top)
    if era in OLD | MID:                                                              # clerestory roof
        _box(mb, M, (0, 0, z0 + H + 0.12), (W * 0.55, L * 0.9, 0.3), body)
    lo, hi = z0 + H * 0.45, z0 + H * 0.82
    nw = max(3, int(L / 1.6))
    for sx in (-1, 1):
        _box(mb, M, (sx * (W / 2 + 0.005), 0, (lo + hi) / 2), (0.02, L - 1.4, hi - lo), "glass")
        for k in range(nw + 1):
            _box(mb, M, (sx * (W / 2 + 0.015), -L / 2 + 0.7 + k * (L - 1.4) / nw, (lo + hi) / 2), (0.02, 0.14, hi - lo + 0.05), body)
        for dy in (-L / 4, L / 4):
            _box(mb, M, (sx * (W / 2 + 0.02), dy, z0 + H * 0.45), (0.02, 1.2, H * 0.85), "dark" if era in OLD | MID else "metal2")
        _box(mb, M, (sx * (W / 2 + 0.01), 0, z0 + 0.3), (0.02, L, 0.12), "trim")
    for sy in (-1, 1):                                                                # end faces
        _box(mb, M, (0, sy * (L / 2 + 0.01), z0 + H * 0.62), (W * 0.7, 0.03, H * 0.38), "glass")
        lights(mb, M, sy * (L / 2 + 0.02), z0 + 0.4, W, sy < 0, era)
    if kind == "tram":
        _box(mb, M, (0, 0, z0 + H + 0.35), (0.6, 1.0, 0.35), "dark")                  # pantograph base
        rod(mb, M, (0, -0.3, z0 + H + 0.5), (0, 0.6, z0 + H + 1.6), 0.03, "metal2")
        rod(mb, M, (0, 0.6, z0 + H + 1.6), (0, -0.2, z0 + H + 2.3), 0.03, "metal2")
        _box(mb, M, (0, -0.2, z0 + H + 2.32), (1.2, 0.08, 0.05), "metal2")
        _box(mb, M, (0, -L / 2 - 0.02, z0 + H * 0.95), (W * 0.5, 0.04, 0.3), "lampshade")  # destination blind


@prop("bicycle", "floor", (0.6, 1.8, 1.1), eras=RAIL, rooms=("street", "parking", "station"))
def bicycle(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("fabric", "accent", "trim", "dark"))
    if era in STEAM:                                       # penny-farthing
        _ring(mb, M, (0, -0.15, 0.7), 0.7, 0.04, "dark", n=18)
        _ring(mb, M, (0, 0.75, 0.22), 0.22, 0.04, "dark", n=10)
        rod(mb, M, (0, -0.15, 1.4), (0, 0.75, 0.3), 0.03, k)
        _box(mb, M, (0, -0.05, 1.47), (0.1, 0.25, 0.05), "dark")
        _box(mb, M, (0, -0.25, 1.42), (0.6, 0.04, 0.04), "metal")
        return
    r = 0.34
    for sy in (-0.55, 0.55):
        _ring(mb, M, (0, sy, r), r, 0.035, "dark", n=14)
        cylx(mb, M, (0, sy, r), 0.03, 0.08, "metal", seg=6)
    b, s, h = (0, 0.05, 0.4), (0, 0.25, 0.85), (0, -0.4, 0.9)
    for a_, b_ in (((0, 0.55, r), b), (b, s), (s, (0, 0.55, r)), (b, h), (s, h), (h, (0, -0.55, r))):
        rod(mb, M, a_, b_, 0.022, k)
    _box(mb, M, (0, 0.27, 0.9), (0.12, 0.25, 0.05), "dark")
    _box(mb, M, (0, -0.45, 1.0), (0.55, 0.04, 0.04), "metal")
    if era in MID and rng.random() < 0.6:
        _box(mb, M, (0, -0.7, 0.75), (0.32, 0.28, 0.2), "wood2")                       # basket


def _ring(mb, M, c, r, t, key, n=14):
    """Wheel/ring in the local YZ plane (axis X), from short boxes."""
    c = Vector(c)
    for i in range(n):
        a = i / n * math.tau
        rbox(mb, M, c + Vector((0, math.cos(a) * r, math.sin(a) * r)), (t, r * math.tau / n * 1.08, t), key, rx=a + math.pi / 2)


@prop("motorbike", "floor", (0.8, 2.1, 1.2), eras=MID | NOW | FUT, rooms=("street", "parking", "garage"))
def motorbike(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("fabric", "accent", "dark", "trim"))
    if era in FUT:
        tbox(mb, M, (0, 0, 0.75), (0.5, 1.9, 0.5), k, top=(0.6, 0.8), shift=(0, 0.1))
        for sy in (-0.75, 0.75):
            cylx(mb, M, (0, sy, 0.35), 0.35, 0.22, "dark", seg=16)
            cylx(mb, M, (0, sy, 0.35), 0.25, 0.24, "accent", seg=16)
        _box(mb, M, (0, 0.25, 1.03), (0.3, 0.7, 0.08), "dark")
        return
    for sy in (-0.7, 0.7):
        wheel(mb, M, (0, sy, 0.33), 0.33, 0.14, era)
    tbox(mb, M, (0, -0.15, 0.85), (0.32, 0.6, 0.28), k, top=(0.8, 0.8))               # tank
    _box(mb, M, (0, 0.0, 0.5), (0.3, 0.6, 0.3), "metal2")                             # engine
    _box(mb, M, (0, 0.38, 0.88), (0.3, 0.6, 0.1), "dark")                             # seat
    rod(mb, M, (0, -0.7, 0.33), (0, -0.48, 1.05), 0.03, "metal")
    _box(mb, M, (0, -0.5, 1.08), (0.7, 0.04, 0.04), "metal")
    cylx(mb, M, (0, -0.58, 0.95), 0.09, 0.08, "lampshade", seg=10, axis="Y")
    rod(mb, M, (0.18, 0.0, 0.35), (0.18, 0.85, 0.42), 0.04, "metal")                 # exhaust
    _box(mb, M, (0, 0.7, 0.62), (0.22, 0.4, 0.04), k)                                 # rear mudguard


@prop("wheelbarrow", "floor", (0.7, 1.5, 0.7), eras=ALL, rooms=("construction", "farm", "street", "market"))
def wheelbarrow(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = "wood" if era in OLD else body_key(rng, era, ("accent", "metal", "fabric"))
    tbox(mb, M, (0, 0.05, 0.45), (0.45, 0.65, 0.3), k, top=(1.35, 1.35))
    for sx in (-0.22, 0.22):
        rod(mb, M, (sx, -0.45, 0.3), (sx * 1.3, 0.75, 0.55), 0.025, "wood2" if era in OLD else "metal2")
        _box(mb, M, (sx, 0.35, 0.15), (0.03, 0.03, 0.3), "metal2")
    if era in OLD:
        spoked(mb, M, (0, -0.48, 0.2), 0.2, 0.05, "wood2", n=8)
    else:
        wheel(mb, M, (0, -0.48, 0.2), 0.2, 0.08, era)
    if rng.random() < 0.6:
        mb.sphere(M @ Vector((0, 0.05, 0.58)), 0.24, rng.choice(("stone", "wood2", "fabric2")), sub=1, squash=0.6)


# ----------------------------------------------------------------------------- more eras
def disc_wheel(mb, M, c, r, w, key="wood2"):
    """Solid plank wheel (ox carts): disc + hub + a cross batten."""
    cylx(mb, M, c, r, w, key, seg=14)
    cylx(mb, M, c, r * 0.22, w * 1.8, "wood", seg=8)
    rbox(mb, M, (c[0] + math.copysign(w * 0.55, c[0] or 1), c[1], c[2]), (0.02, r * 1.7, r * 0.18), "wood")


@prop("chariot", "floor", (1.4, 3.6, 1.2), eras=ANC, rooms=("street", "arena", "forum"))
def chariot(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = rng.choice(("accent", "fabric", "metal"))
    _box(mb, M, (0, 0.35, 0.62), (1.0, 0.8, 0.06), "wood")
    tbox(mb, M, (0, 0.05, 0.92), (1.0, 0.12, 0.6), k, top=(0.85, 1.0))              # curved breastwork
    for sx in (-1, 1):
        tbox(mb, M, (sx * 0.48, 0.35, 0.82), (0.05, 0.7, 0.4), k, top=(1.0, 0.6), shift=(0, -0.2))
    _box(mb, M, (0, 0.05, 1.24), (0.9, 0.05, 0.05), "metal")
    for sx in (-0.68, 0.68):
        spoked(mb, M, (sx, 0.5, 0.5), 0.5, 0.06, "wood2", n=6)
    cylx(mb, M, (0, 0.5, 0.5), 0.04, 1.45, "wood2", seg=6)
    rod(mb, M, (0, 0.1, 0.6), (0, -2.0, 0.95), 0.05, "wood2")                       # draught pole + yoke
    _box(mb, M, (0, -2.0, 0.98), (1.2, 0.08, 0.06), "wood2")


@prop("ox_cart", "floor", (1.8, 4.0, 1.4), eras=ANC | MED | PREIND, rooms=("street", "market", "farm", "forum"))
def ox_cart(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0.3, 0.85), (1.3, 2.2, 0.1), "wood")
    for sx in (-0.65, 0.65):
        for k in range(6):                                                           # stake sides
            _box(mb, M, (sx, -0.6 + k * 0.36, 1.15), (0.06, 0.06, 0.55), "wood2")
        _box(mb, M, (sx, 0.3, 1.38), (0.06, 2.2, 0.06), "wood2")
    for sx in (-0.82, 0.82):
        disc_wheel(mb, M, (sx, 0.4, 0.6), 0.6, 0.14)
    cylx(mb, M, (0, 0.4, 0.6), 0.06, 1.9, "wood2", seg=6)
    rod(mb, M, (0, -0.7, 0.8), (0, -2.6, 0.7), 0.06, "wood2")
    _box(mb, M, (0, -2.6, 0.75), (1.4, 0.12, 0.1), "wood2")                         # yoke
    for i in range(rng.randint(2, 5)):
        p = M @ Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.4, 1.1), 1.1))
        if rng.random() < 0.5:
            mb.sphere(p, rng.uniform(0.22, 0.3), "fabric2", sub=1, squash=1.2)
        else:
            mb.sphere(p, 0.3, "leaf" if rng.random() < 0.3 else "wood2", sub=1, squash=0.8)


@prop("stagecoach", "floor", (2.0, 5.0, 2.9), eras=PREIND | STEAM, rooms=("street", "market"))
def stagecoach(mb, x, y, z, rot, rng, era):
    """Wild-west / mail coach: egg-shaped body on thoroughbraces, luggage on the roof, boot behind."""
    M = M_at(x, y, z, rot)
    body = rng.choice(("fabric", "accent", "wall2"))
    tbox(mb, M, (0, 0.3, 0.95), (1.5, 2.0, 0.5), body, top=(1.0, 1.2))
    tbox(mb, M, (0, 0.3, 1.75), (1.5, 2.4, 1.1), body, top=(0.95, 0.85))
    for sx in (-1, 1):
        _box(mb, M, (sx * 0.76, 0.3, 1.85), (0.04, 0.6, 0.55), "dark")                # window opening
        _box(mb, M, (sx * 0.77, 0.3, 1.25), (0.03, 0.7, 0.55), "trim")
        _box(mb, M, (sx * 0.77, 0.3, 1.18), (0.01, 2.0, 0.08), "paper")
    _box(mb, M, (0, 0.3, 2.34), (1.55, 2.2, 0.08), "trim")
    for sx in (-0.75, 0.75):
        rod(mb, M, (sx, -0.8, 2.38), (sx, 1.4, 2.38), 0.025, "metal")                 # roof rail
    for i in range(rng.randint(2, 4)):
        _box(mb, M, (rng.uniform(-0.35, 0.35), -0.4 + i * 0.5, 2.55), (0.55, 0.42, 0.3), rng.choice(("wood2", "fabric2", "paper")))
    tbox(mb, M, (0, 1.75, 1.2), (1.3, 0.6, 0.8), "dark", top=(1.0, 0.7))              # boot
    _box(mb, M, (0, -1.25, 1.85), (1.4, 0.6, 0.12), "wood2")                          # driver's box
    _box(mb, M, (0, -1.0, 2.1), (1.4, 0.08, 0.45), "wood2")
    _box(mb, M, (0, -1.6, 1.4), (1.2, 0.08, 0.6), "wood2")                            # footboard
    _box(mb, M, (0, 0.3, 0.6), (0.3, 3.8, 0.12), "wood2")
    for sy, r in ((-1.05, 0.55), (1.5, 0.75)):
        for sx in (-0.92, 0.92):
            spoked(mb, M, (sx, sy, r), r, 0.08, "accent" if body != "accent" else "trim", n=12)
    for sx in (-0.45, 0.45):
        rod(mb, M, (sx, -1.4, 0.7), (sx * 0.6, -3.2, 0.85), 0.04, "wood2")


@prop("model_t", "floor", (1.7, 3.6, 2.1), eras=INTER, rooms=("street", "parking", "garage"))
def model_t(mb, x, y, z, rot, rng, era):
    """Tall upright 1910s-20s car: spoked wheels, brass radiator, flat roof on posts."""
    M = M_at(x, y, z, rot)
    k = rng.choice(("dark", "dark", "trim"))
    for sy in (-1.05, 1.1):
        for sx in (-0.72, 0.72):
            spoked(mb, M, (sx, sy, 0.38), 0.38, 0.07, "dark", n=10)
            tbox(mb, M, (sx * 0.95, sy, 0.82), (0.24, 0.85, 0.05), k, top=(1.0, 0.7))   # mudguards
    _box(mb, M, (0, 0.05, 0.68), (1.1, 3.1, 0.18), k)
    tbox(mb, M, (0, -1.0, 0.98), (0.75, 0.9, 0.45), k, top=(0.9, 1.0))              # bonnet
    _box(mb, M, (0, -1.47, 1.0), (0.72, 0.08, 0.6), "metal")                          # brass radiator
    _box(mb, M, (0, 0.4, 1.05), (1.25, 1.7, 0.6), k)                                  # tub
    _box(mb, M, (0, -0.42, 1.6), (1.15, 0.04, 0.6), "glass")                          # upright windscreen
    for sx in (-0.6, 0.6):
        for sy in (-0.42, 1.2):
            _box(mb, M, (sx, sy, 1.65), (0.04, 0.04, 0.7), "dark")
    _box(mb, M, (0, 0.4, 2.02), (1.3, 1.8, 0.05), "dark")
    for sx in (-0.42, 0.42):
        cylx(mb, M, (sx, -1.52, 1.12), 0.1, 0.14, "lampshade", seg=10, axis="Y")
    cylx(mb, M, (0, -0.25, 1.3), 0.18, 0.03, "dark", seg=12, axis="Y")               # steering wheel


@prop("trabant", "floor", (1.6, 3.6, 1.45), eras=COLD | EIGHTIES, rooms=("street", "parking"))
def trabant(mb, x, y, z, rot, rng, era):
    """Small boxy two-door with a pale body and white roof (East-bloc everyman car)."""
    M = M_at(x, y, z, rot)
    body = rng.choice(("wall2", "paper", "wall", "fabric2"))
    for sy in (-1.1, 1.1):
        for sx in (-0.68, 0.68):
            wheel(mb, M, (sx, sy, 0.27), 0.27, 0.16, "modern")
    tbox(mb, M, (0, 0, 0.6), (1.5, 3.5, 0.5), body, top=(1.0, 0.99))
    cabin(mb, M, 0.25, 0.85, 1.9, 1.42, 0.55, body, top=(0.9, 0.78), band=(0.08, 0.9), pillars=0)
    _box(mb, M, (0, 0.25, 1.42), (1.25, 1.5, 0.04), "paper")
    _box(mb, M, (0, -1.76, 0.6), (1.1, 0.04, 0.2), "dark")
    lights(mb, M, -1.76, 0.72, 1.5, True, "1920s-50s", r=0.08)
    _box(mb, M, (0, -1.78, 0.4), (1.5, 0.06, 0.1), "metal")
    _box(mb, M, (0, 1.78, 0.4), (1.5, 0.06, 0.1), "metal")


@prop("hatchback_80s", "floor", (1.7, 3.8, 1.45), eras=EIGHTIES | {"modern", "post_apocalyptic"}, rooms=("street", "parking", "garage"))
def hatchback_80s(mb, x, y, z, rot, rng, era):
    """Boxy wedge hatch: flat panels, black bumpers, square lamps."""
    M = M_at(x, y, z, rot)
    body = body_key(rng, era, ("accent", "fabric", "wall2", "paper", "trim"))
    for sy in (-1.15, 1.2):
        for sx in (-0.74, 0.74):
            wheel(mb, M, (sx, sy, 0.29), 0.29, 0.2, "modern")
    tbox(mb, M, (0, 0, 0.57), (1.66, 3.75, 0.5), body, top=(1.0, 0.99))
    cabin(mb, M, 0.45, 0.82, 2.4, 1.62, 0.6, body, top=(0.9, 0.82), shift=0.12, band=(0.08, 0.9))
    _box(mb, M, (0, -1.9, 0.38), (1.7, 0.1, 0.18), "dark")
    _box(mb, M, (0, 1.9, 0.38), (1.7, 0.1, 0.18), "dark")
    for sx in (-1, 1):
        _box(mb, M, (sx * 0.84, 0, 0.5), (0.02, 3.4, 0.08), "dark")                    # rubbing strip
        _box(mb, M, (sx * 0.55, -1.88, 0.66), (0.4, 0.04, 0.16), "lampshade")
        _box(mb, M, (sx * 0.62, 1.88, 0.68), (0.3, 0.04, 0.2), "fabric")
    _box(mb, M, (0, -1.88, 0.66), (0.5, 0.04, 0.14), "dark")


@prop("electric_car", "floor", (1.9, 4.7, 1.5), eras={"contemporary", "modern"} | NEAR, rooms=("street", "parking", "garage"))
def electric_car(mb, x, y, z, rot, rng, era):
    """Smooth modern EV: one-piece glass roof, full-width light bars, flush wheels, a charge flap."""
    M = M_at(x, y, z, rot)
    body = rng.choice(("paper", "metal", "trim", "wall2", "dark"))
    for sy in (-1.45, 1.45):
        for sx in (-0.8, 0.8):
            wheel(mb, M, (sx, sy, 0.34), 0.34, 0.24, "modern", hub="metal2")
    tbox(mb, M, (0, 0, 0.62), (1.88, 4.7, 0.56), body, top=(0.99, 0.96))
    cabin(mb, M, 0.2, 0.9, 2.9, 1.78, 0.56, "glass", glass="glass", top=(0.8, 0.52), shift=0.25, band=(0.0, 1.0), pillars=0)
    _box(mb, M, (0, -2.36, 0.8), (1.6, 0.03, 0.05), "lampshade")
    _box(mb, M, (0, 2.36, 0.85), (1.7, 0.03, 0.06), "fabric")
    _box(mb, M, (0.95, 1.6, 0.85), (0.02, 0.18, 0.12), "accent" if era in NEAR else "dark")


@prop("steam_locomotive", "floor", (2.8, 11.0, 4.3), eras=STEAM | INTER, rooms=("station", "rail"))
def steam_locomotive(mb, x, y, z, rot, rng, era):
    """Steam engine: boiler, smokebox + chimney, dome, cab, big driving wheels, tender behind."""
    M = M_at(x, y, z, rot)
    k = rng.choice(("dark", "accent", "trim", "fabric"))
    _box(mb, M, (0, 0, 0.95), (2.0, 7.0, 0.35), "dark")                             # frame
    cylx(mb, M, (0, -0.9, 2.15), 0.85, 4.6, k, seg=16, axis="Y")                       # boiler
    cylx(mb, M, (0, -3.35, 2.15), 0.92, 0.6, "dark", seg=16, axis="Y")                 # smokebox
    cylx(mb, M, (0, -3.66, 2.15), 0.5, 0.05, "metal2", seg=12, axis="Y")
    _cyl(mb, M, (0, -3.2, 3.3), 0.24, 0.9, "dark", seg=10, r2=0.34)                   # chimney
    _cyl(mb, M, (0, -1.4, 3.1), 0.28, 0.4, "metal", seg=10, r2=0.2)                   # dome
    _cyl(mb, M, (0, 0.0, 3.05), 0.18, 0.35, "metal", seg=8)
    _box(mb, M, (0, 2.3, 2.45), (2.6, 2.2, 2.6), k)                                   # cab
    _box(mb, M, (0, 2.3, 3.82), (2.8, 2.5, 0.12), "dark")
    for sx in (-1, 1):
        _box(mb, M, (sx * 1.31, 2.1, 2.9), (0.03, 0.8, 0.7), "dark")                   # cab window
        _box(mb, M, (sx * 1.0, -0.9, 1.3), (0.5, 5.2, 0.06), "dark")                   # running board
        for sy in (-1.6, -0.2, 1.2):
            spoked(mb, M, (sx * 0.8, sy, 0.75), 0.75, 0.1, "accent" if k != "accent" else "trim", n=12)
        for sy in (-3.0, -2.4):
            wheel(mb, M, (sx * 0.8, sy, 0.42), 0.42, 0.1, "1920s-50s")
        rod(mb, M, (sx * 0.95, -1.6, 0.85), (sx * 0.95, 1.2, 0.85), 0.05, "metal")      # coupling rod
        cylx(mb, M, (sx * 0.95, -2.7, 1.25), 0.32, 1.0, "dark", seg=10, axis="Y")       # cylinders
    if era in STEAM and rng.random() < 0.6:                                         # cowcatcher
        tbox(mb, M, (0, -3.9, 0.55), (2.0, 0.9, 0.7), "metal2", top=(1.0, 0.2), shift=(0, 0.35))
    else:
        _box(mb, M, (0, -3.75, 0.95), (2.6, 0.2, 0.3), "fabric")                       # buffer beam
    cylx(mb, M, (0, -3.72, 2.95), 0.18, 0.2, "lampshade", seg=10, axis="Y")
    _box(mb, M, (0, 5.0, 1.75), (2.6, 3.4, 1.9), k)                                   # tender + coal
    mb.sphere(M @ Vector((0, 5.0, 2.65)), 1.1, "dark", sub=1, squash=0.35)
    for sy in (4.0, 6.0):
        for sx in (-0.8, 0.8):
            wheel(mb, M, (sx, sy, 0.48), 0.48, 0.1, "1920s-50s")


@prop("rickshaw", "floor", (1.2, 2.6, 1.7), eras=STEAM | INTER, rooms=("street", "market"))
def rickshaw(mb, x, y, z, rot, rng, era):
    """Pulled rickshaw (Meiji Tokyo / Shanghai): seat with folding hood on two tall wheels."""
    M = M_at(x, y, z, rot)
    k = rng.choice(("dark", "fabric", "accent"))
    _box(mb, M, (0, 0.3, 0.75), (0.8, 0.6, 0.1), k)
    _box(mb, M, (0, 0.62, 1.05), (0.8, 0.08, 0.6), k)
    tbox(mb, M, (0, 0.5, 1.5), (0.85, 0.6, 0.5), "fabric2", top=(1.0, 0.4), shift=(0, 0.2))    # hood
    for sx in (-0.5, 0.5):
        spoked(mb, M, (sx, 0.45, 0.62), 0.62, 0.05, "dark", n=12)
        rod(mb, M, (sx * 0.7, 0.2, 0.75), (sx * 0.55, -1.6, 0.85), 0.025, "wood2")
    _box(mb, M, (0, -1.6, 0.86), (0.6, 0.04, 0.04), "wood2")
    _box(mb, M, (0, 0.0, 0.45), (0.5, 0.25, 0.04), k)                                  # footrest


def hull_shell(mb, M, L, B, H, key, inner="wood2", bow_lift=0.3, stern_lift=0.0, stern_w=0.45, n=12, t=0.06,
               rail="trim", deck=False, bow_t=0.55):
    """Open (or decked) boat hull along local Y, bow at -Y: plank sides following a fair waterline
    curve, a bottom, a transom, a gunwale rail. Returns the half-width function w(u), u 0=bow..1=stern."""
    def w(u):
        if u <= bow_t:
            return B / 2 * math.sin(math.pi / 2 * u / bow_t) ** 0.75
        return B / 2 * (1 - (1 - stern_w) * ((u - bow_t) / (1 - bow_t)) ** 2)

    def zt(u):
        return H + bow_lift * max(0.0, 1 - u / 0.35) ** 2 + stern_lift * max(0.0, (u - 0.7) / 0.3) ** 2
    pts = [(u, -L / 2 + L * u) for u in (i / n for i in range(n + 1))]
    for (u0, y0), (u1, y1) in zip(pts, pts[1:]):
        for sx in (-1, 1):
            a, b = Vector((sx * w(u0), y0, 0)), Vector((sx * w(u1), y1, 0))
            d = b - a
            h0 = (zt(u0) + zt(u1)) / 2
            ang = math.atan2(d.x, d.y)
            rbox(mb, M, ((a + b) / 2) + Vector((0, 0, h0 / 2 + 0.02)), (t, d.length + 0.03, h0), key, rz=-ang)
            rbox(mb, M, ((a + b) / 2) + Vector((0, 0, h0 + 0.03)), (t * 1.8, d.length + 0.04, 0.05), rail, rz=-ang)
        ww = min(w(u0), w(u1))
        if ww > 0.05:
            _box(mb, M, (0, (y0 + y1) / 2, 0.06 if not deck else H - 0.05), (2 * ww - t, y1 - y0 + 0.02, 0.1), inner)
    ws = w(1.0)
    _box(mb, M, (0, L / 2, zt(1.0) / 2 + 0.02), (2 * ws + t, t, zt(1.0)), key)
    return w


@prop("gondola", "floor", (1.4, 10.0, 1.4), eras=PREIND | STEAM | MID | NOW, rooms=("canal", "dock"))
def gondola(mb, x, y, z, rot, rng, era):
    """Venetian gondola: long black hull with raised ends, iron ferro at the bow, a red seat."""
    M = M_at(x, y, z, rot)
    hull_shell(mb, M, 10.0, 1.4, 0.45, "dark", inner="wood2", bow_lift=0.8, stern_lift=0.6, stern_w=0.08, bow_t=0.5, rail="dark")
    _box(mb, M, (0, -5.05, 1.05), (0.05, 0.2, 0.75), "metal")                         # ferro
    for k in range(5):
        _box(mb, M, (0, -4.96, 0.85 + k * 0.1), (0.04, 0.32, 0.035), "metal")
    _box(mb, M, (0, 0.6, 0.4), (0.8, 0.9, 0.18), "fabric")                            # seat
    _box(mb, M, (0, 1.0, 0.6), (0.8, 0.1, 0.35), "fabric")
    _box(mb, M, (0, -0.4, 0.13), (0.9, 0.6, 0.04), "fabric2")                          # carpet
    rod(mb, M, (0.6, 3.6, 0.5), (0.45, 3.8, 1.1), 0.04, "wood2")                       # forcola + oar
    rod(mb, M, (0.45, 3.8, 1.1), (1.2, 0.8, -0.1), 0.03, "wood2")


@prop("rowboat", "floor", (1.4, 3.6, 0.8), eras=ALL, rooms=("dock", "canal", "beach", "ship"))
def rowboat(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = rng.choice(("wood", "accent", "wall2", "paper")) if era not in FUT else rng.choice(("wood", "wall2", "paper"))
    hull_shell(mb, M, 3.6, 1.35, 0.5, k, inner="wood2", bow_lift=0.18, stern_w=0.5)
    for yy in (-0.5, 0.5):
        _box(mb, M, (0, yy, 0.38), (1.15, 0.22, 0.05), "wood2")                        # thwarts
    for sx in (-1, 1):
        rod(mb, M, (sx * 0.62, 0.0, 0.58), (sx * 0.3, 1.5, 0.35), 0.025, "wood2")      # oars


# ----------------------------------------------------------------------------- era picks for kits
VEHICLES = ("chariot", "ox_cart", "horse_cart", "carriage", "stagecoach", "rickshaw", "model_t", "sedan_1930s",
            "car_1950s", "trabant", "hatchback_80s", "hatchback", "sedan", "electric_car", "taxi", "van",
            "hover_car", "motorbike", "bicycle", "handcart")
BIG = ("delivery_truck", "bus", "tram")


def era_vehicles(era, big=False, culture=None):
    """Vehicle prop names valid for an era (cars first; carts for pre-industrial eras)."""
    from ..props import PROPS
    names = [n for n in VEHICLES + (BIG if big else ()) if n in PROPS and (PROPS[n]["eras"] is None or era in PROPS[n]["eras"])]
    if culture not in ("meiji_japan", "shanghai") and "rickshaw" in names and len(names) > 2:
        names.remove("rickshaw")
    if culture in ("soviet", "divided_berlin", "post_soviet") and "trabant" in names:
        names += ["trabant"] * 3
    if culture == "wild_west":
        names = [n for n in names if n in ("stagecoach", "horse_cart", "handcart")] or names
    return names or ["handcart"]

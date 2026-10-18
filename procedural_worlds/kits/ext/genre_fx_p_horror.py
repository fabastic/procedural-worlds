"""genre_fx props: sacred / funerary (statues, altars, tombs, pews) and horror dressing
(cobwebs, skulls, chains, stains, boarded windows, broken furniture, dolls, ritual candles, portraits)."""
import math
from mathutils import Vector
from ..props import OLD, MID, NOW, FUT
from .genre_fx_geom import (fxprop, M0, sub, bx, cy, cyx, cyy, sp, lathe, prism, slab, ring, strut, polyline,
                            arch_pts, flame, fire, candle, book, table, surface, ANC, MED, EARLY, PRE, LATE)
from .genre_fx_p_medieval import skull_shape, goblet_shape

SACRED = ("temple", "chapel", "crypt", "monastery", "shrine", "cathedral")
HORROR = ("haunted", "crypt", "ritual", "dungeon", "asylum", "horror", "seance")
NOT_FAR = OLD | MID | NOW | {"near-future", "near_future", "cyberpunk", "post_apocalyptic", "solarpunk"}


# ----------------------------------------------------------------------------- sacred & funerary
@fxprop("statue", "floor", (1.0, 1.0, 2.8), eras=OLD | MID, rooms=("fx_feature",))
def statue(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    k = "stone"
    bx(mb, M, (0, 0, 0.3), (0.85, 0.85, 0.6), k)
    bx(mb, M, (0, 0, 0.63), (0.95, 0.95, 0.06), k)
    bx(mb, M, (0, 0, 0.04), (0.95, 0.95, 0.08), k)
    kind = rng.choice(("robed", "warrior", "urn"))
    z0 = 0.66
    lathe(mb, M, (0, 0, z0), [(0.32, 0), (0.3, 0.3), (0.24, 0.8), (0.2, 1.15), (0.24, 1.35), (0.0, 1.42)], k, seg=10, sc=(1, 0.8))
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.2, 0, z0 + 1.32), 0.11, k, sub=1, sc=(1.1, 0.9, 0.8))
    sp(mb, M, (0, -0.02, z0 + 1.6), 0.13, k, sub=1, sc=(0.9, 1.0, 1.15))
    cy(mb, M, (0, 0, z0 + 1.45), 0.06, 0.1, k, seg=8)
    if kind == "robed":                                  # staff + orb
        strut(mb, M, (0.3, -0.1, z0), (0.3, -0.12, z0 + 2.0), 0.025, k, seg=6)
        sp(mb, M, (0.3, -0.12, z0 + 2.05), 0.08, k, sub=1)
        strut(mb, M, (0.22, 0, z0 + 1.3), (0.3, -0.12, z0 + 1.15), 0.05, k, seg=6)
        strut(mb, M, (-0.22, 0, z0 + 1.3), (-0.12, -0.18, z0 + 0.95), 0.05, k, seg=6)
    elif kind == "warrior":                              # hands on a downward sword
        strut(mb, M, (0.22, 0, z0 + 1.3), (0.03, -0.25, z0 + 1.0), 0.05, k, seg=6)
        strut(mb, M, (-0.22, 0, z0 + 1.3), (-0.03, -0.25, z0 + 1.0), 0.05, k, seg=6)
        bx(mb, M, (0, -0.28, z0 + 0.5), (0.06, 0.02, 0.95), k)
        bx(mb, M, (0, -0.28, z0 + 0.98), (0.28, 0.04, 0.04), k)
        prism(mb, M, (0, 0, z0 + 1.62), [(-0.02, 0), (0.02, 0), (0.0, 0.25), (-0.18, 0.18)], 0.04, k, rz=math.pi / 2)
    else:                                                # bearing an urn on the shoulder
        strut(mb, M, (0.22, 0, z0 + 1.3), (0.28, 0, z0 + 1.7), 0.05, k, seg=6)
        lathe(mb, M, (0.28, 0.05, z0 + 1.65), [(0.05, 0), (0.13, 0.12), (0.08, 0.25), (0.1, 0.3), (0, 0.3)], k, seg=10)
        strut(mb, M, (-0.22, 0, z0 + 1.3), (-0.26, -0.05, z0 + 0.85), 0.05, k, seg=6)


@fxprop("gargoyle", "floor", (0.8, 0.8, 1.3), eras=OLD | MID, rooms=("crypt", "cathedral", "haunted", "castle", "rooftop", "fx_feature"))
def gargoyle(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    k = "stone"
    bx(mb, M, (0, 0, 0.25), (0.6, 0.6, 0.5), k)
    bx(mb, M, (0, 0, 0.52), (0.7, 0.7, 0.05), k)
    z0 = 0.55
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.15, 0.08, z0 + 0.12), 0.13, k, sub=1, sc=(0.8, 1.2, 0.9))           # haunches
        strut(mb, M, (sx * 0.12, -0.12, z0 + 0.3), (sx * 0.13, -0.2, z0 + 0.02), 0.04, k)      # forelegs
        sp(mb, M, (sx * 0.13, -0.23, z0 + 0.02), 0.045, k, sub=0)
        wing = [(0, 0), (0.12, 0.25), (0.38, 0.5), (0.42, 0.25), (0.34, 0.2), (0.33, 0.05), (0.22, 0.06), (0.18, -0.08)]
        prism(mb, sub(M, (sx * 0.1, 0.12, z0 + 0.35), rz=sx * 0.5, ry=0.0), (0, 0, 0), [(sx * u, v) for u, v in wing][::sx], 0.03, k)
    sp(mb, M, (0, -0.02, z0 + 0.33), 0.17, k, sub=1, sc=(0.9, 1.1, 1.2))                      # hunched torso
    sp(mb, M, (0, -0.2, z0 + 0.5), 0.11, k, sub=1, sc=(1, 1.1, 0.9))                          # head
    cy(mb, M, (0, -0.32, z0 + 0.47), 0.05, 0.1, k, seg=6, r2=0.03, rx=math.pi / 2)
    for sx in (-1, 1):
        cy(mb, M, (sx * 0.07, -0.18, z0 + 0.62), 0.025, 0.14, k, seg=4, r2=0.0, ry=sx * 0.5)
        sp(mb, M, (sx * 0.045, -0.29, z0 + 0.52), 0.016, "dark", sub=0)


@fxprop("altar", "floor", (2.1, 1.1, 1.2), eras=OLD | MID, rooms=("fx_feature",))
def altar(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.06), (2.1, 1.1, 0.12), "stone")
    bx(mb, M, (0, 0, 0.5), (1.8, 0.85, 0.8), "stone")
    bx(mb, M, (0, 0, 0.94), (2.0, 1.0, 0.08), "stone")
    for sx in (-0.6, 0, 0.6):
        prism(mb, M, (sx, -0.43, 0.15), arch_pts(0.38, 0.6, 0.45, seg=6), 0.02, "wall2")
    bx(mb, M, (0, 0.0, 0.985), (1.4, 1.02, 0.012), "fabric")
    bx(mb, M, (0, -0.51, 0.8), (0.7, 0.012, 0.38), "fabric")
    bx(mb, M, (0, -0.517, 0.8), (0.12, 0.01, 0.3), "glass2")
    for sx in (-0.8, 0.8):
        lathe(mb, M, (sx, 0.2, 0.98), [(0.08, 0), (0.03, 0.05), (0.025, 0.3), (0.05, 0.32), (0, 0.32)], "glass2", seg=8)
        candle(mb, M, (sx, 0.2, 1.3), 0.25, 0.03)
    goblet_shape(mb, sub(M, (0.1, -0.1, 0.99)), 1.3)
    book(mb, M, (-0.3, -0.1, 1.01), 0.3, 0.22, 0.04, "fabric2", rz=0.2)
    return surface(x, y, z + 0.99, 0.25)


@fxprop("sarcophagus", "floor", (1.1, 2.4, 1.0), eras=OLD | MID, rooms=("fx_feature", "tomb"))
def sarcophagus(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.08), (1.1, 2.4, 0.16), "stone")
    bx(mb, M, (0, 0, 0.45), (0.95, 2.2, 0.6), "stone")
    for sx in (-1, 1):
        for k in range(4):
            prism(mb, M, (sx * 0.48, -0.75 + k * 0.5, 0.2), arch_pts(0.3, 0.45, 0.3, seg=5), 0.02, "wall2", rz=math.pi / 2)
    ajar = rng.random() < 0.3
    lid = sub(M, (0.15 if ajar else 0, 0.1 if ajar else 0, 0.75), rz=0.18 if ajar else 0)
    slab(mb, lid, (0, 0, 0), [(-0.52, -1.15), (0.52, -1.15), (0.52, 1.15), (-0.52, 1.15)], 0.08, "stone")
    slab(mb, lid, (0, 0, 0.08), [(-0.42, -1.05), (0.42, -1.05), (0.42, 1.05), (-0.42, 1.05)], 0.06, "stone")
    # effigy: a carved knight lying on the lid
    sp(mb, lid, (0, -0.75, 0.24), 0.13, "stone", sub=1, sc=(1, 1, 0.8))
    cy(mb, lid, (0, -0.7, 0.21), 0.12, 0.08, "stone", seg=10, rx=math.pi / 2)
    lathe(mb, lid, (0, -0.55, 0.2), [(0.2, 0), (0.22, 0.4), (0.18, 0.9), (0.14, 1.45), (0, 1.5)], "stone", seg=8, rx=-math.pi / 2, sc=(1.2, 0.5))
    strut(mb, lid, (0, -0.45, 0.32), (0, -0.2, 0.36), 0.05, "stone")
    bx(mb, lid, (0, 0.1, 0.3), (0.04, 0.9, 0.02), "stone")
    sp(mb, lid, (0, 0.9, 0.2), 0.1, "stone", sub=0, sc=(1.4, 0.8, 0.6))
    if ajar:
        bx(mb, M, (-0.05, -0.2, 0.755), (0.6, 1.4, 0.02), "dark")


@fxprop("coffin", "floor", (0.75, 2.0, 0.55), eras=PRE | NOW, rooms=("crypt", "haunted", "funeral", "fx_feature"))
def coffin(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    pts = [(-0.2, -1.0), (0.2, -1.0), (0.33, 0.45), (0.24, 1.0), (-0.24, 1.0), (-0.33, 0.45)]
    slab(mb, M, (0, 0, 0), pts, 0.38, "wood2")
    slab(mb, M, (0, 0, 0.02), [(u * 1.03, v * 1.01) for u, v in pts], 0.06, "wood")
    opened = rng.random() < 0.35
    lid = sub(M, (0.25, 0.0, 0.45), rz=0.25, ry=0.2) if opened else sub(M, (0, 0, 0.38))
    slab(mb, lid, (0, 0, 0), [(u * 1.04, v * 1.02) for u, v in pts], 0.07, "wood")
    bx(mb, lid, (0, 0.38, 0.075), (0.05, 0.5, 0.012), "glass2")
    bx(mb, lid, (0, 0.5, 0.075), (0.3, 0.05, 0.012), "glass2")
    if opened:
        slab(mb, M, (0, 0, 0.3), [(u * 0.85, v * 0.92) for u, v in pts], 0.03, "fabric")
    for sy in (-0.5, 0.0, 0.5):
        for sx in (-1, 1):
            bx(mb, M, (sx * (0.27 if sy >= 0 else 0.24), sy, 0.2), (0.03, 0.12, 0.04), "metal2")


@fxprop("iron_cage", "floor", (1.1, 1.1, 2.2), eras=PRE, rooms=("dungeon", "fx_feature", "circus", "witch"))
def iron_cage(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    r, h = 0.5, 1.7
    ring(mb, M, (0, 0, 0.05), r, 0.03, "metal2", seg=14, mseg=4)
    ring(mb, M, (0, 0, h), r, 0.03, "metal2", seg=14, mseg=4)
    ring(mb, M, (0, 0, h * 0.5), r, 0.02, "metal2", seg=14, mseg=3)
    for i in range(12):
        a = i / 12 * math.tau
        strut(mb, M, (math.cos(a) * r, math.sin(a) * r, 0.05), (math.cos(a) * r, math.sin(a) * r, h), 0.014, "metal2")
        strut(mb, M, (math.cos(a) * r, math.sin(a) * r, h), (0, 0, h + 0.35), 0.012, "metal2")
    ring(mb, sub(M, (0, 0, h + 0.42), rx=math.pi / 2), (0, 0, 0), 0.07, 0.015, "metal2", seg=8, mseg=3)
    cy(mb, M, (0, 0, 0.04), r * 0.98, 0.06, "wood2", seg=14)
    if rng.random() < 0.5:
        skull_shape(mb, sub(M, (0.1, 0.0, 0.07), rz=rng.uniform(0, 6)), 1.0)
        for k in range(3):
            strut(mb, M, (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.09), (rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.09), 0.015, "paper", seg=6)


@fxprop("gibbet_cage", "hanging", (0.7, 0.7, 2.4), eras=PRE, rooms=("fx_feature",))
def gibbet_cage(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    drop = rng.uniform(0.3, 0.8)
    for k in range(int(drop / 0.09)):
        ring(mb, sub(M, (0, 0, -0.05 - k * 0.09), rx=math.pi / 2, rz=(k % 2) * math.pi / 2), (0, 0, 0), 0.035, 0.008, "metal2", seg=6, mseg=3)
    top = -drop - 0.1
    prof = [(0.05, 0.0), (0.22, -0.15), (0.3, -0.5), (0.28, -1.0), (0.2, -1.5), (0.05, -1.6)]
    for i in range(8):
        a = i / 8 * math.tau
        polyline(mb, M, [(math.cos(a) * r, math.sin(a) * r, top + zz) for r, zz in prof], 0.012, "metal2")
    for r, zz in prof[1:-1]:
        ring(mb, M, (0, 0, top + zz), r, 0.012, "metal2", seg=12, mseg=3)


@fxprop("stocks", "floor", (1.6, 0.6, 1.3), eras=OLD, rooms=("square", "dungeon", "village", "fx_feature"))
def stocks(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.06), (1.6, 0.5, 0.12), "wood2")
    for sx in (-0.7, 0.7):
        bx(mb, M, (sx, 0, 0.65), (0.14, 0.14, 1.2), "wood2")
    for zz in (0.78, 1.0):
        bx(mb, M, (0, 0, zz), (1.4, 0.1, 0.22), "wood")
    for u, r in ((-0.35, 0.05), (0, 0.09), (0.35, 0.05)):
        cyy(mb, M, (u, -0.052, 0.89), r, 0.01, "dark", seg=10)
    bx(mb, M, (0, -0.055, 1.12), (0.08, 0.02, 0.06), "metal2")


@fxprop("pew", "floor", (2.4, 0.75, 1.0), eras=OLD | MID | NOW, rooms=("fx_feature",))
def pew(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.45), (2.2, 0.42, 0.05), "wood")
    bx(mb, M, (0, 0.22, 0.75), (2.2, 0.05, 0.55), "wood", rx=-0.1)
    bx(mb, M, (0, -0.3, 0.12), (2.1, 0.2, 0.05), "fabric2")              # kneeler of the pew in front
    for sx in (-1.12, 1.12):
        prism(mb, M, (sx, 0, 0), [(-0.25, 0), (0.25, 0), (0.28, 0.95), (0.18, 1.02), (0.0, 0.98), (-0.25, 0.5)], 0.06, "wood2", rz=math.pi / 2)
    bx(mb, M, (0, 0.24, 0.4), (2.2, 0.03, 0.25), "wood2")


@fxprop("prie_dieu", "floor", (0.6, 0.6, 1.0), eras=OLD | MID, rooms=("monastery", "chapel", "cell", "temple"))
def prie_dieu(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, -0.15, 0.08), (0.55, 0.3, 0.16), "fabric2")
    for sx in (-0.25, 0.25):
        bx(mb, M, (sx, 0.1, 0.45), (0.05, 0.05, 0.9), "wood2")
    bx(mb, M, (0, 0.1, 0.72), (0.55, 0.06, 0.4), "wood")
    bx(mb, M, (0, 0.05, 0.95), (0.6, 0.32, 0.04), "wood", rx=0.3)
    book(mb, M, (0, 0.04, 0.99), 0.2, 0.15, 0.03, "fabric", rx=0.3)


@fxprop("wall_shrine", "wall", (0.5, 0.22, 0.75), eras=OLD | MID, rooms=SACRED + ("cell", "domestic", "keep"))
def wall_shrine(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    prism(mb, M, (0, 0.08, -0.35), arch_pts(0.5, 0.72, 0.5, seg=8, pointed=True), 0.08, "trim")
    prism(mb, M, (0, 0.03, -0.3), arch_pts(0.36, 0.58, 0.42, seg=8, pointed=True), 0.04, rng.choice(("accent", "fabric", "wall2")))
    bx(mb, M, (0, -0.03, -0.33), (0.52, 0.18, 0.04), "trim")
    lathe(mb, M, (0, 0.0, -0.3), [(0.06, 0), (0.05, 0.18), (0.035, 0.28), (0, 0.3)], "glass2", seg=8)     # little icon figure
    sp(mb, M, (0, 0.0, 0.03), 0.04, "glass2", sub=1)
    cyy(mb, M, (0, 0.02, 0.06), 0.07, 0.01, "glass2", seg=12)                                            # halo
    candle(mb, M, (0.17, -0.06, -0.31), 0.08, 0.018)


@fxprop("stained_glass", "wall", (1.0, 0.1, 2.0), eras=OLD | MID, rooms=SACRED + ("throne", "castle", "manor"))
def stained_glass(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    W, H = 0.9, 1.9
    prism(mb, M, (0, 0.03, 0), arch_pts(W + 0.14, H + 0.1, H * 0.7, seg=10, pointed=True), 0.06, "stone")
    keys = ("fabric", "accent", "glass", "glass2", "lampshade", "paper")
    nz, nx = 9, 3
    for j in range(nz):
        for i in range(nx):
            zz = 0.1 + j * (H * 0.78) / nz
            u = -W / 2 + (i + 0.5) * W / nx
            if zz > H * 0.7 and abs(u) > W * 0.3:
                continue
            bx(mb, M, (u, -0.0, zz + 0.08), (W / nx - 0.03, 0.02, H * 0.78 / nz - 0.03), rng.choice(keys))
    cyy(mb, M, (0, -0.005, H * 0.82), W * 0.22, 0.02, "glass2", seg=12)
    for i in range(6):
        a = i / 6 * math.tau
        bx(mb, M, (0, -0.012, H * 0.82), (W * 0.42, 0.012, 0.018), "dark", ry=a)


# ----------------------------------------------------------------------------- horror dressing
@fxprop("cobweb", "wall", (1.2, 0.05, 0.95), eras=None, rooms=HORROR + ("attic", "abandoned", "tomb"))
def cobweb(mb, x, y, z, rot, rng, era):
    """Web fanned in the wall plane: top edge at z+0.45, hub below; features rotate it across corners."""
    M = M0(x, y, z, rot)
    hub = (rng.uniform(-0.08, 0.08), 0, 0.1)
    anchors = [(-0.6, 0, 0.45), (-0.3, 0, 0.47), (0.0, 0, 0.47), (0.3, 0, 0.47), (0.6, 0, 0.45),
               (0.35, 0, -0.15), (0.0, 0, -0.45), (-0.35, 0, -0.15)]
    for a in anchors:
        strut(mb, M, hub, a, 0.004, "paper")
    for t in (0.25, 0.45, 0.65, 0.85):
        pts = [Vector(hub).lerp(Vector(a), t + rng.uniform(-0.04, 0.04)) for a in anchors]
        for p, q in zip(pts, pts[1:] + pts[:1]):
            strut(mb, M, p, q, 0.003, "paper")
    for k in range(3):                                      # trailing strands
        u = rng.uniform(-0.5, 0.5)
        strut(mb, M, (u, 0, 0.45), (u + rng.uniform(-0.05, 0.05), 0, rng.uniform(-0.1, 0.25)), 0.003, "paper")


def bone(mb, M, a, b, r=0.018):
    strut(mb, M, a, b, r, "paper", seg=6)
    for p in (a, b):
        sp(mb, M, p, r * 1.6, "paper", sub=0)


@fxprop("skull", "surface", (0.15, 0.2, 0.15), eras=None, rooms=HORROR + ("wizard", "alchemy", "witch", "pirate", "tomb", "plague", "lab"))
def skull(mb, x, y, z, rot, rng, era):
    skull_shape(mb, M0(x, y, z, rot), rng.uniform(0.9, 1.15))


@fxprop("skull_pile", "floor", (1.1, 1.0, 0.7), eras=None, rooms=("crypt", "dungeon", "ritual", "catacomb", "tomb", "dragon"))
def skull_pile(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for layer, (n, r, zz) in enumerate(((7, 0.36, 0.0), (5, 0.22, 0.11), (2, 0.08, 0.22))):
        for i in range(n):
            a = i / n * math.tau + layer
            skull_shape(mb, sub(M, (math.cos(a) * r, math.sin(a) * r, zz), rz=a + math.pi / 2 + rng.uniform(-0.5, 0.5),
                                rx=rng.uniform(-0.2, 0.2)), rng.uniform(1.1, 1.4))
    for k in range(8):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.3, 0.55)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0.03))
        d = Vector((math.cos(a + 1.6), math.sin(a + 1.6), 0)) * rng.uniform(0.15, 0.25)
        bone(mb, M, p - d, p + d)


@fxprop("bone_scatter", "floor", (1.4, 1.0, 0.1), eras=None, rooms=("crypt", "dungeon", "cave", "lair", "ritual", "wasteland", "catacomb"))
def bone_scatter(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for k in range(rng.randint(5, 9)):
        p = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4), 0.025))
        a = rng.uniform(0, math.tau)
        d = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.1, 0.22)
        bone(mb, M, p - d, p + d, rng.uniform(0.012, 0.022))
    if rng.random() < 0.7:
        skull_shape(mb, sub(M, (rng.uniform(-0.3, 0.3), rng.uniform(-0.2, 0.2), 0), rz=rng.uniform(0, 6), ry=rng.uniform(-0.6, 0.6)), 1.0)
    for k in range(4):                                       # ribs arc
        ring(mb, sub(M, (0.3, 0.1 + k * 0.05, 0.02), ry=math.pi / 2), (0, 0, 0), 0.1, 0.008, "paper", seg=8, mseg=3, arc=math.pi)


def chain(mb, M, a, b, link=0.06, key="metal2"):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    n = max(1, int(L / (link * 0.8)))
    d = (b - a).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d).to_matrix().to_4x4()
    from mathutils import Matrix
    for i in range(n):
        p = a + d * (i + 0.5) * L / n
        m = M @ Matrix.Translation(p) @ q
        ring(mb, sub(m, (0, 0, 0), rx=math.pi / 2, rz=(i % 2) * math.pi / 2), (0, 0, 0), link * 0.45, link * 0.12, key, seg=8, mseg=3)


@fxprop("chains_hanging", "hanging", (0.7, 0.3, 2.0), eras=PRE | NOW, rooms=("fx_feature",))
def chains_hanging(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for i in range(rng.randint(2, 3)):
        u = -0.25 + i * 0.25
        L = rng.uniform(0.9, 1.8)
        chain(mb, M, (u, 0, 0), (u + rng.uniform(-0.05, 0.05), 0, -L))
        if rng.random() < 0.5:
            ring(mb, sub(M, (u, 0, -L - 0.06), rx=math.pi / 2), (0, 0, 0), 0.07, 0.016, "metal2", seg=10, mseg=4)     # shackle
        else:
            polyline(mb, M, [(u, 0, -L), (u, 0, -L - 0.12), (u + 0.06, 0, -L - 0.18), (u + 0.1, 0, -L - 0.12)], 0.012, "metal2")


@fxprop("wall_shackles", "wall", (0.9, 0.2, 0.9), eras=PRE, rooms=("dungeon", "crypt", "ritual", "cell"))
def wall_shackles(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.32, 0.32):
        bx(mb, M, (sx, 0.08, 0.35), (0.1, 0.04, 0.1), "metal2")
        ring(mb, sub(M, (sx, 0.04, 0.3), rx=0.0), (0, 0, 0), 0.04, 0.01, "metal2", seg=8, mseg=3, rx=math.pi / 2)
        end = (sx + rng.uniform(-0.1, 0.1) * (1 if sx > 0 else -1), -0.05, rng.uniform(-0.35, -0.1))
        chain(mb, M, (sx, 0.03, 0.27), end, 0.05)
        ring(mb, M, (end[0], end[1], end[2] - 0.05), 0.06, 0.015, "metal2", seg=10, mseg=4, rx=math.pi / 2 - 0.3)


@fxprop("wall_stain", "wall", (1.3, 0.03, 1.4), eras=None, rooms=HORROR + ("abandoned", "basement", "asylum", "slum", "shelter"))
def wall_stain(mb, x, y, z, rot, rng, era):
    """Bloodless, ominous damp stain with drips (sits flush on the wall plane, centred on z)."""
    M = M0(x, y, z, rot)
    for k in range(rng.randint(4, 7)):
        cyy(mb, M, (rng.uniform(-0.35, 0.35), 0.0 - k * 0.0015, rng.uniform(0.0, 0.35)), rng.uniform(0.12, 0.32), 0.004,
            rng.choice(("dark", "wood2", "wall2", "dark")), seg=9)
    for k in range(rng.randint(3, 6)):
        u = rng.uniform(-0.35, 0.35)
        L = rng.uniform(0.25, 0.75)
        bx(mb, M, (u, -0.012, 0.05 - L / 2), (rng.uniform(0.015, 0.035), 0.004, L), "dark")
        sp(mb, M, (u, -0.012, 0.05 - L), 0.02, "dark", sub=0, sc=(1, 0.2, 1.3))


@fxprop("floor_stain", "floor", (1.6, 1.3, 0.01), eras=None, rooms=HORROR + ("abandoned", "basement", "slum", "shelter", "alley"))
def floor_stain(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z + 0.004, rot)
    for k in range(rng.randint(4, 8)):
        cy(mb, M, (rng.uniform(-0.5, 0.5), rng.uniform(-0.35, 0.35), k * 0.0012), rng.uniform(0.1, 0.38), 0.003,
           rng.choice(("dark", "wood2", "dark")), seg=9)
    for k in range(rng.randint(2, 5)):                       # drag smear
        bx(mb, M, (rng.uniform(-0.2, 0.6), rng.uniform(-0.3, 0.3), 0.009), (rng.uniform(0.3, 0.8), rng.uniform(0.03, 0.08), 0.002), "dark",
           rz=rng.uniform(-0.4, 0.4))


@fxprop("boarded_window", "wall", (1.4, 0.15, 1.5), eras=PRE | NOW | {"post_apocalyptic"}, rooms=("haunted", "abandoned", "shelter", "slum"))
def boarded_window(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    W, H = 1.25, 1.35
    bx(mb, M, (0, 0.05, H / 2), (W, 0.02, H), "dark")
    for sx in (-1, 1):
        bx(mb, M, (sx * W / 2, 0.0, H / 2), (0.08, 0.1, H + 0.1), "trim")
    for zz in (0.0, H):
        bx(mb, M, (0, 0.0, zz), (W + 0.16, 0.12, 0.08), "trim")
    n = rng.randint(4, 6)
    for i in range(n):
        zz = 0.15 + i * (H - 0.3) / max(1, n - 1) + rng.uniform(-0.05, 0.05)
        ang = rng.uniform(-0.25, 0.25)
        L = W + rng.uniform(0.1, 0.35)
        bx(mb, M, (rng.uniform(-0.05, 0.05), -0.04 - 0.012 * i, zz), (L, 0.025, rng.uniform(0.11, 0.17)), rng.choice(("wood", "wood2")), ry=ang)
        for sx in (-1, 1):
            bx(mb, M, (sx * (L / 2 - 0.08) * math.cos(ang), -0.06 - 0.012 * i, zz - sx * (L / 2 - 0.08) * math.sin(ang)), (0.015, 0.012, 0.015), "dark")
    if rng.random() < 0.6:
        bx(mb, M, (0, -0.12, H * 0.5), (W * 1.2, 0.025, 0.15), "wood2", ry=0.8)


@fxprop("broken_chair", "floor", (0.7, 0.9, 0.55), eras=None, rooms=HORROR + ("abandoned", "tavern", "shelter", "saloon"))
def broken_chair(mb, x, y, z, rot, rng, era):
    """A chair knocked over on its back, one leg snapped off beside it."""
    M = M0(x, y, z, rot)
    k = "metal" if era in FUT else "wood"
    c = sub(M, (0, 0, 0.24), rx=math.pi / 2 + 0.1)
    bx(mb, c, (0, 0, 0.45), (0.44, 0.44, 0.05), k)
    for sx, sy in ((-0.19, -0.19), (0.19, -0.19), (-0.19, 0.19)):
        bx(mb, c, (sx, sy, 0.22), (0.04, 0.04, 0.44), k)
    bx(mb, c, (0.19, 0.19, 0.38), (0.04, 0.04, 0.12), k)
    bx(mb, c, (0, 0.2, 0.72), (0.44, 0.04, 0.5), k)
    bx(mb, M, (0.45, -0.2, 0.02), (0.04, 0.32, 0.04), k, rz=0.6)


@fxprop("broken_table", "floor", (1.3, 1.0, 0.8), eras=None, rooms=HORROR + ("abandoned", "tavern", "shelter", "saloon"))
def broken_table(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    k = "metal" if era in FUT else "wood"
    top = sub(M, (0, 0, 0.38), ry=0.55)
    bx(mb, top, (0, 0, 0), (1.1, 0.8, 0.05), k)
    for sy in (-0.33, 0.33):
        bx(mb, top, (0.48, sy, -0.36), (0.06, 0.06, 0.72), k)
    bx(mb, M, (-0.4, 0.45, 0.03), (0.72, 0.06, 0.06), k, rz=0.4)
    bx(mb, M, (-0.6, -0.3, 0.03), (0.4, 0.06, 0.06), k, rz=-0.9)
    for i in range(4):
        bx(mb, M, (rng.uniform(-0.6, 0.3), rng.uniform(-0.4, 0.4), 0.01), (0.12, 0.03, 0.02), "wood2", rz=rng.uniform(0, 6))


@fxprop("doll", "surface", (0.16, 0.14, 0.3), eras=PRE | NOW, rooms=("haunted", "nursery", "kids", "attic", "seance", "abandoned"))
def doll(mb, x, y, z, rot, rng, era):
    """A porcelain doll sitting, slightly slumped. One eye missing, sometimes."""
    M = M0(x, y, z, rot + rng.uniform(-0.4, 0.4))
    lathe(mb, M, (0, 0, 0), [(0.0, 0.0), (0.08, 0.0), (0.075, 0.03), (0.045, 0.12), (0.03, 0.16), (0, 0.16)], rng.choice(("fabric", "accent", "paper")), seg=10)
    m = sub(M, (0, 0, 0.16), rx=0.18, ry=rng.uniform(-0.25, 0.25))
    sp(mb, m, (0, 0, 0.06), 0.055, "paper", sub=1)
    sp(mb, m, (0, 0.012, 0.075), 0.058, "wood2", sub=1, sc=(1.05, 1.0, 0.9))          # hair cap behind
    for sx in (-1, 1):
        if not (sx > 0 and rng.random() < 0.4):
            sp(mb, m, (sx * 0.02, -0.05, 0.065), 0.009, "dark", sub=0)
    for sx in (-1, 1):
        strut(mb, M, (sx * 0.04, 0, 0.14), (sx * 0.07, -0.04, 0.06), 0.012, "paper", seg=6)
        strut(mb, M, (sx * 0.03, -0.02, 0.02), (sx * 0.04, -0.13, 0.015), 0.014, "paper", seg=6)


@fxprop("ritual_candles", "floor", (2.3, 2.3, 0.3), eras=None, rooms=("fx_feature",))
def ritual_candles(mb, x, y, z, rot, rng, era):
    """Chalk circle with a seven-pointed sigil, candles around the rim, a dark stain at the centre."""
    M = M0(x, y, z + 0.004, rot)
    R = 1.0
    ring(mb, M, (0, 0, 0), R, 0.012, "paper", seg=32, mseg=3, rz=0.0)
    ring(mb, M, (0, 0, 0), R * 0.84, 0.008, "paper", seg=32, mseg=3)
    pts = [(math.cos(i / 7 * math.tau) * R * 0.84, math.sin(i / 7 * math.tau) * R * 0.84, 0.004) for i in range(7)]
    for i in range(7):
        strut(mb, M, pts[i], pts[(i + 3) % 7], 0.008, "paper")
    for i in range(7):                                        # rune marks in the band
        a = (i + 0.5) / 7 * math.tau
        bx(mb, M, (math.cos(a) * R * 0.92, math.sin(a) * R * 0.92, 0.004), (0.06, 0.012, 0.004), "paper", rz=a + 0.6)
    n = rng.randint(9, 13)
    for i in range(n):
        a = i / n * math.tau + rng.uniform(-0.05, 0.05)
        candle(mb, M, (math.cos(a) * R * 1.08, math.sin(a) * R * 1.08, 0), rng.uniform(0.06, 0.24), rng.uniform(0.02, 0.035),
               lit=rng.random() < 0.85)
        cy(mb, M, (math.cos(a) * R * 1.08, math.sin(a) * R * 1.08, 0.002), 0.05, 0.004, "paper", seg=8)
    cy(mb, M, (0, 0, 0.002), 0.3, 0.004, "dark", seg=10)


@fxprop("candle_cluster", "surface", (0.3, 0.3, 0.25), eras=None, rooms=HORROR + SACRED + ("wizard", "witch", "seance", "cell"))
def candle_cluster(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.004), 0.13, 0.008, "paper", seg=10)
    for k in range(rng.randint(3, 7)):
        a, r = rng.uniform(0, math.tau), rng.uniform(0.0, 0.1)
        candle(mb, M, (math.cos(a) * r, math.sin(a) * r, 0), rng.uniform(0.04, 0.22), rng.uniform(0.015, 0.03), lit=rng.random() < 0.8)


@fxprop("portrait_old", "wall", (0.8, 0.1, 0.98), eras=PRE, rooms=("haunted", "manor", "seance", "castle", "gallery", "parlour"))
def portrait_old(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot + 0.0)
    tilt = rng.uniform(-0.12, 0.12)
    m = sub(M, (0, 0, 0), ry=tilt)
    W, H = rng.uniform(0.55, 0.72), rng.uniform(0.75, 0.95)
    bx(mb, m, (0, 0.02, 0), (W, 0.06, H), "glass2")
    bx(mb, m, (0, -0.0, 0), (W - 0.1, 0.06, H - 0.1), "trim")
    bx(mb, m, (0, -0.012, 0), (W - 0.16, 0.05, H - 0.16), rng.choice(("dark", "wall2", "fabric2")))
    for sx in (-1, 1):                                       # corner ornaments
        for sz in (-1, 1):
            sp(mb, m, (sx * W / 2, -0.02, sz * H / 2), 0.04, "glass2", sub=0)
    sp(mb, m, (0, -0.04, H * 0.1), 0.1, "wood2", sub=1, sc=(0.8, 0.15, 1.0))        # sitter's head
    prism(mb, m, (0, -0.04, 0), [(-0.22, -H / 2 + 0.08), (0.22, -H / 2 + 0.08), (0.16, -0.08), (0.06, -0.02), (-0.06, -0.02), (-0.16, -0.08)], 0.01, "fabric2")
    for sx in (-1, 1):
        sp(mb, m, (sx * 0.03, -0.055, H * 0.13), 0.011, "paper", sub=0)              # eyes that follow you
    if rng.random() < 0.3:
        strut(mb, m, (-0.15, -0.06, 0.2), (0.12, -0.06, -0.2), 0.008, "dark")        # slash


@fxprop("rocking_chair", "floor", (0.65, 0.95, 1.15), eras=PRE | NOW, rooms=("haunted", "porch", "cabin", "domestic", "nursery", "attic"))
def rocking_chair(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.24, 0.24):
        ring(mb, sub(M, (sx, 0, 0.62), ry=math.pi / 2), (0, 0, 0), 0.62, 0.02, "wood2", seg=10, mseg=3, arc=0.85, rz=math.pi * 1.5 - 0.42)
        for sy in (-0.2, 0.2):
            bx(mb, M, (sx, sy, 0.28), (0.04, 0.04, 0.42), "wood")
        bx(mb, M, (sx, 0.0, 0.65), (0.04, 0.44, 0.04), "wood")
    bx(mb, M, (0, 0, 0.46), (0.5, 0.45, 0.04), "wood")
    for i in range(6):
        bx(mb, M, (-0.2 + i * 0.08, 0.24, 0.8), (0.025, 0.025, 0.65), "wood", rx=-0.15)
    bx(mb, M, (0, 0.28, 1.12), (0.55, 0.06, 0.08), "wood", rx=-0.15)
    if rng.random() < 0.5:
        bx(mb, M, (0.05, 0.1, 0.55), (0.42, 0.4, 0.06), "fabric", rx=-0.4)


@fxprop("sheeted_furniture", "floor", (1.7, 1.0, 1.1), eras=PRE | NOW, rooms=("haunted", "manor", "attic", "abandoned"))
def sheeted_furniture(mb, x, y, z, rot, rng, era):
    """Something tall under a dust sheet (armchair, piano, a shape you'd rather not ask about)."""
    M = M0(x, y, z, rot)
    w, d, h = rng.uniform(0.8, 1.6), rng.uniform(0.6, 0.9), rng.uniform(0.8, 1.15)
    lathe(mb, M, (0, 0, 0), [(0.62, 0.0), (0.58, 0.03), (0.5, h * 0.4), (0.47, h * 0.8), (0.3, h * 0.97), (0, h)], "paper", seg=8,
          rz=math.pi / 8, sc=(w * 0.85, d * 0.85))
    for k in range(5):                                         # drape folds
        a = rng.uniform(0, math.tau)
        bx(mb, M, (math.cos(a) * w * 0.48, math.sin(a) * d * 0.48, h * 0.3), (0.06, 0.06, h * 0.6), "paper", rz=a)
    if rng.random() < 0.5:
        sp(mb, M, (w * 0.25, 0, h * 0.95), 0.25, "paper", sub=1, sc=(1, 1, 0.6))


@fxprop("grandfather_clock", "floor", (0.6, 0.45, 2.2), eras=EARLY | MID, rooms=("haunted", "manor", "parlour", "hall", "study"))
def grandfather_clock(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.3), (0.55, 0.42, 0.6), "wood2")
    bx(mb, M, (0, 0, 1.05), (0.42, 0.34, 0.9), "wood")
    bx(mb, M, (0, -0.172, 1.05), (0.2, 0.01, 0.65), "dark")
    strut(mb, M, (0, -0.18, 1.35), (0.03 * rng.uniform(-1, 1), -0.18, 0.9), 0.006, "glass2")
    cyy(mb, M, (0, -0.185, 0.88), 0.05, 0.012, "glass2", seg=10)
    bx(mb, M, (0, 0, 1.7), (0.55, 0.42, 0.4), "wood2")
    prism(mb, M, (0, 0, 1.9), [(-0.3, 0), (0.3, 0), (0.24, 0.14), (0, 0.25), (-0.24, 0.14)], 0.44, "wood2")
    cyy(mb, M, (0, -0.21, 1.7), 0.15, 0.02, "paper", seg=14)
    strut(mb, M, (0, -0.225, 1.7), (0.0, -0.225, 1.82), 0.006, "dark")
    strut(mb, M, (0, -0.225, 1.7), (0.08, -0.225, 1.68), 0.006, "dark")


@fxprop("mirror_cracked", "wall", (0.75, 0.08, 1.5), eras=PRE | NOW, rooms=("haunted", "manor", "bathroom", "bedroom", "attic", "seance"))
def mirror_cracked(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    prism(mb, M, (0, 0.03, 0.05), arch_pts(0.72, 1.45, 1.1, seg=10), 0.05, "glass2")
    prism(mb, M, (0, 0.0, 0.11), arch_pts(0.58, 1.3, 1.0, seg=10), 0.04, "glass")
    c = Vector((rng.uniform(-0.12, 0.12), -0.025, rng.uniform(0.6, 0.9)))
    for k in range(7):
        a = k / 7 * math.tau + rng.uniform(-0.3, 0.3)
        L = rng.uniform(0.15, 0.4)
        e = c + Vector((math.cos(a) * L, 0, math.sin(a) * L))
        e.x = max(-0.27, min(0.27, e.x))
        strut(mb, M, c, e, 0.004, "dark")
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.36, -0.02, 1.15), 0.04, "glass2", sub=0)


@fxprop("gravestone", "floor", (0.8, 0.35, 1.2), eras=PRE | NOW, rooms=("graveyard", "crypt", "haunted", "churchyard"))
def gravestone(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot + rng.uniform(-0.15, 0.15))
    m = sub(M, (0, 0, 0), rx=rng.uniform(-0.12, 0.12), ry=rng.uniform(-0.1, 0.1))
    bx(mb, m, (0, 0, 0.06), (0.8, 0.35, 0.12), "stone")
    kind = rng.choice(("round", "cross", "pointed"))
    if kind == "round":
        prism(mb, m, (0, 0, 0.1), arch_pts(0.6, 0.95, 0.65, seg=8), 0.14, "stone")
    elif kind == "pointed":
        prism(mb, m, (0, 0, 0.1), [(-0.3, 0), (0.3, 0), (0.3, 0.7), (0, 0.95), (-0.3, 0.7)], 0.14, "stone")
    else:
        bx(mb, m, (0, 0, 0.6), (0.12, 0.12, 1.0), "stone")
        bx(mb, m, (0, 0, 0.82), (0.55, 0.12, 0.12), "stone")
    for k in range(3):
        bx(mb, m, (0, -0.075, 0.35 + k * 0.1), (0.3 - k * 0.06, 0.01, 0.025), "dark")
    sp(mb, m, (rng.uniform(-0.2, 0.2), 0, 0.12), 0.12, "leaf", sub=0, sc=(1.4, 1.3, 0.4))


@fxprop("tattered_curtains", "wall", (1.7, 0.15, 2.5), eras=PRE | NOW, rooms=("haunted", "manor", "seance", "theatre", "abandoned", "parlour"))
def tattered_curtains(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    k = rng.choice(("fabric", "fabric2", "rug"))
    cyx(mb, M, (0, 0.02, 2.4), 0.025, 1.8, "metal2", seg=6)
    for sx in (-1, 1):
        for i in range(5):
            u = sx * (0.85 - i * 0.09)
            L = rng.uniform(1.4, 2.35) if i > 1 else 2.35
            bx(mb, M, (u, -0.02 + (0.025 if i % 2 else 0.0), 2.38 - L / 2), (0.1, 0.03, L), k, ry=rng.uniform(-0.04, 0.04))
    if rng.random() < 0.7:
        bx(mb, M, (0, -0.05, 2.28), (1.75, 0.04, 0.25), k)

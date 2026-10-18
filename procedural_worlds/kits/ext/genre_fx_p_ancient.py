"""genre_fx props: antiquity (Greek / Roman / Egyptian / Han) and medieval world cultures
(Norse, Islamic golden age, Heian / Sengoku Japan)."""
import math
from mathutils import Vector
from ..props import OLD, MID
from .genre_fx_geom import (fxprop, M0, sub, bx, cy, cyx, cyy, sp, lathe, prism, slab, ring, strut, polyline, flat_grid,
                            arch_pts, flame, fire, candle, book, table, surface, ANC, MED, EARLY, PRE)

CLASSIC = ("temple", "ruins", "villa", "forum", "senate", "arena", "museum", "palace", "tomb")


# ----------------------------------------------------------------------------- classical
def amphora_shape(mb, M, s=1.0, key="fabric"):
    prof = [(0, 0), (0.03, 0.02), (0.1, 0.12), (0.17, 0.32), (0.19, 0.48), (0.16, 0.6), (0.07, 0.68), (0.05, 0.8), (0.065, 0.84), (0.0, 0.84)]
    lathe(mb, M, (0, 0, 0), [(r * s, z * s) for r, z in prof], key, seg=12)
    for zz, rr in ((0.5, 0.195), (0.4, 0.19)):
        ring(mb, M, (0, 0, zz * s), rr * s, 0.008 * s, "dark", seg=14, mseg=3)
    for sx in (-1, 1):
        ring(mb, sub(M, (sx * 0.1 * s, 0, 0.71 * s), rx=math.pi / 2), (0, 0, 0), 0.05 * s, 0.012 * s, key, seg=8, mseg=3, arc=math.pi,
             rz=0 if sx > 0 else math.pi)


@fxprop("amphora", "floor", (0.6, 0.6, 0.9), eras=OLD, rooms=CLASSIC + ("storage", "hold", "cellar", "shop", "tavern"))
def amphora(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    n = rng.randint(1, 3)
    for i in range(n):
        a = i / n * math.tau + rng.uniform(0, 1)
        r = 0.0 if n == 1 else 0.17
        tilt = rng.uniform(0.05, 0.25) if n > 1 else 0.0
        amphora_shape(mb, sub(M, (math.cos(a) * r, math.sin(a) * r, 0.0), rx=tilt * math.sin(a), ry=-tilt * math.cos(a)),
                      rng.uniform(0.8, 1.05), rng.choice(("fabric", "fabric", "glass2")))


def column_shape(mb, M, h=3.6, r=0.3, style="doric", key="stone"):
    bx(mb, M, (0, 0, 0.08), (r * 2.6, r * 2.6, 0.16), key)
    ring(mb, M, (0, 0, 0.2), r * 1.05, r * 0.12, key, seg=16, mseg=4)
    lathe(mb, M, (0, 0, 0.2), [(r, 0), (r * 1.03, h * 0.3), (r * 0.95, h - 0.65), (r * 0.9, h - 0.5)], key, seg=16)
    for i in range(8):                                   # flutes, drawn as shallow grooves
        a = i / 8 * math.tau
        bx(mb, M, (math.cos(a) * r * 0.97, math.sin(a) * r * 0.97, h * 0.5 - 0.1), (0.02, 0.02, h - 1.0), "wall2", rz=a)
    if style == "ionic":
        bx(mb, M, (0, 0, h - 0.4), (r * 2.4, r * 1.6, 0.16), key)
        for sx in (-1, 1):
            cyy(mb, M, (sx * r * 1.1, 0, h - 0.43), r * 0.32, r * 1.7, key, seg=10)
    else:
        lathe(mb, M, (0, 0, h - 0.5), [(r * 0.9, 0), (r * 1.3, 0.2), (0, 0.2)], key, seg=16)
    bx(mb, M, (0, 0, h - 0.15), (r * 2.8, r * 2.8, 0.3), key)


@fxprop("column", "floor", (0.9, 0.9, 3.6), eras=OLD | MID, rooms=("fx_feature",))
def column(mb, x, y, z, rot, rng, era):
    column_shape(mb, M0(x, y, z, rot), 3.6, 0.3, rng.choice(("doric", "ionic")))


@fxprop("column_fragment", "floor", (1.8, 1.2, 1.3), eras=OLD, rooms=CLASSIC + ("garden",))
def column_fragment(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    r = 0.3
    bx(mb, M, (0, 0, 0.08), (0.8, 0.8, 0.16), "stone")
    h = rng.uniform(0.7, 1.2)
    lathe(mb, M, (0, 0, 0.16), [(r, 0), (r, h), (r * 0.7, h + 0.12), (r * 0.2, h + 0.02), (0, h + 0.1)], "stone", seg=14)
    for i in range(rng.randint(1, 3)):                    # fallen drums
        cyx(mb, sub(M, (rng.uniform(0.6, 1.0), rng.uniform(-0.5, 0.5), r * 0.95), rz=rng.uniform(-0.8, 0.8)), (0, 0, 0), r * 0.95,
            rng.uniform(0.4, 0.7), "stone", seg=14)
    if rng.random() < 0.6:
        bx(mb, M, (-0.6, 0.4, 0.12), (0.8, 0.8, 0.24), "stone", rz=rng.uniform(0, 1))
    for k in range(4):
        sp(mb, M, (rng.uniform(-0.8, 0.8), rng.uniform(-0.6, 0.6), 0.03), rng.uniform(0.05, 0.1), "stone", sub=0)


@fxprop("scroll_pile", "surface", (0.4, 0.3, 0.15), eras=OLD, rooms=CLASSIC + ("library", "study", "scriptorium", "wizard", "observatory", "palace"))
def scroll_pile(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for i in range(rng.randint(2, 5)):
        L = rng.uniform(0.22, 0.32)
        m = sub(M, (rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08), 0.03 + (0.05 if i > 2 else 0.0)), rz=rng.uniform(-0.6, 0.6))
        cyx(mb, m, (0, 0, 0), 0.028, L, "paper", seg=8)
        for sx in (-1, 1):
            cyx(mb, m, (sx * (L / 2 + 0.01), 0, 0), 0.012, 0.03, "wood2", seg=6)
    bx(mb, M, (0.12, -0.08, 0.003), (0.22, 0.3, 0.006), "paper", rz=0.3)          # one unrolled
    for k in range(4):
        bx(mb, M, (0.12, -0.08 - 0.06 * k + 0.08, 0.0075), (0.14, 0.008, 0.002), "dark", rz=0.3)


@fxprop("sundial", "floor", (0.7, 0.7, 1.15), eras=OLD, rooms=CLASSIC + ("garden", "courtyard", "observatory"))
def sundial(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.3, 0), (0.3, 0.1), (0.16, 0.18), (0.12, 0.5), (0.15, 0.85), (0.3, 0.95), (0.0, 0.95)], "stone", seg=12)
    cy(mb, M, (0, 0, 0.97), 0.3, 0.04, "metal", seg=16)
    for i in range(12):
        a = i / 12 * math.pi + math.pi
        bx(mb, M, (math.cos(a) * 0.24, math.sin(a) * 0.24, 0.993), (0.05, 0.01, 0.006), "dark", rz=a)
    prism(mb, M, (0, 0, 0.99), [(-0.2, 0), (0.15, 0), (-0.2, 0.18)], 0.015, "metal2")


@fxprop("oil_lamp", "surface", (0.2, 0.1, 0.12), eras=OLD, rooms=CLASSIC + ("tomb", "crypt", "temple", "monastery", "library", "any_old"))
def oil_lamp(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.03, 0), (0.06, 0.015), (0.065, 0.03), (0.04, 0.045), (0.0, 0.05)], rng.choice(("fabric", "glass2")), seg=10)
    bx(mb, M, (0.075, 0, 0.03), (0.06, 0.03, 0.02), "fabric")
    ring(mb, sub(M, (-0.065, 0, 0.035), rx=math.pi / 2), (0, 0, 0), 0.02, 0.005, "fabric", seg=8, mseg=3, arc=math.pi)
    flame(mb, M, (0.1, 0, 0.038), 1.2)


@fxprop("mosaic_patch", "floor", (2.4, 2.4, 0.02), eras=ANC, rooms=CLASSIC + ("bath",))
def mosaic_patch(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z + 0.006, rot)
    n = 16
    pal = ("floor_a", "accent", "fabric", "paper", "dark", "wall2")
    a, b, c = rng.sample(pal, 3)
    motif = rng.choice(("wave", "rings", "diamond"))
    def key(i, j):
        e = min(i, j, n - 1 - i, n - 1 - j)
        if e == 0:
            return "dark"
        if e == 1:
            return a if (i + j) % 2 else b
        u, v = i - n / 2 + 0.5, j - n / 2 + 0.5
        if motif == "rings":
            return c if int(math.hypot(u, v)) % 3 == 0 else "paper"
        if motif == "diamond":
            return c if (abs(u) + abs(v)) % 4 < 1.5 else "paper"
        return c if (j + int(2 * math.sin(i * 0.8))) % 4 == 0 else "paper"
    flat_grid(mb, M, -1.1, -1.1, 1.1, 1.1, n, n, key, z=0.0, jitter=0.012, rng=rng)


@fxprop("idol", "floor", (0.7, 0.7, 1.4), eras=OLD, rooms=("temple", "jungle_temple", "tomb", "ritual", "shrine", "fx_feature"))
def idol(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    gold = rng.random() < 0.5
    k = "glass2" if gold else "stone"
    bx(mb, M, (0, 0, 0.2), (0.6, 0.6, 0.4), "stone")
    bx(mb, M, (0, 0, 0.43), (0.66, 0.66, 0.06), "stone")
    lathe(mb, M, (0, 0, 0.46), [(0.24, 0), (0.25, 0.15), (0.2, 0.42), (0.12, 0.5), (0, 0.5)], k, seg=8)
    sp(mb, M, (0, -0.02, 1.08), 0.2, k, sub=1, sc=(1.1, 0.9, 1.0))
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.08, -0.19, 1.1), 0.045, "accent" if gold else "glass2", sub=1)
        bx(mb, M, (sx * 0.2, -0.12, 0.72), (0.08, 0.2, 0.08), k)                  # hands on knees
        sp(mb, M, (sx * 0.14, -0.22, 0.55), 0.09, k, sub=1)
    bx(mb, M, (0, -0.18, 0.99), (0.14, 0.03, 0.03), "dark")
    prism(mb, M, (0, 0, 1.18), [(-0.26, 0), (0.26, 0), (0.18, 0.22), (0, 0.3), (-0.18, 0.22)], 0.08, k)


@fxprop("obelisk", "floor", (0.9, 0.9, 3.4), eras=ANC, rooms=("fx_feature", "temple", "tomb", "forum"))
def obelisk(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.15), (0.9, 0.9, 0.3), "stone")
    lathe(mb, M, (0, 0, 0.3), [(0.32, 0), (0.22, 2.8), (0.0, 3.1)], "stone", seg=4, rz=math.pi / 4)
    for i in range(10):
        bx(mb, M, (rng.uniform(-0.1, 0.1), -0.25 + i * 0.006, 0.6 + i * 0.22), (0.08, 0.01, 0.08), "dark")
    lathe(mb, M, (0, 0, 2.8), [(0.23, 0.0), (0.0, 0.32)], "glass2", seg=4, rz=math.pi / 4)


@fxprop("senate_bench", "floor", (3.0, 1.8, 1.3), eras=ANC, rooms=("fx_feature",))
def senate_bench(mb, x, y, z, rot, rng, era):
    """Three marble tiers of benches (faces local -Y)."""
    M = M0(x, y, z, rot)
    for t in range(3):
        y0 = t * 0.6
        bx(mb, M, (0, y0 + 0.3, t * 0.4 + 0.2), (3.0, 0.6, 0.4 * (t + 1)), "stone")
        bx(mb, M, (0, y0 + 0.12, t * 0.4 + 0.42 + 0.0), (2.9, 0.3, 0.05), "fabric" if t == 0 else "stone")
        bx(mb, M, (0, y0 + 0.02, t * 0.4 + 0.22), (3.0, 0.04, 0.05), "trim")
    for sx in (-1.52, 1.52):
        prism(mb, M, (sx, 0, 0), [(-0.0, 0), (1.8, 0), (1.8, 1.3), (1.2, 1.3), (0.0, 0.5)], 0.06, "stone", rz=-math.pi / 2)


@fxprop("arena_gate", "wall", (2.6, 0.5, 3.4), eras=ANC | MED, rooms=("fx_feature",))
def arena_gate(mb, x, y, z, rot, rng, era):
    """Stone arch with a raised iron portcullis (back at +Y)."""
    M = M0(x, y, z, rot)
    for sx in (-1, 1):
        bx(mb, M, (sx * 1.1, 0.1, 1.3), (0.5, 0.5, 2.6), "stone")
    prism(mb, M, (0, 0.1, 0), [(-1.35, 2.6), (1.35, 2.6), (1.35, 3.4), (-1.35, 3.4)], 0.5, "stone")
    bx(mb, M, (0, 0.34, 1.3), (1.7, 0.02, 2.6), "dark")
    lift = rng.uniform(0.3, 1.2)
    for i in range(8):
        bx(mb, M, (-0.75 + i * 0.214, 0.15, 1.3 + lift), (0.04, 0.04, 2.5), "metal2")
    for j in range(5):
        bx(mb, M, (0, 0.15, 0.3 + lift + j * 0.5), (1.65, 0.04, 0.04), "metal2")
    for i in range(8):
        cy(mb, M, (-0.75 + i * 0.214, 0.15, 0.03 + lift), 0.02, 0.06, "metal2", seg=4, r2=0.0, rx=math.pi)
    for sx in (-1.5, 1.5):
        bx(mb, M, (sx, -0.05, 1.8), (0.08, 0.15, 0.3), "metal2")


@fxprop("hieroglyph_slab", "wall", (1.6, 0.12, 2.2), eras=ANC, rooms=("tomb", "temple", "fx_feature"))
def hieroglyph_slab(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.04, 1.1), (1.6, 0.08, 2.2), "wall")
    bx(mb, M, (0, 0.0, 2.1), (1.6, 0.04, 0.14), "accent")
    bx(mb, M, (0, 0.0, 0.08), (1.6, 0.04, 0.14), "accent")
    for col in range(5):
        u = -0.6 + col * 0.3
        bx(mb, M, (u + 0.15, 0.0, 1.1), (0.012, 0.02, 1.8), "trim")
        zz = 1.9
        while zz > 0.3:
            g = rng.random()
            if g < 0.3:
                sp(mb, M, (u, -0.005, zz), 0.045, rng.choice(("dark", "fabric", "accent")), sub=0, sc=(1, 0.2, 1))
            elif g < 0.55:
                bx(mb, M, (u, -0.005, zz), (0.12, 0.012, 0.03), rng.choice(("dark", "trim")))
            elif g < 0.8:
                prism(mb, M, (u, -0.005, zz - 0.04), [(-0.05, 0), (0.05, 0), (0, 0.09)], 0.012, rng.choice(("dark", "fabric")))
            else:                                          # eye glyph
                sp(mb, M, (u, -0.005, zz), 0.05, "paper", sub=0, sc=(1.3, 0.2, 0.6))
                sp(mb, M, (u, -0.012, zz), 0.02, "dark", sub=0)
            zz -= rng.uniform(0.13, 0.2)
    sp(mb, M, (0.55, -0.02, 1.6), 0.18, "glass2", sub=1, sc=(1, 0.15, 1))           # sun disc


@fxprop("sarcophagus_egypt", "floor", (0.9, 2.2, 1.0), eras=ANC, rooms=("tomb", "museum", "fx_feature"))
def sarcophagus_egypt(mb, x, y, z, rot, rng, era):
    """Anthropoid coffin lying on a stone bier, head toward -Y."""
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.2), (1.0, 2.3, 0.4), "stone")
    m = sub(M, (0, 0, 0.4), rx=-math.pi / 2)
    prof = [(0.0, -1.0), (0.2, -0.98), (0.26, -0.6), (0.33, -0.1), (0.36, 0.35), (0.3, 0.6), (0.24, 0.72), (0.28, 0.9), (0.2, 1.05), (0, 1.1)]
    lathe(mb, sub(m, (0, -0.2, 0)), (0, 0, 0), prof, "glass2", seg=12, sc=(1.0, 0.65))
    sp(mb, M, (0, -0.85, 0.62), 0.17, "accent", sub=1, sc=(1.25, 0.7, 0.9))          # striped headdress
    sp(mb, M, (0, -0.95, 0.62), 0.12, "glass2", sub=1, sc=(1, 0.6, 1))               # face
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.04, -1.04, 0.66), 0.018, "dark", sub=0)
        strut(mb, M, (sx * 0.2, -0.5, 0.62), (-sx * 0.05, -0.25, 0.66), 0.035, "accent")   # crossed arms
    for k in range(5):
        bx(mb, M, (0, -0.2 + k * 0.22, 0.6 - k * 0.012), (0.5 - k * 0.04, 0.05, 0.03), "accent")
    bx(mb, M, (0, -0.92, 0.47), (0.05, 0.05, 0.12), "glass2")


@fxprop("canopic_jars", "surface", (0.4, 0.15, 0.3), eras=ANC, rooms=("tomb", "museum", "temple"))
def canopic_jars(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for i in range(4):
        u = -0.15 + i * 0.1
        lathe(mb, M, (u, 0, 0), [(0.03, 0), (0.045, 0.06), (0.04, 0.16), (0.02, 0.18), (0, 0.18)], "stone", seg=8)
        sp(mb, M, (u, 0, 0.21), 0.035, rng.choice(("glass2", "accent", "stone")), sub=1, sc=(1, 1, 1.1))


@fxprop("ding_vessel", "floor", (0.8, 0.8, 1.0), eras=ANC | MED, rooms=("palace", "temple", "shrine", "fx_feature"))
def ding_vessel(mb, x, y, z, rot, rng, era):
    """Han bronze ritual cauldron: round/square body on legs, two upright handles."""
    M = M0(x, y, z, rot)
    k = "accent"                                    # verdigris bronze in antiquity palettes
    square = rng.random() < 0.4
    if square:
        bx(mb, M, (0, 0, 0.55), (0.6, 0.6, 0.4), k)
        bx(mb, M, (0, 0, 0.76), (0.66, 0.66, 0.04), "glass2")
        for sx in (-1, 1):
            for sy in (-1, 1):
                cy(mb, M, (sx * 0.24, sy * 0.24, 0.18), 0.04, 0.36, k, seg=8)
    else:
        lathe(mb, M, (0, 0, 0.3), [(0, 0), (0.25, 0.03), (0.36, 0.2), (0.34, 0.42), (0.36, 0.46), (0.0, 0.46)], k, seg=12)
        for i in range(3):
            a = i / 3 * math.tau
            cy(mb, M, (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.17), 0.05, 0.36, k, seg=8, r2=0.035)
    for zz in (0.5, 0.62):
        if square:
            bx(mb, M, (0, 0, zz), (0.62, 0.62, 0.03), "glass2")
        else:
            ring(mb, M, (0, 0, zz), 0.355, 0.012, "glass2", seg=14, mseg=3)
    for sx in (-1, 1):
        prism(mb, M, (sx * 0.22, 0, 0.78), [(-0.06, 0), (0.06, 0), (0.06, 0.18), (-0.06, 0.18)], 0.03, k, rz=math.pi / 2)
        bx(mb, M, (sx * 0.22, 0, 0.9), (0.04, 0.03, 0.06), "dark")


@fxprop("folding_screen", "floor", (2.0, 0.6, 1.8), eras=OLD | MID, rooms=("palace", "shrine", "keep", "parlour", "dojo", "boudoir"))
def folding_screen(mb, x, y, z, rot, rng, era):
    """Byobu / Chinese palace screen: zig-zag panels with a painted landscape."""
    M = M0(x, y, z, rot)
    n = rng.choice((4, 6))
    w = 2.0 / n
    h = rng.uniform(1.5, 1.8)
    sky = rng.choice(("paper", "glass2"))
    for i in range(n):
        ang = 0.35 if i % 2 else -0.35
        u = -1.0 + (i + 0.5) * w
        m = sub(M, (u, 0.0, 0), rz=ang)
        bx(mb, m, (0, 0, h / 2 + 0.05), (w * 0.95, 0.03, h), "trim")
        bx(mb, m, (0, -0.012, h / 2 + 0.06), (w * 0.82, 0.02, h - 0.14), sky)
        bx(mb, m, (0, -0.024, 0.45 + 0.1 * math.sin(i * 1.3)), (w * 0.8, 0.012, 0.25), "leaf")       # hills
        if i % 2 == 0:
            strut(mb, m, (-w * 0.3, -0.026, 0.5), (w * 0.1, -0.026, h * 0.8), 0.012, "dark")        # pine / branch
            sp(mb, m, (w * 0.1, -0.03, h * 0.8), 0.12, "leaf", sub=0, sc=(1.4, 0.1, 0.5))
        if i == n - 2:
            sp(mb, m, (0.0, -0.03, h * 0.82), 0.09, "fabric", sub=1, sc=(1, 0.1, 1))                # red sun


@fxprop("lattice_screen", "wall", (1.4, 0.1, 2.2), eras=OLD | MID, rooms=("palace", "observatory", "harem", "court", "shrine"))
def lattice_screen(mb, x, y, z, rot, rng, era):
    """Mashrabiya / shoji style lattice panel against the wall."""
    M = M0(x, y, z, rot)
    W, H = 1.3, 2.1
    bx(mb, M, (0, 0.03, H / 2), (W, 0.02, H), rng.choice(("paper", "glass2")))
    bx(mb, M, (0, 0.0, H / 2), (W + 0.1, 0.07, 0.07), "wood2")
    for sx in (-1, 1):
        bx(mb, M, (sx * W / 2, 0, H / 2), (0.07, 0.07, H), "wood2")
    for zz in (0.03, H):
        bx(mb, M, (0, 0, zz), (W + 0.1, 0.07, 0.07), "wood2")
    diag = rng.random() < 0.5
    for i in range(1, 6):
        bx(mb, M, (-W / 2 + i * W / 6, 0.0, H / 2), (0.025, 0.04, H), "wood2")
    for j in range(1, 9):
        bx(mb, M, (0, 0.0, j * H / 9), (W, 0.04, 0.025), "wood2")
    if diag:
        for k in range(-3, 4):
            bx(mb, M, (k * 0.2, -0.01, H * 0.5), (0.02, 0.03, H * 0.9), "wood2", ry=0.5)
            bx(mb, M, (k * 0.2, -0.01, H * 0.5), (0.02, 0.03, H * 0.9), "wood2", ry=-0.5)


@fxprop("paper_lantern", "floor", (0.45, 0.45, 1.0), eras=OLD | MID, rooms=("shrine", "palace", "keep", "teahouse", "dojo"))
def paper_lantern(mb, x, y, z, rot, rng, era):
    """Andon floor lantern: wooden frame around a glowing paper shade."""
    M = M0(x, y, z, rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx(mb, M, (sx * 0.17, sy * 0.17, 0.45), (0.035, 0.035, 0.9), "wood2")
    bx(mb, M, (0, 0, 0.55), (0.3, 0.3, 0.55), "lampshade")
    for zz in (0.25, 0.85, 0.92):
        bx(mb, M, (0, 0, zz), (0.38, 0.38, 0.03), "wood2")
    flame(mb, M, (0, 0, 0.5), 1.4)


@fxprop("chochin", "hanging", (0.4, 0.4, 0.9), eras=OLD | MID, rooms=("fx_feature",))
def chochin(mb, x, y, z, rot, rng, era):
    """Hanging round paper lantern (red or cream) with black caps."""
    M = M0(x, y, z, rot)
    drop = rng.uniform(0.15, 0.4)
    strut(mb, M, (0, 0, 0), (0, 0, -drop), 0.006, "dark")
    zc = -drop - 0.26
    cy(mb, M, (0, 0, -drop - 0.03), 0.08, 0.06, "dark", seg=10)
    sp(mb, M, (0, 0, zc), 0.2, rng.choice(("lampshade", "fabric")), sub=1, sc=(1, 1, 1.25))
    for k in range(5):
        ring(mb, M, (0, 0, zc - 0.18 + k * 0.09), 0.2 * math.sqrt(max(0.05, 1 - ((k - 2) / 2.6) ** 2)), 0.004, "dark", seg=12, mseg=3)
    cy(mb, M, (0, 0, zc - 0.27), 0.08, 0.06, "dark", seg=10)


@fxprop("shrine_altar", "floor", (1.4, 0.8, 1.6), eras=OLD | MID, rooms=("shrine", "keep", "dojo", "temple"))
def shrine_altar(mb, x, y, z, rot, rng, era):
    """Shinto / Buddhist house shrine: raised platform, miniature roofed hall, offerings, mirror."""
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.35), (1.4, 0.8, 0.7), "wood")
    bx(mb, M, (0, 0, 0.72), (1.45, 0.85, 0.05), "wood2")
    bx(mb, M, (0, 0.1, 1.0), (0.7, 0.45, 0.5), "trim")
    bx(mb, M, (0, -0.12, 0.98), (0.4, 0.02, 0.4), "glass2")
    prism(mb, M, (0, 0.1, 1.25), [(-0.55, 0), (0.55, 0), (0.42, 0.12), (0, 0.3), (-0.42, 0.12)], 0.7, "dark")
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.58, -0.25, 0.95), (0.05, 0.05, 0.42), "fabric")                   # tiny torii posts
    bx(mb, M, (0, -0.25, 1.17), (1.3, 0.06, 0.05), "fabric")
    sp(mb, M, (0, -0.06, 1.05), 0.08, "metal", sub=1, sc=(1, 0.2, 1))                        # bronze mirror
    for sx in (-0.45, 0.45):
        cy(mb, M, (sx, -0.25, 0.79), 0.07, 0.1, "paper", seg=8)
        sp(mb, M, (sx, -0.25, 0.88), 0.05, "paper", sub=1)
    for k in range(4):                                                                       # shide paper zig-zags
        prism(mb, M, (-0.45 + k * 0.3, -0.3, 1.0), [(-0.02, 0), (0.02, 0), (0.03, -0.08), (-0.01, -0.1), (0.02, -0.18), (-0.02, -0.18)], 0.01, "paper")


@fxprop("samurai_armour", "floor", (0.9, 0.7, 1.7), eras=EARLY | MED, rooms=("keep", "dojo", "armoury", "fx_feature"))
def samurai_armour(mb, x, y, z, rot, rng, era):
    """O-yoroi on its storage box: laced lames, kabuto with crest, menpo mask."""
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.25), (0.75, 0.55, 0.5), "dark")
    bx(mb, M, (0, -0.28, 0.3), (0.5, 0.02, 0.2), "glass2")
    k = rng.choice(("fabric", "accent", "trim"))
    for i in range(4):
        cy(mb, M, (0, 0, 0.6 + i * 0.07), 0.28 + i * 0.01, 0.07, k if i % 2 else "dark", seg=8)
    lathe(mb, M, (0, 0, 0.88), [(0.24, 0), (0.25, 0.25), (0.2, 0.4), (0, 0.42)], k, seg=8, sc=(1, 0.75))
    for i in range(4):
        bx(mb, M, (0, -0.19, 0.95 + i * 0.08), (0.36, 0.02, 0.03), "glass2")
    for sx in (-1, 1):
        for i in range(4):
            bx(mb, M, (sx * 0.33, 0, 1.25 - i * 0.08), (0.2, 0.3, 0.07), k if i % 2 else "dark", ry=sx * 0.25)
    lathe(mb, M, (0, 0, 1.36), [(0.18, 0), (0.3, 0.02), (0.15, 0.06), (0.15, 0.16), (0.0, 0.24)], "dark", seg=10)
    sp(mb, M, (0, -0.12, 1.36), 0.09, "fabric2", sub=1, sc=(1, 0.6, 0.8))                    # menpo
    for sx in (-1, 1):
        prism(mb, M, (sx * 0.05, -0.12, 1.52), [(0, 0), (0.03, 0), (sx * 0.15 + 0.03, 0.28), (sx * 0.15, 0.28)], 0.015, "glass2")


@fxprop("katana_rack", "surface", (0.6, 0.25, 0.4), eras=EARLY | MED | MID, rooms=("keep", "dojo", "study", "palace"))
def katana_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.02), (0.6, 0.2, 0.04), "dark")
    for sx in (-0.25, 0.25):
        prism(mb, M, (sx, 0, 0.04), [(-0.08, 0), (0.08, 0), (0.06, 0.32), (-0.02, 0.34), (-0.08, 0.2)], 0.04, "dark", rz=math.pi / 2)
    for i in range(rng.randint(1, 3)):
        zz = 0.12 + i * 0.1
        cyx(mb, M, (0, 0, zz), 0.016, 0.78, "dark", seg=6)
        cyx(mb, M, (-0.3, 0, zz), 0.017, 0.2, "fabric" if i % 2 == 0 else "paper", seg=6)
        cyx(mb, M, (-0.19, 0, zz), 0.03, 0.012, "glass2", seg=8)


@fxprop("longship_prow", "floor", (1.2, 3.0, 3.2), eras=MED, rooms=("mead_hall", "dock", "fx_feature"))
def longship_prow(mb, x, y, z, rot, rng, era):
    """Carved dragon prow on a beached bow section (prow rises toward -Y)."""
    M = M0(x, y, z, rot)
    for i in range(6):                                  # clinker strakes narrowing to the stem
        t = i / 5
        y0 = -1.4 * t
        bx(mb, M, (0, y0 + 0.5, 0.25 + i * 0.12), (1.1 - 0.9 * t, 1.6, 0.14), "wood" if i % 2 else "wood2")
    pts = [(0, 0.2), (-0.6, 0.6), (-1.0, 1.4), (-1.15, 2.2), (-1.0, 2.75), (-0.75, 2.95)]
    m = sub(M, (0, -0.9, 0), rz=-math.pi / 2)
    for a, b in zip(pts, pts[1:]):
        strut(mb, m, (a[0], 0, a[1]), (b[0], 0, b[1]), 0.1, "wood2")
    hd = sub(M, (0, -1.65, 2.95))
    sp(mb, hd, (0, 0, 0), 0.16, "wood2", sub=1, sc=(0.8, 1.6, 0.8))
    cy(mb, hd, (0, -0.32, -0.03), 0.07, 0.2, "wood2", seg=6, r2=0.03, rx=math.pi / 2)
    for sx in (-1, 1):
        sp(mb, hd, (sx * 0.1, -0.12, 0.08), 0.03, "fabric", sub=0)
        cy(mb, hd, (sx * 0.06, 0.15, 0.2), 0.03, 0.25, "wood2", seg=4, r2=0.0, rx=-0.6)
    for k in range(3):                                  # round shields along the gunwale
        cyx(mb, M, (0.56, 0.6 - k * 0.45, 0.9), 0.2, 0.03, rng.choice(("fabric", "accent", "paper")), seg=12)
        cyx(mb, M, (-0.56, 0.6 - k * 0.45, 0.9), 0.2, 0.03, rng.choice(("fabric", "accent", "paper")), seg=12)


@fxprop("armillary_sphere", "floor", (0.9, 0.9, 1.7), eras=OLD, rooms=("observatory", "study", "library", "palace", "wizard"))
def armillary_sphere(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for i in range(3):
        a = i / 3 * math.tau
        strut(mb, M, (math.cos(a) * 0.35, math.sin(a) * 0.35, 0), (0, 0, 0.75), 0.03, "wood2")
    cy(mb, M, (0, 0, 0.82), 0.05, 0.2, "glass2", seg=8)
    c = (0, 0, 1.25)
    ring(mb, M, c, 0.42, 0.018, "glass2", seg=24, mseg=4)
    ring(mb, M, c, 0.4, 0.015, "glass2", seg=24, mseg=4, rx=math.pi / 2)
    ring(mb, M, c, 0.38, 0.015, "metal", seg=24, mseg=4, rx=math.pi / 2, rz=math.pi / 2)
    ring(mb, M, c, 0.36, 0.02, "accent", seg=24, mseg=4, rx=0.41)
    strut(mb, M, (0, -0.15, 0.85), (0, 0.15, 1.65), 0.01, "metal")
    sp(mb, M, c, 0.08, "glass2", sub=1)


@fxprop("star_chart", "wall", (1.2, 0.05, 0.9), eras=OLD | MID, rooms=("observatory", "wizard", "study", "cabin", "library", "map_room"))
def star_chart(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.01, 0), (1.1, 0.02, 0.8), "paper")
    cyx(mb, M, (0, 0, 0.42), 0.025, 1.2, "wood2", seg=6)
    cyx(mb, M, (0, 0, -0.42), 0.025, 1.2, "wood2", seg=6)
    ring(mb, sub(M, (0, -0.002, 0), rx=math.pi / 2), (0, 0, 0), 0.33, 0.006, "dark", seg=24, mseg=3)
    ring(mb, sub(M, (0, -0.002, 0), rx=math.pi / 2), (0, 0, 0), 0.2, 0.004, "dark", seg=20, mseg=3)
    pts = []
    for k in range(14):
        p = (rng.uniform(-0.45, 0.45), -0.006, rng.uniform(-0.32, 0.32))
        sp(mb, M, p, rng.uniform(0.008, 0.016), "dark", sub=0)
        pts.append(p)
    for a, b in zip(pts[:6], pts[1:7]):
        strut(mb, M, a, b, 0.002, "trim")


@fxprop("mead_horn_rack", "wall", (1.0, 0.25, 0.6), eras=MED, rooms=("mead_hall", "tavern"))
def mead_horn_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.08, 0.1), (1.0, 0.05, 0.08), "wood2")
    for i in range(4):
        u = -0.36 + i * 0.24
        m = sub(M, (u, 0.0, 0.05), rx=0.3, ry=0.2)
        polyline(mb, m, [(0, 0, 0), (0.0, -0.06, -0.15), (0.03, -0.08, -0.3), (0.07, -0.05, -0.38)], 0.03, "paper", seg=6)
        cy(mb, m, (0, 0, 0.0), 0.04, 0.04, "glass2", seg=8)

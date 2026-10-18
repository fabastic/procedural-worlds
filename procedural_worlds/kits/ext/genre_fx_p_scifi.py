"""genre_fx props: sci-fi near / far future, cyberpunk, solarpunk, post-apocalyptic, space age.
Glow uses palette keys only: glow(era) = neon 'accent' in eras where it is emissive, else the night-lit 'screen';
hot(era) = something that always glows (accent or fire2)."""
import math
from mathutils import Vector
from ..props import OLD, MID, NOW, FUT
from .genre_fx_geom import (fxprop, M0, sub, bx, cy, cyx, cyy, sp, lathe, prism, slab, ring, strut, polyline, flat_grid,
                            arch_pts, flame, fire, candle, table, barrel_shape, surface, glow, hot, ELEC, LATE)

SHIP = ("bridge", "station", "ship", "cargo", "habitat", "spaceship")
TECH = SHIP + ("lab", "server", "reactor", "medbay", "cryo", "hydroponics", "alienlab", "clinic", "control")
ELEC_MID = ELEC | MID


def panel_lights(mb, M, c, w, h, era, rng, n=6, depth=0.012):
    for i in range(n):
        bx(mb, M, (c[0] + rng.uniform(-w / 2, w / 2), c[1], c[2] + rng.uniform(-h / 2, h / 2)), (0.03, depth, 0.02),
           rng.choice((glow(era), "accent", "fabric", "paper")))


def hazard(mb, M, c, w, h, n=6, axis="x"):
    for i in range(n):
        u = -w / 2 + (i + 0.5) * w / n
        p = (c[0] + u, c[1], c[2]) if axis == "x" else (c[0], c[1] + u, c[2])
        bx(mb, M, p, (w / n * 0.5, 0.012, h) if axis == "x" else (0.012, w / n * 0.5, h), "paper" if i % 2 else "dark",
           ry=0.5 if axis == "x" else 0.0, rx=0.5 if axis != "x" else 0.0)


# ----------------------------------------------------------------------------- command & control
@fxprop("console", "floor", (1.5, 0.9, 1.25), eras=ELEC_MID, rooms=TECH + ("control", "bunker"))
def console(mb, x, y, z, rot, rng, era):
    """Angled control desk, operator side at local -Y."""
    M = M0(x, y, z, rot)
    W = 1.4
    side = [(-0.4, 0.0), (0.35, 0.0), (0.35, 1.2), (0.15, 1.25), (-0.1, 0.85), (-0.4, 0.8)]
    prism(mb, M, (0, 0, 0), [(sy, sz) for sy, sz in side], W, "wall2", rz=math.pi / 2)
    for sx in (-W / 2 - 0.02, W / 2 + 0.02):
        prism(mb, M, (sx, 0, 0), side, 0.04, "metal2", rz=math.pi / 2)
    deck = sub(M, (0, -0.25, 0.83), rx=-0.25)
    bx(mb, deck, (0, 0, 0), (W - 0.1, 0.32, 0.02), "metal2")
    for i in range(int(W / 0.08)):
        bx(mb, deck, (-W / 2 + 0.1 + i * 0.08, rng.uniform(-0.1, 0.1), 0.015), (0.04, 0.04, 0.015), rng.choice(("paper", "fabric", glow(era), "dark")))
    scr = sub(M, (0, 0.06, 1.05), rx=-0.9)
    nscr = 3 if era not in MID else 2
    for i in range(nscr):
        u = -W / 2 + (i + 0.5) * W / nscr
        bx(mb, scr, (u, 0, 0), (W / nscr - 0.06, 0.34, 0.03), "metal2")
        bx(mb, scr, (u, 0, 0.016), (W / nscr - 0.12, 0.28, 0.006), glow(era) if era not in MID else "screen")
        for k in range(3):
            bx(mb, scr, (u + rng.uniform(-0.12, 0.12), rng.uniform(-0.08, 0.08), 0.021), (rng.uniform(0.06, 0.18), 0.012, 0.003), "dark")
    if era in MID:                                    # dials + toggle switches on the old ones
        for i in range(5):
            cyy(mb, M, (-0.5 + i * 0.25, -0.405, 0.6), 0.05, 0.02, "paper", seg=10)
    bx(mb, M, (0, -0.39, 0.05), (W, 0.02, 0.08), "dark")


@fxprop("holo_table", "floor", (1.9, 1.9, 1.7), eras=FUT, rooms=("fx_feature",))
def holo_table(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    g = hot(era)
    lathe(mb, M, (0, 0, 0), [(0.5, 0), (0.55, 0.08), (0.35, 0.2), (0.3, 0.8), (0.85, 0.88), (0.85, 0.96), (0, 0.96)], "metal2", seg=16)
    ring(mb, M, (0, 0, 0.95), 0.82, 0.03, "metal", seg=24, mseg=4)
    cy(mb, M, (0, 0, 0.965), 0.7, 0.01, g, seg=20)
    kind = rng.choice(("planet", "terrain", "ship"))
    if kind == "planet":
        sp(mb, M, (0, 0, 1.38), 0.28, g, sub=1)
        ring(mb, M, (0, 0, 1.38), 0.45, 0.01, g, seg=24, mseg=3, rx=0.35)
        sp(mb, M, (0.5, 0.1, 1.55), 0.06, g, sub=0)
    elif kind == "terrain":
        for i in range(-3, 4):
            for j in range(-3, 4):
                if i * i + j * j > 10:
                    continue
                h = 0.05 + 0.25 * abs(math.sin(i * 1.3 + j * 0.7 + rng.uniform(0, 0.5)))
                bx(mb, M, (i * 0.13, j * 0.13, 1.02 + h / 2), (0.1, 0.1, h), g)
    else:
        prism(mb, M, (0, 0, 1.3), [(-0.35, 0), (0.35, 0), (0.1, 0.12), (-0.1, 0.12)], 0.5, g, rz=math.pi / 2)
        prism(mb, M, (0, 0, 1.36), [(-0.4, -0.02), (0.4, -0.02), (0.0, 0.08)], 0.12, g)
    for i in range(6):
        a = i / 6 * math.tau
        bx(mb, M, (math.cos(a) * 0.78, math.sin(a) * 0.78, 0.6), (0.08, 0.08, 0.04), g, rz=a)


@fxprop("captain_chair", "floor", (1.1, 1.0, 1.45), eras=FUT, rooms=("fx_feature",))
def captain_chair(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.06), 0.45, 0.12, "metal2", seg=12)
    cy(mb, M, (0, 0, 0.3), 0.1, 0.4, "metal", seg=8)
    bx(mb, M, (0, 0, 0.52), (0.6, 0.6, 0.12), "fabric")
    prism(mb, M, (0, 0.3, 0.5), [(-0.32, 0), (0.32, 0), (0.28, 0.85), (0.15, 0.95), (-0.15, 0.95), (-0.28, 0.85)], 0.12, "fabric")
    prism(mb, M, (0, 0.37, 0.5), [(-0.34, 0), (0.34, 0), (0.3, 0.88), (0.15, 0.98), (-0.15, 0.98), (-0.3, 0.88)], 0.04, "metal2")
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.4, -0.05, 0.72), (0.14, 0.62, 0.08), "metal2")
        bx(mb, M, (sx * 0.4, -0.22, 0.765), (0.1, 0.22, 0.012), glow(era))
        bx(mb, M, (sx * 0.4, 0.15, 0.6), (0.1, 0.12, 0.2), "metal2")


@fxprop("wall_screen", "wall", (1.7, 0.12, 1.0), eras=ELEC, rooms=TECH + ("office", "bunker", "megablock", "corridor"))
def wall_screen(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    W, H = rng.uniform(1.0, 1.6), rng.uniform(0.6, 0.9)
    bx(mb, M, (0, 0.04, 0), (W, 0.05, H), "metal2")
    bx(mb, M, (0, 0.012, 0), (W - 0.08, 0.012, H - 0.08), glow(era))
    kind = rng.choice(("bars", "graph", "map", "text"))
    if kind == "bars":
        for i in range(8):
            h = rng.uniform(0.1, H - 0.25)
            bx(mb, M, (-W / 2 + 0.15 + i * (W - 0.3) / 7, 0.0, -H / 2 + 0.1 + h / 2), (0.06, 0.006, h), "dark")
    elif kind == "graph":
        pts = [(-W / 2 + 0.1 + i * (W - 0.2) / 9, 0.0, rng.uniform(-H / 3, H / 3)) for i in range(10)]
        polyline(mb, M, pts, 0.008, "dark")
    elif kind == "map":
        ring(mb, sub(M, (0, 0, 0), rx=math.pi / 2), (0, 0, 0), H * 0.32, 0.006, "dark", seg=20, mseg=3)
        for k in range(5):
            sp(mb, M, (rng.uniform(-W / 3, W / 3), 0.0, rng.uniform(-H / 3, H / 3)), 0.02, "dark", sub=0)
        bx(mb, M, (0, 0.0, 0), (W - 0.2, 0.006, 0.008), "dark")
        bx(mb, M, (0, 0.0, 0), (0.008, 0.006, H - 0.2), "dark")
    else:
        for k in range(int(H / 0.09)):
            bx(mb, M, (-W / 2 + 0.1 + rng.uniform(0.1, 0.35), 0.0, H / 2 - 0.1 - k * 0.09), (rng.uniform(0.2, W * 0.7), 0.006, 0.02), "dark")
    bx(mb, M, (0, 0.0, H / 2 - 0.06), (W - 0.1, 0.01, 0.04), "dark")


@fxprop("holo_terminal", "floor", (0.7, 0.7, 1.5), eras=FUT, rooms=TECH + ("megablock", "lobby", "station"))
def holo_terminal(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.3, 0), (0.3, 0.05), (0.12, 0.12), (0.1, 0.95), (0.18, 1.0), (0.0, 1.0)], "metal2", seg=10)
    bx(mb, M, (0, -0.05, 1.03), (0.3, 0.2, 0.06), "metal", rx=-0.3)
    bx(mb, sub(M, (0, -0.05, 1.3), rx=0.15), (0, 0, 0), (0.55, 0.01, 0.35), hot(era))
    for k in range(4):
        bx(mb, sub(M, (0, -0.06, 1.3), rx=0.15), (rng.uniform(-0.15, 0.15), 0, rng.uniform(-0.1, 0.12)), (rng.uniform(0.08, 0.25), 0.006, 0.02), "dark")
    cy(mb, M, (0, -0.05, 1.075), 0.03, 0.02, "glass", seg=8)


@fxprop("datapad", "surface", (0.25, 0.18, 0.02), eras=ELEC, rooms=TECH + ("office", "megablock", "bunker"))
def datapad(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot + rng.uniform(-0.6, 0.6))
    bx(mb, M, (0, 0, 0.006), (0.24, 0.17, 0.012), "metal2")
    bx(mb, M, (0, 0, 0.0125), (0.21, 0.14, 0.002), glow(era))


# ----------------------------------------------------------------------------- crew & cargo
@fxprop("cryo_pod", "floor", (1.0, 1.0, 2.35), eras=FUT, rooms=("fx_feature",))
def cryo_pod(mb, x, y, z, rot, rng, era):
    """Upright capsule; frosted window faces local -Y."""
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.48, 0), (0.48, 0.18), (0.42, 0.22), (0.0, 0.22)], "metal2", seg=14)
    lathe(mb, M, (0, 0.04, 0.2), [(0.36, 0), (0.4, 0.3), (0.42, 1.1), (0.38, 1.7), (0.26, 1.95), (0.0, 2.02)], "wall2", seg=14, sc=(1, 0.85))
    prism(mb, M, (0, -0.3, 0.3), arch_pts(0.5, 1.7, 1.42, seg=8), 0.06, "metal")
    prism(mb, M, (0, -0.33, 0.36), arch_pts(0.4, 1.56, 1.36, seg=8), 0.04, "glass")
    for k in range(4):                                     # frost streaks
        bx(mb, M, (rng.uniform(-0.14, 0.14), -0.356, rng.uniform(0.6, 1.6)), (rng.uniform(0.05, 0.16), 0.006, 0.012), "paper", ry=rng.uniform(-0.6, 0.6))
    for zz in (0.25, 2.05):
        ring(mb, M, (0, 0.04, zz), 0.37 if zz < 1 else 0.24, 0.02, hot(era), seg=16, mseg=3)
    bx(mb, M, (0.3, -0.36, 1.1), (0.12, 0.03, 0.22), "dark")
    bx(mb, M, (0.3, -0.38, 1.12), (0.08, 0.01, 0.14), glow(era))
    for sx in (-0.2, 0.2):
        strut(mb, M, (sx, 0.32, 1.9), (sx, 0.5, 2.3), 0.04, "metal2", seg=6)


@fxprop("medbay_pod", "floor", (1.0, 2.2, 1.6), eras=ELEC, rooms=("medbay", "clinic", "alienlab", "habitat", "hospital", "fx_feature"))
def medbay_pod(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.25), (0.5, 1.4, 0.5), "metal2")
    bx(mb, M, (0, 0, 0.58), (0.85, 2.0, 0.16), "wall2")
    bx(mb, M, (0, 0.05, 0.68), (0.75, 1.85, 0.06), "paper")
    bx(mb, M, (0, -0.8, 0.73), (0.5, 0.3, 0.06), "paper")
    for k in range(4):                                     # canopy hoops
        ring(mb, sub(M, (0, -0.7 + k * 0.45, 0.66), rx=math.pi / 2), (0, 0, 0), 0.44, 0.02, "metal", seg=10, mseg=3, arc=math.pi)
    strut(mb, M, (0, 0.95, 0.66), (0, 0.95, 1.5), 0.04, "metal2")
    bx(mb, M, (0, 0.2, 1.5), (0.12, 1.5, 0.08), "metal2")
    bx(mb, M, (0, 0.0, 1.45), (0.5, 0.06, 0.03), hot(era))
    bx(mb, M, (0.55, 0.7, 1.2), (0.05, 0.4, 0.3), "metal2")
    bx(mb, M, (0.53, 0.7, 1.2), (0.01, 0.34, 0.24), glow(era))
    polyline(mb, M, [(0.55, 0.7, 1.05), (0.5, 0.7, 0.7), (0.3, 0.6, 0.72)], 0.008, "dark")


@fxprop("glow_crate", "floor", (1.0, 0.8, 0.85), eras=FUT, rooms=("cargo", "storage", "hangar", "station", "ship", "megablock", "smuggler"))
def glow_crate(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    w, d, h = rng.uniform(0.7, 1.0), rng.uniform(0.6, 0.8), rng.uniform(0.5, 0.8)
    bx(mb, M, (0, 0, h / 2), (w, d, h), "metal2")
    for sx in (-1, 1):
        bx(mb, M, (sx * w / 2, 0, h / 2), (0.06, d + 0.04, h + 0.04), "metal")
    bx(mb, M, (0, 0, h + 0.005), (w - 0.1, d - 0.1, 0.02), "wall2")
    for sy in (-1, 1):
        bx(mb, M, (0, sy * (d / 2 + 0.006), h * 0.5), (w - 0.14, 0.01, 0.025), hot(era))
        bx(mb, M, (0, sy * (d / 2 + 0.006), h * 0.25), (0.14, 0.01, h * 0.3), "dark")
    bx(mb, M, (0, -d / 2 - 0.008, h * 0.78), (w * 0.4, 0.008, 0.06), "paper")
    if rng.random() < 0.4:
        glow_crate_small = (w * 0.6, d * 0.6, h * 0.6)
        bx(mb, M, (0.05, 0.0, h + glow_crate_small[2] / 2), glow_crate_small, "metal2", rz=rng.uniform(-0.3, 0.3))
        bx(mb, M, (0.05, 0.0, h + glow_crate_small[2] * 0.5), (glow_crate_small[0] + 0.01, 0.03, 0.02), hot(era), rz=0.0)


@fxprop("cargo_container", "floor", (6.1, 2.5, 2.6), eras=ELEC_MID, rooms=("fx_feature",))
def cargo_container(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    L, W, H = 6.0, 2.4, 2.55
    col = rng.choice(("accent", "fabric", "wall2", "trim", "fabric2")) if era not in FUT else rng.choice(("wall2", "trim", "fabric2"))
    bx(mb, M, (0, 0, H / 2), (L, W, H), col)
    for i in range(int(L / 0.3)):
        u = -L / 2 + 0.15 + i * 0.3
        for sy in (-1, 1):
            bx(mb, M, (u, sy * (W / 2 + 0.02), H / 2), (0.1, 0.04, H - 0.16), col)
    for zz in (0.05, H - 0.05):
        for sy in (-1, 1):
            bx(mb, M, (0, sy * W / 2, zz), (L + 0.02, 0.1, 0.1), "metal2")
    for sx in (-1, 1):
        bx(mb, M, (sx * L / 2, 0, H / 2), (0.08, W + 0.06, H), "metal2")
    for k in range(4):
        bx(mb, M, (L / 2 + 0.05, -0.8 + k * 0.53, H / 2), (0.04, 0.04, H - 0.3), "metal")
    bx(mb, M, (-L / 4, -W / 2 - 0.05, H * 0.7), (1.4, 0.01, 0.35), "paper")
    bx(mb, M, (-L / 4, -W / 2 - 0.056, H * 0.7), (1.2, 0.01, 0.16), "dark")


@fxprop("power_cell", "floor", (0.45, 0.45, 0.85), eras=FUT, rooms=TECH + ("cargo", "storage", "hangar", "megablock", "shelter"))
def power_cell(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    h = rng.uniform(0.55, 0.85)
    cy(mb, M, (0, 0, 0.05), 0.2, 0.1, "metal2", seg=10)
    cy(mb, M, (0, 0, h / 2), 0.14, h - 0.1, hot(era), seg=10)
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        bx(mb, M, (math.cos(a) * 0.15, math.sin(a) * 0.15, h / 2), (0.06, 0.06, h - 0.1), "metal", rz=a)
    cy(mb, M, (0, 0, h - 0.03), 0.18, 0.08, "metal2", seg=10)
    ring(mb, sub(M, (0, 0, h + 0.07), rx=math.pi / 2), (0, 0, 0), 0.08, 0.012, "metal", seg=10, mseg=3, arc=math.pi)
    hazard(mb, M, (0, -0.205, 0.05), 0.3, 0.06, 5)


@fxprop("drone", "hanging", (0.8, 0.8, 0.35), eras=ELEC, rooms=("fx_feature",))
def drone(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z - rng.uniform(0.6, 1.4), rot + rng.uniform(-0.5, 0.5))
    sp(mb, M, (0, 0, 0), 0.14, "metal2", sub=1, sc=(1.2, 1.0, 0.55))
    sp(mb, M, (0, -0.15, -0.03), 0.045, glow(era) if era not in FUT else hot(era), sub=1)
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        p = (math.cos(a) * 0.32, math.sin(a) * 0.32, 0.03)
        strut(mb, M, (0, 0, 0.0), p, 0.018, "metal")
        cy(mb, M, (p[0], p[1], p[2] + 0.03), 0.13, 0.008, "dark", seg=12)
        ring(mb, M, (p[0], p[1], p[2] + 0.03), 0.15, 0.012, "metal2", seg=14, mseg=3)
    for sx in (-1, 1):
        strut(mb, M, (sx * 0.06, 0, -0.05), (sx * 0.12, 0, -0.16), 0.008, "metal")
    strut(mb, M, (0.05, 0.05, 0.06), (0.08, 0.1, 0.2), 0.004, "metal")


@fxprop("robot_arm", "floor", (1.2, 1.2, 2.4), eras=ELEC, rooms=("factory", "lab", "clinic", "hangar", "cargo", "fx_feature"))
def robot_arm(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.1), 0.42, 0.2, "metal2", seg=12)
    hazard(mb, M, (0, -0.43, 0.1), 0.6, 0.1, 6)
    cy(mb, M, (0, 0, 0.32), 0.26, 0.24, "accent" if era not in FUT else "wall2", seg=12)
    a1, a2 = rng.uniform(0.3, 0.7), rng.uniform(1.2, 2.0)
    sh = Vector((0, 0, 0.55))
    el = sh + Vector((0, -math.sin(a1), math.cos(a1))) * 0.95
    wr = el + Vector((0, -math.sin(a1 + a2 - math.pi / 2), math.cos(a1 + a2 - math.pi / 2) * -1)) * 0.75
    wr.z = max(wr.z, 0.5)
    for p in (sh, el, wr):
        cyx(mb, M, p, 0.13 if p is sh else 0.1, 0.32, "metal2", seg=12)
    strut(mb, M, sh, el, 0.1, "accent" if era not in FUT else "wall2")
    strut(mb, M, el, wr, 0.08, "accent" if era not in FUT else "wall2")
    strut(mb, M, sh + Vector((0.12, 0, 0.1)), el + Vector((0.12, 0, -0.05)), 0.02, "metal")
    tip = wr + Vector((0, -0.18, -0.12))
    strut(mb, M, wr, tip, 0.05, "metal2")
    for sx in (-1, 1):
        polyline(mb, M, [tip, tip + Vector((sx * 0.08, -0.06, -0.05)), tip + Vector((sx * 0.05, -0.16, -0.1))], 0.018, "metal")
    sp(mb, M, tip, 0.03, glow(era), sub=0)


@fxprop("mech_suit", "floor", (1.7, 1.4, 3.1), eras=ELEC, rooms=("fx_feature",))
def mech_suit(mb, x, y, z, rot, rng, era):
    """Parked exosuit / loader mech; cockpit faces local -Y."""
    M = M0(x, y, z, rot)
    hull = rng.choice(("accent", "wall2", "fabric")) if era not in FUT else rng.choice(("wall2", "trim", "metal"))
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.42, -0.1, 0.06), (0.4, 0.6, 0.12), "metal2")                  # feet
        knee = Vector((sx * 0.42, -0.18, 0.75))
        strut(mb, M, (sx * 0.42, 0.0, 0.12), knee, 0.12, "metal2")
        sp(mb, M, knee, 0.15, "metal", sub=1)
        strut(mb, M, knee, (sx * 0.38, 0.05, 1.45), 0.14, hull)
        bx(mb, M, (sx * 0.43, -0.3, 0.45), (0.2, 0.08, 0.5), hull)                       # shin guard
        strut(mb, M, (sx * 0.48, 0.0, 0.3), (sx * 0.48, 0.0, 1.0), 0.025, "metal")        # piston
    bx(mb, M, (0, 0.05, 1.5), (0.95, 0.7, 0.3), "metal2")
    bx(mb, M, (0, 0.05, 2.05), (1.05, 0.95, 0.85), hull)
    prism(mb, M, (0, -0.44, 2.1), [(-0.35, -0.3), (0.35, -0.3), (0.38, 0.25), (0.0, 0.38), (-0.38, 0.25)], 0.05, "glass")
    bx(mb, M, (0, -0.46, 1.72), (0.6, 0.06, 0.08), glow(era))
    hazard(mb, M, (0, -0.48, 1.62), 0.9, 0.08, 7)
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.65, 0.05, 2.35), 0.25, hull, sub=1, sc=(1, 1.1, 0.8))            # shoulder pods
        el = Vector((sx * 0.75, -0.25, 1.75))
        strut(mb, M, (sx * 0.68, 0.05, 2.25), el, 0.09, "metal2")
        strut(mb, M, el, (sx * 0.72, -0.6, 1.5), 0.08, hull)
        for k in (-1, 1):
            polyline(mb, M, [(sx * 0.72, -0.6, 1.5), (sx * 0.72 + k * 0.06, -0.78, 1.45), (sx * 0.72 + k * 0.03, -0.85, 1.3)], 0.025, "metal")
    cy(mb, M, (0.3, -0.48, 2.42), 0.06, 0.06, hot(era), seg=8, rx=math.pi / 2)
    bx(mb, M, (0, 0.55, 2.0), (0.6, 0.15, 0.6), "metal2")


@fxprop("captain_bunk", "floor", (1.0, 2.1, 1.9), eras=ELEC_MID, rooms=("habitat", "bunker", "barracks", "ship", "shelter", "station"))
def captain_bunk(mb, x, y, z, rot, rng, era):
    """Double bunk bed (metal frame, thin mattresses, a blanket hanging over the side)."""
    M = M0(x, y, z, rot)
    for sx in (-0.45, 0.45):
        for sy in (-0.98, 0.98):
            bx(mb, M, (sx, sy, 0.92), (0.05, 0.05, 1.84), "metal2")
    for zz in (0.35, 1.3):
        bx(mb, M, (0, 0, zz), (0.95, 2.0, 0.06), "metal2")
        bx(mb, M, (0, 0, zz + 0.08), (0.88, 1.92, 0.1), "paper")
        bx(mb, M, (0, 0.2, zz + 0.14), (0.9, 1.2, 0.03), "fabric")
        bx(mb, M, (0, -0.8, zz + 0.17), (0.5, 0.25, 0.08), "paper")
    bx(mb, M, (0.47, 0.3, 1.1), (0.02, 0.9, 0.5), "fabric")
    for k in range(5):
        bx(mb, M, (-0.47, 0.6, 0.5 + k * 0.25), (0.04, 0.3, 0.03), "metal")


# ----------------------------------------------------------------------------- infrastructure
@fxprop("server_rack", "floor", (0.75, 1.05, 2.15), eras=ELEC, rooms=("server", "control", "bunker", "lab", "office"))
def server_rack(mb, x, y, z, rot, rng, era):
    """Rack cabinet; front face at local -Y."""
    M = M0(x, y, z, rot)
    W, D, H = 0.7, 1.0, 2.1
    bx(mb, M, (0, 0, H / 2), (W, D, H), "dark")
    bx(mb, M, (0, 0, H - 0.02), (W + 0.02, D + 0.02, 0.04), "metal2")
    n = 14
    for i in range(n):
        zz = 0.15 + i * (H - 0.3) / n
        if rng.random() < 0.12:
            continue
        bx(mb, M, (0, -D / 2 - 0.005, zz), (W - 0.08, 0.02, (H - 0.3) / n - 0.025), "metal2")
        for k in range(rng.randint(1, 4)):
            bx(mb, M, (-W / 2 + 0.08 + k * 0.04, -D / 2 - 0.018, zz), (0.018, 0.008, 0.018), rng.choice((glow(era), "accent", "leaf")))
        for k in range(3):
            bx(mb, M, (0.05 + k * 0.07, -D / 2 - 0.016, zz), (0.05, 0.006, 0.012), "dark")
    for sx in (-1, 1):
        bx(mb, M, (sx * (W / 2 - 0.02), -D / 2 - 0.01, H / 2), (0.03, 0.03, H - 0.05), "metal2")


@fxprop("conduit_bundle", "wall", (2.0, 0.35, 0.6), eras=ELEC_MID, rooms=TECH + ("basement", "factory", "megablock", "corridor", "bunker", "boiler"))
def conduit_bundle(mb, x, y, z, rot, rng, era):
    """Horizontal pipes along a wall, clamped, with a junction box (centred on z)."""
    M = M0(x, y, z, rot)
    L = 2.0
    pipes = [(rng.uniform(0.03, 0.09), rng.uniform(-0.22, 0.22)) for _ in range(rng.randint(3, 5))]
    for r, zz in pipes:
        cyx(mb, M, (0, 0.17 - r - 0.02, zz), r, L, rng.choice(("metal", "metal2", "trim", "accent" if era not in FUT else "metal")), seg=8)
    for u in (-0.8, 0.0, 0.8):
        bx(mb, M, (u, 0.1, 0), (0.06, 0.16, 0.52), "metal2")
    bx(mb, M, (rng.uniform(-0.5, 0.5), 0.05, 0.0), (0.3, 0.12, 0.35), "metal2")
    if era in FUT:
        cyx(mb, M, (0, 0.08, -0.26), 0.012, L, hot(era), seg=6)


@fxprop("cable_spool", "floor", (1.0, 0.7, 1.0), eras=ELEC_MID, rooms=("server", "reactor", "cargo", "factory", "hangar", "storage", "bunker", "shelter"))
def cable_spool(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    r = rng.uniform(0.35, 0.48)
    for sx in (-0.25, 0.25):
        cyx(mb, M, (sx, 0, r), r, 0.04, "wood" if era in MID else "metal2", seg=14)
    cyx(mb, M, (0, 0, r), r * 0.75, 0.46, "dark", seg=12)
    for k in range(4):
        ring(mb, sub(M, (-0.18 + k * 0.12, 0, r), ry=math.pi / 2), (0, 0, 0), r * 0.75, 0.018, "dark", seg=12, mseg=3)
    polyline(mb, M, [(0.1, -r * 0.7, r * 0.4), (0.2, -r - 0.2, 0.02), (0.6, -r - 0.5, 0.02), (0.9, -r - 0.3, 0.02)], 0.02, "dark", seg=6)


@fxprop("airlock_door", "wall", (2.6, 0.5, 3.0), eras=ELEC, rooms=("fx_feature",))
def airlock_door(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    frame = [(-1.3, 0), (1.3, 0), (1.3, 2.6), (1.0, 2.95), (-1.0, 2.95), (-1.3, 2.6)]
    hole = [(-0.95, 0.05), (0.95, 0.05), (0.95, 2.35), (0.75, 2.6), (-0.75, 2.6), (-0.95, 2.35)]
    prism(mb, M, (0, 0.12, 0), frame, 0.2, "metal2")
    prism(mb, M, (0, 0.0, 0), hole, 0.1, "wall2")
    bx(mb, M, (0, -0.06, 1.3), (0.03, 0.02, 2.5), "dark")
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.45, -0.06, 1.0), (0.7, 0.02, 0.16), "metal")
        for i in range(6):
            bx(mb, M, (sx * 1.15, -0.02, 0.2 + i * 0.4), (0.18, 0.02, 0.16), "paper" if i % 2 else "dark")
    cyy(mb, M, (0, -0.08, 1.7), 0.28, 0.06, "metal", seg=16)
    cyy(mb, M, (0, -0.1, 1.7), 0.2, 0.04, "glass", seg=16)
    ring(mb, sub(M, (0, -0.1, 1.05), rx=math.pi / 2), (0, 0, 0), 0.22, 0.025, "metal", seg=14, mseg=4)
    for i in range(4):
        bx(mb, M, (0, -0.1, 1.05), (0.44, 0.02, 0.03), "metal", ry=i * math.pi / 4)
    bx(mb, M, (1.15, -0.1, 2.75), (0.2, 0.04, 0.1), hot(era))
    bx(mb, M, (-1.0, -0.06, 1.3), (0.14, 0.04, 0.24), "metal2")
    bx(mb, M, (-1.0, -0.085, 1.33), (0.08, 0.01, 0.1), glow(era))


@fxprop("reactor_core", "floor", (3.2, 3.2, 5.2), eras=ELEC_MID, rooms=("fx_feature",))
def reactor_core(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    g = hot(era)
    lathe(mb, M, (0, 0, 0), [(1.6, 0), (1.6, 0.25), (1.3, 0.35), (1.25, 0.6), (0.95, 0.75), (0.0, 0.75)], "metal2", seg=20)
    cy(mb, M, (0, 0, 2.6), 0.62, 3.7, g, seg=16)
    for zz in (1.0, 1.7, 2.4, 3.1, 3.8):
        ring(mb, M, (0, 0, zz), 0.72, 0.08, "metal", seg=20, mseg=4)
    for i in range(8):
        a = i / 8 * math.tau
        strut(mb, M, (math.cos(a) * 0.95, math.sin(a) * 0.95, 0.75), (math.cos(a) * 0.72, math.sin(a) * 0.72, 4.45), 0.06, "metal2")
    lathe(mb, M, (0, 0, 4.4), [(0.0, 0), (1.05, 0), (1.05, 0.25), (0.6, 0.6), (0.3, 0.8), (0.0, 0.85)], "metal2", seg=20)
    for i in range(4):
        a = i / 4 * math.tau + 0.3
        polyline(mb, M, [(math.cos(a) * 0.9, math.sin(a) * 0.9, 4.6), (math.cos(a) * 1.6, math.sin(a) * 1.6, 4.9), (math.cos(a) * 2.6, math.sin(a) * 2.6, 4.9)],
                 0.12, "metal", seg=8)
    hazard(mb, M, (0, -1.61, 0.12), 2.6, 0.18, 12)


@fxprop("hydro_vat", "floor", (2.1, 0.85, 1.8), eras=ELEC, rooms=("hydroponics", "greenhouse", "habitat", "alienlab", "station"))
def hydro_vat(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    L = 2.0
    bx(mb, M, (0, 0, 0.6), (L, 0.75, 0.3), "metal2")
    for sx in (-0.9, 0.9):
        for sy in (-0.3, 0.3):
            bx(mb, M, (sx, sy, 0.22), (0.06, 0.06, 0.45), "metal")
    bx(mb, M, (0, 0, 0.755), (L - 0.1, 0.65, 0.02), "water")
    n = rng.randint(5, 8)
    for i in range(n):
        u = -L / 2 + 0.2 + i * (L - 0.4) / max(1, n - 1)
        for sy in (-0.17, 0.17):
            h = rng.uniform(0.15, 0.45)
            strut(mb, M, (u, sy, 0.76), (u + rng.uniform(-0.05, 0.05), sy, 0.76 + h), 0.008, "leaf")
            sp(mb, M, (u, sy, 0.76 + h), rng.uniform(0.08, 0.14), "leaf", sub=1, sc=(1, 1, 0.75))
            if rng.random() < 0.3:
                sp(mb, M, (u + 0.05, sy - 0.06, 0.76 + h * 0.7), 0.035, rng.choice(("fabric", "glass2", "accent")), sub=0)
    for sx in (-0.95, 0.95):
        bx(mb, M, (sx, 0.32, 1.25), (0.04, 0.04, 1.1), "metal")
    bx(mb, M, (0, 0.32, 1.78), (L, 0.06, 0.05), "metal")
    bx(mb, M, (0, 0.0, 1.72), (L - 0.15, 0.22, 0.04), "metal2")
    bx(mb, M, (0, 0.0, 1.695), (L - 0.25, 0.16, 0.012), hot(era))
    cyx(mb, M, (0, -0.38, 0.5), 0.03, L, "metal", seg=6)


@fxprop("alien_plant", "floor", (1.0, 1.0, 1.8), eras=FUT, rooms=("alienlab", "hydroponics", "greenhouse", "alien", "jungle", "crystal"))
def alien_plant(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    sp(mb, M, (0, 0, 0.15), 0.3, "leaf", sub=1, sc=(1.1, 1.1, 0.6))
    for k in range(rng.randint(3, 6)):
        a = rng.uniform(0, math.tau)
        h = rng.uniform(0.6, 1.6)
        bend = rng.uniform(0.15, 0.45)
        pts = [Vector((0, 0, 0.2))]
        for t in (0.33, 0.66, 1.0):
            pts.append(Vector((math.cos(a) * bend * t * t, math.sin(a) * bend * t * t, 0.2 + h * t)))
        polyline(mb, M, pts, 0.03 * (1.0 - 0.1 * k), "leaf", seg=6)
        sp(mb, M, pts[-1], rng.uniform(0.07, 0.13), hot(era), sub=1, sc=(1, 1, 1.4))
    for k in range(5):                                          # tongue leaves
        a = k / 5 * math.tau + rng.uniform(-0.2, 0.2)
        prism(mb, sub(M, (math.cos(a) * 0.25, math.sin(a) * 0.25, 0.15), rz=a + math.pi / 2, ry=0.0),
              (0, 0, 0), [(-0.07, 0), (0.07, 0), (0.12, 0.25), (0.0, 0.5), (-0.12, 0.25)], 0.02, "fabric2", rx=0.0)


@fxprop("specimen_tank", "floor", (1.0, 1.0, 2.5), eras=ELEC, rooms=("alienlab", "lab", "fx_feature"))
def specimen_tank(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.48, 0), (0.48, 0.3), (0.42, 0.36), (0.0, 0.36)], "metal2", seg=16)
    cy(mb, M, (0, 0, 1.25), 0.38, 1.8, hot(era) if era in FUT else "glass", seg=16)
    lathe(mb, M, (0, 0, 2.15), [(0.42, 0), (0.48, 0.06), (0.48, 0.2), (0.25, 0.32), (0.0, 0.34)], "metal2", seg=16)
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        bx(mb, M, (math.cos(a) * 0.4, math.sin(a) * 0.4, 1.25), (0.05, 0.05, 1.82), "metal")
    # silhouette of the specimen pressing against the front glass
    sp(mb, M, (0, -0.33, 1.5), 0.15, "dark", sub=1, sc=(1.0, 0.5, 1.2))
    sp(mb, M, (0, -0.3, 1.15), 0.18, "dark", sub=1, sc=(1.0, 0.5, 1.4))
    for sx in (-1, 1):
        polyline(mb, M, [(sx * 0.1, -0.33, 1.2), (sx * 0.22, -0.36, 0.95), (sx * 0.18, -0.36, 0.7)], 0.025, "dark", seg=6)
    for k in range(5):
        sp(mb, M, (rng.uniform(-0.25, 0.25), -0.37, rng.uniform(0.6, 2.0)), 0.02, "paper", sub=0)
    polyline(mb, M, [(0.2, 0.0, 2.45), (0.2, 0.3, 2.8), (0.5, 0.5, 2.8)], 0.03, "metal2", seg=6)


@fxprop("lab_bench", "floor", (1.9, 0.85, 1.05), eras=MID | ELEC, rooms=("lab", "alienlab", "medbay", "clinic", "school_lab"))
def lab_bench(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.45), (1.8, 0.75, 0.86), "wall2")
    bx(mb, M, (0, 0, 0.9), (1.86, 0.8, 0.05), "paper" if era in FUT else "dark")
    for sx in (-0.6, 0.0, 0.6):
        bx(mb, M, (sx, -0.38, 0.45), (0.55, 0.01, 0.75), "trim")
    bx(mb, M, (-0.55, 0.0, 0.92), (0.4, 0.35, 0.02), "metal2")                    # sink
    polyline(mb, M, [(-0.55, 0.25, 0.92), (-0.55, 0.25, 1.15), (-0.55, 0.1, 1.15)], 0.012, "metal", seg=6)
    lathe(mb, M, (0.2, 0.1, 0.925), [(0.08, 0), (0.08, 0.02), (0.02, 0.04), (0.02, 0.2), (0, 0.2)], "dark", seg=8)     # microscope
    strut(mb, M, (0.2, 0.12, 1.0), (0.2, 0.02, 1.25), 0.025, "metal2", seg=6)
    bx(mb, M, (0.2, 0.0, 1.0), (0.12, 0.1, 0.02), "metal2")
    for k in range(rng.randint(3, 6)):
        u = rng.uniform(0.4, 0.85)
        cy(mb, M, (u, rng.uniform(-0.25, 0.25), 0.925 + 0.06), 0.035, 0.12, rng.choice(("glass", "accent", "glass2")), seg=8)
    return surface(x, y, z + 0.925, 0.25)


@fxprop("beaker_rack", "surface", (0.3, 0.12, 0.2), eras=MID | ELEC | {"victorian_industrial"}, rooms=("lab", "alienlab", "clinic", "medbay", "school_lab", "gaslab"))
def beaker_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.01), (0.3, 0.1, 0.02), "wood" if era not in FUT else "metal2")
    bx(mb, M, (0, 0, 0.1), (0.3, 0.1, 0.015), "wood" if era not in FUT else "metal2")
    for sx in (-0.14, 0.14):
        bx(mb, M, (sx, 0, 0.06), (0.015, 0.1, 0.1), "wood" if era not in FUT else "metal2")
    for i in range(5):
        cy(mb, M, (-0.1 + i * 0.05, 0, 0.08), 0.012, 0.14, rng.choice(("glass", "accent", "glass2", "fabric")), seg=6)


@fxprop("space_helmet", "surface", (0.35, 0.35, 0.35), eras=MID | ELEC, rooms=("habitat", "station", "bridge", "airlock", "hangar", "launch", "ship"))
def space_helmet(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot + rng.uniform(-0.6, 0.6))
    cy(mb, M, (0, 0, 0.03), 0.14, 0.06, "metal2", seg=12)
    sp(mb, M, (0, 0, 0.18), 0.16, "paper" if era not in FUT else "wall2", sub=2)
    sp(mb, M, (0, -0.06, 0.2), 0.13, "glass2" if era in MID else "glass", sub=1, sc=(1, 0.8, 0.8))
    bx(mb, M, (0.12, 0.05, 0.28), (0.04, 0.04, 0.06), glow(era))


@fxprop("vending_machine", "floor", (1.0, 0.8, 1.95), eras=ELEC, rooms=("megablock", "corridor", "station", "lobby", "arcade", "metro", "alley"))
def vending_machine(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    body = rng.choice(("fabric", "accent", "wall2", "trim")) if era not in FUT else rng.choice(("wall2", "fabric", "trim"))
    bx(mb, M, (0, 0, 0.95), (0.95, 0.75, 1.9), body)
    bx(mb, M, (-0.1, -0.38, 1.15), (0.62, 0.02, 1.2), glow(era))
    for j in range(5):
        bx(mb, M, (-0.1, -0.395, 0.65 + j * 0.24), (0.6, 0.02, 0.025), "dark")
        for i in range(4):
            cy(mb, M, (-0.32 + i * 0.145, -0.38, 0.72 + j * 0.24), 0.03, 0.12, rng.choice(("fabric", "paper", "leaf", "accent", "glass2")), seg=6)
    bx(mb, M, (0.33, -0.385, 1.2), (0.14, 0.02, 0.4), "metal2")
    bx(mb, M, (0.33, -0.395, 1.3), (0.08, 0.01, 0.08), glow(era))
    bx(mb, M, (-0.1, -0.385, 0.32), (0.55, 0.03, 0.18), "dark")
    bx(mb, M, (0, -0.38, 1.82), (0.9, 0.03, 0.12), hot(era) if era in FUT or era in ("analog_digital",) else "paper")


@fxprop("neon_sign", "wall", (1.3, 0.12, 0.6), eras=ELEC | MID, rooms=("megablock", "corridor", "alley", "arcade", "bar", "clinic", "nightclub", "den"))
def neon_sign(mb, x, y, z, rot, rng, era):
    """Glyph strokes on a dark backing plate (no real letters, reads as signage)."""
    M = M0(x, y, z, rot)
    W, H = rng.uniform(0.8, 1.3), rng.uniform(0.35, 0.55)
    bx(mb, M, (0, 0.05, 0), (W, 0.03, H), "dark")
    g = hot(era) if era in FUT else glow(era)
    u = -W / 2 + 0.12
    while u < W / 2 - 0.12:
        for k in range(rng.randint(2, 4)):
            a = rng.choice((0.0, math.pi / 2, math.pi / 4, -math.pi / 4))
            L = rng.uniform(0.08, H * 0.6)
            bx(mb, M, (u + rng.uniform(-0.04, 0.04), 0.02, rng.uniform(-H / 4, H / 4)), (L, 0.02, 0.025), g, ry=a)
        u += rng.uniform(0.14, 0.22)
    if rng.random() < 0.5:
        ring(mb, sub(M, (0, 0.025, 0), rx=math.pi / 2), (0, 0, 0), 0.0001 + W * 0.0, 0.0, g, seg=4, mseg=3) if False else None
        bx(mb, M, (0, 0.02, -H / 2 + 0.05), (W - 0.1, 0.02, 0.02), g)


@fxprop("security_camera", "wall", (0.3, 0.4, 0.25), eras=ELEC | {"cold_war"}, rooms=TECH + ("megablock", "corridor", "bunker", "vault", "office"))
def security_camera(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.15, 0.05), (0.1, 0.04, 0.12), "metal2")
    strut(mb, M, (0, 0.13, 0.05), (0, -0.02, 0.05), 0.015, "metal2")
    m = sub(M, (0, -0.05, 0.0), rx=-0.35, rz=rng.uniform(-0.5, 0.5))
    bx(mb, m, (0, -0.05, 0), (0.1, 0.24, 0.1), "paper")
    cyy(mb, m, (0, -0.18, 0), 0.035, 0.03, "dark", seg=8)
    bx(mb, m, (0.035, 0.05, 0.035), (0.015, 0.015, 0.015), glow(era) if era in FUT else "fabric")


@fxprop("wall_fan", "wall", (0.8, 0.25, 0.8), eras=ELEC_MID, rooms=("megablock", "corridor", "server", "reactor", "basement", "bunker", "factory", "kitchen_ind"))
def wall_fan(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.06, 0), (0.75, 0.12, 0.75), "metal2")
    cyy(mb, M, (0, -0.01, 0), 0.3, 0.04, "dark", seg=16)
    for i in range(5):
        bx(mb, M, (0, -0.03, 0), (0.55, 0.01, 0.1), "metal", ry=i / 5 * math.pi + rng.uniform(0, 0.3), rx=0.3)
    cyy(mb, M, (0, -0.04, 0), 0.06, 0.04, "metal2", seg=8)
    for k in range(4):
        bx(mb, M, (0, -0.06, -0.24 + k * 0.16), (0.62, 0.012, 0.012), "metal2")


@fxprop("trash_bags", "floor", (1.1, 0.9, 0.7), eras=ELEC_MID | {"post_apocalyptic"}, rooms=("megablock", "corridor", "alley", "slum", "shelter", "basement"))
def trash_bags(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for k in range(rng.randint(3, 6)):
        r = rng.uniform(0.18, 0.3)
        p = (rng.uniform(-0.35, 0.35), rng.uniform(-0.25, 0.25), r * 0.75 + (0.2 if k > 3 else 0.0))
        sp(mb, M, p, r, rng.choice(("dark", "dark", "fabric2", "leaf")), sub=1, sc=(1.0, 0.9, 0.8))
        cy(mb, M, (p[0], p[1], p[2] + r * 0.8), 0.04, 0.1, "dark", seg=6, r2=0.07)
    for k in range(4):
        cy(mb, M, (rng.uniform(-0.6, 0.6), rng.uniform(-0.5, 0.5), 0.03), 0.03, 0.11, rng.choice(("fabric", "metal", "accent")), seg=8,
           rx=math.pi / 2, rz=rng.uniform(0, 6))
    for k in range(3):
        bx(mb, M, (rng.uniform(-0.6, 0.6), rng.uniform(-0.5, 0.5), 0.004), (0.2, 0.25, 0.008), "paper", rz=rng.uniform(0, 6))


# ----------------------------------------------------------------------------- futures: clinic / solarpunk / apocalypse / crystal
@fxprop("surgical_chair", "floor", (1.0, 2.0, 1.6), eras=ELEC, rooms=("clinic", "medbay", "alienlab", "fx_feature"))
def surgical_chair(mb, x, y, z, rot, rng, era):
    """Reclined cyber-surgery chair under a ring lamp."""
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0.2, 0.08), 0.35, 0.16, "metal2", seg=12)
    cy(mb, M, (0, 0.2, 0.4), 0.08, 0.5, "metal", seg=8)
    bx(mb, M, (0, 0.1, 0.7), (0.6, 0.7, 0.12), "fabric")
    bx(mb, M, (0, -0.55, 0.85), (0.55, 0.7, 0.1), "fabric", rx=-0.5)
    bx(mb, M, (0, 0.75, 0.55), (0.5, 0.6, 0.1), "fabric", rx=0.4)
    sp(mb, M, (0, -0.85, 1.05), 0.12, "fabric", sub=1, sc=(1.2, 0.6, 0.6))
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.38, 0.0, 0.8), (0.08, 0.5, 0.05), "metal2")
        bx(mb, M, (sx * 0.38, -0.05, 0.84), (0.09, 0.08, 0.04), "dark")              # restraints
    strut(mb, M, (0.6, 0.6, 0.0), (0.6, 0.6, 2.0), 0.04, "metal2")
    strut(mb, M, (0.6, 0.6, 2.0), (0.0, -0.6, 1.85), 0.035, "metal2")
    ring(mb, M, (0.0, -0.6, 1.8), 0.25, 0.04, "metal2", seg=16, mseg=4)
    cy(mb, M, (0.0, -0.6, 1.78), 0.21, 0.02, hot(era), seg=14)


@fxprop("planter_box", "floor", (1.6, 0.7, 1.2), eras=FUT | NOW, rooms=("greenhouse", "hydroponics", "habitat", "rooftop_garden", "solarpunk", "garden"))
def planter_box(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.25), (1.5, 0.6, 0.5), "wood")
    for i in range(6):
        bx(mb, M, (-0.75 + i * 0.3, -0.302, 0.25), (0.02, 0.01, 0.48), "wood2")
    bx(mb, M, (0, 0, 0.49), (1.42, 0.52, 0.02), "wood2")
    for k in range(rng.randint(5, 9)):
        p = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.18, 0.18), 0.5))
        h = rng.uniform(0.15, 0.6)
        strut(mb, M, p, p + Vector((rng.uniform(-0.05, 0.05), 0, h)), 0.01, "leaf")
        sp(mb, M, p + Vector((0, 0, h)), rng.uniform(0.09, 0.18), "leaf", sub=1, sc=(1, 1, 0.8))
        if rng.random() < 0.35:
            sp(mb, M, p + Vector((0.06, -0.05, h * 0.8)), 0.04, rng.choice(("fabric", "glass2", "paper")), sub=0)
    if rng.random() < 0.5:                                   # trellis
        for sx in (-0.7, 0.7):
            strut(mb, M, (sx, 0.28, 0.5), (sx, 0.28, 1.6), 0.015, "wood2")
        for zz in (0.9, 1.25, 1.58):
            strut(mb, M, (-0.7, 0.28, zz), (0.7, 0.28, zz), 0.012, "wood2")


@fxprop("solar_panel_rack", "floor", (1.6, 1.0, 1.4), eras=FUT | NOW | {"post_apocalyptic"}, rooms=("rooftop_garden", "solarpunk", "habitat", "shelter", "greenhouse"))
def solar_panel_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.65, 0.65):
        strut(mb, M, (sx, -0.3, 0), (sx, -0.3, 0.7), 0.025, "metal2")
        strut(mb, M, (sx, 0.3, 0), (sx, 0.3, 1.1), 0.025, "metal2")
    p = sub(M, (0, 0, 0.92), rx=0.6)
    bx(mb, p, (0, 0, 0), (1.5, 0.9, 0.04), "metal2")
    for i in range(4):
        for j in range(3):
            bx(mb, p, (-0.56 + i * 0.375, -0.28 + j * 0.28, 0.022), (0.34, 0.25, 0.006), "trim")


@fxprop("scrap_wall", "wall", (2.0, 0.25, 2.2), eras=NOW | {"post_apocalyptic", "near-future", "near_future", "cyberpunk"}, rooms=("shelter", "slum", "wasteland", "makeshift"))
def scrap_wall(mb, x, y, z, rot, rng, era):
    """Patchwork of corrugated sheets, doors and signs bolted together."""
    M = M0(x, y, z, rot)
    for k in range(rng.randint(5, 8)):
        w, h = rng.uniform(0.5, 1.1), rng.uniform(0.6, 1.4)
        u, zz = rng.uniform(-0.75, 0.75), rng.uniform(h / 2, 2.1 - h / 2)
        key = rng.choice(("metal2", "metal", "accent", "wood2", "fabric2", "trim"))
        bx(mb, M, (u, 0.06 - k * 0.01, zz), (w, 0.02, h), key, ry=rng.uniform(-0.08, 0.08))
        for i in range(int(w / 0.1)):
            bx(mb, M, (u - w / 2 + 0.05 + i * 0.1, 0.045 - k * 0.01, zz), (0.02, 0.01, h * 0.95), key, ry=rng.uniform(-0.08, 0.08))
        for sx in (-1, 1):
            bx(mb, M, (u + sx * (w / 2 - 0.05), 0.04 - k * 0.01, zz + h / 2 - 0.05), (0.02, 0.01, 0.02), "dark")
    for sx in (-0.9, 0.9):
        bx(mb, M, (sx, 0.1, 1.1), (0.08, 0.08, 2.2), "wood2")


@fxprop("oil_drum_fire", "floor", (0.7, 0.7, 1.2), eras=MID | NOW | {"post_apocalyptic", "cyberpunk"}, rooms=("shelter", "slum", "wasteland", "alley", "camp", "megablock"))
def oil_drum_fire(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.45), 0.29, 0.9, rng.choice(("accent", "metal2", "fabric2")), seg=12)
    for zz in (0.3, 0.6):
        ring(mb, M, (0, 0, zz), 0.3, 0.015, "metal2", seg=14, mseg=3)
    for k in range(4):
        a = rng.uniform(0, math.tau)
        bx(mb, M, (math.cos(a) * 0.29, math.sin(a) * 0.29, rng.uniform(0.1, 0.3)), (0.06, 0.02, 0.06), "dark", rz=a)
    fire(mb, M, (0, 0, 0.88), 1.0, n=4, rng=rng)


@fxprop("cot", "floor", (0.8, 2.0, 0.55), eras=MID | ELEC | {"post_apocalyptic"}, rooms=("shelter", "bunker", "barracks", "camp", "clinic", "habitat"))
def cot(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.33, 0.33):
        cy(mb, M, (sx, 0, 0.4), 0.02, 1.95, "metal2", seg=6, rx=math.pi / 2)
    for sy in (-0.85, 0.85):
        strut(mb, M, (-0.33, sy - 0.1, 0.0), (0.33, sy + 0.1, 0.4), 0.015, "metal2")
        strut(mb, M, (0.33, sy - 0.1, 0.0), (-0.33, sy + 0.1, 0.4), 0.015, "metal2")
    bx(mb, M, (0, 0, 0.41), (0.64, 1.9, 0.02), rng.choice(("fabric2", "leaf", "paper")))
    bx(mb, M, (0.04, 0.3, 0.44), (0.6, 1.0, 0.05), rng.choice(("fabric", "rug")), rz=rng.uniform(-0.1, 0.1))
    sp(mb, M, (0, -0.75, 0.47), 0.15, "paper", sub=1, sc=(1.5, 1, 0.5))


@fxprop("crystal_cluster", "floor", (1.3, 1.3, 2.2), eras=FUT, rooms=("crystal", "alien", "alienlab", "cave", "temple_fut"))
def crystal_cluster(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    g = hot(era)
    for k in range(rng.randint(4, 8)):
        a, r = rng.uniform(0, math.tau), rng.uniform(0, 0.35)
        h = rng.uniform(0.5, 2.0) * (1.0 if k == 0 else 0.6)
        tilt = rng.uniform(0.0, 0.5)
        m = sub(M, (math.cos(a) * r, math.sin(a) * r, 0), rx=tilt * math.sin(a), ry=-tilt * math.cos(a))
        cy(mb, m, (0, 0, h * 0.4), rng.uniform(0.08, 0.18), h * 0.8, g if k % 2 == 0 else "glass", seg=6)
        cy(mb, m, (0, 0, h * 0.9), rng.uniform(0.08, 0.18), h * 0.2, g if k % 2 == 0 else "glass", seg=6, r2=0.0)
    sp(mb, M, (0, 0, 0.05), 0.45, "stone", sub=1, sc=(1.2, 1.2, 0.3))


@fxprop("glow_pillar", "floor", (1.0, 1.0, 4.0), eras=FUT, rooms=("fx_feature",))
def glow_pillar(mb, x, y, z, rot, rng, era):
    """Far-future fluted pillar with a light channel running up it (height ~4 m, features scale)."""
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.5, 0), (0.45, 0.2), (0.3, 0.35), (0.26, 3.5), (0.4, 3.7), (0.5, 3.95), (0, 3.95)], "wall", seg=8)
    for i in range(4):
        a = i / 4 * math.tau
        bx(mb, M, (math.cos(a) * 0.27, math.sin(a) * 0.27, 1.9), (0.05, 0.05, 3.1), hot(era), rz=a)

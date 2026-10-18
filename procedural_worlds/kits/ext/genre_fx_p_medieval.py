"""genre_fx props: medieval / fantasy (weapons, armour, regalia, alchemy, forge, hall furniture).
Builders follow kits/props.py: fn(mb, x, y, z, rot, rng, era); wall props face local -Y with their back at +Y;
tall wall props (size z >= 1) start at z, short ones are centred on z; hanging props hang below z."""
import math
from mathutils import Vector
from ..props import OLD, MID
from .genre_fx_geom import (fxprop, M0, sub, bx, cy, cyx, cyy, sp, lathe, prism, slab, ring, strut, polyline,
                            arch_pts, flame, fire, candle, book, table, barrel_shape, surface, ANC, MED, EARLY, PRE)

ARMS = ("armoury", "castle", "barracks", "dungeon", "smithy")


# ----------------------------------------------------------------------------- weapon parts
def sword(mb, M, L=0.9, key="metal", grip="fabric2"):
    """Sword with its pommel at the local origin and the blade along +Z."""
    sp(mb, M, (0, 0, 0.0), 0.028, "metal2", sub=1)
    cy(mb, M, (0, 0, 0.1), 0.018, 0.17, grip, seg=6)
    bx(mb, M, (0, 0, 0.2), (0.24, 0.035, 0.035), "metal2")
    prism(mb, M, (0, 0, 0), [(-0.032, 0.21), (0.032, 0.21), (0.026, 0.21 + L * 0.82), (0, 0.21 + L), (-0.026, 0.21 + L * 0.82)], 0.012, key)


def spear(mb, M, L=2.0):
    cy(mb, M, (0, 0, L / 2), 0.018, L, "wood2", seg=6)
    prism(mb, M, (0, 0, 0), [(0, L - 0.02), (0.042, L + 0.08), (0, L + 0.32), (-0.042, L + 0.08)], 0.014, "metal")


def axe(mb, M, L=0.9):
    cy(mb, M, (0, 0, L / 2), 0.02, L, "wood2", seg=6)
    prism(mb, M, (0, 0, 0), [(0.0, L - 0.2), (0.15, L - 0.27), (0.2, L - 0.08), (0.15, L + 0.08), (0, L - 0.02)], 0.03, "metal")


def mace(mb, M, L=0.8):
    cy(mb, M, (0, 0, L / 2), 0.022, L, "wood2", seg=6)
    sp(mb, M, (0, 0, L + 0.06), 0.08, "metal2", sub=1)
    for a in range(6):
        t = a / 6 * math.tau
        cy(mb, M, (math.cos(t) * 0.08, math.sin(t) * 0.08, L + 0.06), 0.02, 0.06, "metal", seg=4, r2=0.0, ry=math.pi / 2, rz=t)


def gladius(mb, M, L=0.6):
    sword(mb, M, L, grip="wood2")


def trident(mb, M, L=1.9):
    cy(mb, M, (0, 0, L / 2), 0.016, L, "wood2", seg=6)
    bx(mb, M, (0, 0, L), (0.24, 0.02, 0.03), "metal")
    for sx in (-0.11, 0, 0.11):
        cy(mb, M, (sx, 0, L + 0.14), 0.012, 0.28, "metal", seg=4, r2=0.002)


def weapon(mb, M, kind, era):
    {"sword": lambda: sword(mb, M, 0.85), "spear": lambda: spear(mb, M, 1.9), "axe": lambda: axe(mb, M, 0.9),
     "mace": lambda: mace(mb, M, 0.75), "gladius": lambda: gladius(mb, M, 0.55), "trident": lambda: trident(mb, M, 1.8)}[kind]()


def weapon_kinds(era):
    return ("gladius", "spear", "trident", "sword") if era in ANC else ("sword", "spear", "axe", "mace", "sword")


# ----------------------------------------------------------------------------- arms & armour
@fxprop("weapon_rack", "wall", (1.4, 0.35, 2.0), eras=OLD, rooms=ARMS)
def weapon_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.66, 0.66):
        bx(mb, M, (sx, 0.08, 1.0), (0.08, 0.08, 2.0), "wood2")
    for zz, d in ((0.3, 0.22), (1.35, 0.16)):
        bx(mb, M, (0, 0.02, zz), (1.42, d, 0.06), "wood")
    bx(mb, M, (0, 0.14, 1.0), (1.3, 0.03, 1.7), "wood2")
    for i in range(6):
        k = rng.choice(weapon_kinds(era))
        px = -0.55 + i * 0.22
        m = sub(M, (px, -0.02, 0.33 if k in ("spear", "trident") else 0.36), ry=rng.uniform(-0.04, 0.04))
        weapon(mb, m, k, era)


@fxprop("spear_rack", "floor", (1.2, 0.6, 2.3), eras=OLD, rooms=ARMS)
def spear_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.05), (1.2, 0.6, 0.1), "wood2")
    for sx in (-0.55, 0.55):
        strut(mb, M, (sx, -0.25, 0.1), (sx, 0.0, 1.3), 0.03, "wood")
        strut(mb, M, (sx, 0.25, 0.1), (sx, 0.0, 1.3), 0.03, "wood")
    bx(mb, M, (0, 0, 1.25), (1.2, 0.08, 0.06), "wood")
    for i in range(rng.randint(4, 7)):
        px = -0.45 + i * 0.15
        side = 1 if i % 2 else -1
        m = sub(M, (px, side * 0.18, 0.1), rx=-side * 0.14)
        (spear if era not in ANC or i % 3 else trident)(mb, m, 1.9 + rng.uniform(-0.1, 0.1))


@fxprop("shield", "wall", (0.8, 0.12, 0.9), eras=OLD, rooms=ARMS + ("hall", "tavern", "mead_hall"))
def shield(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    kind = "round" if era in ANC or rng.random() < 0.45 else "kite"
    paint = rng.choice(("fabric", "accent", "trim", "wall2"))
    if kind == "round":
        r = rng.uniform(0.34, 0.42)
        cyy(mb, M, (0, 0.02, 0), r, 0.04, paint, seg=16)
        ring(mb, sub(M, (0, 0, 0), rx=math.pi / 2), (0, 0, 0.0), r, 0.022, "metal2", seg=16, mseg=4)
        sp(mb, M, (0, -0.02, 0), 0.08, "metal", sub=1, sc=(1, 0.6, 1))
        if rng.random() < 0.6:
            for a in range(4 if rng.random() < 0.5 else 2):
                bx(mb, M, (0, -0.004, 0), (r * 1.9, 0.01, 0.07), "paper", ry=a * math.pi / (4 if a else 1) + 0.4)
    else:
        pts = [(-0.34, 0.36), (0.34, 0.36), (0.32, 0.0), (0.18, -0.3), (0, -0.48), (-0.18, -0.3), (-0.32, 0.0)]
        prism(mb, M, (0, 0.02, 0), pts, 0.04, paint)
        prism(mb, M, (0, -0.004, 0.02), [(-0.06, 0.34), (0.06, 0.34), (0.06, -0.36), (0, -0.44), (-0.06, -0.36)], 0.01, "paper")
        bx(mb, M, (0, -0.006, 0.12), (0.62, 0.01, 0.1), "paper")


@fxprop("armour_stand", "floor", (0.8, 0.6, 1.95), eras=OLD, rooms=ARMS + ("castle", "hall", "museum"))
def armour_stand(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.04), (0.6, 0.12, 0.08), "wood2")
    bx(mb, M, (0, 0, 0.04), (0.12, 0.6, 0.08), "wood2")
    cy(mb, M, (0, 0, 0.55), 0.03, 1.0, "wood2", seg=6)
    gold = era in ANC
    mk = "metal" if not gold else "glass2"
    lathe(mb, M, (0, 0, 0.95), [(0.2, 0.0), (0.24, 0.18), (0.27, 0.42), (0.22, 0.55), (0.12, 0.6), (0, 0.6)], mk, seg=10, sc=(1, 0.7))
    lathe(mb, M, (0, 0, 0.62), [(0.0, 0.0), (0.27, 0.0), (0.23, 0.36), (0, 0.36)], "fabric" if not gold else "fabric2", seg=10, sc=(1, 0.75))
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.27, 0, 1.47), 0.11, "metal2", sub=1, sc=(1.1, 0.9, 0.7))
        cy(mb, M, (sx * 0.31, 0, 1.18), 0.055, 0.42, mk, seg=8)
    if gold:                                   # crested hoplite helm
        lathe(mb, M, (0, 0, 1.58), [(0.11, 0), (0.13, 0.12), (0.11, 0.24), (0, 0.28)], mk, seg=10)
        prism(mb, M, (0, 0, 1.8), [(-0.02, 0), (0.02, 0), (0.0, 0.2), (-0.22, 0.12)], 0.05, "fabric", rz=math.pi / 2)
    else:                                      # great helm with visor slit
        cy(mb, M, (0, 0, 1.7), 0.12, 0.26, mk, seg=10)
        lathe(mb, M, (0, 0, 1.83), [(0.12, 0), (0.08, 0.06), (0, 0.08)], mk, seg=10)
        bx(mb, M, (0, -0.115, 1.73), (0.16, 0.02, 0.025), "dark")
    if rng.random() < 0.5:                      # spear propped beside it
        spear(mb, sub(M, (0.4, 0.1, 0.0), ry=-0.06), 1.9)


@fxprop("training_dummy", "floor", (0.8, 0.5, 1.8), eras=OLD, rooms=ARMS + ("courtyard",))
def training_dummy(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.1), 0.25, 0.2, "wood2", seg=8, r2=0.2)
    cy(mb, M, (0, 0, 0.8), 0.04, 1.4, "wood2", seg=6)
    bx(mb, M, (0, 0, 1.25), (0.9, 0.06, 0.06), "wood2", ry=rng.uniform(-0.1, 0.1))
    sp(mb, M, (0, 0, 1.15), 0.24, "fabric2", sub=1, sc=(1.0, 0.75, 1.5))
    sp(mb, M, (0, 0, 1.62), 0.13, "fabric2", sub=1)
    for zz in (0.95, 1.3):
        cy(mb, M, (0, 0, zz), 0.245, 0.03, "wood2", seg=10)
    bx(mb, M, (0.1, -0.2, 1.1), (0.04, 0.02, 0.3), "dark", ry=0.5)


@fxprop("weapons_barrel", "floor", (0.65, 0.65, 1.6), eras=OLD, rooms=ARMS + ("storage",))
def weapons_barrel(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    barrel_shape(mb, M, (0, 0, 0), 0.28, 0.75, "wood", "metal2")
    for i in range(rng.randint(4, 7)):
        a = rng.uniform(0, math.tau)
        k = rng.choice(weapon_kinds(era))
        m = sub(M, (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.3 if k != "spear" else 0.1),
                rx=rng.uniform(-0.25, 0.25), ry=rng.uniform(-0.25, 0.25))
        weapon(mb, m, k, era)


@fxprop("sword", "surface", (0.9, 0.2, 0.05), eras=OLD, rooms=ARMS + ("castle", "tavern", "throne"))
def sword_lying(mb, x, y, z, rot, rng, era):
    sword(mb, sub(M0(x, y, z + 0.02, rot), (-0.45, 0, 0), ry=math.pi / 2, rz=0.0), 0.7 if era not in ANC else 0.5)


@fxprop("dagger", "surface", (0.35, 0.1, 0.04), eras=OLD, rooms=ARMS + ("tavern", "alchemy", "ritual", "crypt", "study"))
def dagger(mb, x, y, z, rot, rng, era):
    sword(mb, sub(M0(x, y, z + 0.018, rot), (-0.16, 0, 0), ry=math.pi / 2), 0.2)


@fxprop("sword_in_stone", "floor", (1.3, 1.2, 1.5), eras=OLD)
def sword_in_stone(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    sp(mb, M, (0, 0, 0.25), 0.62, "stone", sub=1, sc=(1.0, 0.85, 0.6))
    sp(mb, M, (0.25, 0.2, 0.42), 0.35, "stone", sub=1, sc=(1, 1, 0.8))
    sword(mb, sub(M, (0.05, 0, 1.3), rx=math.pi + 0.08), 0.95)
    for i in range(5):
        sp(mb, M, (rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6), 0.03), rng.uniform(0.05, 0.12), "leaf", sub=1, sc=(1, 1, 0.4))


# ----------------------------------------------------------------------------- regalia & hangings
@fxprop("banner", "wall", (0.9, 0.08, 2.6), eras=OLD, rooms=("castle", "throne", "armoury", "temple", "hall", "mead_hall"))
def banner(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    L = rng.uniform(1.9, 2.4)
    cyx(mb, M, (0, 0.0, L + 0.12), 0.025, 1.0, "wood2", seg=6)
    for sx in (-0.52, 0.52):
        sp(mb, M, (sx, 0, L + 0.12), 0.045, "metal", sub=1)
    col = rng.choice(("fabric", "accent", "fabric2"))
    tail = rng.choice(("swallow", "point", "flat"))
    bot = {"swallow": [(0.42, 0.0), (0.0, 0.3), (-0.42, 0.0)], "point": [(0.42, 0.25), (0.0, 0.0), (-0.42, 0.25)],
           "flat": [(0.42, 0.1), (-0.42, 0.1)]}[tail]
    pts = [(-0.42, L + 0.08), (0.42, L + 0.08)] + bot
    prism(mb, M, (0, 0.02, 0), pts, 0.03, col)
    for sx in (-0.36, 0.36):
        bx(mb, M, (sx, 0.0, L * 0.6 + 0.2), (0.05, 0.02, L * 0.75), "glass2")
    em = rng.choice(("disc", "diamond", "chevron"))
    zc = L * 0.62
    if em == "disc":
        cyy(mb, M, (0, 0.0, zc), 0.18, 0.012, "paper", seg=12)
        cyy(mb, M, (0, -0.006, zc), 0.08, 0.012, col, seg=8)
    elif em == "diamond":
        prism(mb, M, (0, 0.0, 0), [(0, zc - 0.25), (0.18, zc), (0, zc + 0.25), (-0.18, zc)], 0.012, "paper")
    else:
        for k in range(2):
            prism(mb, M, (0, 0.0, 0), [(-0.3, zc - 0.1 - k * 0.22), (0, zc + 0.08 - k * 0.22), (0.3, zc - 0.1 - k * 0.22),
                                       (0.3, zc - 0.02 - k * 0.22), (0, zc + 0.16 - k * 0.22), (-0.3, zc - 0.02 - k * 0.22)], 0.012, "paper")


@fxprop("tapestry", "wall", (2.2, 0.1, 2.5), eras=OLD, rooms=("castle", "throne", "hall", "wizard", "monastery", "temple"))
def tapestry(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    W, H = rng.uniform(1.6, 2.2), rng.uniform(1.6, 2.1)
    z0 = 0.35
    cyx(mb, M, (0, 0.0, z0 + H + 0.06), 0.03, W + 0.25, "wood2", seg=6)
    n = 6
    base = rng.choice(("fabric", "accent", "rug", "wall2"))
    for i in range(n):                                  # draped folds
        u = -W / 2 + W * (i + 0.5) / n
        bx(mb, M, (u, 0.02 + (0.02 if i % 2 else 0.0), z0 + H / 2), (W / n + 0.01, 0.025, H), base, rz=(0.12 if i % 2 else -0.12))
    for zz in (z0 + 0.12, z0 + H - 0.12):
        bx(mb, M, (0, -0.005, zz), (W * 0.98, 0.03, 0.1), "glass2")
    for sx in (-1, 1):
        bx(mb, M, (sx * (W / 2 - 0.08), -0.005, z0 + H / 2), (0.1, 0.03, H * 0.95), "glass2")
    motif = rng.choice(("tree", "beast", "stars"))
    zc = z0 + H / 2
    if motif == "tree":
        bx(mb, M, (0, -0.02, zc - 0.2), (0.1, 0.02, H * 0.45), "wood2")
        sp(mb, M, (0, -0.02, zc + 0.25), H * 0.24, "leaf", sub=1, sc=(1.3, 0.08, 1.0))
    elif motif == "beast":
        sp(mb, M, (0, -0.02, zc), H * 0.18, "paper", sub=1, sc=(1.6, 0.08, 0.9))
        sp(mb, M, (W * 0.18, -0.025, zc + H * 0.14), H * 0.09, "paper", sub=1, sc=(1, 0.1, 1))
        for k in range(4):
            bx(mb, M, (-W * 0.15 + k * W * 0.1, -0.02, zc - H * 0.2), (0.05, 0.02, H * 0.2), "paper")
    else:
        for k in range(7):
            cyy(mb, M, (rng.uniform(-W * 0.35, W * 0.35), -0.02, zc + rng.uniform(-H * 0.3, H * 0.3)), rng.uniform(0.04, 0.1), 0.01, "paper", seg=5)
    for i in range(int(W / 0.08)):                      # fringe
        bx(mb, M, (-W / 2 + 0.04 + i * 0.08, 0.01, z0 - 0.06), (0.02, 0.02, 0.12), "glass2")


@fxprop("throne_gilded", "floor", (1.3, 1.1, 2.6), eras=OLD | MID, rooms=("fx_feature",))
def throne_gilded(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    g = "glass2"
    bx(mb, M, (0, 0.05, 0.12), (1.3, 1.1, 0.24), "stone")
    bx(mb, M, (0, 0.05, 0.42), (0.95, 0.85, 0.36), "wood2")
    bx(mb, M, (0, -0.0, 0.66), (0.86, 0.75, 0.12), "fabric")
    prism(mb, M, (0, 0.4, 0), arch_pts(0.95, 2.55, 1.85, seg=8, pointed=True), 0.16, "wood2")
    prism(mb, M, (0, 0.31, 0), [(-0.35, 0.75), (0.35, 0.75)] + arch_pts(0.7, 2.3, 1.75, seg=8, pointed=True)[2:], 0.04, "fabric")
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.5, 0.0, 0.85), (0.12, 0.8, 0.12), g)
        bx(mb, M, (sx * 0.5, -0.35, 0.6), (0.12, 0.12, 0.4), g)
        cy(mb, M, (sx * 0.5, 0.4, 1.3), 0.06, 2.3, g, seg=8)
        sp(mb, M, (sx * 0.5, 0.4, 2.5), 0.09, g, sub=1)
        sp(mb, M, (sx * 0.5, -0.38, 0.93), 0.07, g, sub=1)
    sp(mb, M, (0, 0.38, 2.62), 0.1, g, sub=1)
    cy(mb, M, (0, 0.33, 2.0), 0.13, 0.02, g, seg=10, rx=math.pi / 2)


@fxprop("throne_stone", "floor", (1.4, 1.1, 1.9), eras=OLD)
def throne_stone(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.05, 0.15), (1.5, 1.2, 0.3), "stone")
    bx(mb, M, (0, 0.05, 0.5), (1.0, 0.9, 0.4), "stone")
    bx(mb, M, (0, 0.42, 1.2), (1.1, 0.25, 1.6), "stone")
    prism(mb, M, (0, 0.42, 0), [(-0.55, 1.9), (0.55, 1.9), (0.0, 2.15)], 0.25, "stone")
    for sx in (-1, 1):
        bx(mb, M, (sx * 0.6, 0.0, 0.8), (0.25, 0.9, 0.25), "stone")
        sp(mb, M, (sx * 0.6, -0.42, 0.98), 0.14, "stone", sub=1, sc=(0.9, 1.2, 0.9))     # beast-head armrest ends
        bx(mb, M, (sx * 0.6, -0.5, 0.95), (0.1, 0.06, 0.04), "dark")
    bx(mb, M, (0, -0.0, 0.73), (0.9, 0.7, 0.06), "fabric2")


@fxprop("throne_bone", "floor", (1.3, 1.1, 2.4), eras=OLD)
def throne_bone(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.05, 0.2), (1.2, 1.0, 0.4), "dark")
    bx(mb, M, (0, 0.0, 0.47), (0.9, 0.75, 0.14), "fabric2")
    for i in range(9):
        u = -0.45 + i * 0.1125
        top = 1.6 + 0.6 * math.cos(u * 2.6)
        strut(mb, M, (u * 0.9, 0.38, 0.4), (u * 1.15, 0.45, top), 0.025, "paper", seg=6)
        sp(mb, M, (u * 1.15, 0.45, top), 0.04, "paper", sub=1)
    for k in range(5):                                 # crown of skulls
        u = -0.4 + k * 0.2
        skull_shape(mb, sub(M, (u, 0.45, 1.65 + 0.55 * math.cos(u * 2.6)), rz=math.pi + rng.uniform(-0.3, 0.3)), 0.9)
    for sx in (-1, 1):
        strut(mb, M, (sx * 0.5, -0.35, 0.4), (sx * 0.5, -0.35, 0.85), 0.03, "paper", seg=6)
        strut(mb, M, (sx * 0.5, -0.4, 0.85), (sx * 0.5, 0.4, 0.85), 0.035, "paper", seg=6)
        skull_shape(mb, sub(M, (sx * 0.5, -0.42, 0.92), rz=math.pi), 0.8)


def skull_shape(mb, M, s=1.0):
    """Skull facing local -Y, base at origin."""
    sp(mb, M, (0, 0, 0.07 * s), 0.07 * s, "paper", sub=1, sc=(0.85, 1.0, 0.9))
    bx(mb, M, (0, -0.04 * s, 0.022 * s), (0.08 * s, 0.06 * s, 0.04 * s), "paper")
    for sx in (-1, 1):
        sp(mb, M, (sx * 0.024 * s, -0.062 * s, 0.065 * s), 0.016 * s, "dark", sub=0)
    bx(mb, M, (0, -0.069 * s, 0.04 * s), (0.012 * s, 0.01 * s, 0.018 * s), "dark")


FEATURE_ROOMS = ("fx_feature",)


@fxprop("chandelier", "hanging", (1.4, 1.4, 1.3), eras=OLD | MID, rooms=FEATURE_ROOMS)
def chandelier(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    drop = rng.uniform(0.6, 1.0)
    for k in range(int(drop / 0.09)):
        ring(mb, sub(M, (0, 0, -0.05 - k * 0.09), rx=math.pi / 2, rz=(k % 2) * math.pi / 2), (0, 0, 0), 0.03, 0.007, "metal2", seg=6, mseg=3)
    zr = -drop - 0.05
    Rr = rng.uniform(0.5, 0.7)
    ring(mb, M, (0, 0, zr), Rr, 0.025, "metal2", seg=18, mseg=4)
    ring(mb, M, (0, 0, zr + 0.25), Rr * 0.45, 0.02, "metal2", seg=12, mseg=4)
    n = rng.choice((6, 8, 10))
    for i in range(n):
        a = i / n * math.tau
        strut(mb, M, (0, 0, zr + 0.4), (math.cos(a) * Rr, math.sin(a) * Rr, zr), 0.012, "metal2")
        candle(mb, M, (math.cos(a) * Rr, math.sin(a) * Rr, zr + 0.02), 0.12, 0.022)
    strut(mb, M, (0, 0, -0.05), (0, 0, zr + 0.4), 0.015, "metal2")
    sp(mb, M, (0, 0, zr - 0.06), 0.06, "metal2", sub=1)


@fxprop("candelabra", "surface", (0.4, 0.15, 0.55), eras=OLD | MID, rooms=("castle", "throne", "temple", "crypt", "haunted", "ritual", "wizard", "seance", "monastery"))
def candelabra(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.08, 0), (0.07, 0.02), (0.02, 0.05), (0.015, 0.3), (0.03, 0.32), (0, 0.33)], "metal", seg=10)
    arms = rng.choice((1, 2))
    for k in range(1, arms + 1):
        for sx in (-1, 1):
            u = sx * 0.09 * k
            polyline(mb, M, [(0, 0, 0.26 - 0.03 * k), (u, 0, 0.2 - 0.03 * k), (u, 0, 0.32)], 0.008, "metal")
            cy(mb, M, (u, 0, 0.33), 0.022, 0.02, "metal", seg=8)
            candle(mb, M, (u, 0, 0.34), rng.uniform(0.08, 0.14), 0.015, lit=rng.random() < 0.85)
    candle(mb, M, (0, 0, 0.33), 0.14, 0.016)


@fxprop("torch_wall", "wall", (0.25, 0.35, 0.7), eras=OLD, rooms=("castle", "dungeon", "crypt", "armoury", "temple", "throne", "mead_hall"))
def torch_wall(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.13, 0), (0.1, 0.03, 0.22), "metal2")
    strut(mb, M, (0, 0.12, -0.05), (0, -0.05, 0.02), 0.012, "metal2")
    ring(mb, M, (0, -0.06, 0.03), 0.04, 0.01, "metal2", seg=8, mseg=3)
    m = sub(M, (0, -0.07, -0.1), rx=-0.3)
    cy(mb, m, (0, 0, 0.15), 0.025, 0.42, "wood2", seg=6, r2=0.035)
    cy(mb, m, (0, 0, 0.38), 0.05, 0.08, "fabric2", seg=6)
    fire(mb, m, (0, 0, 0.4), 0.85, n=3, rng=rng)


@fxprop("brazier", "floor", (0.8, 0.8, 1.2), eras=OLD, rooms=("temple", "throne", "castle", "crypt", "ritual", "mead_hall", "arena"))
def brazier(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    h = rng.uniform(0.75, 1.0)
    for i in range(3):
        a = i / 3 * math.tau
        strut(mb, M, (math.cos(a) * 0.32, math.sin(a) * 0.32, 0), (math.cos(a) * 0.18, math.sin(a) * 0.18, h), 0.022, "metal2")
        sp(mb, M, (math.cos(a) * 0.33, math.sin(a) * 0.33, 0.03), 0.04, "metal2", sub=0)
    ring(mb, M, (0, 0, h * 0.45), 0.24, 0.012, "metal2", seg=12, mseg=3)
    lathe(mb, M, (0, 0, h), [(0.0, -0.06), (0.15, -0.05), (0.3, 0.06), (0.34, 0.14), (0.31, 0.15)], "metal", seg=12)
    for k in range(5):
        sp(mb, M, (rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), h + 0.1), 0.07, "dark", sub=0)
    fire(mb, M, (0, 0, h + 0.1), 1.0, n=4, rng=rng)


@fxprop("lantern_hanging", "hanging", (0.3, 0.3, 0.7), eras=OLD | MID, rooms=FEATURE_ROOMS)
def lantern_hanging(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    drop = rng.uniform(0.15, 0.4)
    strut(mb, M, (0, 0, 0), (0, 0, -drop), 0.006, "metal2")
    zb = -drop - 0.35
    ring(mb, sub(M, (0, 0, -drop - 0.02), rx=math.pi / 2), (0, 0, 0), 0.03, 0.007, "metal2", seg=6, mseg=3)
    cy(mb, M, (0, 0, zb + 0.32), 0.12, 0.08, "metal2", seg=6, r2=0.03)
    bx(mb, M, (0, 0, zb + 0.15), (0.15, 0.15, 0.22), "lampshade")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx(mb, M, (sx * 0.08, sy * 0.08, zb + 0.15), (0.02, 0.02, 0.26), "metal2")
    bx(mb, M, (0, 0, zb + 0.02), (0.19, 0.19, 0.04), "metal2")
    flame(mb, M, (0, 0, zb + 0.08), 1.0)


# ----------------------------------------------------------------------------- treasure
@fxprop("treasure_chest", "floor", (0.95, 0.65, 0.8), eras=OLD, rooms=("treasure", "castle", "pirate", "dungeon", "cabin", "hold", "crypt"))
def treasure_chest(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    W, D, H = 0.9, 0.58, 0.42
    bx(mb, M, (0, 0, H / 2), (W, D, H), "wood")
    for sx in (-0.3, 0.3):
        bx(mb, M, (sx, 0, H / 2), (0.06, D + 0.02, H + 0.01), "metal2")
    arch = [(D / 2 * math.cos(a), 0.17 * math.sin(a)) for a in (i / 8 * math.pi for i in range(9))]
    is_open = rng.random() < 0.45
    if is_open:
        lid = sub(M, (0, D / 2, H), rx=-1.9)
        prism(mb, lid, (0, 0, 0), [(u - D / 2, v) for u, v in arch], W, "wood", rz=math.pi / 2)
        for k in range(9):
            sp(mb, M, (rng.uniform(-0.35, 0.35), rng.uniform(-0.2, 0.2), H - 0.02), rng.uniform(0.08, 0.13), "glass2", sub=1, sc=(1, 1, 0.5))
        for k in range(3):
            sp(mb, M, (rng.uniform(-0.3, 0.3), rng.uniform(-0.15, 0.15), H + 0.06), 0.03, rng.choice(("accent", "fabric", "glass")), sub=0)
    else:
        prism(mb, M, (0, 0, H), arch, W, "wood", rz=math.pi / 2)
        for sx in (-0.3, 0.3):
            prism(mb, M, (sx, 0, H), [(u * 1.04, v * 1.08) for u, v in arch], 0.06, "metal2", rz=math.pi / 2)
        bx(mb, M, (0, -D / 2 - 0.01, H - 0.02), (0.12, 0.03, 0.14), "glass2")


@fxprop("treasure_pile", "floor", (1.5, 1.3, 0.7), eras=OLD, rooms=("treasure", "hold", "dragon", "fx_feature"))
def treasure_pile(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    sp(mb, M, (0, 0, 0.05), 0.7, "glass2", sub=2, sc=(1.0, 0.85, 0.45))
    for k in range(14):
        a, r = rng.uniform(0, math.tau), rng.uniform(0.2, 0.8)
        cy(mb, M, (math.cos(a) * r, math.sin(a) * r, 0.0 + max(0.0, 0.28 - r * 0.32)), 0.035, 0.008, "glass2", seg=8,
           rx=rng.uniform(-0.5, 0.5), ry=rng.uniform(-0.5, 0.5))
    for k in range(4):
        a, r = rng.uniform(0, math.tau), rng.uniform(0.1, 0.5)
        sp(mb, M, (math.cos(a) * r, math.sin(a) * r, 0.3 - r * 0.25), 0.04, rng.choice(("accent", "fabric", "glass")), sub=0)
    goblet_shape(mb, sub(M, (0.25, -0.1, 0.22), ry=0.4), 1.2)
    ring(mb, M, (-0.2, 0.1, 0.33), 0.11, 0.015, "glass2", seg=12, mseg=3)              # crown
    for i in range(6):
        a = i / 6 * math.tau
        cy(mb, M, (-0.2 + math.cos(a) * 0.11, 0.1 + math.sin(a) * 0.11, 0.37), 0.015, 0.08, "glass2", seg=4, r2=0.0)


def goblet_shape(mb, M, s=1.0, key="glass2"):
    lathe(mb, M, (0, 0, 0), [(0.04 * s, 0), (0.035 * s, 0.01 * s), (0.008 * s, 0.03 * s), (0.008 * s, 0.09 * s),
                             (0.035 * s, 0.11 * s), (0.045 * s, 0.17 * s), (0.0, 0.16 * s)], key, seg=10)


@fxprop("goblet", "surface", (0.1, 0.1, 0.18), eras=OLD, rooms=("castle", "throne", "tavern", "temple", "treasure", "ritual", "mead_hall", "banquet"))
def goblet(mb, x, y, z, rot, rng, era):
    goblet_shape(mb, M0(x, y, z, rot), rng.uniform(0.9, 1.1), rng.choice(("glass2", "metal")))


@fxprop("coin_stack", "surface", (0.15, 0.15, 0.08), eras=OLD, rooms=("treasure", "tavern", "castle", "pirate", "cabin", "shop"))
def coin_stack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for s in range(rng.randint(1, 3)):
        ox, oy = rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)
        n = rng.randint(2, 7)
        cy(mb, M, (ox, oy, n * 0.006), 0.022, n * 0.012, "glass2", seg=8)
    bx(mb, M, (0.06, 0.04, 0.04), (0.08, 0.08, 0.08), "fabric2", rz=0.5)


# ----------------------------------------------------------------------------- alchemy & magic
def flask(mb, M, c, kind, liquid, s=1.0):
    if kind == "round":
        sp(mb, M, (c[0], c[1], c[2] + 0.06 * s), 0.06 * s, liquid, sub=1)
        cy(mb, M, (c[0], c[1], c[2] + 0.14 * s), 0.014 * s, 0.07 * s, "glass", seg=6)
        cy(mb, M, (c[0], c[1], c[2] + 0.18 * s), 0.017 * s, 0.02 * s, "wood2", seg=6)
    elif kind == "vial":
        cy(mb, M, (c[0], c[1], c[2] + 0.07 * s), 0.02 * s, 0.14 * s, liquid, seg=6)
        cy(mb, M, (c[0], c[1], c[2] + 0.15 * s), 0.022 * s, 0.025 * s, "wood2", seg=6)
    elif kind == "cone":
        cy(mb, M, (c[0], c[1], c[2] + 0.05 * s), 0.055 * s, 0.1 * s, liquid, seg=8, r2=0.016 * s)
        cy(mb, M, (c[0], c[1], c[2] + 0.13 * s), 0.016 * s, 0.06 * s, "glass", seg=6)
    else:   # square bottle
        bx(mb, M, (c[0], c[1], c[2] + 0.07 * s), (0.07 * s, 0.07 * s, 0.14 * s), liquid)
        cy(mb, M, (c[0], c[1], c[2] + 0.16 * s), 0.015 * s, 0.04 * s, "glass", seg=6)


LIQ = ("accent", "glass", "glass2", "fabric", "leaf")


@fxprop("potion", "surface", (0.12, 0.12, 0.2), eras=PRE, rooms=("alchemy", "wizard", "witch", "apothecary", "lab", "plague"))
def potion(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for k in range(rng.randint(1, 3)):
        flask(mb, M, (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0), rng.choice(("round", "vial", "cone", "square")), rng.choice(LIQ),
              rng.uniform(0.7, 1.2))


@fxprop("potion_shelf", "wall", (1.2, 0.32, 1.9), eras=PRE, rooms=("alchemy", "wizard", "witch", "apothecary", "plague"))
def potion_shelf(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.58, 0.58):
        bx(mb, M, (sx, 0, 0.95), (0.05, 0.3, 1.9), "wood2")
    bx(mb, M, (0, 0.14, 0.95), (1.2, 0.02, 1.9), "wood")
    for zz in (0.05, 0.5, 0.95, 1.4, 1.86):
        bx(mb, M, (0, 0, zz), (1.2, 0.3, 0.035), "wood2")
        if zz > 1.8:
            continue
        u = -0.5
        while u < 0.5:
            s = rng.uniform(0.7, 1.35)
            flask(mb, M, (u, rng.uniform(-0.05, 0.04), zz + 0.018), rng.choice(("round", "vial", "cone", "square", "round")),
                  rng.choice(LIQ), s)
            u += 0.07 * s + rng.uniform(0.04, 0.1)
    for k in range(2):                                     # labels / jars of leaves
        cy(mb, M, (rng.uniform(-0.4, 0.4), 0.0, 1.86 + 0.08), 0.06, 0.16, "paper", seg=8)


@fxprop("alchemy_table", "floor", (1.7, 0.85, 1.1), eras=PRE, rooms=("alchemy", "wizard", "witch", "lab"))
def alchemy_table(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    table(mb, M, 1.6, 0.8, 0.82, "wood", leg=0.09, top=0.07)
    bx(mb, M, (0, 0, 0.18), (1.4, 0.65, 0.04), "wood2")
    t = 0.82
    # retort on a stand over a burner
    for i in range(3):
        a = i / 3 * math.tau
        strut(mb, M, (-0.5 + math.cos(a) * 0.09, 0.1 + math.sin(a) * 0.09, t), (-0.5, 0.1, t + 0.16), 0.006, "metal2")
    ring(mb, M, (-0.5, 0.1, t + 0.16), 0.07, 0.006, "metal2", seg=10, mseg=3)
    flame(mb, M, (-0.5, 0.1, t + 0.02), 1.2)
    sp(mb, M, (-0.5, 0.1, t + 0.24), 0.09, rng.choice(("accent", "glass2")), sub=1)
    strut(mb, M, (-0.45, 0.1, t + 0.3), (-0.2, 0.05, t + 0.38), 0.016, "glass", seg=6)
    strut(mb, M, (-0.2, 0.05, t + 0.38), (-0.08, 0.0, t + 0.2), 0.012, "glass", seg=6)
    flask(mb, M, (-0.07, 0.0, t), "cone", "glass", 1.1)
    # alembic tower
    lathe(mb, M, (0.15, 0.18, t), [(0.08, 0), (0.1, 0.08), (0.06, 0.18), (0.08, 0.26), (0.03, 0.36), (0.02, 0.44), (0, 0.45)], "metal", seg=10)
    strut(mb, M, (0.17, 0.18, t + 0.4), (0.4, 0.2, t + 0.3), 0.01, "metal", seg=6)
    for k in range(rng.randint(4, 7)):
        flask(mb, M, (rng.uniform(0.3, 0.72), rng.uniform(-0.3, 0.3), t), rng.choice(("round", "vial", "cone", "square")), rng.choice(LIQ), rng.uniform(0.7, 1.2))
    book(mb, M, (0.15, -0.22, t + 0.02), 0.32, 0.22, 0.03, "fabric", rz=0.3)
    mortar_shape(mb, sub(M, (-0.3, -0.25, t)))
    skull_shape(mb, sub(M, (-0.68, -0.2, t), rz=math.pi + 0.5), 1.0)
    candle(mb, M, (-0.7, 0.25, t), 0.1, 0.02)
    return surface(x, y, z + t + 0.035, 0.2)


def mortar_shape(mb, M):
    lathe(mb, M, (0, 0, 0), [(0.05, 0), (0.07, 0.02), (0.075, 0.07), (0.06, 0.08), (0.0, 0.05)], "stone", seg=10)
    strut(mb, M, (0.0, 0.0, 0.04), (0.04, 0.02, 0.15), 0.012, "stone", seg=6)


@fxprop("mortar", "surface", (0.16, 0.16, 0.15), eras=PRE, rooms=("alchemy", "wizard", "witch", "apothecary", "kitchen", "plague"))
def mortar(mb, x, y, z, rot, rng, era):
    mortar_shape(mb, M0(x, y, z, rot))


@fxprop("cauldron", "floor", (1.0, 1.0, 1.0), eras=PRE, rooms=("alchemy", "witch", "wizard", "ritual", "mead_hall", "fx_feature"))
def cauldron(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    zb = 0.18
    lathe(mb, M, (0, 0, zb), [(0, 0), (0.28, 0.03), (0.42, 0.22), (0.44, 0.38), (0.38, 0.54), (0.42, 0.58), (0.0, 0.58)], "metal2", seg=14)
    cy(mb, M, (0, 0, zb + 0.585), 0.36, 0.02, rng.choice(("accent", "leaf", "fabric")), seg=12)
    for k in range(4):
        sp(mb, M, (rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), zb + 0.6), rng.uniform(0.03, 0.06), "accent", sub=0)
    for i in range(3):
        a = i / 3 * math.tau + 0.3
        strut(mb, M, (math.cos(a) * 0.28, math.sin(a) * 0.28, zb + 0.05), (math.cos(a) * 0.36, math.sin(a) * 0.36, 0), 0.03, "metal2")
    for sx in (-1, 1):
        ring(mb, sub(M, (sx * 0.43, 0, zb + 0.5), rx=math.pi / 2, rz=0), (0, 0, 0), 0.07, 0.012, "metal2", seg=10, mseg=3)
    for k in range(4):
        a = k / 4 * math.pi + 0.3
        bx(mb, M, (0, 0, 0.05), (0.7, 0.08, 0.08), "wood2", rz=a)
    if rng.random() < 0.75:
        fire(mb, M, (0, 0, 0.06), 0.6, n=3, rng=rng)
    strut(mb, M, (0.1, -0.05, zb + 0.4), (0.25, -0.2, zb + 1.0), 0.015, "wood2", seg=6)       # stirring paddle


@fxprop("spellbook_lectern", "floor", (0.7, 0.6, 1.35), eras=PRE, rooms=("wizard", "library", "temple", "monastery", "ritual", "fx_feature"))
def spellbook_lectern(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.04), 0.28, 0.08, "wood2", seg=8)
    lathe(mb, M, (0, 0, 0.08), [(0.09, 0), (0.06, 0.15), (0.08, 0.35), (0.05, 0.6), (0.07, 0.85), (0.1, 0.9)], "wood", seg=8)
    top = sub(M, (0, 0.0, 1.02), rx=-0.45)
    bx(mb, top, (0, 0, 0), (0.62, 0.45, 0.05), "wood")
    bx(mb, top, (0, -0.24, 0.02), (0.6, 0.03, 0.05), "wood2")
    for sx in (-1, 1):                                   # open book: two pages lifted at the spine
        bx(mb, top, (sx * 0.135, 0, 0.04), (0.27, 0.36, 0.02), "fabric", ry=-sx * 0.06)
        bx(mb, top, (sx * 0.13, 0, 0.058), (0.25, 0.33, 0.018), "paper", ry=-sx * 0.1)
        for k in range(4):
            bx(mb, top, (sx * 0.13, 0.1 - k * 0.06, 0.07), (0.18, 0.012, 0.004), "dark", ry=-sx * 0.1)
    bx(mb, top, (0.03, -0.19, 0.02), (0.02, 0.1, 0.004), "fabric")
    if rng.random() < 0.7:
        candle(mb, M, (0.28, 0.12, 1.1), 0.1, 0.02)


@fxprop("crystal_ball", "surface", (0.22, 0.22, 0.3), eras=PRE, rooms=("wizard", "seance", "witch", "fortune", "alchemy"))
def crystal_ball(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.1, 0), (0.1, 0.02), (0.06, 0.05), (0.08, 0.1), (0.0, 0.1)], "metal", seg=10)
    for i in range(3):
        a = i / 3 * math.tau
        strut(mb, M, (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.08), (math.cos(a) * 0.07, math.sin(a) * 0.07, 0.15), 0.008, "metal")
    sp(mb, M, (0, 0, 0.19), 0.1, "glass", sub=2)
    sp(mb, M, (0, -0.02, 0.2), 0.04, "screen", sub=1)


@fxprop("astrolabe", "surface", (0.35, 0.35, 0.5), eras=OLD, rooms=("wizard", "observatory", "study", "library", "cabin", "map_room"))
def astrolabe(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    lathe(mb, M, (0, 0, 0), [(0.12, 0), (0.12, 0.02), (0.05, 0.04), (0.02, 0.1), (0.02, 0.18), (0, 0.18)], "metal", seg=10)
    c = (0, 0, 0.33)
    ring(mb, M, c, 0.15, 0.008, "glass2", seg=20, mseg=3, rx=math.pi / 2)
    ring(mb, M, c, 0.14, 0.008, "glass2", seg=20, mseg=3, rx=math.pi / 2, rz=math.pi / 2)
    ring(mb, M, c, 0.13, 0.008, "metal", seg=20, mseg=3, rx=0.41)
    ring(mb, M, c, 0.155, 0.01, "metal", seg=20, mseg=3)
    sp(mb, M, c, 0.035, "glass2", sub=1)
    strut(mb, M, (0, 0, 0.16), (0, 0, 0.5), 0.005, "metal")


@fxprop("hourglass", "surface", (0.14, 0.14, 0.3), eras=OLD, rooms=("wizard", "study", "alchemy", "monastery", "library", "cabin"))
def hourglass(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for zz in (0.01, 0.27):
        cy(mb, M, (0, 0, zz), 0.07, 0.02, "wood2", seg=8)
    for i in range(3):
        a = i / 3 * math.tau
        cy(mb, M, (math.cos(a) * 0.06, math.sin(a) * 0.06, 0.14), 0.007, 0.25, "wood2", seg=4)
    lathe(mb, M, (0, 0, 0.02), [(0, 0), (0.04, 0.005), (0.045, 0.05), (0.008, 0.125), (0.045, 0.2), (0.04, 0.245), (0, 0.25)], "glass", seg=10)
    cy(mb, M, (0, 0, 0.05), 0.04, 0.05, "glass2", seg=8, r2=0.01)


@fxprop("bookstack_tall", "floor", (0.7, 0.6, 1.2), eras=PRE, rooms=("wizard", "library", "study", "alchemy", "scriptorium", "monastery"))
def bookstack_tall(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for s in range(rng.randint(2, 3)):
        ox, oy = rng.uniform(-0.18, 0.18), rng.uniform(-0.15, 0.15)
        zz = 0.0
        lean = rng.uniform(-0.04, 0.04)
        for i in range(rng.randint(5, 14)):
            t = rng.uniform(0.04, 0.09)
            book(mb, M, (ox + lean * zz * 4, oy, zz + t / 2), rng.uniform(0.22, 0.34), rng.uniform(0.16, 0.24), t,
                 rng.choice(("fabric", "accent", "trim", "wood2", "fabric2")), rz=rng.uniform(-0.3, 0.3))
            zz += t
    if rng.random() < 0.5:
        candle(mb, M, (0.0, 0.0, zz), 0.08, 0.02)


@fxprop("scroll_rack", "wall", (1.2, 0.4, 1.9), eras=OLD, rooms=("library", "scriptorium", "wizard", "study", "temple", "palace"))
def scroll_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    nx, nz = 5, 5
    w, h = 1.2 / nx, 1.8 / nz
    bx(mb, M, (0, 0.18, 0.95), (1.24, 0.03, 1.9), "wood2")
    for i in range(nx + 1):
        bx(mb, M, (-0.6 + i * w, 0, 0.95), (0.025, 0.36, 1.85), "wood")
    for j in range(nz + 1):
        bx(mb, M, (0, 0, 0.05 + j * h), (1.22, 0.36, 0.025), "wood")
    for i in range(nx):
        for j in range(nz):
            for k in range(rng.randint(0, 4)):
                cx = -0.6 + (i + 0.5) * w + rng.uniform(-0.06, 0.06)
                cz = 0.05 + j * h + 0.04 + k * 0.05
                if cz > 0.05 + (j + 1) * h - 0.04:
                    break
                cyy(mb, M, (cx, -0.02, cz), 0.03, 0.3, "paper", seg=6)
                cyy(mb, M, (cx, -0.18, cz), 0.035, 0.02, "wood2", seg=6)


@fxprop("herb_rack", "hanging", (1.4, 0.25, 0.8), eras=PRE, rooms=FEATURE_ROOMS)
def herb_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.65, 0.65):
        strut(mb, M, (sx, 0, 0), (sx, 0, -0.25), 0.006, "wood2")
    cyx(mb, M, (0, 0, -0.25), 0.025, 1.4, "wood2", seg=6)
    for i in range(rng.randint(5, 8)):
        u = -0.6 + i * 0.18 + rng.uniform(-0.03, 0.03)
        L = rng.uniform(0.2, 0.45)
        strut(mb, M, (u, 0, -0.25), (u, 0, -0.32), 0.004, "paper")
        cy(mb, M, (u, 0, -0.32 - L / 2), 0.06, L, rng.choice(("leaf", "leaf", "wood2", "fabric2")), seg=6, r2=0.012, rx=math.pi)


# ----------------------------------------------------------------------------- forge & hall
@fxprop("anvil", "floor", (0.8, 0.45, 0.9), eras=OLD | MID, rooms=("smithy", "armoury", "forge", "workshop"))
def anvil(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    cy(mb, M, (0, 0, 0.26), 0.25, 0.52, "wood2", seg=10)
    bx(mb, M, (0, 0, 0.56), (0.32, 0.22, 0.08), "metal2")
    bx(mb, M, (0, 0, 0.64), (0.18, 0.14, 0.1), "metal2")
    bx(mb, M, (0.0, 0, 0.75), (0.42, 0.18, 0.12), "metal2")
    cy(mb, M, (0.33, 0, 0.77), 0.065, 0.26, "metal2", seg=8, r2=0.008, ry=math.pi / 2)
    bx(mb, M, (-0.25, 0, 0.77), (0.08, 0.14, 0.08), "metal2")
    strut(mb, M, (-0.05, -0.05, 0.82), (0.22, -0.12, 0.86), 0.015, "wood2", seg=6)       # hammer
    bx(mb, M, (-0.07, -0.04, 0.84), (0.06, 0.05, 0.1), "metal")


@fxprop("grindstone", "floor", (0.9, 0.6, 1.0), eras=OLD, rooms=("smithy", "armoury", "workshop"))
def grindstone(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    for sx in (-0.2, 0.2):
        strut(mb, M, (sx, -0.25, 0), (sx, 0, 0.7), 0.035, "wood2")
        strut(mb, M, (sx, 0.25, 0), (sx, 0, 0.7), 0.035, "wood2")
    cyx(mb, M, (0, 0, 0.72), 0.3, 0.12, "stone", seg=14)
    cyx(mb, M, (0, 0, 0.72), 0.02, 0.6, "metal2", seg=6)
    strut(mb, M, (0.3, 0, 0.72), (0.3, -0.15, 0.72), 0.012, "metal2")
    bx(mb, M, (0, 0, 0.3), (0.5, 0.35, 0.2), "wood")


@fxprop("forge", "wall", (2.0, 1.2, 2.8), eras=OLD | MID, rooms=("smithy", "forge", "fx_feature"))
def forge(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0, 0.42), (1.8, 1.1, 0.84), "stone")
    bx(mb, M, (0, -0.1, 0.84), (1.2, 0.7, 0.06), "dark")
    for k in range(10):
        sp(mb, M, (rng.uniform(-0.45, 0.45), rng.uniform(-0.35, 0.15), 0.88), rng.uniform(0.05, 0.09), "fire" if k % 3 else "dark", sub=0)
    fire(mb, M, (0, -0.1, 0.86), 0.6, n=3, rng=rng)
    lathe(mb, M, (0, 0.1, 1.5), [(0.95, 0), (0.85, 0.05), (0.25, 0.75), (0, 0.75)], "metal2", seg=4, rz=math.pi / 4, sc=(1.0, 0.75))
    bx(mb, M, (0, 0.25, 2.5), (0.42, 0.42, 1.3), "stone")
    m = sub(M, (1.1, -0.1, 0.65))                       # bellows
    prism(mb, m, (0, 0, 0), [(-0.1, -0.12), (0.1, -0.12), (0.4, 0.0), (0.1, 0.12), (-0.1, 0.12)], 0.4, "fabric2", rz=math.pi / 2)
    strut(mb, m, (0, -0.32, 0), (-0.2, -0.6, 0.15), 0.02, "wood2")
    for k in range(3):                                   # tongs hanging on the hood edge
        polyline(mb, M, [(-0.7 + k * 0.12, -0.42, 1.55), (-0.7 + k * 0.12, -0.45, 1.1)], 0.01, "metal2")
    barrel_shape(mb, M, (-1.15, -0.2, 0), 0.25, 0.6, "wood", "metal2")
    cy(mb, M, (-1.15, -0.2, 0.6), 0.22, 0.01, "water", seg=10)


@fxprop("ale_barrel_rack", "floor", (2.0, 0.9, 1.5), eras=OLD | MID, rooms=("tavern", "mead_hall", "cellar", "storage", "hold"))
def ale_barrel_rack(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    n = rng.choice((2, 3))
    for sx in (-0.95, 0.95):
        bx(mb, M, (sx, 0, 0.35), (0.08, 0.8, 0.7), "wood2")
    for sy in (-0.3, 0.3):
        bx(mb, M, (0, sy, 0.15), (1.95, 0.08, 0.08), "wood2")
    for i in range(n):
        px = -0.6 + i * (1.2 / max(1, n - 1)) if n > 1 else 0
        barrel_shape(mb, M, (px, -0.38, 0.62), 0.3, 0.76, "wood", "metal2", rx=-math.pi / 2)
        cy(mb, M, (px, -0.43, 0.48), 0.015, 0.08, "metal", seg=6, rx=math.pi / 2)
    if rng.random() < 0.6:
        barrel_shape(mb, M, (0.0, -0.3, 1.18), 0.22, 0.6, "wood", "metal2", rx=-math.pi / 2)


@fxprop("longtable", "floor", (3.2, 1.9, 0.82), eras=OLD, rooms=("mead_hall", "banquet", "castle", "monastery", "barracks", "fx_feature"))
def longtable(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    L = 3.0
    bx(mb, M, (0, 0, 0.78), (L, 0.9, 0.08), "wood")
    for sx in (-1.2, 0, 1.2):
        strut(mb, M, (sx, -0.35, 0), (sx, 0.0, 0.74), 0.045, "wood2")
        strut(mb, M, (sx, 0.35, 0), (sx, 0.0, 0.74), 0.045, "wood2")
    bx(mb, M, (0, 0, 0.3), (L * 0.9, 0.07, 0.07), "wood2")
    for sy in (-0.78, 0.78):
        bx(mb, M, (0, sy, 0.45), (L * 0.95, 0.3, 0.06), "wood")
        for sx in (-1.25, 0, 1.25):
            bx(mb, M, (sx, sy, 0.21), (0.07, 0.25, 0.42), "wood2")
    return [(Vector((x, y, z + 0.82)), 0.4)] + [(Vector(M0(x, y, z, rot) @ Vector((s, 0, 0.82))), 0.35) for s in (-1.0, 1.0)]


@fxprop("bedroll", "floor", (0.85, 2.0, 0.3), eras=PRE | {"post_apocalyptic"}, rooms=("camp", "barracks", "monastery", "dungeon", "shelter", "cell"))
def bedroll(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    bx(mb, M, (0, 0.1, 0.03), (0.75, 1.8, 0.06), "fabric2", rz=rng.uniform(-0.05, 0.05))
    bx(mb, M, (0.04, 0.35, 0.08), (0.7, 1.1, 0.05), "fabric", rz=rng.uniform(-0.1, 0.1))
    cyx(mb, M, (0, -0.85, 0.12), 0.12, 0.72, "fabric", seg=10)
    ring(mb, sub(M, (0.2, -0.85, 0.12), ry=math.pi / 2), (0, 0, 0), 0.125, 0.012, "wood2", seg=10, mseg=3)
    ring(mb, sub(M, (-0.2, -0.85, 0.12), ry=math.pi / 2), (0, 0, 0), 0.125, 0.012, "wood2", seg=10, mseg=3)


@fxprop("map_table", "floor", (1.8, 1.2, 1.05), eras=OLD | MID, rooms=("war_room", "castle", "cabin", "map_room", "fx_feature"))
def map_table(mb, x, y, z, rot, rng, era):
    M = M0(x, y, z, rot)
    table(mb, M, 1.7, 1.1, 0.88, "wood", leg=0.1, top=0.08)
    bx(mb, M, (0, 0, 0.885), (1.4, 0.9, 0.006), "paper", rz=rng.uniform(-0.05, 0.05))
    for k in range(6):                                     # coastline + roads inked onto the map
        a = rng.uniform(0, math.tau)
        bx(mb, M, (rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3), 0.89), (rng.uniform(0.2, 0.5), 0.012, 0.003), "wood2", rz=a)
    for k in range(rng.randint(4, 8)):
        cy(mb, M, (rng.uniform(-0.6, 0.6), rng.uniform(-0.35, 0.35), 0.93), 0.025, 0.08, rng.choice(("fabric", "accent", "metal")), seg=6, r2=0.008)
    sword(mb, sub(M, (0.3, 0.15, 1.6), rx=math.pi + 0.15), 0.6)
    candle(mb, M, (-0.75, 0.45, 0.88), 0.1, 0.03)
    return surface(x, y, z + 0.9, 0.15)

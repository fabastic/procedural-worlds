"""Interiors asset pack, part 1: domestic props (kitchen, bathroom, bedroom, kids, living, attic, generic).
Conventions (origin / facing per place type) are in interiors_geo. Era variants switch on sub(era)."""
import math
from mathutils import Vector
from ..props import prop
from .interiors_geo import (frame, box, cyl, sph, rod, surf, legs4, drawers, doors, tier, sub,
                            ANTIQ, MEDV, PRE, VIC, INTER, COLD, MIDC, ANALOG, NOWS, FUTS, INDUSTRIAL_ON, ELECTRIC, ALL)

KITCHEN = ("kitchen", "apartment")


# ============================================================================ kitchen
@prop("fridge", "wall", (0.8, 0.7, 1.8), eras=INDUSTRIAL_ON, rooms=KITCHEN)
def fridge(mb, x, y, z, rot, rng, era):
    """Icebox (19th c.) / round-shouldered enamel fridge / steel two-door / smart fridge with screen."""
    M, s = frame(x, y, z, rot), sub(era)
    if s == "vic":
        box(mb, M, (0, -0.28, 0.75), (0.8, 0.54, 1.4), "wood")
        box(mb, M, (0, -0.28, 1.48), (0.86, 0.6, 0.06), "wood2")
        for zc, h in ((1.15, 0.42), (0.5, 0.75)):
            box(mb, M, (0, -0.56, zc), (0.66, 0.03, h), "wood2")
            box(mb, M, (0.26, -0.59, zc), (0.05, 0.04, 0.12), "metal")
            for zz in (zc - h / 2 + 0.08, zc + h / 2 - 0.08):
                box(mb, M, (-0.3, -0.58, zz), (0.08, 0.03, 0.04), "metal")
        return []
    if s in ("inter", "cold"):
        box(mb, M, (0, -0.34, 0.8), (0.74, 0.66, 1.5), "paper")
        box(mb, M, (0, -0.34, 1.6), (0.66, 0.6, 0.14), "paper")
        box(mb, M, (0, -0.68, 0.86), (0.7, 0.03, 1.2), "paper")
        box(mb, M, (0.26, -0.72, 1.0), (0.06, 0.06, 0.26), "metal")
        box(mb, M, (0, -0.69, 0.12), (0.6, 0.03, 0.12), "metal2")
        box(mb, M, (0, -0.70, 1.38), (0.18, 0.02, 0.05), "metal")
        return []
    k = "metal"
    box(mb, M, (0, -0.35, 0.92), (0.8, 0.68, 1.84), k)
    split = 1.3 if s != "analog" else 1.35
    box(mb, M, (0, -0.70, (split + 1.82) / 2), (0.76, 0.03, 1.82 - split - 0.02), k)
    box(mb, M, (0, -0.70, (0.08 + split) / 2), (0.76, 0.03, split - 0.1), k)
    box(mb, M, (-0.3, -0.74, split + 0.2), (0.04, 0.05, 0.3), "dark")
    box(mb, M, (-0.3, -0.74, split - 0.4), (0.04, 0.05, 0.5), "dark")
    if s in ("fut", "cyber", "solar", "space"):
        box(mb, M, (0.1, -0.725, 0.95), (0.36, 0.02, 0.26), "screen")
        box(mb, M, (0, -0.72, split - 0.01), (0.7, 0.02, 0.025), "accent")
    else:                                    # magnets + notes: story clutter on every lived-in fridge
        for i in range(rng.randint(2, 4)):
            box(mb, M, (rng.uniform(-0.2, 0.25), -0.725, rng.uniform(0.7, 1.15)), (0.12, 0.01, 0.15),
                rng.choice(("paper", "paper", "accent")), r=(0, rng.uniform(-0.2, 0.2), 0))
    return []


@prop("stove", "wall", (0.9, 0.65, 1.0), eras=INDUSTRIAL_ON, rooms=KITCHEN)
def stove(mb, x, y, z, rot, rng, era):
    """Cast-iron range with flue / enamel range / steel range + hood / induction slab."""
    M, s = frame(x, y, z, rot), sub(era)
    if s == "vic":
        box(mb, M, (0, -0.32, 0.45), (1.0, 0.6, 0.7), "dark")
        box(mb, M, (0, -0.32, 0.82), (1.06, 0.64, 0.05), "metal2")
        legs4(mb, M, 0.96, 0.56, 0.12, 0.06, "dark", z0=0.0)
        for sx in (-0.24, 0.24):
            box(mb, M, (sx, -0.63, 0.45), (0.38, 0.03, 0.4), "metal")
            box(mb, M, (sx + 0.12, -0.66, 0.45), (0.06, 0.04, 0.04), "dark")
        for sx in (-0.25, 0.25):
            cyl(mb, M, (sx, -0.32, 0.86), 0.12, 0.03, "metal", seg=12)
        cyl(mb, M, (0.3, -0.12, 1.6), 0.07, 1.5, "dark", seg=8)
        return [surf(M, (-0.15, -0.32, 0.87), 0.2)]
    if s in ("inter", "cold"):
        box(mb, M, (0, -0.33, 0.5), (0.9, 0.62, 0.86), "paper")
        legs4(mb, M, 0.86, 0.58, 0.08, 0.05, "metal")
        box(mb, M, (0, -0.06, 1.08), (0.9, 0.08, 0.36), "paper")
        box(mb, M, (0, -0.11, 1.08), (0.3, 0.02, 0.14), "metal")
        box(mb, M, (-0.12, -0.65, 0.48), (0.56, 0.03, 0.52), "paper")
        box(mb, M, (-0.12, -0.68, 0.7), (0.4, 0.04, 0.04), "metal")
        box(mb, M, (0.31, -0.65, 0.48), (0.22, 0.03, 0.52), "metal2")
        for i in range(4):
            cyl(mb, M, (-0.38 + i * 0.25, -0.66, 0.84), 0.025, 0.04, "dark", seg=8, axis="Y")
        for sx, sy in ((-0.2, -0.22), (0.2, -0.22), (-0.2, -0.45), (0.2, -0.45)):
            cyl(mb, M, (sx, sy, 0.945), 0.08, 0.02, "dark", seg=10)
        return []
    fut = s in ("fut", "cyber", "solar", "space")
    box(mb, M, (0, -0.33, 0.46), (0.76, 0.64, 0.92), "metal")
    box(mb, M, (0, -0.33, 0.93), (0.78, 0.66, 0.03), "dark")
    box(mb, M, (0, -0.66, 0.42), (0.6, 0.03, 0.44), "dark")
    box(mb, M, (0, -0.68, 0.7), (0.56, 0.04, 0.035), "metal2")
    for sx, sy in ((-0.18, -0.2), (0.18, -0.2), (-0.18, -0.46), (0.18, -0.46)):
        cyl(mb, M, (sx, sy, 0.95), 0.09 if fut else 0.08, 0.012, "accent" if fut else "metal2", seg=12)
    if fut:
        box(mb, M, (0, -0.665, 0.82), (0.5, 0.02, 0.06), "screen")
    else:
        for i in range(4):
            cyl(mb, M, (-0.27 + i * 0.18, -0.67, 0.83), 0.022, 0.04, "dark", seg=8, axis="Y")
    # hood + chimney
    box(mb, M, (0, -0.28, 1.72), (0.8, 0.5, 0.16), "metal", r=None)
    box(mb, M, (0, -0.16, 2.05), (0.3, 0.24, 0.5), "metal")
    return []


@prop("kitchen_sink", "wall", (1.0, 0.62, 1.0), eras=ALL, rooms=KITCHEN)
def kitchen_sink(mb, x, y, z, rot, rng, era):
    """Stone trough + pump / enamel sink on legs with a fabric skirt (the reference) / cabinet sink."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("antiq", "med", "ren", "enl", "vic"):
        box(mb, M, (0, -0.3, 0.35), (1.0, 0.56, 0.7), "wood")
        box(mb, M, (0, -0.3, 0.8), (0.9, 0.5, 0.2), "stone")
        box(mb, M, (0, -0.3, 0.905), (0.74, 0.36, 0.02), "dark")
        if s == "vic":
            cyl(mb, M, (0.3, -0.12, 1.1), 0.05, 0.42, "metal2", seg=8)
            rod(mb, M, (0.3, -0.12, 1.3), (0.3, -0.36, 1.18), 0.02, "metal2")
            rod(mb, M, (0.3, -0.12, 1.33), (0.1, -0.12, 1.45), 0.02, "metal2")
        else:
            cyl(mb, M, (-0.32, -0.3, 1.0), 0.11, 0.18, "wood2", seg=10, r2=0.13)
        return [surf(M, (0.32, -0.3, 0.92), 0.12)]
    if s in ("inter", "cold"):
        box(mb, M, (0, -0.3, 0.84), (1.1, 0.56, 0.2), "paper")
        box(mb, M, (-0.18, -0.3, 0.945), (0.5, 0.36, 0.02), "dark")
        box(mb, M, (0, -0.03, 1.08), (1.1, 0.06, 0.28), "paper")
        legs4(mb, M, 1.04, 0.5, 0.74, 0.04, "metal")
        for i in range(5):                                  # pleated skirt
            box(mb, M, (-0.44 + i * 0.22, -0.6 + (i % 2) * 0.02, 0.4), (0.24, 0.03, 0.7), "fabric" if i % 2 else "fabric2")
        rod(mb, M, (-0.18, -0.08, 1.0), (-0.18, -0.08, 1.24), 0.02, "metal")
        rod(mb, M, (-0.18, -0.08, 1.24), (-0.18, -0.24, 1.18), 0.018, "metal")
        for sx in (-0.32, -0.04):
            cyl(mb, M, (sx, -0.08, 1.0), 0.03, 0.05, "metal", seg=8)
        return [surf(M, (0.32, -0.3, 0.95), 0.12)]
    fut = s in ("fut", "cyber", "solar", "space")
    box(mb, M, (0, -0.3, 0.44), (1.0, 0.58, 0.88), "metal" if fut else "wood")
    doors(mb, M, 0, -0.59, 0.1, 0.96, 0.7, 2, key="metal2" if fut else "trim")
    box(mb, M, (0, -0.31, 0.9), (1.04, 0.62, 0.04), "dark" if fut else "stone")
    box(mb, M, (-0.1, -0.32, 0.925), (0.52, 0.38, 0.015), "metal")
    box(mb, M, (-0.1, -0.32, 0.93), (0.44, 0.3, 0.012), "dark")
    rod(mb, M, (-0.1, -0.06, 0.92), (-0.1, -0.06, 1.2), 0.02, "metal")
    rod(mb, M, (-0.1, -0.06, 1.2), (-0.1, -0.24, 1.14), 0.018, "metal")
    return [surf(M, (0.34, -0.32, 0.92), 0.12)]


@prop("base_cabinet", "wall", (1.0, 0.62, 1.0), eras=ALL, rooms=KITCHEN)
def base_cabinet(mb, x, y, z, rot, rng, era):
    """Counter run unit: drawer row over two doors, worktop (sage in mid-century, like the reference)."""
    M, t = frame(x, y, z, rot), tier(era)
    body = {0: "wood", 1: "wood", 2: "paper", 3: "wood", 4: "metal"}[t]
    top = {0: "wood2", 1: "wood2", 2: "wall2", 3: "stone", 4: "dark"}[t]
    box(mb, M, (0, -0.3, 0.45), (1.0, 0.58, 0.82), body)
    box(mb, M, (0, -0.28, 0.04), (0.96, 0.5, 0.08), "dark")
    drawers(mb, M, 0, -0.59, 0.66, 0.96, 0.18, 1, key="trim" if t != 2 else "paper", knob="metal")
    doors(mb, M, 0, -0.59, 0.1, 0.96, 0.54, 2, key="trim" if t != 2 else "paper")
    if t == 2:                                         # teal edge banding
        box(mb, M, (0, -0.6, 0.64), (1.0, 0.02, 0.025), "trim")
    box(mb, M, (0, -0.31, 0.9), (1.04, 0.64, 0.05), top)
    return [surf(M, (0, -0.32, 0.925), 0.4)]


@prop("wall_cupboard", "wall", (1.0, 0.35, 0.7), eras=ALL, rooms=KITCHEN + ("bathroom", "lab", "office"))
def wall_cupboard(mb, x, y, z, rot, rng, era):
    """Mounted cupboard with raised-panel doors (centre at z)."""
    M, t = frame(x, y, z, rot), tier(era)
    body = {0: "wood", 1: "wood", 2: "paper", 3: "wood", 4: "metal"}[t]
    box(mb, M, (0, -0.17, 0), (1.0, 0.34, 0.7), body)
    box(mb, M, (0, -0.18, 0.37), (1.06, 0.38, 0.04), "trim")
    for sx in (-0.25, 0.25):
        box(mb, M, (sx, -0.35, 0), (0.46, 0.02, 0.62), "trim" if t == 2 else body)
        box(mb, M, (sx, -0.365, 0), (0.32, 0.02, 0.46), "wall2" if t == 2 else "wood2")
        box(mb, M, (sx - 0.18 * (1 if sx > 0 else -1), -0.38, -0.2), (0.025, 0.02, 0.08), "metal")
    return []


@prop("pan_rail", "wall", (1.2, 0.14, 0.55), eras=ALL, rooms=KITCHEN)
def pan_rail(mb, x, y, z, rot, rng, era):
    """Rail of hanging copper pans + ladle (centre at z), like the reference's shelf of pots."""
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, -0.07, 0.22), 0.015, 1.2, "metal", seg=6, axis="X")
    for sx in (-0.58, 0.58):
        box(mb, M, (sx, -0.035, 0.22), (0.03, 0.07, 0.05), "metal")
    n = rng.randint(4, 6)
    for i in range(n):
        px = -0.5 + i * 1.0 / max(1, n - 1)
        rod(mb, M, (px, -0.07, 0.22), (px, -0.07, 0.12), 0.006, "metal")
        k = rng.choice(("glass2", "glass2", "metal", "dark"))
        if rng.random() < 0.75:
            r = rng.uniform(0.07, 0.12)
            box(mb, M, (px, -0.08, 0.12 - 0.1), (0.03, 0.015, 0.2), k)
            cyl(mb, M, (px, -0.09, 0.12 - 0.2 - r), r, 0.035, k, seg=12, axis="Y")
        else:
            box(mb, M, (px, -0.08, 0.0), (0.025, 0.015, 0.26), "metal")
            cyl(mb, M, (px, -0.09, -0.16), 0.045, 0.03, "metal", seg=8, axis="Y")
    return []


@prop("spice_shelf", "wall", (0.8, 0.16, 0.32), eras=ALL, rooms=KITCHEN)
def spice_shelf(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, -0.08, -0.12), (0.8, 0.16, 0.03), "wood")
    for sx in (-0.38, 0.38):
        box(mb, M, (sx, -0.07, -0.02), (0.03, 0.14, 0.22), "wood2")
    px = -0.33
    while px < 0.33:
        h = rng.uniform(0.08, 0.16)
        cyl(mb, M, (px, -0.08, -0.105 + h / 2), 0.03, h, rng.choice(("glass", "glass2", "paper", "accent")), seg=8)
        cyl(mb, M, (px, -0.08, -0.105 + h + 0.01), 0.032, 0.02, "metal2", seg=8)
        px += rng.uniform(0.075, 0.1)
    return []


@prop("kettle", "surface", (0.24, 0.2, 0.26), eras=ALL, rooms=KITCHEN + ("diner", "office", "domestic"))
def kettle(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = {0: "dark", 1: "dark", 2: "accent", 3: "metal", 4: "metal"}[t]
    if t == 0:
        cyl(mb, M, (0, 0, 0.12), 0.12, 0.2, "dark", seg=10, r2=0.1)
        rod(mb, M, (-0.11, 0, 0.22), (0, 0, 0.32), 0.008, "metal2")
        rod(mb, M, (0.11, 0, 0.22), (0, 0, 0.32), 0.008, "metal2")
        return []
    cyl(mb, M, (0, 0, 0.08), 0.095, 0.16, k, seg=12, r2=0.07)
    cyl(mb, M, (0, 0, 0.17), 0.04, 0.03, k, seg=8)
    sph(mb, M, (0, 0, 0.195), 0.018, "dark")
    rod(mb, M, (0.07, 0, 0.06), (0.16, 0, 0.14), 0.015, k)
    rod(mb, M, (-0.05, 0, 0.16), (-0.03, 0, 0.24), 0.01, "dark")
    rod(mb, M, (0.05, 0, 0.16), (0.03, 0, 0.24), 0.01, "dark")
    rod(mb, M, (-0.03, 0, 0.24), (0.03, 0, 0.24), 0.012, "dark")
    return []


@prop("saucepan", "surface", (0.35, 0.2, 0.14), eras=ALL, rooms=KITCHEN)
def saucepan(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "glass2" if tier(era) <= 1 else rng.choice(("metal", "dark", "accent"))
    cyl(mb, M, (0, 0, 0.06), 0.1, 0.12, k, seg=12)
    box(mb, M, (0.17, 0, 0.1), (0.16, 0.03, 0.025), "dark")
    if rng.random() < 0.5:
        cyl(mb, M, (0, 0, 0.125), 0.105, 0.012, k, seg=12)
        sph(mb, M, (0, 0, 0.14), 0.016, "dark")
    return []


@prop("canisters", "surface", (0.4, 0.14, 0.26), eras=ALL, rooms=KITCHEN + ("shop",))
def canisters(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = {0: "stone", 1: "stone", 2: "paper", 3: "metal", 4: "metal"}[t]
    for i, h in enumerate((0.24, 0.19, 0.15)):
        px = -0.12 + i * 0.12
        cyl(mb, M, (px, 0, h / 2), 0.05, h, k, seg=10)
        cyl(mb, M, (px, 0, h + 0.012), 0.052, 0.024, "accent" if t != 4 else "dark", seg=10)
        box(mb, M, (px, -0.05, h * 0.55), (0.05, 0.01, 0.05), "trim")
    return []


@prop("toaster", "surface", (0.3, 0.18, 0.22), eras=ELECTRIC, rooms=KITCHEN + ("diner",))
def toaster(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "metal" if sub(era) != "cold" else "paper"
    box(mb, M, (0, 0, 0.09), (0.28, 0.16, 0.18), k)
    box(mb, M, (0, 0, 0.19), (0.24, 0.12, 0.02), k)
    for sy in (-0.03, 0.03):
        box(mb, M, (0, sy, 0.2), (0.18, 0.02, 0.012), "dark")
    box(mb, M, (0.15, 0, 0.12), (0.02, 0.03, 0.04), "dark")
    box(mb, M, (0, 0, 0.01), (0.3, 0.17, 0.02), "dark")
    return []


@prop("microwave", "surface", (0.5, 0.38, 0.3), eras=ANALOG | NOWS | FUTS, rooms=KITCHEN + ("office",))
def microwave(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "paper" if sub(era) == "analog" else "metal"
    box(mb, M, (0, 0, 0.15), (0.5, 0.36, 0.28), k)
    box(mb, M, (-0.06, -0.185, 0.15), (0.32, 0.02, 0.2), "dark")
    box(mb, M, (0.18, -0.185, 0.15), (0.1, 0.02, 0.22), "metal2")
    box(mb, M, (0.18, -0.2, 0.2), (0.07, 0.01, 0.04), "screen")
    return []


@prop("dish_rack", "surface", (0.4, 0.3, 0.24), eras=ALL, rooms=KITCHEN)
def dish_rack(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "wood" if tier(era) <= 1 else "metal"
    box(mb, M, (0, 0, 0.015), (0.4, 0.28, 0.03), k)
    for sx in (-0.19, 0.19):
        box(mb, M, (sx, 0, 0.07), (0.02, 0.28, 0.1), k)
    for i in range(rng.randint(3, 5)):
        cyl(mb, M, (-0.14 + i * 0.07, 0, 0.13), 0.11, 0.015, rng.choice(("paper", "paper", "accent")), seg=12, axis="X")
    cyl(mb, M, (0.14, 0.06, 0.08), 0.04, 0.12, "paper", seg=8)
    return []


@prop("washing_machine", "wall", (0.62, 0.62, 1.0), eras=MIDC | ANALOG | NOWS | FUTS, rooms=("kitchen", "bathroom", "apartment", "laundry"))
def washing_machine(mb, x, y, z, rot, rng, era):
    """Wringer washer tub on legs / front-loader / smart front-loader."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("inter", "cold"):
        cyl(mb, M, (0, -0.32, 0.6), 0.27, 0.5, "paper", seg=14)
        for a in range(3):
            ang = a * math.tau / 3
            rod(mb, M, (math.cos(ang) * 0.2, -0.32 + math.sin(ang) * 0.2, 0.36), (math.cos(ang) * 0.27, -0.32 + math.sin(ang) * 0.27, 0.0), 0.02, "metal")
        cyl(mb, M, (0, -0.32, 0.86), 0.28, 0.03, "metal", seg=14)
        for zz in (1.0, 1.08):
            cyl(mb, M, (0, -0.32, zz), 0.04, 0.5, "metal2", seg=8, axis="X")
        box(mb, M, (0.27, -0.32, 1.04), (0.04, 0.08, 0.26), "metal")
        rod(mb, M, (0.3, -0.32, 1.1), (0.36, -0.42, 1.22), 0.012, "dark")
        return []
    fut = s in ("fut", "cyber", "solar", "space")
    box(mb, M, (0, -0.31, 0.43), (0.6, 0.6, 0.86), "metal" if fut else "paper")
    box(mb, M, (0, -0.31, 0.78), (0.58, 0.6, 0.14), "metal2" if fut else "paper")
    box(mb, M, (-0.12, -0.615, 0.8), (0.26, 0.02, 0.06), "screen" if fut else "metal2")
    cyl(mb, M, (0.18, -0.62, 0.8), 0.035, 0.03, "dark", seg=10, axis="Y")
    cyl(mb, M, (0, -0.62, 0.4), 0.2, 0.04, "metal", seg=16, axis="Y")
    cyl(mb, M, (0, -0.64, 0.4), 0.15, 0.03, "glass", seg=16, axis="Y")
    return []


@prop("bin", "floor", (0.34, 0.34, 0.6), eras=ALL, rooms=("kitchen", "office", "waiting", "hospital", "classroom", "police", "shop", "apartment", "factory", "lab"))
def bin_(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    if t <= 1:
        cyl(mb, M, (0, 0, 0.25), 0.16, 0.5, "wood", seg=10, r2=0.18)
        for zz in (0.08, 0.42):
            cyl(mb, M, (0, 0, zz), 0.18, 0.03, "metal2", seg=10)
        return []
    k = {2: "metal", 3: rng.choice(("metal", "accent", "dark")), 4: "metal"}[t]
    cyl(mb, M, (0, 0, 0.26), 0.15, 0.52, k, seg=12, r2=0.165)
    cyl(mb, M, (0, 0, 0.535), 0.172, 0.04, "metal2", seg=12)
    sph(mb, M, (0, 0, 0.56), 0.03, "dark")
    if t == 4:
        cyl(mb, M, (0, 0, 0.45), 0.168, 0.025, "accent", seg=12)
    box(mb, M, (0, -0.17, 0.03), (0.1, 0.06, 0.03), "dark")
    return []


# ============================================================================ bathroom
BATH = ("bathroom",)


def _stadium(mb, M, c, L, W, h, key, seg=12):
    """Rounded-end slab (tub / trough top view) centred at c, long along local X."""
    box(mb, M, c, (L - W, W, h), key)
    for sx in (-1, 1):
        cyl(mb, M, (c[0] + sx * (L - W) / 2, c[1], c[2]), W / 2, h, key, seg=seg)


@prop("bathtub", "wall", (1.7, 0.8, 1.0), eras=ALL, rooms=BATH)
def bathtub(mb, x, y, z, rot, rng, era):
    """Wooden tub (pre-modern) / claw-foot (19th c. + interwar) / built-in panel tub / pod tub."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("antiq", "med", "ren", "enl"):
        cyl(mb, M, (0, -0.55, 0.32), 0.52, 0.64, "wood", seg=14, sq=(1.3, 1.0, 1.0))
        for zz in (0.12, 0.5):
            cyl(mb, M, (0, -0.55, zz), 0.535, 0.05, "metal2", seg=14, sq=(1.3, 1.0, 1.0))
        cyl(mb, M, (0, -0.55, 0.645), 0.46, 0.015, "glass", seg=14, sq=(1.3, 1.0, 1.0))
        box(mb, M, (0.4, -0.55, 0.7), (0.3, 0.3, 0.05), "fabric2", r=(0, 0.3, 0.4))
        return []
    if s in ("vic", "inter", "cold"):
        _stadium(mb, M, (0, -0.42, 0.52), 1.6, 0.74, 0.44, "paper")
        _stadium(mb, M, (0, -0.42, 0.76), 1.68, 0.8, 0.06, "paper")
        _stadium(mb, M, (0, -0.42, 0.795), 1.5, 0.62, 0.012, "glass")
        for sx in (-0.6, 0.6):
            for sy in (-0.15, -0.69):
                cyl(mb, M, (sx, sy, 0.15), 0.035, 0.3, "metal", seg=8, r2=0.06)
                sph(mb, M, (sx, sy, 0.03), 0.05, "metal", sq=(1.2, 1.2, 0.6))
        rod(mb, M, (-0.72, -0.08, 0.7), (-0.72, -0.08, 1.05), 0.022, "metal")
        rod(mb, M, (-0.72, -0.08, 1.05), (-0.62, -0.3, 0.98), 0.02, "metal")
        return []
    fut = s in ("fut", "cyber", "solar", "space")
    box(mb, M, (0, -0.4, 0.29), (1.7, 0.78, 0.58), "paper")
    box(mb, M, (0, -0.4, 0.6), (1.72, 0.8, 0.05), "metal" if fut else "paper")
    _stadium(mb, M, (0, -0.4, 0.63), 1.5, 0.6, 0.012, "glass")
    box(mb, M, (0, -0.795, 0.29), (1.6, 0.02, 0.48), "metal2" if fut else "wall2")
    if fut:
        box(mb, M, (0, -0.8, 0.07), (1.6, 0.02, 0.03), "accent")
    rod(mb, M, (-0.7, -0.03, 0.85), (-0.7, -0.15, 0.85), 0.02, "metal")
    return []


@prop("toilet", "wall", (0.45, 0.72, 1.0), eras=INDUSTRIAL_ON, rooms=BATH)
def toilet(mb, x, y, z, rot, rng, era):
    """High-tank pull-chain (Victorian) / low tank / close-coupled / wall-hung."""
    M, s = frame(x, y, z, rot), sub(era)
    fut = s in ("fut", "cyber", "solar", "space")
    if not fut:
        cyl(mb, M, (0, -0.38, 0.18), 0.12, 0.36, "paper", seg=10, r2=0.15, sq=(1.0, 1.25, 1.0))
    cyl(mb, M, (0, -0.42, 0.4), 0.18, 0.1, "paper", seg=12, sq=(1.0, 1.3, 1.0))
    seat = "wood" if s in ("vic", "inter") else "paper"
    cyl(mb, M, (0, -0.42, 0.465), 0.19, 0.03, seat, seg=12, sq=(1.0, 1.3, 1.0))
    if s == "vic":
        box(mb, M, (0, -0.12, 2.0), (0.46, 0.22, 0.26), "wood")
        rod(mb, M, (0.12, -0.12, 1.87), (0.12, -0.18, 0.5), 0.022, "metal")
        rod(mb, M, (-0.18, -0.2, 1.95), (-0.18, -0.2, 1.4), 0.006, "metal")
        cyl(mb, M, (-0.18, -0.2, 1.36), 0.022, 0.08, "wood2", seg=8)
        box(mb, M, (0, -0.08, 0.68), (0.4, 0.1, 0.42), "wood")             # seat back board
    elif fut:
        box(mb, M, (0, -0.07, 0.75), (0.5, 0.12, 0.9), "metal")
        box(mb, M, (0, -0.135, 0.95), (0.16, 0.02, 0.1), "accent")
    else:
        tz = 0.72 if s in ("inter", "cold") else 0.66
        box(mb, M, (0, -0.12, tz), (0.44, 0.2, 0.36 if s != "now" else 0.4), "paper")
        box(mb, M, (0, -0.12, tz + 0.2), (0.48, 0.23, 0.04), "paper")
        box(mb, M, (0.16, -0.23, tz + 0.1), (0.07, 0.03, 0.025), "metal")
        box(mb, M, (0, -0.24, 0.72), (0.38, 0.06, 0.4), seat, r=(-0.2, 0, 0))   # lid up
    return []


@prop("chamber_pot", "floor", (0.3, 0.3, 0.22), eras=PRE | VIC, rooms=BATH + ("bedroom",))
def chamber_pot(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.09), 0.12, 0.18, "paper", seg=12, r2=0.13)
    cyl(mb, M, (0, 0, 0.18), 0.145, 0.025, "paper", seg=12)
    rod(mb, M, (0.13, 0, 0.15), (0.2, 0, 0.11), 0.015, "paper")
    return []


@prop("basin", "wall", (0.62, 0.5, 1.0), eras=ALL, rooms=BATH + ("hotel", "hospital"))
def basin(mb, x, y, z, rot, rng, era):
    """Washstand with jug and bowl (pre-plumbing) / pedestal sink / vanity / floating vanity."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("antiq", "med", "ren", "enl", "vic"):
        box(mb, M, (0, -0.24, 0.76), (0.78, 0.46, 0.05), "stone" if s in ("vic", "enl") else "wood2")
        legs4(mb, M, 0.74, 0.42, 0.74, 0.05, "wood")
        box(mb, M, (0, -0.24, 0.2), (0.7, 0.4, 0.03), "wood")
        box(mb, M, (0, -0.02, 0.9), (0.78, 0.04, 0.24), "wood")
        cyl(mb, M, (0, -0.26, 0.83), 0.18, 0.09, "paper", seg=12, r2=0.2)
        cyl(mb, M, (0.24, -0.26, 0.92), 0.06, 0.26, "paper", seg=10, r2=0.05)
        rod(mb, M, (0.28, -0.26, 1.0), (0.34, -0.26, 0.97), 0.02, "paper")
        return [surf(M, (-0.28, -0.24, 0.79), 0.08)]
    if s in ("inter", "cold", "analog"):
        cyl(mb, M, (0, -0.22, 0.38), 0.09, 0.76, "paper", seg=10, r2=0.06)
        box(mb, M, (0, -0.26, 0.82), (0.56, 0.42, 0.16), "paper")
        cyl(mb, M, (0, -0.26, 0.905), 0.17, 0.012, "glass", seg=12, sq=(1.3, 1.0, 1.0))
        for sx in (-0.18, 0.18):
            cyl(mb, M, (sx, -0.08, 0.95), 0.025, 0.08, "metal", seg=8)
            box(mb, M, (sx, -0.08, 0.99), (0.07, 0.02, 0.02), "metal")
        return []
    fut = s in ("fut", "cyber", "solar", "space")
    if fut:
        box(mb, M, (0, -0.25, 0.72), (0.66, 0.48, 0.3), "metal")
        box(mb, M, (0, -0.495, 0.58), (0.6, 0.02, 0.02), "accent")
    else:
        box(mb, M, (0, -0.25, 0.42), (0.66, 0.48, 0.82), "wood")
        doors(mb, M, 0, -0.49, 0.1, 0.62, 0.66, 2)
    box(mb, M, (0, -0.25, 0.86), (0.68, 0.5, 0.04), "stone" if not fut else "paper")
    cyl(mb, M, (0, -0.28, 0.9), 0.17, 0.08, "paper", seg=12, sq=(1.2, 1.0, 1.0))
    cyl(mb, M, (0, -0.28, 0.945), 0.14, 0.012, "glass", seg=12, sq=(1.2, 1.0, 1.0))
    rod(mb, M, (0, -0.06, 0.88), (0, -0.06, 1.1), 0.018, "metal")
    rod(mb, M, (0, -0.06, 1.1), (0, -0.16, 1.07), 0.016, "metal")
    return [surf(M, (0.24, -0.25, 0.88), 0.06)]


@prop("bath_mirror", "wall", (0.6, 0.06, 0.75), eras=ALL, rooms=BATH + ("bedroom", "hotel"))
def bath_mirror(mb, x, y, z, rot, rng, era):
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("antiq", "med"):
        cyl(mb, M, (0, -0.02, 0), 0.2, 0.03, "metal", seg=14, axis="Y")
        return []
    fr = "metal" if s in ("ren", "enl", "vic") else ("trim" if s != "now" else "metal2")
    if s in ("inter",):                                  # art-deco round mirror
        cyl(mb, M, (0, -0.02, 0), 0.33, 0.03, fr, seg=18, axis="Y")
        cyl(mb, M, (0, -0.035, 0), 0.29, 0.02, "glass", seg=18, axis="Y")
        return []
    box(mb, M, (0, -0.02, 0), (0.6, 0.03, 0.75), fr)
    box(mb, M, (0, -0.035, 0), (0.52, 0.02, 0.67), "glass")
    box(mb, M, (0.12, -0.046, 0.12), (0.06, 0.01, 0.3), "paper", r=(0, 0.5, 0))   # glint
    if s in ("fut", "cyber", "solar", "space"):
        box(mb, M, (0, -0.04, 0.39), (0.6, 0.02, 0.03), "accent")
    return []


@prop("towel_rail", "wall", (0.7, 0.12, 0.5), eras=ALL, rooms=BATH + ("hotel", "kitchen"))
def towel_rail(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "wood" if tier(era) <= 1 else "metal"
    for sx in (-0.33, 0.33):
        box(mb, M, (sx, -0.04, 0.2), (0.04, 0.08, 0.06), k)
    cyl(mb, M, (0, -0.08, 0.2), 0.018, 0.7, k, seg=8, axis="X")
    for i, (px, w) in enumerate(((-0.14, 0.32), (0.18, 0.26))):
        kk = rng.choice(("fabric", "fabric2", "paper", "accent")) if tier(era) != 4 else "fabric"
        box(mb, M, (px, -0.065, 0.02), (w, 0.03, 0.38), kk)
        box(mb, M, (px, -0.1, -0.02), (w, 0.03, 0.42 - i * 0.08), kk)
        box(mb, M, (px, -0.095, -0.2 + i * 0.03), (w + 0.01, 0.035, 0.03), "paper")
    return []


@prop("shower", "wall", (0.95, 0.95, 2.1), eras=MIDC | ANALOG | NOWS | FUTS, rooms=BATH + ("hotel",))
def shower(mb, x, y, z, rot, rng, era):
    """Shower tray + head; curtain on a rail (mid-century) or glass screen (modern / future)."""
    M, s = frame(x, y, z, rot), sub(era)
    box(mb, M, (0, -0.47, 0.04), (0.92, 0.92, 0.08), "paper")
    box(mb, M, (0, -0.47, 0.085), (0.8, 0.8, 0.012), "wall2")
    cyl(mb, M, (0, -0.47, 0.09), 0.04, 0.012, "dark", seg=8)
    rod(mb, M, (0.25, -0.02, 1.95), (0.25, -0.22, 1.95), 0.018, "metal")
    cyl(mb, M, (0.25, -0.24, 1.9), 0.08, 0.05, "metal", seg=12, r2=0.05)
    box(mb, M, (0.25, -0.03, 1.15), (0.1, 0.04, 0.12), "metal")
    if s in ("inter", "cold", "analog", "post"):
        for a, b in (((-0.46, 0, 2.02), (-0.46, -0.93, 2.02)), ((-0.46, -0.93, 2.02), (0.46, -0.93, 2.02))):
            rod(mb, M, a, b, 0.012, "metal")
        for i in range(6):                                   # bunched curtain along the front
            box(mb, M, (-0.42 + i * 0.09, -0.93 + (i % 2) * 0.025, 1.12), (0.1, 0.03, 1.75), "fabric" if i % 2 else "fabric2")
        for i in range(3):
            box(mb, M, (-0.46 + (i % 2) * 0.025, -0.1 - i * 0.12, 1.12), (0.03, 0.13, 1.75), "fabric2" if i % 2 else "fabric")
    else:
        box(mb, M, (-0.46, -0.47, 1.05), (0.025, 0.92, 1.9), "glass")
        box(mb, M, (-0.05, -0.93, 1.05), (0.8, 0.025, 1.9), "glass")
        box(mb, M, (-0.46, -0.47, 2.0), (0.04, 0.94, 0.04), "metal")
        box(mb, M, (-0.05, -0.93, 2.0), (0.84, 0.04, 0.04), "metal")
        if s in ("fut", "cyber", "solar", "space"):
            box(mb, M, (0.25, -0.03, 1.4), (0.12, 0.02, 0.2), "screen")
    return []


@prop("bath_mat", "floor", (0.8, 0.5, 0.02), eras=ALL, rooms=BATH)
def bath_mat(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.008), (0.8, 0.5, 0.016), "fabric2")
    box(mb, M, (0, 0, 0.018), (0.66, 0.08, 0.006), "paper")
    return []


@prop("laundry_basket", "floor", (0.5, 0.4, 0.55), eras=ALL, rooms=BATH + ("bedroom", "kids", "apartment", "hotel"))
def laundry_basket(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "wood" if tier(era) < 3 else rng.choice(("wood", "paper", "accent"))
    cyl(mb, M, (0, 0, 0.24), 0.2, 0.48, k, seg=10, r2=0.23, sq=(1.2, 1.0, 1.0))
    for zz in (0.1, 0.3):
        cyl(mb, M, (0, 0, zz), 0.215 + zz * 0.06, 0.025, "wood2", seg=10, sq=(1.2, 1.0, 1.0))
    sph(mb, M, (0.05, 0.02, 0.48), 0.16, "fabric", sq=(1.4, 1.0, 0.5))
    box(mb, M, (0.22, -0.05, 0.36), (0.06, 0.12, 0.3), "fabric2", r=(0, 0.3, 0))
    return []


@prop("toiletries", "surface", (0.3, 0.15, 0.22), eras=ALL, rooms=BATH + ("hotel",))
def toiletries(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    if t <= 1:
        cyl(mb, M, (-0.06, 0, 0.015), 0.06, 0.03, "paper", seg=10)
        box(mb, M, (-0.06, 0, 0.04), (0.07, 0.04, 0.025), "fabric2")
        cyl(mb, M, (0.08, 0, 0.06), 0.035, 0.12, "glass2", seg=8)
        return []
    for i in range(rng.randint(2, 4)):
        h = rng.uniform(0.1, 0.2)
        cyl(mb, M, (-0.11 + i * 0.07, rng.uniform(-0.03, 0.03), h / 2), 0.028, h, rng.choice(("paper", "accent", "glass", "fabric")), seg=8)
    cyl(mb, M, (0.12, 0, 0.05), 0.03, 0.1, "glass", seg=8)
    rod(mb, M, (0.12, 0, 0.08), (0.135, 0.01, 0.2), 0.006, "accent")
    return []


# ============================================================================ bedroom
BED = ("bedroom", "hotel", "apartment")


@prop("double_bed", "wall", (1.6, 2.1, 1.2), eras=ALL, rooms=BED)
def double_bed(mb, x, y, z, rot, rng, era):
    """Head at the wall: four-poster with canopy (pre-modern) / carved / iron / upholstered / platform."""
    M, s = frame(x, y, z, rot), sub(era)
    pre, fut = s in ("antiq", "med", "ren", "enl"), s in ("fut", "cyber", "solar", "space")
    frm = "metal2" if s in ("cold",) else ("metal" if fut else "wood")
    if fut:
        box(mb, M, (0, -1.05, 0.15), (1.6, 2.08, 0.3), "metal2")
        box(mb, M, (0, -1.05, 0.03), (1.5, 1.98, 0.04), "accent")
    else:
        box(mb, M, (0, -1.05, 0.3), (1.6, 2.06, 0.2), frm)
        legs4(mb, M, 1.6, 2.06, 0.22, 0.07, frm)
    box(mb, M, (0, -1.05, 0.5), (1.52, 1.98, 0.2), "paper")
    box(mb, M, (0, -1.25, 0.62), (1.58, 1.56, 0.08), "fabric")              # duvet
    box(mb, M, (0, -2.03, 0.42), (1.58, 0.04, 0.32), "fabric")
    box(mb, M, (0, -0.52, 0.665), (1.58, 0.16, 0.06), "paper")               # turned-down sheet
    for sx in (-0.38, 0.38):
        box(mb, M, (sx, -0.25, 0.68), (0.62, 0.32, 0.14), "paper", r=(0.25, 0, 0))
    if pre:                                    # four-poster + canopy + drapes
        for sx in (-0.77, 0.77):
            for sy in (-0.04, -2.06):
                cyl(mb, M, (sx, sy, 1.1), 0.045, 2.2, "wood", seg=8)
        box(mb, M, (0, -1.05, 2.22), (1.66, 2.16, 0.1), "fabric2")
        for sx in (-0.8, 0.8):
            box(mb, M, (sx, -1.9, 1.4), (0.06, 0.3, 1.5), "fabric2")
        box(mb, M, (0, -0.03, 0.95), (1.5, 0.05, 0.9), "wood")
    elif s == "vic":
        box(mb, M, (0, -0.03, 0.85), (1.6, 0.06, 1.1), "wood")
        cyl(mb, M, (0, -0.03, 1.4), 0.5, 0.06, "wood", seg=14, axis="Y")
        box(mb, M, (0, -2.06, 0.55), (1.6, 0.06, 0.5), "wood")
    elif s in ("inter", "cold"):
        for sx in (-0.78, 0.78):
            cyl(mb, M, (sx, -0.04, 0.6), 0.03, 1.2, "metal2", seg=8)
            cyl(mb, M, (sx, -2.06, 0.45), 0.03, 0.9, "metal2", seg=8)
        for zz in (1.15, 0.7):
            cyl(mb, M, (0, -0.04, zz), 0.022, 1.56, "metal2", seg=8, axis="X")
        for i in range(5):
            rod(mb, M, (-0.5 + i * 0.25, -0.04, 0.7), (-0.5 + i * 0.25, -0.04, 1.15), 0.012, "metal2")
        cyl(mb, M, (0, -2.06, 0.85), 0.022, 1.56, "metal2", seg=8, axis="X")
    else:
        box(mb, M, (0, -0.05, 0.8), (1.7, 0.1, 0.9 if not fut else 0.7), "fabric2" if not fut else "metal")
        if fut:
            box(mb, M, (0, -0.105, 1.1), (1.5, 0.02, 0.03), "accent")
    return []


@prop("wardrobe", "wall", (1.1, 0.6, 2.0), eras=ALL, rooms=BED + ("attic",))
def wardrobe(mb, x, y, z, rot, rng, era):
    M, s = frame(x, y, z, rot), sub(era)
    fut = s in ("fut", "cyber", "solar", "space")
    k = "metal" if fut else ("paper" if s == "now" and rng.random() < 0.4 else "wood")
    box(mb, M, (0, -0.3, 1.0), (1.1, 0.58, 1.86), k)
    if s in ("ren", "enl", "vic", "med", "antiq"):
        box(mb, M, (0, -0.31, 1.96), (1.22, 0.66, 0.1), "wood2")
        box(mb, M, (0, -0.31, 2.04), (1.1, 0.6, 0.06), "wood2")
        for sx in (-0.48, 0.48):
            for sy in (-0.06, -0.54):
                sph(mb, M, (sx, sy, 0.04), 0.06, "wood2", sq=(1, 1, 0.8))
    else:
        box(mb, M, (0, -0.3, 0.04), (1.06, 0.54, 0.08), "dark")
    doors(mb, M, 0, -0.59, 0.12, 1.06, 1.76, 2, key="wood2" if k == "wood" else ("metal2" if fut else "trim"))
    if s in ("inter", "cold"):
        box(mb, M, (0.26, -0.615, 1.1), (0.34, 0.02, 1.1), "glass")
    if fut:
        box(mb, M, (0, -0.61, 1.0), (0.02, 0.02, 1.7), "accent")
    return [surf(M, (0, -0.3, 1.94), 0.3)]


@prop("dresser", "wall", (1.0, 0.5, 1.0), eras=ALL, rooms=BED + ("kids",))
def dresser(mb, x, y, z, rot, rng, era):
    """Chest of drawers (mirror on top for 19th c. / mid-century)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "metal" if s in ("fut", "cyber", "solar", "space") else "wood"
    box(mb, M, (0, -0.25, 0.47), (1.0, 0.48, 0.8), k)
    legs4(mb, M, 0.96, 0.44, 0.08, 0.05, "wood2")
    drawers(mb, M, 0, -0.49, 0.1, 0.96, 0.76, 3 if s != "now" else 4, key="wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.25, 0.885), (1.04, 0.5, 0.03), "wood2" if k == "wood" else "metal2")
    if s in ("vic", "inter", "cold", "enl"):
        cyl(mb, M, (0, -0.05, 1.3), 0.3, 0.03, "wood2", seg=16, axis="Y", sq=(1.0, 1.0, 1.25))
        cyl(mb, M, (0, -0.067, 1.3), 0.26, 0.01, "glass", seg=16, axis="Y", sq=(1.0, 1.0, 1.25))
        for sx in (-0.2, 0.2):
            box(mb, M, (sx, -0.05, 0.96), (0.04, 0.04, 0.12), "wood2")
    return [surf(M, (0, -0.28, 0.9), 0.35)]


@prop("nightstand", "wall", (0.45, 0.4, 1.0), eras=ALL, rooms=BED + ("hospital",))
def nightstand(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = "metal" if t == 4 else "wood"
    box(mb, M, (0, -0.2, 0.33), (0.44, 0.38, 0.5), k)
    legs4(mb, M, 0.4, 0.34, 0.1, 0.04, "wood2" if k == "wood" else "metal2")
    drawers(mb, M, 0, -0.39, 0.38, 0.42, 0.2, 1, key="wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.39, 0.22), (0.38, 0.02, 0.18), "dark")
    box(mb, M, (0, -0.2, 0.595), (0.47, 0.4, 0.03), "wood2" if k == "wood" else "metal2")
    return [surf(M, (0, -0.2, 0.61), 0.12)]


# ============================================================================ kids
KIDS = ("kids",)


@prop("crib", "floor", (1.3, 0.72, 1.0), eras=ALL, rooms=KIDS)
def crib(mb, x, y, z, rot, rng, era):
    """Rocking cradle (pre-modern) / barred cot."""
    M, t = frame(x, y, z, rot), tier(era)
    if t <= 1:
        for sx in (-0.42, 0.42):
            cyl(mb, M, (sx, 0, 0.2), 0.4, 0.05, "wood2", seg=14, axis="X", sq=(1.0, 0.9, 0.5))
        box(mb, M, (0, 0, 0.45), (1.0, 0.5, 0.36), "wood")
        box(mb, M, (0, 0, 0.635), (0.9, 0.42, 0.02), "fabric")
        box(mb, M, (-0.48, 0, 0.75), (0.06, 0.52, 0.5), "wood")
        box(mb, M, (-0.36, 0, 0.98), (0.3, 0.52, 0.04), "fabric2", r=(0, 0.4, 0))
        return []
    k = "paper" if t in (3, 4) else "wood"
    for sx in (-0.62, 0.62):
        for sy in (-0.33, 0.33):
            box(mb, M, (sx, sy, 0.5), (0.05, 0.05, 1.0), k)
    for zz in (0.3, 0.95):
        for sy in (-0.33, 0.33):
            box(mb, M, (0, sy, zz), (1.22, 0.04, 0.05), k)
        for sx in (-0.62, 0.62):
            box(mb, M, (sx, 0, zz), (0.04, 0.64, 0.05), k)
    for i in range(11):
        bx = -0.55 + i * 0.11
        box(mb, M, (bx, -0.33, 0.62), (0.025, 0.025, 0.62), k)
        box(mb, M, (bx, 0.33, 0.62), (0.025, 0.025, 0.62), k)
    box(mb, M, (0, 0, 0.38), (1.16, 0.6, 0.12), "paper")
    box(mb, M, (0.15, 0, 0.46), (0.7, 0.58, 0.05), rng.choice(("fabric", "accent", "leaf")))
    sph(mb, M, (-0.35, 0.05, 0.52), 0.09, "wood", sq=(1, 1, 1))          # teddy
    return []


@prop("kids_bed", "wall", (1.0, 1.9, 1.0), eras=ALL, rooms=KIDS)
def kids_bed(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = "wood" if t != 4 else "metal"
    box(mb, M, (0, -0.95, 0.24), (0.96, 1.86, 0.16), k)
    legs4(mb, M, 0.96, 1.86, 0.18, 0.06, k)
    box(mb, M, (0, -0.95, 0.4), (0.9, 1.8, 0.16), "paper")
    cov = rng.choice(("accent", "leaf", "fabric"))
    box(mb, M, (0, -1.15, 0.5), (0.98, 1.42, 0.07), cov)
    for i in range(4):                                       # quilt stripes
        box(mb, M, (0, -0.65 - i * 0.32, 0.538), (0.99, 0.08, 0.01), "paper")
    box(mb, M, (0, -0.25, 0.55), (0.6, 0.3, 0.13), "paper", r=(0.25, 0, 0))
    box(mb, M, (0, -0.03, 0.62), (1.0, 0.06, 0.65), k)
    for i in range(3):                                       # star / heart cut-outs as painted dots
        cyl(mb, M, (-0.3 + i * 0.3, -0.065, 0.75), 0.06, 0.012, rng.choice(("paper", "accent", "leaf")), seg=5, axis="Y")
    box(mb, M, (0, -1.87, 0.42), (1.0, 0.05, 0.42), k)
    sph(mb, M, (0.25, -0.45, 0.62), 0.1, "wood")               # teddy on the pillow
    sph(mb, M, (0.25, -0.45, 0.76), 0.07, "wood")
    return []


@prop("toy_box", "floor", (0.75, 0.45, 0.62), eras=ALL, rooms=KIDS + ("attic",))
def toy_box(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = "wood" if t <= 2 else rng.choice(("accent", "leaf", "fabric"))
    box(mb, M, (0, 0, 0.22), (0.72, 0.42, 0.42), k)
    box(mb, M, (0, 0, 0.06), (0.74, 0.44, 0.06), "wood2")
    box(mb, M, (0, -0.215, 0.24), (0.4, 0.02, 0.16), "paper")
    box(mb, M, (0, 0.27, 0.6), (0.74, 0.04, 0.44), k, r=(0.35, 0, 0))     # open lid leaning back
    sph(mb, M, (-0.18, 0.0, 0.5), 0.1, "accent")                         # ball
    box(mb, M, (0.08, -0.05, 0.47), (0.1, 0.1, 0.1), "leaf", r=(0, 0, 0.5))
    box(mb, M, (0.2, 0.06, 0.52), (0.04, 0.04, 0.26), "fabric", r=(0.3, 0.2, 0))
    sph(mb, M, (0.05, 0.08, 0.55), 0.08, "wood")
    return []


@prop("rocking_horse", "floor", (1.0, 0.36, 0.95), eras=ALL, rooms=KIDS + ("attic",))
def rocking_horse(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    for sy in (-0.14, 0.14):                                 # curved rockers from short segments
        pts = [(math.sin(a) * 0.55, sy, 0.62 - math.cos(a) * 0.6) for a in [(-0.85 + i * 0.34) for i in range(6)]]
        for a, b in zip(pts, pts[1:]):
            rod(mb, M, a, b, 0.025, "wood2", seg=6)
    for sx in (-0.26, 0.26):
        for sy in (-0.14, 0.14):
            rod(mb, M, (sx * 1.25, sy, 0.06), (sx * 0.8, sy * 0.4, 0.45), 0.03, "wood")
    cyl(mb, M, (0, 0, 0.52), 0.14, 0.62, "paper", seg=10, axis="X")
    for sx in (-0.31, 0.31):
        sph(mb, M, (sx, 0, 0.52), 0.14, "paper")
    rod(mb, M, (0.3, 0, 0.58), (0.42, 0, 0.82), 0.08, "paper", seg=8)
    box(mb, M, (0.5, 0, 0.84), (0.24, 0.12, 0.12), "paper", r=(0, 0.35, 0))
    box(mb, M, (0.36, 0, 0.82), (0.16, 0.04, 0.22), "dark", r=(0, -0.5, 0))   # mane
    rod(mb, M, (-0.42, 0, 0.56), (-0.52, 0, 0.34), 0.03, "dark")              # tail
    box(mb, M, (0, 0, 0.67), (0.26, 0.3, 0.05), "fabric")
    rod(mb, M, (0.42, -0.12, 0.88), (0.42, 0.12, 0.88), 0.015, "dark")
    for sx in (-0.1, 0.1):
        cyl(mb, M, (0.55, sx * 0.6, 0.86), 0.015, 0.01, "dark", seg=6, axis="Y")
    return []


@prop("toys_floor", "floor", (0.9, 0.6, 0.25), eras=ALL, rooms=KIDS)
def toys_floor(mb, x, y, z, rot, rng, era):
    """Scattered blocks, a ball and a pull-along train."""
    M, t = frame(x, y, z, rot), tier(era)
    for i in range(rng.randint(4, 7)):
        s = rng.uniform(0.07, 0.1)
        box(mb, M, (rng.uniform(-0.4, 0.1), rng.uniform(-0.25, 0.25), s / 2), (s, s, s),
            rng.choice(("accent", "leaf", "fabric", "paper", "glass")), r=(0, 0, rng.uniform(0, 1.5)))
    box(mb, M, (-0.2, 0.0, 0.135), (0.08, 0.08, 0.08), "accent", r=(0, 0, 0.3))
    sph(mb, M, (0.3, 0.2, 0.1), 0.1, rng.choice(("accent", "fabric", "leaf")))
    for i in range(2 if t >= 2 else 1):                         # train cars
        cx = 0.15 + i * 0.2
        box(mb, M, (cx, -0.2, 0.07), (0.17, 0.09, 0.08), "fabric" if i else "accent")
        for wx in (-0.05, 0.05):
            for wy in (-0.05, 0.05):
                cyl(mb, M, (cx + wx, -0.2 + wy, 0.03), 0.03, 0.02, "dark", seg=8, axis="Y")
    cyl(mb, M, (0.15, -0.2, 0.15), 0.025, 0.08, "dark", seg=8)
    return []


@prop("teddy_bear", "surface", (0.24, 0.2, 0.32), eras=ALL, rooms=KIDS)
def teddy_bear(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = rng.choice(("wood", "wood", "fabric2"))
    sph(mb, M, (0, 0, 0.09), 0.09, k, sq=(1, 0.9, 1.1))
    sph(mb, M, (0, -0.01, 0.23), 0.07, k)
    for sx in (-0.05, 0.05):
        sph(mb, M, (sx, 0, 0.3), 0.025, k)
        sph(mb, M, (sx * 1.6, -0.04, 0.03), 0.04, k)
        sph(mb, M, (sx * 1.9, -0.02, 0.13), 0.035, k)
    sph(mb, M, (0, -0.07, 0.22), 0.025, "paper")
    return []


@prop("poster", "wall", (0.5, 0.02, 0.7), eras=ALL, rooms=KIDS + ("bedroom", "apartment", "classroom", "garage", "arcade"))
def poster(mb, x, y, z, rot, rng, era):
    """Paper poster with bold graphic (rocket / star / band stripes); framed print before the 20th c."""
    M, t = frame(x, y, z, rot), tier(era)
    w, h = rng.uniform(0.4, 0.55), rng.uniform(0.55, 0.75)
    if t <= 1:
        box(mb, M, (0, -0.012, 0), (w + 0.06, 0.02, h + 0.06), "trim")
    box(mb, M, (0, -0.025, 0), (w, 0.01, h), "paper")
    k1, k2 = rng.sample(("accent", "fabric", "leaf", "glass", "trim"), 2)
    g = rng.randint(0, 2)
    if g == 0:
        cyl(mb, M, (0, -0.033, h * 0.12), w * 0.3, 0.008, k1, seg=14, axis="Y")
        box(mb, M, (0, -0.033, -h * 0.32), (w * 0.8, 0.008, h * 0.12), k2)
    elif g == 1:
        box(mb, M, (0, -0.033, h * 0.05), (w * 0.18, 0.008, h * 0.55), k1)
        box(mb, M, (0, -0.033, h * 0.33), (w * 0.12, 0.008, h * 0.12), k1, r=(0, 0.785, 0))
        box(mb, M, (0, -0.033, -h * 0.25), (w * 0.45, 0.008, h * 0.06), k2)
    else:
        for i in range(3):
            box(mb, M, (0, -0.033, -h * 0.3 + i * h * 0.22), (w * 0.86, 0.008, h * 0.1), (k1, k2, k1)[i])
    return []


# ============================================================================ living room
LIVING = ("living", "domestic", "apartment", "hotel", "study")


@prop("armchair", "floor", (0.9, 0.85, 1.05), eras=ALL, rooms=("living", "domestic", "study", "hotel", "apartment", "waiting"))
def armchair(mb, x, y, z, rot, rng, era):
    """Wing-back (pre-1900) / chunky club chair (interwar..) / low modern / pod chair (future); faces -Y."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("fut", "cyber", "solar", "space"):
        cyl(mb, M, (0, 0, 0.06), 0.25, 0.12, "metal", seg=12)
        sph(mb, M, (0, 0.05, 0.6), 0.48, "fabric", sq=(1.0, 0.9, 1.05), sub=2)
        sph(mb, M, (0, -0.15, 0.55), 0.36, "fabric2", sq=(0.9, 0.6, 0.6), sub=2)
        return []
    if s in ("antiq", "med", "ren", "enl", "vic"):
        box(mb, M, (0, -0.02, 0.4), (0.78, 0.74, 0.2), "fabric")
        box(mb, M, (0, 0.33, 0.8), (0.78, 0.14, 0.86), "fabric")
        for sx in (-0.38, 0.38):
            box(mb, M, (sx, 0.05, 0.62), (0.08, 0.66, 0.24), "fabric")
            box(mb, M, (sx * 1.02, 0.22, 0.98), (0.08, 0.26, 0.5), "fabric2")        # wings
        box(mb, M, (0, -0.05, 0.53), (0.66, 0.6, 0.08), "fabric2")
        for sx in (-0.33, 0.33):
            for sy in (-0.32, 0.32):
                cyl(mb, M, (sx, sy, 0.15), 0.03, 0.3, "wood", seg=8, r2=0.02)
        return []
    if s in ("inter", "cold"):
        box(mb, M, (0, 0, 0.27), (0.9, 0.84, 0.42), "fabric")
        box(mb, M, (0, 0.33, 0.66), (0.9, 0.2, 0.5), "fabric")
        for sx in (-0.37, 0.37):
            box(mb, M, (sx, 0.0, 0.52), (0.18, 0.84, 0.18), "fabric")
            cyl(mb, M, (sx, 0.0, 0.6), 0.09, 0.84, "fabric", seg=10, axis="Y")
        box(mb, M, (0, -0.07, 0.52), (0.56, 0.66, 0.1), "fabric2")
        return []
    box(mb, M, (0, 0, 0.3), (0.84, 0.78, 0.18), "fabric")
    box(mb, M, (0, 0.32, 0.6), (0.84, 0.14, 0.46), "fabric")
    for sx in (-0.38, 0.38):
        box(mb, M, (sx, 0.0, 0.48), (0.08, 0.78, 0.2), "fabric")
    box(mb, M, (0, -0.06, 0.43), (0.66, 0.6, 0.08), "fabric2")
    for sx in (-0.36, 0.36):
        for sy in (-0.34, 0.34):
            rod(mb, M, (sx * 1.08, sy * 1.08, 0.0), (sx, sy, 0.22), 0.018, "dark")
    return []


@prop("coffee_table", "floor", (1.1, 0.6, 0.45), eras=ALL, rooms=("living", "apartment", "hotel", "waiting"))
def coffee_table(mb, x, y, z, rot, rng, era):
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("cold", "analog"):                              # kidney / boomerang top, splayed legs
        _stadium(mb, M, (0, 0, 0.42), 1.1, 0.55, 0.04, "wood")
        for sx in (-0.4, 0.4):
            for sy in (-0.18, 0.18):
                rod(mb, M, (sx * 1.1, sy * 1.3, 0.0), (sx, sy, 0.4), 0.018, "dark")
    elif s in ("fut", "cyber", "solar", "space", "now"):
        box(mb, M, (0, 0, 0.4), (1.1, 0.6, 0.04), "glass" if s != "now" else "wood")
        box(mb, M, (0, 0, 0.2), (0.9, 0.45, 0.36), "metal2" if s != "now" else "wood2")
        box(mb, M, (0, 0, 0.08), (1.0, 0.5, 0.03), "wood2" if s == "now" else "metal")
    else:
        box(mb, M, (0, 0, 0.42), (1.1, 0.6, 0.05), "wood")
        box(mb, M, (0, 0, 0.36), (1.0, 0.5, 0.07), "wood2")
        legs4(mb, M, 1.0, 0.5, 0.36, 0.06, "wood")
        box(mb, M, (0, 0, 0.1), (0.94, 0.44, 0.025), "wood2")
    return [surf(M, (0, 0, 0.445), 0.35)]


@prop("side_table", "floor", (0.5, 0.5, 0.62), eras=ALL, rooms=("living", "bedroom", "hotel", "study", "apartment", "waiting"))
def side_table(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = "metal" if t == 4 else "wood"
    cyl(mb, M, (0, 0, 0.6), 0.25, 0.04, k, seg=14)
    cyl(mb, M, (0, 0, 0.3), 0.035, 0.58, "wood2" if k == "wood" else "metal2", seg=8)
    if t <= 2:
        for a in range(3):
            ang = a * math.tau / 3
            rod(mb, M, (0, 0, 0.12), (math.cos(ang) * 0.2, math.sin(ang) * 0.2, 0.0), 0.022, "wood2")
    else:
        cyl(mb, M, (0, 0, 0.015), 0.18, 0.03, "metal2", seg=12)
    return [surf(M, (0, 0, 0.62), 0.12)]


@prop("tv_set", "wall", (1.1, 0.5, 1.15), eras=MIDC | ANALOG | NOWS | FUTS, rooms=LIVING)
def tv_set(mb, x, y, z, rot, rng, era):
    """Radio-gram console (interwar) / wooden console TV with rabbit ears / CRT on a stand (80s-90s) /
    flat screen on a media unit / holo frame."""
    M, s = frame(x, y, z, rot), sub(era)
    if s == "inter":
        box(mb, M, (0, -0.24, 0.5), (1.1, 0.46, 0.8), "wood")
        legs4(mb, M, 1.04, 0.4, 0.12, 0.05, "wood2")
        box(mb, M, (-0.24, -0.475, 0.55), (0.46, 0.02, 0.5), "fabric2")
        for i in range(4):
            box(mb, M, (-0.24, -0.49, 0.36 + i * 0.12), (0.46, 0.015, 0.025), "wood2")
        box(mb, M, (0.28, -0.475, 0.7), (0.34, 0.02, 0.16), "paper")
        for sx in (0.18, 0.38):
            cyl(mb, M, (sx, -0.49, 0.5), 0.035, 0.03, "dark", seg=10, axis="Y")
        return [surf(M, (0, -0.24, 0.91), 0.35)]
    if s == "cold":
        box(mb, M, (0, -0.25, 0.48), (1.0, 0.48, 0.72), "wood")
        legs4(mb, M, 0.94, 0.42, 0.14, 0.04, "dark")
        box(mb, M, (-0.12, -0.495, 0.55), (0.56, 0.03, 0.44), "dark")
        box(mb, M, (-0.12, -0.51, 0.55), (0.48, 0.02, 0.36), "screen")
        box(mb, M, (0.33, -0.495, 0.55), (0.22, 0.02, 0.44), "fabric2")
        for zz in (0.68, 0.56):
            cyl(mb, M, (0.33, -0.51, zz), 0.035, 0.03, "metal", seg=10, axis="Y")
        rod(mb, M, (0, -0.25, 0.84), (-0.25, -0.3, 1.3), 0.008, "metal")
        rod(mb, M, (0, -0.25, 0.84), (0.25, -0.3, 1.3), 0.008, "metal")
        sph(mb, M, (0, -0.25, 0.86), 0.05, "dark")
        return []
    if s in ("analog", "post"):
        box(mb, M, (0, -0.25, 0.25), (0.9, 0.46, 0.5), "wood")
        box(mb, M, (0, -0.48, 0.25), (0.8, 0.02, 0.4), "dark")
        box(mb, M, (0, -0.27, 0.78), (0.66, 0.5, 0.56), "metal2")
        box(mb, M, (-0.07, -0.525, 0.78), (0.46, 0.02, 0.38), "screen")
        for zz in (0.9, 0.78, 0.66):
            box(mb, M, (0.25, -0.525, zz), (0.07, 0.02, 0.05), "dark")
        box(mb, M, (0.2, -0.3, 0.53), (0.36, 0.26, 0.08), "dark")      # VCR
        return []
    fut = s in ("fut", "cyber", "solar", "space")
    box(mb, M, (0, -0.22, 0.22), (1.4, 0.42, 0.44), "wood" if not fut else "metal")
    doors(mb, M, 0, -0.43, 0.04, 1.36, 0.36, 3, key="wood2" if not fut else "metal2")
    if fut:
        box(mb, M, (0, -0.06, 1.05), (1.2, 0.02, 0.7), "accent")
        box(mb, M, (0, -0.08, 1.05), (1.14, 0.02, 0.64), "screen")
    else:
        box(mb, M, (0, -0.05, 1.05), (1.24, 0.06, 0.72), "dark")
        box(mb, M, (0, -0.085, 1.05), (1.16, 0.01, 0.64), "screen")
        box(mb, M, (0.4, -0.2, 0.49), (0.3, 0.2, 0.06), "dark")
    return []


@prop("radio", "surface", (0.38, 0.22, 0.42), eras=MIDC | ANALOG | NOWS | FUTS, rooms=LIVING + ("kitchen", "office", "police", "garage", "bunker"))
def radio(mb, x, y, z, rot, rng, era):
    """Cathedral radio (interwar) / bakelite set (50s) / boombox (80s) / bluetooth speaker / smart puck."""
    M, s = frame(x, y, z, rot), sub(era)
    if s == "inter":
        box(mb, M, (0, 0, 0.14), (0.34, 0.2, 0.28), "wood")
        cyl(mb, M, (0, 0, 0.28), 0.17, 0.2, "wood", seg=14, axis="Y")
        cyl(mb, M, (0, -0.105, 0.24), 0.11, 0.02, "fabric2", seg=12, axis="Y")
        for i in range(3):
            box(mb, M, (-0.05 + i * 0.05, -0.12, 0.25), (0.015, 0.01, 0.2), "wood2")
        for sx in (-0.08, 0.08):
            cyl(mb, M, (sx, -0.11, 0.06), 0.022, 0.03, "dark", seg=8, axis="Y")
        return []
    if s == "cold":
        box(mb, M, (0, 0, 0.11), (0.36, 0.18, 0.22), "accent")
        box(mb, M, (-0.07, -0.095, 0.12), (0.18, 0.015, 0.14), "paper")
        cyl(mb, M, (0.11, -0.1, 0.12), 0.05, 0.02, "dark", seg=12, axis="Y")
        box(mb, M, (0, 0, 0.23), (0.3, 0.14, 0.03), "accent")
        return []
    if s in ("analog", "post"):
        box(mb, M, (0, 0, 0.13), (0.5, 0.16, 0.26), "metal2")
        for sx in (-0.16, 0.16):
            cyl(mb, M, (sx, -0.085, 0.12), 0.08, 0.02, "dark", seg=12, axis="Y")
        box(mb, M, (0, -0.085, 0.13), (0.14, 0.02, 0.08), "metal")
        rod(mb, M, (-0.2, 0, 0.26), (-0.2, 0, 0.32), 0.012, "dark")
        rod(mb, M, (0.2, 0, 0.26), (0.2, 0, 0.32), 0.012, "dark")
        rod(mb, M, (-0.2, 0, 0.32), (0.2, 0, 0.32), 0.015, "dark")
        return []
    fut = s in ("fut", "cyber", "solar", "space")
    cyl(mb, M, (0, 0, 0.09), 0.07, 0.18, "dark" if not fut else "metal", seg=14)
    cyl(mb, M, (0, 0, 0.185), 0.072, 0.012, "accent" if fut else "metal2", seg=14)
    return []


@prop("gramophone", "surface", (0.4, 0.45, 0.6), eras=VIC | INTER, rooms=LIVING + ("cabaret", "speakeasy", "attic"))
def gramophone(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.07), (0.34, 0.34, 0.14), "wood")
    cyl(mb, M, (0, 0, 0.15), 0.15, 0.02, "dark", seg=16)
    cyl(mb, M, (0, 0, 0.165), 0.03, 0.02, "accent", seg=8)
    cyl(mb, M, (0.13, 0.12, 0.2), 0.02, 0.12, "glass2", seg=8)
    rod(mb, M, (0.13, 0.12, 0.25), (0.05, 0.04, 0.19), 0.012, "glass2")
    cyl(mb, M, (0.13, 0.2, 0.38), 0.03, 0.3, "glass2", seg=10, r2=0.2, rr=(math.radians(-60), 0, 0))
    box(mb, M, (-0.18, 0, 0.09), (0.03, 0.03, 0.05), "metal")
    return []


@prop("record_player", "surface", (0.45, 0.35, 0.14), eras=COLD | ANALOG | NOWS | FUTS, rooms=LIVING + ("arcade", "nightclub"))
def record_player(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.04), (0.45, 0.35, 0.08), "wood" if tier(era) == 2 else "metal2")
    cyl(mb, M, (-0.05, 0, 0.09), 0.15, 0.015, "dark", seg=16)
    cyl(mb, M, (-0.05, 0, 0.1), 0.04, 0.008, "accent", seg=10)
    rod(mb, M, (0.17, 0.12, 0.1), (0.05, -0.06, 0.1), 0.01, "metal")
    if tier(era) == 2:                                   # lid propped open
        box(mb, M, (0, 0.24, 0.2), (0.44, 0.012, 0.3), "glass", r=(-0.35, 0, 0))
    return []


@prop("piano", "wall", (1.5, 0.62, 1.3), eras=ALL - ANTIQ - MEDV,
      rooms=("living", "saloon", "cabaret", "speakeasy", "church", "classroom", "hotel", "parlour"))
def piano(mb, x, y, z, rot, rng, era):
    """Upright piano (keys, music sheet, candle arms for the 19th c.)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "dark" if s not in ("vic", "ren", "enl") or rng.random() < 0.5 else "wood2"
    box(mb, M, (0, -0.2, 0.65), (1.5, 0.38, 1.3), k)
    box(mb, M, (0, -0.21, 1.32), (1.56, 0.42, 0.05), k)
    box(mb, M, (0, -0.48, 0.74), (1.42, 0.24, 0.08), k)
    box(mb, M, (0, -0.48, 0.785), (1.32, 0.2, 0.015), "paper")
    for i in range(14):
        if i % 7 in (2, 6):
            continue
        box(mb, M, (-0.6 + i * 0.09, -0.43, 0.8), (0.035, 0.1, 0.02), "dark")
    box(mb, M, (0, -0.4, 0.98), (1.32, 0.03, 0.3), k)
    box(mb, M, (0, -0.42, 1.06), (0.4, 0.02, 0.26), "paper", r=(-0.15, 0, 0))
    for sx in (-0.68, 0.68):
        box(mb, M, (sx, -0.52, 0.36), (0.06, 0.06, 0.72), k)
    box(mb, M, (0, -0.395, 0.3), (1.3, 0.02, 0.5), "wood2" if k == "dark" else "wood")
    if s in ("vic", "enl", "ren"):
        for sx in (-0.5, 0.5):
            cyl(mb, M, (sx, -0.42, 1.12), 0.04, 0.02, "metal", seg=8)
            cyl(mb, M, (sx, -0.42, 1.2), 0.015, 0.14, "paper", seg=6)
            cyl(mb, M, (sx, -0.42, 1.29), 0.008, 0.035, "flame", seg=6)
    return [surf(M, (0.4, -0.22, 1.35), 0.25)]


@prop("fireplace_tools", "floor", (0.3, 0.3, 0.8), eras=ALL, rooms=("hearth",))
def fireplace_tools(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.02), 0.12, 0.04, "dark", seg=10)
    cyl(mb, M, (0, 0, 0.36), 0.015, 0.68, "dark", seg=6)
    box(mb, M, (0, 0, 0.66), (0.22, 0.03, 0.025), "dark")
    for i, sx in enumerate((-0.09, 0, 0.09)):
        rod(mb, M, (sx, -0.02, 0.68), (sx * 1.3, -0.04, 0.12), 0.01, "metal2")
        if i == 0:
            box(mb, M, (sx * 1.3, -0.04, 0.09), (0.08, 0.02, 0.08), "metal2")
        elif i == 2:
            cyl(mb, M, (sx * 1.3, -0.04, 0.1), 0.03, 0.1, "dark", seg=6)
    sph(mb, M, (0, 0, 0.72), 0.03, "metal")
    return []


@prop("floor_lamp", "floor", (0.45, 0.45, 1.7), eras=ALL, rooms=("living", "bedroom", "hotel", "study", "apartment", "waiting", "parlour"))
def floor_lamp(mb, x, y, z, rot, rng, era):
    """Iron candle stand (pre-1700) / brass oil standard lamp (18th-19th c.) / fringed standard lamp /
    arc lamp (modern) / light column (future)."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("antiq", "med", "ren"):
        for a in range(3):
            ang = a * math.tau / 3
            rod(mb, M, (0, 0, 0.25), (math.cos(ang) * 0.22, math.sin(ang) * 0.22, 0.0), 0.02, "dark")
        cyl(mb, M, (0, 0, 0.8), 0.02, 1.2, "dark", seg=6)
        cyl(mb, M, (0, 0, 1.42), 0.1, 0.04, "dark", seg=10)
        cyl(mb, M, (0, 0, 1.53), 0.035, 0.18, "paper", seg=8)
        cyl(mb, M, (0, 0, 1.65), 0.012, 0.06, "flame", seg=6)
        return []
    if s in ("enl", "vic"):
        cyl(mb, M, (0, 0, 0.03), 0.18, 0.06, "metal", seg=12)
        cyl(mb, M, (0, 0, 0.7), 0.02, 1.3, "metal", seg=8)
        sph(mb, M, (0, 0, 1.38), 0.08, "glass2", sq=(1, 1, 0.8))
        cyl(mb, M, (0, 0, 1.52), 0.03, 0.18, "glass", seg=8)
        cyl(mb, M, (0, 0, 1.6), 0.24, 0.2, "lampshade", seg=12, r2=0.12)
        return []
    if s in ("inter", "cold"):
        cyl(mb, M, (0, 0, 0.03), 0.17, 0.06, "dark" if s == "inter" else "metal", seg=12)
        cyl(mb, M, (0, 0, 0.75), 0.018, 1.4, "metal", seg=8)
        cyl(mb, M, (0, 0, 1.5), 0.26, 0.3, "lampshade", seg=14, r2=0.18)
        cyl(mb, M, (0, 0, 1.33), 0.265, 0.04, "fabric2", seg=14)            # fringe
        return []
    if s in ("fut", "cyber", "solar", "space"):
        cyl(mb, M, (0, 0, 0.02), 0.16, 0.04, "metal", seg=12)
        box(mb, M, (0, 0, 0.85), (0.08, 0.08, 1.6), "metal2")
        box(mb, M, (0, -0.042, 0.95), (0.04, 0.02, 1.2), "lampshade")
        return []
    box(mb, M, (0, 0, 0.04), (0.32, 0.32, 0.08), "dark")                    # arc lamp
    pts = [(math.sin(a) * 0.55, 0, 0.08 + math.cos(a - 0.2) * 1.55 - 0.05) for a in [i * 0.25 for i in range(6)]]
    for a, b in zip(pts, pts[1:]):
        rod(mb, M, a, b, 0.018, "metal", seg=6)
    ex = pts[-1]
    cyl(mb, M, (ex[0], 0, ex[2] - 0.12), 0.06, 0.2, "metal2", seg=12, r2=0.2)
    cyl(mb, M, (ex[0], 0, ex[2] - 0.22), 0.16, 0.02, "lampshade", seg=12)
    return []


@prop("table_lamp", "surface", (0.3, 0.3, 0.55), eras=ALL, rooms=("living", "bedroom", "hotel", "study", "office", "apartment", "parlour"))
def table_lamp(mb, x, y, z, rot, rng, era):
    """Clay oil lamp / brass oil lamp with glass chimney / deco or ceramic electric / modern cone / orb."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("antiq", "med"):
        cyl(mb, M, (0, 0, 0.03), 0.08, 0.06, "stone", seg=10, sq=(1.4, 1.0, 1.0))
        rod(mb, M, (0.09, 0, 0.05), (0.14, 0, 0.07), 0.02, "stone")
        cyl(mb, M, (0.15, 0, 0.1), 0.012, 0.05, "flame", seg=6)
        return []
    if s in ("ren", "enl", "vic"):
        cyl(mb, M, (0, 0, 0.03), 0.08, 0.06, "metal", seg=10)
        cyl(mb, M, (0, 0, 0.12), 0.02, 0.12, "metal", seg=8)
        sph(mb, M, (0, 0, 0.22), 0.07, "glass2", sq=(1, 1, 0.8))
        cyl(mb, M, (0, 0, 0.36), 0.035, 0.2, "glass", seg=8, r2=0.025)
        cyl(mb, M, (0, 0, 0.32), 0.012, 0.05, "flame", seg=6)
        return []
    if s == "inter":                                     # deco: stepped base, glass torch shade
        for i, r in enumerate((0.1, 0.075, 0.05)):
            cyl(mb, M, (0, 0, 0.02 + i * 0.04), r, 0.04, "metal", seg=10)
        cyl(mb, M, (0, 0, 0.22), 0.015, 0.26, "metal", seg=6)
        cyl(mb, M, (0, 0, 0.4), 0.06, 0.16, "lampshade", seg=10, r2=0.14)
        return []
    if s in ("cold", "analog"):
        sph(mb, M, (0, 0, 0.12), 0.1, rng.choice(("accent", "glass", "paper")), sq=(1, 1, 1.2))
        cyl(mb, M, (0, 0, 0.27), 0.012, 0.1, "metal", seg=6)
        cyl(mb, M, (0, 0, 0.4), 0.17, 0.2, "lampshade", seg=12, r2=0.13)
        return []
    if s in ("fut", "cyber", "solar", "space"):
        cyl(mb, M, (0, 0, 0.02), 0.06, 0.04, "metal", seg=10)
        sph(mb, M, (0, 0, 0.16), 0.11, "lampshade")
        return []
    cyl(mb, M, (0, 0, 0.015), 0.08, 0.03, "metal2", seg=10)
    cyl(mb, M, (0, 0, 0.2), 0.012, 0.36, "metal", seg=6)
    cyl(mb, M, (0, 0, 0.4), 0.14, 0.18, "lampshade", seg=12, r2=0.1)
    return []


@prop("candelabra", "surface", (0.35, 0.12, 0.45), eras=PRE | VIC, rooms=("church", "dining", "parlour", "castle", "living", "court"))
def candelabra(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.02), 0.08, 0.04, "metal", seg=10)
    cyl(mb, M, (0, 0, 0.14), 0.015, 0.22, "metal", seg=6)
    rod(mb, M, (-0.14, 0, 0.22), (0.14, 0, 0.22), 0.012, "metal")
    for sx in (-0.14, 0, 0.14):
        zb = 0.24 if sx else 0.27
        cyl(mb, M, (sx, 0, zb), 0.03, 0.02, "metal", seg=8)
        cyl(mb, M, (sx, 0, zb + 0.08), 0.014, 0.14, "paper", seg=6)
        cyl(mb, M, (sx, 0, zb + 0.17), 0.007, 0.035, "flame", seg=6)
    return []


@prop("gas_lamp", "wall", (0.25, 0.3, 0.45), eras=VIC | INTER, rooms=("parlour", "living", "saloon", "court", "office", "shop", "police", "hallway"))
def gas_lamp(mb, x, y, z, rot, rng, era):
    """Wall gas bracket: back plate, swan-neck pipe, frosted globe (centre at z)."""
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, -0.01, 0), 0.06, 0.02, "metal", seg=10, axis="Y")
    rod(mb, M, (0, -0.02, 0), (0, -0.2, -0.05), 0.014, "metal")
    rod(mb, M, (0, -0.2, -0.05), (0, -0.24, 0.05), 0.014, "metal")
    cyl(mb, M, (0, -0.24, 0.07), 0.03, 0.04, "metal", seg=8)
    sph(mb, M, (0, -0.24, 0.17), 0.09, "lampshade", sq=(1, 1, 1.15))
    cyl(mb, M, (0, -0.24, 0.13), 0.01, 0.03, "flame", seg=6)
    return []


@prop("curtain_panel", "wall", (0.45, 0.16, 2.4), eras=ALL, rooms=("curtains",))
def curtain_panel(mb, x, y, z, rot, rng, era):
    """One pleated drape (floor-length, top at ~2.3 m) with a tie-back."""
    M = frame(x, y, z, rot)
    k = "fabric"
    n = 4
    for i in range(n):
        px = -0.17 + i * 0.115
        box(mb, M, (px, -0.07 - (i % 2) * 0.03, 1.16), (0.13, 0.05, 2.28), k if i % 2 == 0 else "fabric2")
    box(mb, M, (0, -0.1, 0.95), (0.5, 0.1, 0.05), "accent")
    box(mb, M, (0, -0.08, 2.3), (0.5, 0.12, 0.06), "fabric2")
    return []


@prop("grandfather_clock", "wall", (0.5, 0.32, 2.05), eras=(PRE - ANTIQ - MEDV) | VIC | MIDC, rooms=("living", "parlour", "hallway", "study", "court", "attic"))
def grandfather_clock(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, -0.16, 0.15), (0.52, 0.32, 0.3), "wood2")
    box(mb, M, (0, -0.15, 0.85), (0.38, 0.26, 1.1), "wood")
    box(mb, M, (0, -0.16, 1.68), (0.5, 0.3, 0.56), "wood2")
    box(mb, M, (0, -0.16, 2.0), (0.56, 0.34, 0.08), "wood")
    cyl(mb, M, (0, -0.32, 1.66), 0.17, 0.02, "paper", seg=16, axis="Y")
    rod(mb, M, (0, -0.335, 1.66), (0.0, -0.335, 1.78), 0.01, "dark")
    rod(mb, M, (0, -0.335, 1.66), (0.08, -0.335, 1.62), 0.01, "dark")
    box(mb, M, (0, -0.285, 0.95), (0.22, 0.02, 0.7), "glass")
    rod(mb, M, (0, -0.3, 1.25), (0, -0.3, 0.8), 0.006, "metal")
    cyl(mb, M, (0, -0.305, 0.76), 0.06, 0.02, "metal", seg=12, axis="Y")
    return []


@prop("telephone", "surface", (0.24, 0.2, 0.32), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("office", "police", "living", "hotel", "reception", "domestic", "apartment", "bunker"))
def telephone(mb, x, y, z, rot, rng, era):
    """Candlestick (1890s-1920s) / rotary desk phone / push-button corded / cordless / smartphone dock."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("vic", "inter"):
        cyl(mb, M, (0, 0, 0.02), 0.07, 0.04, "dark", seg=12)
        cyl(mb, M, (0, 0, 0.15), 0.016, 0.24, "dark", seg=8)
        cyl(mb, M, (0, -0.04, 0.27), 0.03, 0.06, "dark", seg=10, r2=0.04, rr=(math.radians(70), 0, 0))
        rod(mb, M, (0.03, 0, 0.24), (0.07, 0, 0.24), 0.008, "metal")
        cyl(mb, M, (0.08, 0, 0.17), 0.022, 0.12, "dark", seg=8, r2=0.03)
        return []
    if s in ("cold", "analog", "post"):
        k = "dark" if s != "analog" else rng.choice(("paper", "accent", "dark"))
        cyl(mb, M, (0, 0, 0.05), 0.11, 0.1, k, seg=12, r2=0.08, sq=(1.0, 1.15, 1.0))
        box(mb, M, (0, 0.0, 0.12), (0.22, 0.05, 0.04), k)
        for sx in (-0.1, 0.1):
            box(mb, M, (sx, 0.0, 0.135), (0.05, 0.07, 0.05), k)
        if s == "analog":
            box(mb, M, (0, -0.06, 0.07), (0.08, 0.06, 0.04), "paper", r=(0.5, 0, 0))
        else:
            cyl(mb, M, (0, -0.08, 0.06), 0.04, 0.02, "paper", seg=12, axis="Y", rr=(0.6, 0, 0))
        rod(mb, M, (-0.11, 0.02, 0.1), (-0.2, 0.06, 0.0), 0.006, k)
        return []
    if s == "now":
        box(mb, M, (0, 0, 0.025), (0.14, 0.16, 0.05), "dark")
        box(mb, M, (0, 0.03, 0.09), (0.05, 0.03, 0.17), "dark", r=(0.2, 0, 0))
        box(mb, M, (0, -0.06, 0.052), (0.08, 0.02, 0.006), "screen")
        return []
    box(mb, M, (0, 0, 0.012), (0.12, 0.12, 0.024), "metal")
    box(mb, M, (0, 0.02, 0.09), (0.08, 0.012, 0.15), "dark", r=(0.3, 0, 0))
    box(mb, M, (0, 0.012, 0.09), (0.07, 0.006, 0.13), "screen", r=(0.3, 0, 0))
    return []


@prop("wall_phone", "wall", (0.3, 0.14, 0.55), eras=VIC | MIDC | ANALOG, rooms=("kitchen", "hallway", "saloon", "shop", "police", "apartment", "diner"))
def wall_phone(mb, x, y, z, rot, rng, era):
    """Wooden crank phone with twin bells (19th c./interwar) / wall rotary or push-button (centre at z)."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("vic", "inter"):
        box(mb, M, (0, -0.06, 0), (0.24, 0.12, 0.46), "wood")
        for sx in (-0.06, 0.06):
            sph(mb, M, (sx, -0.13, 0.16), 0.045, "metal", sq=(1, 0.7, 1))
        cyl(mb, M, (0, -0.15, 0.0), 0.03, 0.08, "dark", seg=10, axis="Y", r2=0.045)
        box(mb, M, (0, -0.1, -0.22), (0.26, 0.1, 0.03), "wood2")
        rod(mb, M, (0.12, -0.08, 0.02), (0.18, -0.08, 0.02), 0.01, "metal")
        rod(mb, M, (0.18, -0.08, 0.02), (0.18, -0.13, 0.08), 0.012, "dark")
        cyl(mb, M, (-0.16, -0.1, 0.0), 0.02, 0.12, "dark", seg=8)
        return []
    k = "accent" if s == "analog" else "dark"
    box(mb, M, (0, -0.04, 0), (0.12, 0.08, 0.22), k)
    box(mb, M, (0.0, -0.1, 0.0), (0.05, 0.05, 0.22), k)
    for zz in (-0.1, 0.1):
        box(mb, M, (0, -0.1, zz), (0.07, 0.07, 0.05), k)
    rod(mb, M, (0, -0.06, -0.12), (0.06, -0.08, -0.4), 0.006, k)
    return []


@prop("radiator", "wall", (0.8, 0.16, 0.7), eras=VIC | MIDC | ANALOG | NOWS, rooms=("bathroom", "classroom", "office", "hospital", "waiting", "apartment", "hotel", "police", "court", "bedroom"))
def radiator(mb, x, y, z, rot, rng, era):
    """Cast-iron column radiator (centre at z ~0.45)."""
    M, t = frame(x, y, z, rot), tier(era)
    k = "metal2" if t <= 2 else "paper"
    n = 9
    for i in range(n):
        box(mb, M, (-0.36 + i * 0.09, -0.08, 0.0), (0.06, 0.12, 0.62), k)
    for zz in (-0.27, 0.27):
        box(mb, M, (0, -0.08, zz), (0.8, 0.08, 0.06), k)
    for sx in (-0.36, 0.36):
        box(mb, M, (sx, -0.08, -0.36), (0.06, 0.1, 0.1), k)
    cyl(mb, M, (0.44, -0.08, -0.25), 0.03, 0.06, "metal", seg=8, axis="X")
    return []


@prop("coat_hooks", "wall", (0.9, 0.28, 0.7), eras=ALL, rooms=("hallway", "office", "classroom", "police", "waiting", "saloon", "apartment"))
def coat_hooks(mb, x, y, z, rot, rng, era):
    """Peg board with coats and a hat (centre at z ~1.5)."""
    M = frame(x, y, z, rot)
    box(mb, M, (0, -0.02, 0.25), (0.9, 0.04, 0.12), "wood")
    for i in range(4):
        rod(mb, M, (-0.33 + i * 0.22, -0.04, 0.24), (-0.33 + i * 0.22, -0.12, 0.27), 0.015, "metal")
    for i in rng.sample(range(4), rng.randint(2, 3)):
        px = -0.33 + i * 0.22
        k = rng.choice(("fabric", "fabric2", "wood2", "dark"))
        cyl(mb, M, (px, -0.13, -0.15), 0.09, 0.75, k, seg=8, r2=0.05, sq=(1.3, 0.7, 1.0))
        box(mb, M, (px, -0.13, 0.2), (0.16, 0.08, 0.08), k)
    if rng.random() < 0.7:
        px = -0.33 + rng.randint(0, 3) * 0.22
        cyl(mb, M, (px, -0.14, 0.33), 0.13, 0.015, "dark", seg=12)
        cyl(mb, M, (px, -0.14, 0.38), 0.08, 0.1, "dark", seg=12)
    return []


@prop("coat_stand", "floor", (0.5, 0.5, 1.85), eras=ALL, rooms=("office", "police", "waiting", "hallway", "study", "saloon", "speakeasy", "hotel"))
def coat_stand(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "wood" if tier(era) <= 2 else "metal"
    for a in range(3):
        ang = a * math.tau / 3
        rod(mb, M, (0, 0, 0.2), (math.cos(ang) * 0.24, math.sin(ang) * 0.24, 0.0), 0.02, k)
    cyl(mb, M, (0, 0, 0.9), 0.025, 1.7, k, seg=8)
    sph(mb, M, (0, 0, 1.78), 0.04, k)
    for a in range(4):
        ang = a * math.tau / 4
        rod(mb, M, (0, 0, 1.6), (math.cos(ang) * 0.15, math.sin(ang) * 0.15, 1.7), 0.012, k)
    cc = rng.choice(("fabric", "fabric2", "dark"))
    cyl(mb, M, (0.12, 0, 1.15), 0.12, 0.85, cc, seg=8, r2=0.06, sq=(1.0, 0.8, 1.0))
    if rng.random() < 0.6:
        cyl(mb, M, (-0.12, 0, 1.7), 0.12, 0.015, "dark", seg=12)
        cyl(mb, M, (-0.12, 0, 1.75), 0.075, 0.09, "dark", seg=12)
    return []


@prop("umbrella_stand", "floor", (0.3, 0.3, 0.9), eras=VIC | MIDC | ANALOG | NOWS, rooms=("hallway", "waiting", "office", "hotel"))
def umbrella_stand(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.27), 0.12, 0.54, rng.choice(("metal2", "stone", "accent")), seg=10)
    for i in range(rng.randint(2, 3)):
        a = i * 2.1
        tip = (math.cos(a) * 0.07, math.sin(a) * 0.07)
        cyl(mb, M, (tip[0], tip[1], 0.55), 0.05, 0.5, rng.choice(("dark", "fabric", "fabric2")), seg=8, r2=0.015)
        rod(mb, M, (tip[0], tip[1], 0.8), (tip[0] * 1.6, tip[1] * 1.6, 0.92), 0.012, "wood2")
    return []


@prop("potted_fern", "floor", (0.55, 0.55, 1.0), eras=ALL, rooms=("domestic", "living", "office", "waiting", "hotel", "parlour", "hallway", "apartment", "church", "court", "cafe", "lab", "shop"))
def potted_fern(mb, x, y, z, rot, rng, era):
    """Fern / palm in a pot; on a tall plant stand for the 19th c. parlour."""
    M, s = frame(x, y, z, rot), sub(era)
    z0 = 0.0
    if s in ("vic", "enl"):
        cyl(mb, M, (0, 0, 0.35), 0.03, 0.7, "wood2", seg=8)
        for a in range(3):
            ang = a * math.tau / 3
            rod(mb, M, (0, 0, 0.12), (math.cos(ang) * 0.18, math.sin(ang) * 0.18, 0.0), 0.02, "wood2")
        cyl(mb, M, (0, 0, 0.71), 0.16, 0.03, "wood2", seg=10)
        z0 = 0.72
    pot = {"antiq": "stone", "med": "stone"}.get(s, rng.choice(("accent", "stone", "paper", "wall2")))
    cyl(mb, M, (0, 0, z0 + 0.14), 0.15, 0.28, pot, seg=10, r2=0.19)
    cyl(mb, M, (0, 0, z0 + 0.285), 0.2, 0.03, pot, seg=10)
    n = rng.randint(6, 9)
    for i in range(n):
        a = i / n * math.tau + rng.uniform(-0.2, 0.2)
        L = rng.uniform(0.35, 0.55)
        tilt = rng.uniform(0.5, 1.0)
        base = (0, 0, z0 + 0.3)
        mid = (math.cos(a) * L * 0.5 * tilt, math.sin(a) * L * 0.5 * tilt, z0 + 0.3 + L * 0.6)
        sph(mb, M, mid, L * 0.5, "leaf", sq=(0.45, 0.45, 1.0) if tilt < 0.7 else (0.6, 0.6, 0.7))
    return []


@prop("rug_round", "floor", (1.8, 1.8, 0.02), eras=ALL, rooms=("kids", "living", "bedroom", "hotel", "apartment", "parlour"))
def rug_round(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    r = rng.uniform(0.7, 0.9)
    cyl(mb, M, (0, 0, 0.007), r, 0.014, "rug", seg=20)
    cyl(mb, M, (0, 0, 0.016), r * 0.75, 0.006, "fabric2", seg=20)
    cyl(mb, M, (0, 0, 0.021), r * 0.45, 0.006, "rug", seg=16)
    return []


@prop("painting", "wall", (0.9, 0.06, 0.7), eras=ALL, rooms=("living", "parlour", "hallway", "hotel", "study", "court", "office", "church", "attic"))
def painting(mb, x, y, z, rot, rng, era):
    """Framed landscape (gilt frame before 1900) - centre at z."""
    M, t = frame(x, y, z, rot), tier(era)
    w, h = rng.uniform(0.7, 1.0), rng.uniform(0.5, 0.75)
    fr = "metal" if t <= 1 else ("dark" if t >= 3 else "trim")
    box(mb, M, (0, -0.025, 0), (w + 0.12, 0.05, h + 0.12), fr)
    box(mb, M, (0, -0.052, h * 0.18), (w, 0.01, h * 0.64), "glass" if rng.random() < 0.5 else "paper")
    box(mb, M, (0, -0.052, -h * 0.33), (w, 0.01, h * 0.34), "leaf")
    box(mb, M, (-w * 0.15, -0.058, -h * 0.1), (w * 0.5, 0.008, h * 0.25), "wall2", r=(0, 0.25, 0))
    cyl(mb, M, (w * 0.28, -0.06, h * 0.25), h * 0.1, 0.008, "accent", seg=12, axis="Y")
    return []


@prop("standing_mirror", "floor", (0.7, 0.5, 1.7), eras=ALL, rooms=("bedroom", "attic", "hotel", "boutique", "shop"))
def standing_mirror(mb, x, y, z, rot, rng, era):
    """Cheval mirror on a swing frame."""
    M = frame(x, y, z, rot)
    k = "wood" if tier(era) <= 2 else "metal"
    for sx in (-0.3, 0.3):
        box(mb, M, (sx, 0, 0.03), (0.06, 0.48, 0.06), k)
        box(mb, M, (sx, 0, 0.8), (0.05, 0.05, 1.56), k)
    cyl(mb, M, (0, 0, 0.9), 0.24, 0.04, k, seg=16, axis="Y", sq=(1.0, 1.0, 2.6), rr=(-0.12, 0, 0))
    cyl(mb, M, (0, -0.022, 0.9), 0.2, 0.02, "glass", seg=16, axis="Y", sq=(1.0, 1.0, 2.8), rr=(-0.12, 0, 0))
    return []


@prop("suitcase", "floor", (0.7, 0.26, 0.55), eras=ALL, rooms=("hotel", "attic", "bedroom", "station", "waiting"))
def suitcase(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = {0: "wood2", 1: "wood2", 2: "wood", 3: rng.choice(("fabric", "accent", "dark")), 4: "metal"}[t]
    box(mb, M, (0, 0, 0.27), (0.68, 0.24, 0.48), k)
    rod(mb, M, (-0.08, 0, 0.51), (-0.08, 0, 0.56), 0.012, "dark")
    rod(mb, M, (0.08, 0, 0.51), (0.08, 0, 0.56), 0.012, "dark")
    rod(mb, M, (-0.09, 0, 0.56), (0.09, 0, 0.56), 0.016, "dark")
    if t <= 2:
        for sx in (-0.2, 0.2):
            box(mb, M, (sx, 0, 0.27), (0.05, 0.25, 0.49), "trim")
        for sx in (-0.34, 0.34):
            box(mb, M, (sx, 0, 0.05), (0.04, 0.25, 0.08), "metal")
        box(mb, M, (0.1, -0.122, 0.36), (0.14, 0.01, 0.09), "paper")
    else:
        for sx in (-0.28, 0.28):
            cyl(mb, M, (sx, 0, 0.025), 0.025, 0.05, "dark", seg=8, axis="Y")
    return []


# ============================================================================ attic
ATTIC = ("attic",)


@prop("trunk", "floor", (0.95, 0.52, 0.62), eras=ALL, rooms=ATTIC + ("bedroom", "pirate", "nautical", "ship"))
def trunk(mb, x, y, z, rot, rng, era):
    """Domed steamer / sea chest with straps and brass corners."""
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0, 0.22), (0.9, 0.5, 0.44), "wood")
    cyl(mb, M, (0, 0, 0.42), 0.25, 0.9, "wood", seg=12, axis="X", sq=(1.0, 1.0, 0.55))
    for sx in (-0.3, 0.3):
        box(mb, M, (sx, 0, 0.3), (0.06, 0.52, 0.6), "wood2")
    box(mb, M, (0, -0.252, 0.44), (0.92, 0.02, 0.04), "metal")
    box(mb, M, (0, -0.262, 0.4), (0.08, 0.02, 0.1), "metal")
    for sx in (-0.44, 0.44):
        for sy in (-0.24, 0.24):
            box(mb, M, (sx, sy, 0.04), (0.06, 0.06, 0.08), "metal")
        box(mb, M, (sx * 1.04, 0, 0.3), (0.03, 0.12, 0.05), "dark")
    return [surf(M, (0, 0, 0.56), 0.25)]


@prop("dust_sheet", "floor", (1.0, 0.8, 1.2), eras=ALL, rooms=ATTIC + ("abandoned",))
def dust_sheet(mb, x, y, z, rot, rng, era):
    """Furniture under a white dust sheet: tall bureau, armchair or table shape (rng)."""
    M = frame(x, y, z, rot)
    kind = rng.randint(0, 2)
    if kind == 0:
        w, d, h = 0.8, 0.5, rng.uniform(1.3, 1.7)
    elif kind == 1:
        w, d, h = 0.85, 0.8, 0.95
    else:
        w, d, h = 1.0, 0.7, 0.78
    cyl(mb, M, (0, 0, h * 0.45), max(w, d) * 0.55, h * 0.9, "paper", seg=10, r2=max(w, d) * 0.5, sq=(w / max(w, d), d / max(w, d), 1.0))
    if kind == 1:
        sph(mb, M, (0, 0.22, h * 0.95), 0.4, "paper", sq=(1.0, 0.45, 0.6))
        for sx in (-0.38, 0.38):
            sph(mb, M, (sx, 0, h * 0.62), 0.18, "paper", sq=(0.7, 1.6, 0.6))
    else:
        sph(mb, M, (0, 0, h * 0.9), max(w, d) * 0.55, "paper", sq=(w / max(w, d), d / max(w, d), 0.25))
    for i in range(5):                                        # hanging folds at the hem
        a = i / 5 * math.tau + rng.uniform(0, 0.5)
        box(mb, M, (math.cos(a) * w * 0.5, math.sin(a) * d * 0.5, 0.15), (0.12, 0.06, 0.3), "paper", r=(0, 0, a))
    return []


@prop("boxes_stack", "floor", (0.8, 0.6, 1.1), eras=ELECTRIC | VIC, rooms=ATTIC + ("storage", "shop", "garage", "apartment"))
def boxes_stack(mb, x, y, z, rot, rng, era):
    """Stacked cardboard boxes with tape and scrawled labels."""
    M = frame(x, y, z, rot)
    zz = 0.0
    for i in range(rng.randint(2, 4)):
        w, d, h = rng.uniform(0.45, 0.7), rng.uniform(0.35, 0.55), rng.uniform(0.25, 0.4)
        ox, oy, a = rng.uniform(-0.06, 0.06), rng.uniform(-0.05, 0.05), rng.uniform(-0.25, 0.25)
        box(mb, M, (ox, oy, zz + h / 2), (w, d, h), "wood", r=(0, 0, a))
        box(mb, M, (ox, oy, zz + h + 0.002), (w * 0.15, d + 0.005, 0.008), "glass2", r=(0, 0, a))
        box(mb, M, (ox - math.sin(a) * 0.0, oy - d / 2 - 0.004, zz + h * 0.55), (w * 0.4, 0.008, h * 0.3), "paper", r=(0, 0, a))
        zz += h
        w *= 0.9
    return []


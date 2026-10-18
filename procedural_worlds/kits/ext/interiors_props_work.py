"""Interiors asset pack, part 2: civic / work props (office, police, hospital, classroom, lab, factory,
shop, courtroom, church, waiting room). Conventions in interiors_geo; era variants switch on sub(era)."""
import math
from ..props import prop
from .interiors_geo import (frame, box, cyl, sph, rod, surf, legs4, drawers, doors, tier, sub,
                            ANTIQ, MEDV, PRE, VIC, INTER, COLD, MIDC, ANALOG, NOWS, FUTS, INDUSTRIAL_ON, ELECTRIC, ALL)

FUTSUB = ("fut", "cyber", "solar", "space")


# ============================================================================ office
OFFICE = ("office", "police", "study", "bunker", "counting_house", "cubicles")


@prop("filing_cabinet", "wall", (0.5, 0.65, 1.35), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=OFFICE + ("hospital", "classroom", "lab", "court"))
def filing_cabinet(mb, x, y, z, rot, rng, era):
    """Oak card cabinet (19th c.) / 4-drawer steel cabinet, one drawer pulled out."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s in ("vic", "inter") else ("metal" if s in FUTSUB else "metal2" if s == "cold" else "metal")
    box(mb, M, (0, -0.33, 0.67), (0.5, 0.64, 1.34), k)
    n = 4
    out = rng.randrange(n) if rng.random() < 0.5 else -1
    for i in range(n):
        zc = 0.17 + i * 0.33
        dy = -0.25 if i == out else 0.0
        box(mb, M, (0, -0.66 + dy, zc), (0.46, 0.03, 0.29), "wood2" if k == "wood" else "metal2" if k == "metal" else "metal")
        box(mb, M, (0, -0.69 + dy, zc + 0.04), (0.16, 0.03, 0.03), "dark")
        box(mb, M, (0, -0.68 + dy, zc + 0.1), (0.1, 0.01, 0.05), "paper")
        if dy:
            box(mb, M, (0, -0.55, zc + 0.04), (0.42, 0.24, 0.2), "metal2" if k != "wood" else "wood2")
            for j in range(5):
                box(mb, M, (0, -0.47 - j * 0.035, zc + 0.12), (0.38, 0.012, 0.18), "paper" if j % 2 else "accent")
    return [surf(M, (0, -0.33, 1.34), 0.18)]


@prop("typewriter", "surface", (0.42, 0.34, 0.24), eras=VIC | MIDC, rooms=OFFICE + ("newsroom",))
def typewriter(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    box(mb, M, (0, 0.02, 0.06), (0.38, 0.3, 0.12), "dark")
    box(mb, M, (0, -0.1, 0.1), (0.34, 0.14, 0.06), "dark", r=(0.35, 0, 0))
    for row in range(3):
        for i in range(8):
            cyl(mb, M, (-0.13 + i * 0.037 + row * 0.01, -0.15 + row * 0.04, 0.115 + row * 0.018), 0.012, 0.012, "paper", seg=6)
    cyl(mb, M, (0, 0.12, 0.17), 0.035, 0.44, "dark", seg=10, axis="X")
    box(mb, M, (0, 0.16, 0.27), (0.22, 0.01, 0.2), "paper", r=(-0.2, 0, 0))
    rod(mb, M, (-0.22, 0.12, 0.18), (-0.27, 0.06, 0.2), 0.01, "metal")
    return []


@prop("computer", "surface", (0.5, 0.45, 0.45), eras=ANALOG | NOWS | FUTS | COLD, rooms=OFFICE + ("lab", "reception", "garage", "classroom", "hospital", "arcade"))
def computer(mb, x, y, z, rot, rng, era):
    """Teletype terminal (cold war) / beige CRT + keyboard (80s-90s) / flat monitor + tower / holo pane."""
    M, s = frame(x, y, z, rot), sub(era)
    if s == "cold":
        box(mb, M, (0, 0.05, 0.16), (0.46, 0.4, 0.32), "metal2")
        box(mb, M, (0, -0.155, 0.2), (0.3, 0.02, 0.18), "screen")
        box(mb, M, (0, -0.2, 0.03), (0.46, 0.18, 0.06), "metal2")
        for i in range(3):
            cyl(mb, M, (-0.15 + i * 0.15, 0.255, 0.22), 0.05, 0.02, "dark", seg=10, axis="Y")
        return []
    if s in ("analog", "post"):
        box(mb, M, (0, 0.08, 0.04), (0.42, 0.36, 0.08), "paper")               # desktop case
        box(mb, M, (0.1, -0.105, 0.045), (0.12, 0.012, 0.012), "dark")
        box(mb, M, (0, 0.1, 0.25), (0.36, 0.34, 0.32), "paper")                 # CRT
        box(mb, M, (0, 0.2, 0.24), (0.26, 0.2, 0.24), "paper")
        box(mb, M, (0, -0.075, 0.26), (0.28, 0.02, 0.22), "screen")
        box(mb, M, (0, -0.22, 0.015), (0.44, 0.16, 0.03), "paper", r=(0.08, 0, 0))
        for i in range(3):
            box(mb, M, (0, -0.25 + i * 0.04, 0.035), (0.38, 0.025, 0.012), "metal2")
        return []
    if s in FUTSUB:
        box(mb, M, (0, 0.05, 0.02), (0.18, 0.12, 0.04), "metal")
        box(mb, M, (0, 0.05, 0.3), (0.56, 0.015, 0.34), "accent")
        box(mb, M, (0, 0.04, 0.3), (0.52, 0.012, 0.3), "screen")
        box(mb, M, (0, -0.2, 0.008), (0.4, 0.14, 0.016), "glass")
        return []
    box(mb, M, (0, 0.08, 0.27), (0.56, 0.04, 0.34), "dark")
    box(mb, M, (0, 0.058, 0.27), (0.51, 0.01, 0.29), "screen")
    box(mb, M, (0, 0.1, 0.06), (0.06, 0.06, 0.12), "dark")
    box(mb, M, (0, 0.1, 0.008), (0.22, 0.16, 0.016), "dark")
    box(mb, M, (0, -0.17, 0.01), (0.44, 0.15, 0.02), "metal2")
    box(mb, M, (0.3, -0.17, 0.012), (0.06, 0.1, 0.024), "metal2")
    return []


@prop("water_cooler", "floor", (0.4, 0.4, 1.4), eras=MIDC | ANALOG | NOWS | FUTS, rooms=("office", "waiting", "police", "cubicles", "hospital", "reception"))
def water_cooler(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = "paper" if tier(era) == 2 else "metal"
    box(mb, M, (0, 0, 0.5), (0.34, 0.34, 1.0), k)
    box(mb, M, (0, -0.172, 0.85), (0.22, 0.02, 0.14), "metal2")
    for sx in (-0.05, 0.05):
        box(mb, M, (sx, -0.2, 0.86), (0.03, 0.05, 0.04), "accent" if sx < 0 else "glass")
    box(mb, M, (0, -0.19, 0.72), (0.2, 0.06, 0.02), "metal2")
    cyl(mb, M, (0, 0, 1.22), 0.15, 0.4, "glass", seg=14)
    cyl(mb, M, (0, 0, 1.03), 0.05, 0.06, "glass", seg=10)
    cyl(mb, M, (0.2, 0, 0.6), 0.04, 0.24, "paper", seg=8)                        # cup dispenser
    return []


@prop("cubicle", "floor", (1.8, 1.6, 1.4), eras=ANALOG | NOWS | FUTS, rooms=("cubicles",))
def cubicle(mb, x, y, z, rot, rng, era):
    """L-shaped fabric partition with built-in desk, monitor, phone, pinned memos (opening toward -Y)."""
    M, s = frame(x, y, z, rot), sub(era)
    pk = "fabric" if s != "fut" else "metal2"
    box(mb, M, (0, 0.78, 0.7), (1.8, 0.06, 1.4), pk)
    box(mb, M, (-0.88, 0.0, 0.7), (0.06, 1.6, 1.4), pk)
    box(mb, M, (0, 0.78, 1.41), (1.82, 0.08, 0.03), "metal2")
    box(mb, M, (-0.88, 0.0, 1.41), (0.08, 1.62, 0.03), "metal2")
    box(mb, M, (0.05, 0.47, 0.74), (1.6, 0.56, 0.04), "wood" if s != "fut" else "paper")
    box(mb, M, (-0.56, -0.1, 0.74), (0.56, 0.7, 0.04), "wood" if s != "fut" else "paper")
    box(mb, M, (0.62, 0.47, 0.36), (0.42, 0.54, 0.72), "metal2")
    drawers(mb, M, 0.62, 0.2, 0.05, 0.4, 0.62, 3, key="metal", knob="dark")
    for i in range(rng.randint(3, 6)):
        box(mb, M, (rng.uniform(-0.7, 0.7), 0.745, rng.uniform(0.95, 1.3)), (0.1, 0.01, 0.12), rng.choice(("paper", "paper", "accent")))
    from ..props import PROPS
    _place_local(mb, PROPS["computer"]["fn"], M @ frame(-0.1, 0.48, 0.76, 0.0), rng, era)
    _place_local(mb, PROPS["telephone"]["fn"], M @ frame(0.45, 0.55, 0.76, 0.0), rng, era)
    _place_local(mb, PROPS["office_chair"]["fn"], M @ frame(-0.05, -0.15, 0.0, math.pi + rng.uniform(-0.5, 0.5)), rng, era)
    return [surf(M, (-0.56, -0.15, 0.76), 0.15)]


def _place_local(mb, fn, W, rng, era):
    """Call a prop builder in a parent prop's frame W (props build from frame(x, y, z, rot))."""
    loc = W.to_translation()
    rot = W.to_euler().z
    fn(mb, loc.x, loc.y, loc.z, rot, rng, era)


@prop("whiteboard", "wall", (1.8, 0.08, 1.2), eras=ANALOG | NOWS | FUTS, rooms=("office", "classroom", "lab", "police", "garage", "cubicles"))
def whiteboard(mb, x, y, z, rot, rng, era):
    """Whiteboard with marker diagrams and tray (centre at z ~1.5); a glowing smart board in the future."""
    M, s = frame(x, y, z, rot), sub(era)
    fut = s in FUTSUB
    box(mb, M, (0, -0.02, 0), (1.8, 0.03, 1.1), "metal" if not fut else "dark")
    box(mb, M, (0, -0.036, 0), (1.72, 0.01, 1.02), "paper" if not fut else "screen")
    for i in range(rng.randint(4, 7)):
        k = rng.choice(("dark", "accent", "fabric", "glass"))
        box(mb, M, (rng.uniform(-0.6, 0.5), -0.044, rng.uniform(-0.35, 0.35)), (rng.uniform(0.2, 0.6), 0.006, 0.025), k, r=(0, rng.uniform(-0.3, 0.3), 0))
    cyl(mb, M, (0.45, -0.044, 0.15), 0.16, 0.006, "accent", seg=12, axis="Y")
    cyl(mb, M, (0.45, -0.048, 0.15), 0.13, 0.006, "paper" if not fut else "screen", seg=12, axis="Y")
    box(mb, M, (0, -0.06, -0.57), (1.4, 0.08, 0.03), "metal")
    for i in range(3):
        cyl(mb, M, (-0.3 + i * 0.12, -0.07, -0.55), 0.01, 0.12, ("dark", "accent", "fabric")[i], seg=6, axis="X")
    return []


@prop("corkboard", "wall", (1.2, 0.05, 0.9), eras=VIC | MIDC | ANALOG | NOWS, rooms=("office", "kitchen", "classroom", "police", "lab", "garage", "waiting", "hospital"))
def corkboard(mb, x, y, z, rot, rng, era):
    """Pin board covered in notes, photos and a calendar (centre at z) - the reference's cork board."""
    M = frame(x, y, z, rot)
    box(mb, M, (0, -0.02, 0), (1.2, 0.04, 0.9), "trim")
    box(mb, M, (0, -0.04, 0), (1.1, 0.02, 0.8), "glass2")
    for i in range(rng.randint(5, 9)):
        w, h = rng.uniform(0.12, 0.26), rng.uniform(0.12, 0.3)
        cx, cz = rng.uniform(-0.42, 0.42), rng.uniform(-0.27, 0.27)
        box(mb, M, (cx, -0.052 - i * 0.001, cz), (w, 0.006, h), rng.choice(("paper", "paper", "paper", "accent", "wall")), r=(0, rng.uniform(-0.15, 0.15), 0))
        sph(mb, M, (cx, -0.06, cz + h / 2 - 0.03), 0.012, rng.choice(("accent", "fabric", "leaf")))
    return []


@prop("safe", "floor", (0.6, 0.6, 0.85), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("office", "counting_house", "bank", "study", "saloon", "shop"))
def safe(mb, x, y, z, rot, rng, era):
    """Cast-iron safe on castors: dial, handle, hinges, painted name plate."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "dark" if s in ("vic", "inter") else ("metal2" if s not in FUTSUB else "metal")
    box(mb, M, (0, 0, 0.45), (0.6, 0.58, 0.8), k)
    box(mb, M, (0, -0.3, 0.45), (0.48, 0.03, 0.66), k)
    for sx in (-0.24, 0.24):
        for sy in (-0.24, 0.24):
            cyl(mb, M, (sx, sy, 0.03), 0.035, 0.05, "metal", seg=8, axis="X")
    if s in FUTSUB:
        box(mb, M, (0, -0.32, 0.6), (0.14, 0.02, 0.1), "screen")
    else:
        cyl(mb, M, (0, -0.33, 0.6), 0.08, 0.04, "metal", seg=14, axis="Y")
        cyl(mb, M, (0, -0.355, 0.6), 0.03, 0.03, "dark", seg=8, axis="Y")
    rod(mb, M, (0.12, -0.34, 0.42), (0.12, -0.34, 0.32), 0.015, "metal")
    rod(mb, M, (0.12, -0.34, 0.42), (0.2, -0.34, 0.42), 0.015, "metal")
    for zz in (0.25, 0.68):
        box(mb, M, (-0.25, -0.325, zz), (0.04, 0.03, 0.08), "metal")
    if s in ("vic", "inter"):
        box(mb, M, (0, -0.317, 0.82), (0.3, 0.01, 0.05), "accent")
    return [surf(M, (0, 0, 0.86), 0.2)]


@prop("office_chair", "floor", (0.6, 0.6, 1.0), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("office", "police", "cubicles", "study", "reception", "lab", "bunker"))
def office_chair(mb, x, y, z, rot, rng, era):
    """Wooden swivel banker's chair (to the 50s) / 5-star swivel with padded back; faces -Y."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("vic", "inter", "cold"):
        for a in range(4):
            ang = a * math.tau / 4 + 0.785
            rod(mb, M, (0, 0, 0.12), (math.cos(ang) * 0.26, math.sin(ang) * 0.26, 0.03), 0.02, "metal2")
            sph(mb, M, (math.cos(ang) * 0.26, math.sin(ang) * 0.26, 0.03), 0.03, "dark")
        cyl(mb, M, (0, 0, 0.27), 0.03, 0.3, "metal2", seg=8)
        cyl(mb, M, (0, 0, 0.45), 0.24, 0.05, "wood", seg=14)
        for i in range(5):
            a = math.pi * 0.1 + i * math.pi * 0.2
            rod(mb, M, (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.47), (math.cos(a) * 0.24, math.sin(a) * 0.24, 0.78), 0.015, "wood")
        cyl(mb, M, (0, 0.0, 0.8), 0.25, 0.06, "wood", seg=14, sq=(1.0, 1.0, 1.0))
        box(mb, M, (0, -0.15, 0.8), (0.5, 0.3, 0.07), "wood")               # cut the front of the rail ring
        return []
    for a in range(5):
        ang = a * math.tau / 5
        rod(mb, M, (0, 0, 0.1), (math.cos(ang) * 0.3, math.sin(ang) * 0.3, 0.05), 0.022, "dark")
        sph(mb, M, (math.cos(ang) * 0.3, math.sin(ang) * 0.3, 0.035), 0.035, "dark")
    cyl(mb, M, (0, 0, 0.3), 0.03, 0.4, "metal", seg=8)
    box(mb, M, (0, 0, 0.5), (0.5, 0.48, 0.09), "fabric" if s != "analog" else "fabric2")
    rod(mb, M, (0, 0.18, 0.5), (0, 0.24, 0.66), 0.025, "dark")
    box(mb, M, (0, 0.25, 0.85), (0.46, 0.08, 0.48), "fabric" if s != "analog" else "fabric2", r=(-0.12, 0, 0))
    for sx in (-0.25, 0.25):
        box(mb, M, (sx, 0, 0.66), (0.05, 0.3, 0.04), "dark")
        rod(mb, M, (sx, 0.05, 0.52), (sx, 0.05, 0.66), 0.015, "dark")
    return []


@prop("desk_lamp", "surface", (0.3, 0.25, 0.45), eras=INTER | COLD | ANALOG | NOWS | FUTS, rooms=OFFICE + ("lab", "classroom", "garage", "reception"))
def desk_lamp(mb, x, y, z, rot, rng, era):
    """Green banker's lamp (interwar) / anglepoise (later) / light bar (future)."""
    M, s = frame(x, y, z, rot), sub(era)
    if s == "inter":
        box(mb, M, (0, 0, 0.02), (0.22, 0.12, 0.04), "metal")
        rod(mb, M, (0, 0, 0.04), (0, 0, 0.32), 0.012, "metal")
        cyl(mb, M, (0, -0.03, 0.34), 0.07, 0.3, "leaf", seg=12, axis="X", sq=(1.0, 1.0, 0.6))
        cyl(mb, M, (0, -0.03, 0.31), 0.05, 0.26, "lampshade", seg=10, axis="X", sq=(1.0, 1.0, 0.3))
        return []
    if s in FUTSUB:
        cyl(mb, M, (0, 0, 0.01), 0.07, 0.02, "metal", seg=10)
        rod(mb, M, (0, 0, 0.02), (0, -0.05, 0.38), 0.01, "metal")
        box(mb, M, (0, -0.14, 0.39), (0.06, 0.22, 0.02), "lampshade")
        return []
    cyl(mb, M, (0, 0, 0.015), 0.08, 0.03, "dark", seg=10)
    rod(mb, M, (0, 0, 0.03), (0, 0.08, 0.28), 0.012, "metal")
    rod(mb, M, (0, 0.08, 0.28), (0, -0.1, 0.4), 0.012, "metal")
    cyl(mb, M, (0, -0.13, 0.36), 0.03, 0.12, rng.choice(("accent", "dark", "metal2")), seg=10, r2=0.08, rr=(0.6, 0, 0))
    return []


# ============================================================================ police
POLICE = ("police",)


@prop("evidence_board", "wall", (1.6, 0.06, 1.1), eras=MIDC | ANALOG | NOWS | FUTS, rooms=POLICE + ("detective",))
def evidence_board(mb, x, y, z, rot, rng, era):
    """Cork board of photos, clippings and a map tied together with red string (centre at z ~1.5)."""
    M, s = frame(x, y, z, rot), sub(era)
    fut = s in FUTSUB
    box(mb, M, (0, -0.02, 0), (1.6, 0.04, 1.1), "trim" if not fut else "dark")
    box(mb, M, (0, -0.04, 0), (1.5, 0.02, 1.0), "glass2" if not fut else "screen")
    box(mb, M, (0.45, -0.052, 0.12), (0.5, 0.006, 0.4), "paper")                  # map
    box(mb, M, (0.45, -0.056, 0.1), (0.4, 0.004, 0.06), "glass")
    box(mb, M, (0.36, -0.056, 0.2), (0.05, 0.004, 0.25), "glass")
    pins = []
    for i in range(rng.randint(6, 9)):
        cx, cz = rng.uniform(-0.65, 0.2), rng.uniform(-0.38, 0.38)
        w, h = rng.uniform(0.13, 0.2), rng.uniform(0.15, 0.22)
        photo = rng.random() < 0.55
        box(mb, M, (cx, -0.052 - i * 0.0012, cz), (w, 0.006, h), "paper", r=(0, rng.uniform(-0.12, 0.12), 0))
        if photo:
            box(mb, M, (cx, -0.058 - i * 0.0012, cz + 0.01), (w * 0.8, 0.004, h * 0.65), "dark" if not fut else "glass")
            sph(mb, M, (cx, -0.062, cz + h * 0.05), w * 0.18, "paper", sq=(1, 0.2, 1.2))   # face silhouette
        pin = (cx, -0.068, cz + h / 2 - 0.02)
        sph(mb, M, pin, 0.015, "accent")
        pins.append(pin)
    pins.append((0.45, -0.068, 0.15))
    sph(mb, M, pins[-1], 0.018, "accent")
    order = list(range(len(pins)))
    rng.shuffle(order)
    for a, b in zip(order, order[1:] + order[:2]):
        rod(mb, M, pins[a], pins[b], 0.006, "accent", seg=4)
    return []


@prop("lockers", "wall", (1.2, 0.5, 1.9), eras=MIDC | ANALOG | NOWS | FUTS, rooms=POLICE + ("classroom", "factory", "hospital", "gym", "bunker"))
def lockers(mb, x, y, z, rot, rng, era):
    """Row of three steel lockers with vents, handles and name cards; one door ajar."""
    M, s = frame(x, y, z, rot), sub(era)
    k = rng.choice(("wall2", "metal", "trim")) if s not in FUTSUB else "metal"
    box(mb, M, (0, -0.25, 0.95), (1.2, 0.48, 1.86), k)
    box(mb, M, (0, -0.25, 0.04), (1.2, 0.44, 0.08), "dark")
    ajar = rng.randrange(3)
    for i in range(3):
        cx = -0.4 + i * 0.4
        if i == ajar:
            box(mb, M, (cx - 0.18, -0.68, 1.0), (0.02, 0.38, 1.7), k, r=(0, 0, 0.0))
            box(mb, M, (cx, -0.47, 1.0), (0.36, 0.02, 1.7), "dark")
            box(mb, M, (cx + 0.02, -0.4, 0.95), (0.18, 0.1, 0.7), rng.choice(("fabric", "fabric2")))
            box(mb, M, (cx, -0.4, 1.68), (0.3, 0.2, 0.02), "metal2")
            continue
        box(mb, M, (cx, -0.495, 1.0), (0.36, 0.02, 1.7), k)
        for j in range(4):
            box(mb, M, (cx, -0.51, 1.6 + j * 0.05), (0.2, 0.012, 0.015), "dark")
        box(mb, M, (cx + 0.12, -0.515, 1.0), (0.03, 0.03, 0.14), "metal")
        box(mb, M, (cx, -0.508, 1.4), (0.12, 0.01, 0.06), "paper")
    return [surf(M, (0, -0.25, 1.88), 0.4)]


@prop("holding_bench", "wall", (1.8, 0.5, 1.0), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=POLICE + ("court",))
def holding_bench(mb, x, y, z, rot, rng, era):
    """Bolted wall bench with a cuff rail."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s in ("vic", "inter", "cold") else "metal2"
    box(mb, M, (0, -0.24, 0.46), (1.8, 0.42, 0.06), k)
    for sx in (-0.75, 0, 0.75):
        box(mb, M, (sx, -0.24, 0.22), (0.06, 0.38, 0.44), "metal2")
    cyl(mb, M, (0, -0.06, 0.62), 0.02, 1.7, "metal", seg=8, axis="X")
    for sx in (-0.8, 0.8):
        rod(mb, M, (sx, 0, 0.62), (sx, -0.06, 0.62), 0.02, "metal")
    for sx in (-0.4, 0.3):
        cyl(mb, M, (sx, -0.08, 0.56), 0.035, 0.012, "metal", seg=10, axis="X")
    box(mb, M, (0, -0.02, 0.85), (1.8, 0.04, 0.5), k)
    return []


@prop("wanted_poster", "wall", (0.42, 0.02, 0.58), eras=VIC | MIDC | ANALOG | NOWS, rooms=POLICE + ("saloon", "western", "post_office"))
def wanted_poster(mb, x, y, z, rot, rng, era):
    """WANTED bill: headline bar, mugshot, reward line (centre at z)."""
    M = frame(x, y, z, rot)
    w, h = 0.4, 0.56
    paper = "paper" if tier(era) >= 2 else "wall"
    box(mb, M, (0, -0.01, 0), (w, 0.01, h), paper, r=(0, rng.uniform(-0.05, 0.05), 0))
    box(mb, M, (0, -0.018, 0.21), (w * 0.85, 0.006, 0.07), "dark")
    box(mb, M, (0, -0.018, 0.02), (w * 0.55, 0.006, 0.24), "trim")
    sph(mb, M, (0, -0.024, 0.04), 0.07, paper, sq=(0.85, 0.2, 1.1))
    box(mb, M, (0, -0.024, -0.06), (0.16, 0.006, 0.07), paper)
    box(mb, M, (0, -0.018, -0.18), (w * 0.7, 0.006, 0.04), "dark")
    box(mb, M, (0, -0.018, -0.23), (w * 0.5, 0.006, 0.025), "accent")
    return []


@prop("archive_boxes", "floor", (0.9, 0.5, 0.9), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=POLICE + ("office", "storage", "court", "counting_house"))
def archive_boxes(mb, x, y, z, rot, rng, era):
    """Stacked evidence / archive boxes with handle holes and labels."""
    M = frame(x, y, z, rot)
    for col in range(2):
        zz = 0.0
        for i in range(rng.randint(1, 3)):
            cx = -0.22 + col * 0.44 + rng.uniform(-0.03, 0.03)
            a = rng.uniform(-0.12, 0.12)
            box(mb, M, (cx, 0, zz + 0.15), (0.4, 0.32, 0.28), "wood", r=(0, 0, a))
            box(mb, M, (cx, 0, zz + 0.295), (0.42, 0.34, 0.03), "wood2", r=(0, 0, a))
            box(mb, M, (cx, -0.165, zz + 0.2), (0.14, 0.01, 0.04), "dark", r=(0, 0, a))
            box(mb, M, (cx, -0.165, zz + 0.12), (0.18, 0.01, 0.08), "paper", r=(0, 0, a))
            zz += 0.31
    return []


# ============================================================================ hospital
HOSP = ("hospital", "clinic")


@prop("iv_stand", "floor", (0.5, 0.5, 1.9), eras=MIDC | ANALOG | NOWS | FUTS, rooms=HOSP)
def iv_stand(mb, x, y, z, rot, rng, era):
    M, s = frame(x, y, z, rot), sub(era)
    for a in range(5):
        ang = a * math.tau / 5
        rod(mb, M, (0, 0, 0.06), (math.cos(ang) * 0.24, math.sin(ang) * 0.24, 0.04), 0.016, "metal")
        sph(mb, M, (math.cos(ang) * 0.24, math.sin(ang) * 0.24, 0.03), 0.03, "dark")
    cyl(mb, M, (0, 0, 0.95), 0.016, 1.8, "metal", seg=8)
    rod(mb, M, (-0.14, 0, 1.82), (0.14, 0, 1.82), 0.012, "metal")
    for sx in (-0.12, 0.12):
        rod(mb, M, (sx, 0, 1.82), (sx, 0, 1.76), 0.006, "metal")
    box(mb, M, (0.12, 0, 1.64), (0.12, 0.05, 0.2), "glass")
    box(mb, M, (0.12, -0.026, 1.6), (0.08, 0.006, 0.08), "paper")
    rod(mb, M, (0.12, 0, 1.53), (0.2, -0.1, 0.9), 0.005, "glass")
    if s in FUTSUB or s in ("now",):
        box(mb, M, (0, -0.06, 1.15), (0.16, 0.1, 0.18), "metal2")
        box(mb, M, (0, -0.112, 1.18), (0.1, 0.01, 0.06), "screen")
    return []


@prop("gurney", "floor", (0.75, 2.0, 0.95), eras=MIDC | ANALOG | NOWS | FUTS, rooms=HOSP)
def gurney(mb, x, y, z, rot, rng, era):
    """Wheeled stretcher with sheet, pillow and folded side rails."""
    M, s = frame(x, y, z, rot), sub(era)
    box(mb, M, (0, 0, 0.72), (0.66, 1.9, 0.06), "metal")
    box(mb, M, (0, 0, 0.79), (0.62, 1.86, 0.08), "paper")
    box(mb, M, (0, 0.72, 0.86), (0.48, 0.3, 0.1), "paper", r=(-0.2, 0, 0))
    box(mb, M, (0, -0.25, 0.85), (0.64, 1.1, 0.04), "fabric2" if s not in FUTSUB else "glass")
    for sy in (-0.75, 0.75):
        box(mb, M, (0, sy, 0.4), (0.6, 0.05, 0.05), "metal2")
        for sx in (-0.28, 0.28):
            box(mb, M, (sx, sy, 0.38), (0.04, 0.04, 0.68), "metal2")
            cyl(mb, M, (sx, sy, 0.05), 0.05, 0.03, "dark", seg=10, axis="X")
    for sx in (-0.34, 0.34):
        cyl(mb, M, (sx, 0, 0.9), 0.015, 1.2, "metal", seg=6, axis="Y")
    return []


@prop("privacy_screen", "floor", (1.6, 0.6, 1.8), eras=MIDC | ANALOG | NOWS | FUTS | VIC, rooms=HOSP + ("bedroom", "cabaret", "boutique"))
def privacy_screen(mb, x, y, z, rot, rng, era):
    """Three-panel folding / wheeled curtain screen."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "metal" if s not in ("vic", "inter") else "wood"
    cloth = "glass" if s in ("cold", "analog", "now") else ("fabric" if s in ("vic", "inter") else "paper")
    for i, (cx, ang) in enumerate(((-0.52, 0.45), (0, 0.0), (0.52, -0.45))):
        Mp = M @ frame(cx, 0.1 * abs(i - 1), 0, ang)
        for sx in (-0.25, 0.25):
            box(mb, Mp, (sx, 0, 0.9), (0.04, 0.04, 1.8), k)
        box(mb, Mp, (0, 0, 1.78), (0.54, 0.04, 0.04), k)
        box(mb, Mp, (0, 0, 0.98), (0.46, 0.015, 1.5), cloth)
        cyl(mb, Mp, (0, 0, 0.04), 0.035, 0.03, "dark", seg=8, axis="Y")
    return []


@prop("vitals_monitor", "floor", (0.5, 0.5, 1.5), eras=COLD | ANALOG | NOWS | FUTS, rooms=HOSP)
def vitals_monitor(mb, x, y, z, rot, rng, era):
    """Monitor on a rolling pole: glowing trace screen, cables."""
    M, s = frame(x, y, z, rot), sub(era)
    for a in range(4):
        ang = a * math.tau / 4 + 0.785
        rod(mb, M, (0, 0, 0.06), (math.cos(ang) * 0.22, math.sin(ang) * 0.22, 0.04), 0.016, "metal")
        sph(mb, M, (math.cos(ang) * 0.22, math.sin(ang) * 0.22, 0.03), 0.03, "dark")
    cyl(mb, M, (0, 0, 0.6), 0.02, 1.1, "metal", seg=8)
    crt = s in ("cold", "analog")
    box(mb, M, (0, 0.05 if crt else 0, 1.28), (0.4, 0.34 if crt else 0.08, 0.32), "metal2" if crt else "dark")
    box(mb, M, (-0.04, -0.13 if crt else -0.045, 1.29), (0.28, 0.01, 0.22), "screen")
    for i in range(5):                                         # heartbeat trace
        zz = 1.29 + (0.06 if i == 2 else 0.0) - (0.04 if i == 3 else 0.0)
        box(mb, M, (-0.15 + i * 0.055, -0.14 if crt else -0.055, zz), (0.05, 0.006, 0.012), "dark", r=(0, 0.8 if i in (2, 3) else 0, 0))
    for zz in (1.36, 1.29, 1.22):
        cyl(mb, M, (0.15, -0.13 if crt else -0.045, zz), 0.02, 0.02, "accent", seg=8, axis="Y")
    rod(mb, M, (0.15, 0, 1.1), (0.4, -0.2, 0.8), 0.006, "dark")
    return []


@prop("wheelchair", "floor", (0.65, 0.8, 0.95), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=HOSP + ("waiting",))
def wheelchair(mb, x, y, z, rot, rng, era):
    """Big rear wheels, castors, sling seat and back, push handles; faces -Y."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "metal" if s != "vic" else "wood"
    for sx in (-0.3, 0.3):
        cyl(mb, M, (sx, 0.15, 0.3), 0.3, 0.03, "dark", seg=18, axis="X")
        cyl(mb, M, (sx * 0.93, 0.15, 0.3), 0.25, 0.015, "metal2", seg=18, axis="X")
        cyl(mb, M, (sx * 0.93, 0.15, 0.3), 0.05, 0.05, k, seg=8, axis="X")
        cyl(mb, M, (sx * 0.8, -0.3, 0.07), 0.07, 0.03, "dark", seg=10, axis="X")
        rod(mb, M, (sx * 0.8, -0.3, 0.1), (sx * 0.8, -0.25, 0.48), 0.015, k)
        rod(mb, M, (sx * 0.8, 0.2, 0.48), (sx * 0.8, 0.25, 0.95), 0.015, k)
        rod(mb, M, (sx * 0.8, 0.25, 0.95), (sx * 0.8, 0.38, 0.95), 0.02, "dark")
        rod(mb, M, (sx * 0.8, -0.25, 0.48), (sx * 0.8, 0.2, 0.48), 0.015, k)
        rod(mb, M, (sx * 0.8, -0.25, 0.68), (sx * 0.8, 0.15, 0.68), 0.02, "dark")
        rod(mb, M, (sx * 0.8, -0.25, 0.48), (sx * 0.8, -0.32, 0.12), 0.012, k)
    box(mb, M, (0, -0.03, 0.5), (0.48, 0.44, 0.04), "fabric" if s != "vic" else "fabric2")
    box(mb, M, (0, 0.23, 0.72), (0.48, 0.03, 0.4), "fabric" if s != "vic" else "fabric2", r=(-0.12, 0, 0))
    box(mb, M, (0, -0.36, 0.1), (0.4, 0.12, 0.02), k)
    return []


@prop("medicine_cabinet", "wall", (0.8, 0.3, 0.9), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=HOSP + ("bathroom", "lab", "pharmacy"))
def medicine_cabinet(mb, x, y, z, rot, rng, era):
    """Glass-fronted cabinet of bottles and boxes with a red cross (centre at z ~1.45)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s == "vic" else ("paper" if s in ("inter", "cold") else "metal")
    box(mb, M, (0, -0.15, 0), (0.8, 0.3, 0.9), k)
    for zz in (-0.15, 0.15):
        box(mb, M, (0, -0.15, zz), (0.74, 0.26, 0.02), k)
    for zz in (-0.42, -0.14, 0.16):
        px = -0.32
        while px < 0.32:
            h = rng.uniform(0.08, 0.18)
            if rng.random() < 0.7:
                cyl(mb, M, (px, -0.16, zz + h / 2 + 0.01), 0.03, h, rng.choice(("glass", "glass2", "paper")), seg=8)
            else:
                box(mb, M, (px, -0.16, zz + h / 2 + 0.01), (0.07, 0.06, h), rng.choice(("paper", "accent")))
            px += rng.uniform(0.07, 0.11)
    for sx in (-0.2, 0.2):
        box(mb, M, (sx, -0.31, 0), (0.38, 0.02, 0.86), "trim")
        box(mb, M, (sx, -0.315, 0), (0.32, 0.015, 0.78), "glass")
    box(mb, M, (0, -0.325, 0.36), (0.12, 0.01, 0.04), "fabric")
    box(mb, M, (0, -0.325, 0.36), (0.04, 0.01, 0.12), "fabric")
    return []


@prop("hospital_bed", "wall", (1.0, 2.1, 1.1), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=HOSP)
def hospital_bed(mb, x, y, z, rot, rng, era):
    """Head at the wall: steel bed with side rails, raised back section, crank and chart clipboard."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "paper" if s in ("vic", "inter", "cold") else "metal"
    box(mb, M, (0, -1.05, 0.5), (0.92, 2.0, 0.08), k)
    box(mb, M, (0, -1.3, 0.6), (0.88, 1.5, 0.14), "paper")
    box(mb, M, (0, -0.4, 0.72), (0.88, 0.6, 0.12), "paper", r=(0.45, 0, 0))
    box(mb, M, (0, -0.25, 0.92), (0.5, 0.2, 0.12), "paper", r=(0.45, 0, 0))
    box(mb, M, (0, -1.4, 0.69), (0.92, 1.3, 0.05), "fabric2" if s not in FUTSUB else "glass")
    for sy in (-0.05, -2.05):
        box(mb, M, (0, sy, 0.68), (0.96, 0.05, 0.6 if sy > -1 else 0.42), k)
        for sx in (-0.46, 0.46):
            cyl(mb, M, (sx, sy, 0.5), 0.025, 1.0 if sy > -1 else 0.8, "metal", seg=8)
            cyl(mb, M, (sx, sy, 0.05), 0.05, 0.03, "dark", seg=10, axis="X")
    for sx in (-0.49, 0.49):
        cyl(mb, M, (sx, -1.0, 0.82), 0.015, 0.9, "metal", seg=6, axis="Y")
        for sy in (-0.6, -1.0, -1.4):
            rod(mb, M, (sx, sy, 0.56), (sx, sy, 0.82), 0.012, "metal")
    rod(mb, M, (0.25, -2.08, 0.25), (0.25, -2.18, 0.25), 0.012, "metal")
    box(mb, M, (0, -2.1, 0.75), (0.24, 0.015, 0.32), "wood")
    box(mb, M, (0, -2.11, 0.73), (0.2, 0.01, 0.26), "paper")
    return []


# ============================================================================ classroom
SCHOOL = ("school",)


@prop("school_desk", "floor", (0.7, 0.9, 0.9), eras=ALL - ANTIQ - MEDV, rooms=SCHOOL)
def school_desk(mb, x, y, z, rot, rng, era):
    """Pupil's desk + seat (faces -Y = toward the blackboard): bench desk with slanted lid and
    inkwell (to 1900) / iron-frame combo desk (to the 50s) / plastic chair + laminate table."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("ren", "enl", "vic"):
        box(mb, M, (0, -0.15, 0.68), (0.7, 0.42, 0.04), "wood", r=(-0.18, 0, 0))
        box(mb, M, (0, -0.15, 0.45), (0.66, 0.38, 0.36), "wood")
        cyl(mb, M, (0.25, -0.3, 0.73), 0.025, 0.04, "dark", seg=8)
        box(mb, M, (0, 0.28, 0.4), (0.7, 0.3, 0.04), "wood2")
        for sx in (-0.3, 0.3):
            box(mb, M, (sx, 0.28, 0.2), (0.05, 0.28, 0.4), "wood2")
        box(mb, M, (0, 0.42, 0.62), (0.7, 0.04, 0.4), "wood2")
        return [surf(M, (0, -0.15, 0.72), 0.15)]
    if s in ("inter", "cold"):
        box(mb, M, (0, -0.15, 0.72), (0.62, 0.42, 0.035), "wood", r=(-0.1, 0, 0))
        box(mb, M, (0, -0.15, 0.62), (0.58, 0.38, 0.12), "wood2")
        for sx in (-0.28, 0.28):
            rod(mb, M, (sx, -0.3, 0.0), (sx, -0.1, 0.56), 0.02, "dark")
            rod(mb, M, (sx, 0.0, 0.0), (sx, -0.15, 0.56), 0.02, "dark")
            rod(mb, M, (sx, -0.3, 0.02), (sx, 0.5, 0.02), 0.02, "dark")
            rod(mb, M, (sx, 0.45, 0.0), (sx, 0.45, 0.42), 0.02, "dark")
        box(mb, M, (0, 0.32, 0.43), (0.5, 0.36, 0.04), "wood")
        box(mb, M, (0, 0.52, 0.68), (0.5, 0.04, 0.26), "wood")
        rod(mb, M, (0.25, 0.52, 0.42), (0.25, 0.52, 0.8), 0.018, "dark")
        rod(mb, M, (-0.25, 0.52, 0.42), (-0.25, 0.52, 0.8), 0.018, "dark")
        return [surf(M, (0, -0.15, 0.75), 0.15)]
    fut = s in FUTSUB
    box(mb, M, (0, -0.18, 0.72), (0.7, 0.5, 0.03), "paper" if not fut else "glass")
    for sx in (-0.32, 0.32):
        for sy in (-0.4, 0.04):
            box(mb, M, (sx, sy, 0.36), (0.03, 0.03, 0.72), "metal")
    box(mb, M, (0, -0.18, 0.55), (0.62, 0.42, 0.02), "metal2")
    ck = rng.choice(("accent", "fabric", "leaf")) if not fut else "metal"
    box(mb, M, (0, 0.3, 0.45), (0.42, 0.4, 0.04), ck)
    box(mb, M, (0, 0.5, 0.7), (0.42, 0.03, 0.32), ck, r=(-0.1, 0, 0))
    for sx in (-0.19, 0.19):
        for sy in (0.12, 0.48):
            box(mb, M, (sx, sy, 0.22), (0.025, 0.025, 0.44), "metal")
    return [surf(M, (0, -0.2, 0.74), 0.18)]


@prop("globe", "surface", (0.35, 0.35, 0.5), eras=ALL - ANTIQ - MEDV, rooms=("classroom", "study", "library", "office", "school", "counting_house"))
def globe(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.02), 0.09, 0.04, "wood2", seg=10)
    cyl(mb, M, (0, 0, 0.1), 0.02, 0.12, "wood2", seg=8)
    sph(mb, M, (0, 0, 0.32), 0.16, "glass", sub=2)
    for i in range(4):
        a = i * 1.6 + rng.uniform(0, 0.5)
        sph(mb, M, (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.32 + rng.uniform(-0.08, 0.08)), 0.07, "leaf", sq=(1.0, 1.0, 0.8))
    rr = (0, math.radians(23), 0)
    cyl(mb, M, (0, 0, 0.32), 0.185, 0.02, "metal", seg=16, axis="X", rr=rr)
    return []


@prop("wall_map", "wall", (1.4, 0.05, 1.0), eras=ALL - ANTIQ, rooms=("classroom", "school", "study", "office", "police", "bunker", "counting_house", "nautical"))
def wall_map(mb, x, y, z, rot, rng, era):
    """Pull-down map on a roller with continents (centre at z)."""
    M, t = frame(x, y, z, rot), tier(era)
    cyl(mb, M, (0, -0.04, 0.5), 0.035, 1.46, "wood2", seg=8, axis="X")
    box(mb, M, (0, -0.03, 0.0), (1.38, 0.01, 0.98), "paper" if t >= 2 else "wall")
    box(mb, M, (0, -0.036, 0.0), (1.3, 0.006, 0.9), "glass")
    for i in range(rng.randint(4, 6)):
        cx, cz = rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3)
        sph(mb, M, (cx, -0.04, cz), rng.uniform(0.08, 0.18), rng.choice(("leaf", "wall", "accent")), sq=(1.3, 0.04, 1.0))
    cyl(mb, M, (0, -0.04, -0.5), 0.02, 1.4, "wood2", seg=6, axis="X")
    return []


@prop("teacher_desk", "floor", (1.5, 0.75, 0.78), eras=ALL - ANTIQ - MEDV, rooms=SCHOOL)
def teacher_desk(mb, x, y, z, rot, rng, era):
    """Heavy pedestal desk with modesty panel toward +Y (pupils), books, apple, bell (faces -Y)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s not in FUTSUB else "metal"
    box(mb, M, (0, 0, 0.75), (1.5, 0.75, 0.05), k)
    for sx in (-0.55, 0.55):
        box(mb, M, (sx, 0, 0.37), (0.38, 0.7, 0.72), k)
        drawers(mb, M, sx, -0.35, 0.02, 0.36, 0.7, 3, key="wood2" if k == "wood" else "metal2")
    box(mb, M, (0, 0.34, 0.45), (0.74, 0.04, 0.56), "wood2" if k == "wood" else "metal2")
    sph(mb, M, (0.45, 0.1, 0.83), 0.045, "fabric")
    rod(mb, M, (0.45, 0.1, 0.87), (0.46, 0.1, 0.9), 0.006, "leaf")
    if s in ("vic", "inter", "cold", "ren", "enl"):
        cyl(mb, M, (-0.5, 0.15, 0.8), 0.05, 0.05, "metal", seg=10, r2=0.025)
        cyl(mb, M, (-0.5, 0.15, 0.86), 0.01, 0.08, "wood2", seg=6)
    return [surf(M, (-0.1, 0, 0.78), 0.4)]


# ============================================================================ lab
LAB = ("lab", "science")


@prop("lab_bench", "floor", (2.0, 0.9, 1.3), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("labx",))
def lab_bench(mb, x, y, z, rot, rng, era):
    """Island bench: dark resin top, cupboards, gas taps, reagent shelf down the middle."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s in ("vic", "inter", "cold") else ("paper" if s not in FUTSUB else "metal")
    box(mb, M, (0, 0, 0.44), (1.96, 0.86, 0.82), k)
    doors(mb, M, 0, -0.435, 0.08, 1.9, 0.68, 4, key="wood2" if k == "wood" else "metal2")
    box(mb, M, (0, 0, 0.88), (2.04, 0.92, 0.05), "dark")
    box(mb, M, (0, 0, 1.15), (1.9, 0.14, 0.03), k)
    for sx in (-0.9, 0.9):
        box(mb, M, (sx, 0, 1.02), (0.04, 0.14, 0.3), k)
    box(mb, M, (-0.6, 0, 0.91), (0.34, 0.3, 0.02), "metal")                      # sink
    rod(mb, M, (-0.6, 0.05, 0.9), (-0.6, 0.05, 1.12), 0.015, "metal")
    rod(mb, M, (-0.6, 0.05, 1.12), (-0.6, -0.08, 1.06), 0.013, "metal")
    for sx in (0.2, 0.55):
        rod(mb, M, (sx, -0.02, 0.9), (sx, -0.02, 0.98), 0.012, "metal")
        box(mb, M, (sx, -0.04, 0.98), (0.02, 0.06, 0.012), "accent")
    px = -0.8
    while px < 0.8:
        h = rng.uniform(0.08, 0.15)
        cyl(mb, M, (px, 0, 1.165 + h / 2), 0.03, h, rng.choice(("glass", "glass2", "paper")), seg=8)
        px += rng.uniform(0.08, 0.16)
    return [surf(M, (0.3, -0.25, 0.905), 0.5), surf(M, (0.3, 0.25, 0.905), 0.5)]


@prop("flask_rack", "surface", (0.45, 0.2, 0.35), eras=ALL - ANTIQ, rooms=LAB + ("wizard", "alchemist", "hospital"))
def flask_rack(mb, x, y, z, rot, rng, era):
    """Conical + round-bottom flasks, beakers and a test-tube rack with coloured liquids."""
    M = frame(x, y, z, rot)
    cyl(mb, M, (-0.16, 0, 0.09), 0.07, 0.16, "glass", seg=10, r2=0.02)
    cyl(mb, M, (-0.16, 0, 0.2), 0.018, 0.08, "glass", seg=8)
    cyl(mb, M, (-0.16, 0, 0.04), 0.055, 0.06, rng.choice(("accent", "leaf", "glass2")), seg=10, r2=0.045)
    sph(mb, M, (0.0, 0.03, 0.08), 0.07, "glass")
    cyl(mb, M, (0.0, 0.03, 0.18), 0.016, 0.1, "glass", seg=8)
    cyl(mb, M, (0.12, -0.04, 0.06), 0.04, 0.12, "glass", seg=10)
    cyl(mb, M, (0.12, -0.04, 0.035), 0.038, 0.06, rng.choice(("accent", "glass2")), seg=10)
    box(mb, M, (0.12, 0.07, 0.06), (0.2, 0.06, 0.02), "wood")
    for i in range(4):
        cyl(mb, M, (0.05 + i * 0.045, 0.07, 0.1), 0.012, 0.12, rng.choice(("glass", "accent", "leaf", "glass2")), seg=6)
    box(mb, M, (0.12, 0.07, 0.13), (0.2, 0.06, 0.015), "wood")
    return []


@prop("microscope", "surface", (0.2, 0.25, 0.38), eras=ALL - ANTIQ - MEDV, rooms=LAB + ("hospital", "classroom", "study"))
def microscope(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = "metal" if t <= 1 else ("dark" if t <= 3 else "paper")
    box(mb, M, (0, 0.02, 0.02), (0.16, 0.2, 0.04), k)
    rod(mb, M, (0, 0.08, 0.04), (0, 0.06, 0.24), 0.025, k)
    box(mb, M, (0, -0.02, 0.12), (0.12, 0.12, 0.015), k)
    cyl(mb, M, (0, -0.02, 0.26), 0.028, 0.2, k, seg=10, rr=(0.35, 0, 0))
    cyl(mb, M, (0, -0.06, 0.37), 0.018, 0.06, "dark", seg=8, rr=(0.35, 0, 0))
    cyl(mb, M, (0, -0.0, 0.16), 0.02, 0.05, "metal2", seg=8)
    cyl(mb, M, (0.06, 0.05, 0.18), 0.03, 0.02, "metal2", seg=10, axis="X")
    return []


@prop("fume_hood", "wall", (1.5, 0.8, 2.3), eras=COLD | ANALOG | NOWS | FUTS, rooms=LAB)
def fume_hood(mb, x, y, z, rot, rng, era):
    """Fume cupboard: base cabinets, glass sash half raised, lit interior, duct to the ceiling."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "paper" if s != "fut" else "metal"
    box(mb, M, (0, -0.4, 0.42), (1.5, 0.78, 0.84), k)
    doors(mb, M, 0, -0.79, 0.06, 1.44, 0.7, 3, key="metal2")
    box(mb, M, (0, -0.4, 0.86), (1.52, 0.8, 0.04), "dark")
    for sx in (-0.72, 0.72):
        box(mb, M, (sx, -0.4, 1.45), (0.06, 0.78, 1.18), k)
    box(mb, M, (0, -0.06, 1.45), (1.4, 0.06, 1.18), "dark")
    box(mb, M, (0, -0.4, 2.1), (1.5, 0.78, 0.24), k)
    box(mb, M, (0, -0.76, 1.55), (1.38, 0.025, 0.7), "glass")
    box(mb, M, (0, -0.78, 1.2), (1.38, 0.04, 0.04), "metal")
    box(mb, M, (0, -0.4, 1.95), (1.2, 0.5, 0.03), "lampshade")
    box(mb, M, (0, -0.3, 2.45), (0.4, 0.4, 0.3), "metal2")
    for i in range(3):
        cyl(mb, M, (-0.4 + i * 0.3, -0.35, 0.95), 0.04, 0.12, rng.choice(("glass", "glass2")), seg=8, r2=0.015)
    return []


@prop("specimen_jars", "surface", (0.45, 0.16, 0.3), eras=ALL - ANTIQ, rooms=LAB + ("wizard", "museum", "study", "alchemist"))
def specimen_jars(mb, x, y, z, rot, rng, era):
    """Jars of murky fluid with pale curled specimens inside (just visible through the 'glass')."""
    M = frame(x, y, z, rot)
    for i in range(3):
        h = rng.uniform(0.18, 0.28)
        px = -0.15 + i * 0.15
        cyl(mb, M, (px, 0, h / 2), 0.06, h, rng.choice(("glass", "glass", "glass2")), seg=10)
        cyl(mb, M, (px, 0, h + 0.015), 0.064, 0.03, "metal2", seg=10)
        sph(mb, M, (px, -0.045, h * 0.45), 0.035, "paper", sq=(1.0, 0.4, 1.4))
        box(mb, M, (px, -0.062, h * 0.2), (0.07, 0.005, 0.04), "paper")
    return []


@prop("chem_shelf", "wall", (1.0, 0.32, 1.9), eras=ALL - ANTIQ, rooms=LAB + ("pharmacy", "alchemist", "wizard"))
def chem_shelf(mb, x, y, z, rot, rng, era):
    """Open shelf of labelled reagent bottles, jars and a skull / model on top."""
    M, t = frame(x, y, z, rot), tier(era)
    k = "wood" if t <= 2 else "metal"
    for sx in (-0.48, 0.48):
        box(mb, M, (sx, -0.16, 0.95), (0.04, 0.3, 1.9), k)
    box(mb, M, (0, -0.02, 0.95), (1.0, 0.03, 1.9), "wood2" if k == "wood" else "metal2")
    for zz in (0.05, 0.5, 0.95, 1.4, 1.86):
        box(mb, M, (0, -0.16, zz), (1.0, 0.3, 0.03), k)
        if zz > 1.8:
            continue
        px = -0.4
        while px < 0.4:
            h = rng.uniform(0.12, 0.3)
            kk = rng.choice(("glass", "glass2", "paper", "accent", "glass"))
            if rng.random() < 0.7:
                cyl(mb, M, (px, -0.17, zz + 0.015 + h / 2), 0.04, h, kk, seg=8)
                cyl(mb, M, (px, -0.17, zz + 0.02 + h), 0.015, 0.04, "dark", seg=6)
            else:
                box(mb, M, (px, -0.17, zz + 0.015 + h / 2), (0.08, 0.1, h), kk)
            box(mb, M, (px, -0.215, zz + 0.015 + h * 0.4), (0.05, 0.006, 0.04), "paper")
            px += rng.uniform(0.09, 0.14)
    sph(mb, M, (0.25, -0.16, 1.96), 0.07, "paper", sq=(0.9, 1.1, 1.0))
    return []


# ============================================================================ factory
FACTORY = ("factory", "workshop", "garage")


@prop("conveyor", "floor", (3.0, 0.9, 1.0), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("factory_line",))
def conveyor(mb, x, y, z, rot, rng, era):
    """3 m belt conveyor on legs: rollers at the ends, side guards, boxes / parts riding on it."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "metal2"
    box(mb, M, (0, 0, 0.82), (3.0, 0.62, 0.05), "dark")
    for sy in (-0.34, 0.34):
        box(mb, M, (0, sy, 0.86), (3.0, 0.05, 0.14), k)
    for sx in (-1.5, 1.5):
        cyl(mb, M, (sx, 0, 0.82), 0.08, 0.64, "metal", seg=12, axis="Y")
    for sx in (-1.3, -0.4, 0.5, 1.3):
        for sy in (-0.3, 0.3):
            box(mb, M, (sx, sy, 0.4), (0.06, 0.06, 0.8), k)
        box(mb, M, (sx, 0, 0.2), (0.06, 0.62, 0.05), k)
    for i in range(rng.randint(3, 5)):
        px = -1.2 + i * 0.6 + rng.uniform(-0.1, 0.1)
        if s in ("vic",) or rng.random() < 0.3:
            cyl(mb, M, (px, 0, 0.95), 0.12, 0.2, rng.choice(("metal", "glass2")), seg=10)
        else:
            sz = rng.uniform(0.25, 0.4)
            box(mb, M, (px, 0, 0.845 + sz / 2), (sz, sz * 0.9, sz * 0.8), "wood", r=(0, 0, rng.uniform(-0.2, 0.2)))
    box(mb, M, (1.3, -0.45, 1.0), (0.2, 0.08, 0.3), "metal")
    box(mb, M, (1.3, -0.495, 1.08), (0.06, 0.02, 0.06), "accent")
    return []


@prop("lathe", "floor", (1.8, 0.7, 1.35), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=FACTORY)
def lathe(mb, x, y, z, rot, rng, era):
    """Metal lathe: cabinet legs, bed, headstock with chuck, tailstock, tool post, chip tray (faces -Y)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "leaf" if s in ("cold", "analog") else ("metal2" if s != "vic" else "dark")
    for sx in (-0.65, 0.65):
        box(mb, M, (sx, 0, 0.4), (0.4, 0.55, 0.8), k)
    box(mb, M, (0, 0, 0.84), (1.8, 0.4, 0.1), "metal2")
    box(mb, M, (0, -0.08, 0.83), (1.5, 0.5, 0.04), "dark")
    box(mb, M, (-0.7, 0, 1.1), (0.4, 0.42, 0.42), k)
    cyl(mb, M, (-0.45, 0, 1.12), 0.12, 0.1, "metal", seg=12, axis="X")
    cyl(mb, M, (-0.1, 0, 1.12), 0.035, 0.6, "metal", seg=8, axis="X")
    box(mb, M, (0.6, 0, 1.05), (0.2, 0.3, 0.3), k)
    cyl(mb, M, (0.42, 0, 1.12), 0.04, 0.2, "metal", seg=8, axis="X", r2=0.01)
    box(mb, M, (0.05, -0.05, 0.97), (0.22, 0.3, 0.12), "metal")
    box(mb, M, (0.05, -0.12, 1.06), (0.08, 0.1, 0.06), "dark")
    for zz in (1.2, 1.04):
        cyl(mb, M, (-0.7, -0.22, zz), 0.03, 0.03, "dark", seg=8, axis="Y")
    if s == "vic":                                           # line-shaft belt
        rod(mb, M, (-0.75, 0, 1.3), (-0.75, 0, 2.6), 0.03, "dark")
    else:
        cyl(mb, M, (-0.85, -0.25, 1.32), 0.05, 0.03, "accent", seg=8)
    return []


@prop("oil_drum", "floor", (0.6, 0.6, 0.9), eras=MIDC | ANALOG | NOWS | FUTS, rooms=FACTORY + ("storage", "dock", "bunker", "ruin"))
def oil_drum(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot)
    k = rng.choice(("accent", "leaf", "metal2", "fabric", "wall2"))
    cyl(mb, M, (0, 0, 0.44), 0.29, 0.86, k, seg=14)
    for zz in (0.3, 0.6):
        cyl(mb, M, (0, 0, zz), 0.3, 0.03, k, seg=14)
    cyl(mb, M, (0, 0, 0.875), 0.295, 0.02, "metal2", seg=14)
    cyl(mb, M, (0.15, 0.05, 0.89), 0.035, 0.02, "dark", seg=8)
    box(mb, M, (0, -0.29, 0.45), (0.22, 0.02, 0.18), "paper")
    if rng.random() < 0.5:
        sph(mb, M, (0, 0, 0.885), 0.2, "dark", sq=(1.0, 0.8, 0.03))
    return []


@prop("pallet", "floor", (1.2, 1.0, 0.9), eras=MIDC | ANALOG | NOWS | FUTS, rooms=FACTORY + ("storage", "dock", "shop", "warehouse"))
def pallet(mb, x, y, z, rot, rng, era):
    """Wooden pallet, often loaded with shrink-wrapped boxes or sacks."""
    M, t = frame(x, y, z, rot), tier(era)
    for sy in (-0.42, 0, 0.42):
        box(mb, M, (0, sy, 0.05), (1.2, 0.12, 0.08), "wood2")
    for i in range(6):
        box(mb, M, (-0.52 + i * 0.208, 0, 0.115), (0.14, 1.0, 0.025), "wood")
    if rng.random() < 0.75:
        h = rng.uniform(0.4, 0.75)
        box(mb, M, (0, 0, 0.13 + h / 2), (1.05, 0.88, h), "wood" if t < 3 else "glass")
        for k in range(2):
            box(mb, M, (0, -0.445, 0.13 + h * (0.3 + 0.4 * k)), (1.06, 0.01, 0.03), "trim")
        box(mb, M, (0.25, -0.448, 0.13 + h * 0.6), (0.2, 0.01, 0.14), "paper")
    return []


@prop("workbench", "wall", (1.8, 0.75, 1.0), eras=ALL - ANTIQ, rooms=FACTORY + ("shed", "lab", "basement"))
def workbench(mb, x, y, z, rot, rng, era):
    """Heavy bench: thick top, vice, drawer, shelf of cans, tools scattered on top."""
    M, t = frame(x, y, z, rot), tier(era)
    box(mb, M, (0, -0.37, 0.88), (1.8, 0.72, 0.08), "wood")
    legs4(mb, M, 1.74, 0.66, 0.84, 0.08, "wood2" if t <= 2 else "metal2")
    box(mb, M, (0, -0.37, 0.18), (1.7, 0.62, 0.03), "wood2")
    drawers(mb, M, 0.5, -0.73, 0.68, 0.5, 0.14, 1, key="wood2")
    box(mb, M, (-0.7, -0.68, 0.98), (0.18, 0.16, 0.12), "dark" if t > 1 else "metal2")
    box(mb, M, (-0.7, -0.78, 0.98), (0.18, 0.04, 0.12), "dark" if t > 1 else "metal2")
    rod(mb, M, (-0.79, -0.8, 0.98), (-0.61, -0.8, 0.98), 0.012, "metal")
    for i in range(rng.randint(2, 4)):
        box(mb, M, (rng.uniform(-0.3, 0.7), rng.uniform(-0.6, -0.2), 0.935), (rng.uniform(0.15, 0.3), 0.04, 0.025), rng.choice(("metal", "dark", "accent")), r=(0, 0, rng.uniform(0, 3)))
    for i in range(3):
        cyl(mb, M, (-0.5 + i * 0.3, -0.3, 0.27), 0.08, 0.16, rng.choice(("accent", "metal2", "leaf")), seg=10)
    return [surf(M, (0.3, -0.37, 0.92), 0.5)]


@prop("tool_wall", "wall", (1.6, 0.08, 1.0), eras=ALL - ANTIQ, rooms=FACTORY + ("shed", "basement"))
def tool_wall(mb, x, y, z, rot, rng, era):
    """Pegboard with hanging hammers, wrenches, saws and their painted outlines (centre at z ~1.5)."""
    M, t = frame(x, y, z, rot), tier(era)
    box(mb, M, (0, -0.015, 0), (1.6, 0.03, 1.0), "wood" if t < 2 else "wall2")
    items = rng.randint(7, 10)
    for i in range(items):
        cx = -0.68 + i * 1.36 / max(1, items - 1)
        cz = rng.uniform(-0.2, 0.25)
        kind = rng.randint(0, 3)
        sph(mb, M, (cx, -0.035, cz + 0.28), 0.012, "metal")
        if kind == 0:                                              # hammer
            box(mb, M, (cx, -0.045, cz), (0.03, 0.025, 0.34), "wood2")
            box(mb, M, (cx, -0.05, cz + 0.17), (0.13, 0.04, 0.05), "dark")
        elif kind == 1:                                            # wrench
            box(mb, M, (cx, -0.045, cz), (0.035, 0.015, 0.3), "metal")
            cyl(mb, M, (cx, -0.045, cz + 0.16), 0.04, 0.015, "metal", seg=8, axis="Y")
        elif kind == 2:                                            # saw
            box(mb, M, (cx, -0.04, cz - 0.05), (0.14, 0.008, 0.4), "metal", r=(0, 0.1, 0))
            box(mb, M, (cx, -0.045, cz + 0.2), (0.1, 0.03, 0.1), "wood2")
        else:                                                      # screwdriver / pliers
            cyl(mb, M, (cx, -0.045, cz + 0.08), 0.02, 0.12, rng.choice(("accent", "fabric", "leaf")), seg=6)
            cyl(mb, M, (cx, -0.045, cz - 0.04), 0.006, 0.14, "metal", seg=6)
    box(mb, M, (0, -0.06, -0.48), (1.6, 0.1, 0.03), "wood2")
    return []


@prop("drill_press", "floor", (0.6, 0.6, 1.7), eras=MIDC | ANALOG | NOWS | FUTS, rooms=FACTORY)
def drill_press(mb, x, y, z, rot, rng, era):
    M, s = frame(x, y, z, rot), sub(era)
    k = "leaf" if s in ("cold", "analog") else "metal2"
    box(mb, M, (0, 0.05, 0.04), (0.5, 0.55, 0.08), k)
    cyl(mb, M, (0, 0.18, 0.8), 0.05, 1.5, "metal", seg=10)
    box(mb, M, (0, 0.0, 0.7), (0.34, 0.34, 0.04), k)
    box(mb, M, (0, 0.08, 1.4), (0.26, 0.5, 0.26), k)
    cyl(mb, M, (0, 0.2, 1.62), 0.1, 0.2, k, seg=10)
    cyl(mb, M, (0, -0.08, 1.18), 0.03, 0.22, "metal", seg=8)
    cyl(mb, M, (0, -0.08, 1.02), 0.008, 0.12, "dark", seg=6)
    for a in range(3):
        ang = a * math.tau / 3
        rod(mb, M, (0.13, 0.08, 1.35), (0.13 + 0.15, 0.08 + math.cos(ang) * 0.15, 1.35 + math.sin(ang) * 0.15), 0.01, "dark")
    return []


# ============================================================================ shop
SHOP = ("shop", "store")


@prop("gondola_shelf", "floor", (1.8, 0.9, 1.6), eras=INTER | COLD | ANALOG | NOWS | FUTS, rooms=("shop_aisle",))
def gondola_shelf(mb, x, y, z, rot, rng, era):
    """Double-sided supermarket shelf packed with boxes, cans and bottles; price strips; end sign."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "metal" if s not in ("inter",) else "wood"
    box(mb, M, (0, 0, 0.8), (1.8, 0.06, 1.6), k)
    box(mb, M, (0, 0, 0.08), (1.8, 0.86, 0.16), "metal2")
    for zz in (0.17, 0.55, 0.93, 1.31):
        for side in (-1, 1):
            box(mb, M, (0, side * 0.23, zz), (1.8, 0.4, 0.025), k)
            box(mb, M, (0, side * 0.43, zz - 0.02), (1.8, 0.012, 0.05), rng.choice(("paper", "accent")))
            px = -0.84
            while px < 0.84:
                w = rng.uniform(0.08, 0.2)
                h = rng.uniform(0.12, 0.3)
                kk = rng.choice(("accent", "fabric", "leaf", "paper", "glass", "wall2", "fabric2", "glass2"))
                if rng.random() < 0.35:
                    for j in range(int(w / 0.07) + 1):
                        cyl(mb, M, (px + j * 0.07, side * 0.25, zz + 0.0125 + h * 0.35), 0.032, h * 0.7, kk, seg=8)
                else:
                    box(mb, M, (px + w / 2, side * 0.25, zz + 0.0125 + h / 2), (w, 0.3, h), kk)
                px += w + 0.02
    box(mb, M, (0.9, 0, 1.75), (0.04, 0.6, 0.3), "accent" if s not in FUTSUB else "screen")
    return []


@prop("cash_register", "surface", (0.45, 0.4, 0.45), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=SHOP + ("diner", "bar", "saloon", "speakeasy", "cafe", "pharmacy"))
def cash_register(mb, x, y, z, rot, rng, era):
    """Ornate brass register with pop-up flags (to the 50s) / beige electronic till / POS screen + drawer / tablet."""
    M, s = frame(x, y, z, rot), sub(era)
    if s in ("vic", "inter", "cold"):
        k = "metal" if s != "cold" else "metal2"
        box(mb, M, (0, 0, 0.08), (0.42, 0.38, 0.16), k)
        box(mb, M, (0, 0.04, 0.24), (0.38, 0.28, 0.18), k, r=(-0.25, 0, 0))
        for row in range(3):
            for i in range(5):
                cyl(mb, M, (-0.14 + i * 0.07, -0.08 + row * 0.06, 0.27 + row * 0.03), 0.018, 0.02, "paper", seg=8, rr=(-0.25, 0, 0))
        box(mb, M, (0, 0.12, 0.42), (0.3, 0.08, 0.12), k)
        for i in range(3):
            box(mb, M, (-0.08 + i * 0.08, 0.1, 0.52), (0.05, 0.01, 0.06), "paper")
        cyl(mb, M, (0.25, 0.0, 0.25), 0.01, 0.12, "metal", seg=6, axis="X")
        sph(mb, M, (0.32, 0.0, 0.25), 0.025, "dark")
        box(mb, M, (0, -0.19, 0.07), (0.38, 0.02, 0.1), "wood2" if s == "vic" else k)
        return []
    if s in ("analog", "post"):
        box(mb, M, (0, 0, 0.06), (0.42, 0.4, 0.12), "paper")
        box(mb, M, (0, 0.02, 0.17), (0.36, 0.3, 0.1), "paper", r=(-0.3, 0, 0))
        box(mb, M, (0, 0.14, 0.3), (0.2, 0.06, 0.08), "dark")
        box(mb, M, (0, 0.11, 0.3), (0.16, 0.01, 0.05), "screen")
        for i in range(12):
            box(mb, M, (-0.12 + (i % 4) * 0.08, -0.08 + (i // 4) * 0.06, 0.21 + (i // 4) * 0.02), (0.05, 0.04, 0.02), "metal2", r=(-0.3, 0, 0))
        return []
    box(mb, M, (0, 0, 0.05), (0.42, 0.4, 0.1), "dark")
    rod(mb, M, (0, 0.1, 0.1), (0, 0.08, 0.25), 0.02, "metal")
    box(mb, M, (0, 0.06, 0.32), (0.32, 0.03, 0.22), "dark", r=(-0.3, 0, 0))
    box(mb, M, (0, 0.05, 0.32), (0.28, 0.01, 0.18), "screen", r=(-0.3, 0, 0))
    box(mb, M, (0.17, -0.12, 0.13), (0.07, 0.07, 0.06), "dark")
    return []


@prop("mannequin", "floor", (0.5, 0.4, 1.8), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=SHOP + ("boutique", "attic", "tailor"))
def mannequin(mb, x, y, z, rot, rng, era):
    """Dress form on a tripod (19th c. / attic) or full shop mannequin in a coloured dress."""
    M, s = frame(x, y, z, rot), sub(era)
    for a in range(3):
        ang = a * math.tau / 3
        rod(mb, M, (0, 0, 0.15), (math.cos(ang) * 0.22, math.sin(ang) * 0.22, 0.0), 0.015, "wood2" if s == "vic" else "metal")
    cyl(mb, M, (0, 0, 0.5), 0.015, 0.8, "wood2" if s == "vic" else "metal", seg=6)
    dress = rng.choice(("fabric", "accent", "fabric2", "leaf"))
    cyl(mb, M, (0, 0, 0.95), 0.12, 0.4, dress, seg=10, r2=0.26 if s != "vic" else 0.2, rr=(math.pi, 0, 0))
    sph(mb, M, (0, 0, 1.28), 0.17, dress if s != "vic" else "fabric2", sq=(1.0, 0.7, 1.3))
    if s != "vic":
        cyl(mb, M, (0, 0, 1.53), 0.035, 0.1, "paper", seg=8)
        sph(mb, M, (0, 0, 1.68), 0.1, "paper", sq=(0.85, 0.9, 1.15))
        for sx in (-1, 1):
            rod(mb, M, (sx * 0.17, 0, 1.4), (sx * 0.24, -0.04, 1.05), 0.03, "paper")
    else:
        cyl(mb, M, (0, 0, 1.5), 0.03, 0.06, "wood2", seg=8)
    return []


@prop("display_counter", "wall", (1.8, 0.65, 1.0), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("shop_counter",))
def display_counter(mb, x, y, z, rot, rng, era):
    """Glass-topped display counter (merchandise visible inside); used as a shop / pharmacy counter."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s in ("vic", "inter", "cold") else ("metal" if s in FUTSUB else "paper")
    box(mb, M, (0, -0.32, 0.25), (1.8, 0.6, 0.5), k)
    for sx in (-0.88, 0.88):
        box(mb, M, (sx, -0.32, 0.72), (0.05, 0.6, 0.44), k)
    box(mb, M, (0, -0.6, 0.72), (1.72, 0.02, 0.42), "glass")
    box(mb, M, (0, -0.32, 0.96), (1.82, 0.62, 0.04), "glass")
    box(mb, M, (0, -0.32, 0.51), (1.74, 0.56, 0.02), "fabric2")
    for i in range(rng.randint(5, 8)):
        box(mb, M, (rng.uniform(-0.75, 0.75), rng.uniform(-0.5, -0.15), 0.56), (rng.uniform(0.08, 0.2), 0.12, rng.uniform(0.04, 0.12)),
            rng.choice(("accent", "paper", "metal", "glass2", "fabric")))
    box(mb, M, (0, -0.635, 0.25), (1.7, 0.02, 0.4), "wood2" if k == "wood" else "metal2")
    return [surf(M, (0.4, -0.32, 0.98), 0.4)]


@prop("clothes_rack", "floor", (1.4, 0.5, 1.6), eras=INTER | COLD | ANALOG | NOWS | FUTS | VIC, rooms=SHOP + ("boutique", "theatre", "cabaret"))
def clothes_rack(mb, x, y, z, rot, rng, era):
    """Rolling rail of hanging garments in mixed colours."""
    M = frame(x, y, z, rot)
    for sx in (-0.65, 0.65):
        box(mb, M, (sx, 0, 0.03), (0.06, 0.5, 0.04), "metal")
        cyl(mb, M, (sx, 0, 0.8), 0.018, 1.55, "metal", seg=6)
    cyl(mb, M, (0, 0, 1.55), 0.018, 1.32, "metal", seg=6, axis="X")
    n = rng.randint(6, 10)
    for i in range(n):
        cx = -0.55 + i * 1.1 / max(1, n - 1)
        k = rng.choice(("fabric", "fabric2", "accent", "leaf", "paper", "dark", "glass"))
        h = rng.uniform(0.6, 1.0)
        box(mb, M, (cx, 0, 1.5 - h / 2), (0.06, 0.4, h), k, r=(0, 0, rng.uniform(-0.1, 0.1)))
        rod(mb, M, (cx, 0, 1.55), (cx, 0, 1.5), 0.006, "metal")
    return []


@prop("shop_goods", "surface", (0.45, 0.3, 0.3), eras=ALL, rooms=SHOP + ("market", "counting_house", "saloon"))
def shop_goods(mb, x, y, z, rot, rng, era):
    """Counter-top goods: jars of sweets / boxes / tins / a scale before the 20th c."""
    M, t = frame(x, y, z, rot), tier(era)
    if t <= 1:
        cyl(mb, M, (-0.12, 0, 0.02), 0.08, 0.04, "metal", seg=10)
        rod(mb, M, (-0.12, 0, 0.04), (-0.12, 0, 0.22), 0.012, "metal")
        rod(mb, M, (-0.24, 0, 0.22), (0.0, 0, 0.22), 0.01, "metal")
        for sx in (-0.24, 0.0):
            cyl(mb, M, (sx, 0, 0.14), 0.06, 0.015, "metal", seg=10)
        cyl(mb, M, (0.14, 0, 0.1), 0.06, 0.2, "glass", seg=10)
        cyl(mb, M, (0.14, 0, 0.06), 0.058, 0.1, "accent", seg=10)
        return []
    for i in range(rng.randint(3, 5)):
        if rng.random() < 0.5:
            h = rng.uniform(0.08, 0.14)
            cyl(mb, M, (-0.16 + i * 0.09, rng.uniform(-0.06, 0.06), h / 2), 0.035, h, rng.choice(("accent", "leaf", "paper", "fabric")), seg=8)
        else:
            w, h = rng.uniform(0.06, 0.12), rng.uniform(0.1, 0.22)
            box(mb, M, (-0.16 + i * 0.09, rng.uniform(-0.06, 0.06), h / 2), (w, 0.06, h), rng.choice(("accent", "fabric", "paper", "glass")))
    return []


# ============================================================================ courtroom / church
COURT = ("court",)


@prop("judge_bench", "wall", (3.0, 1.2, 1.6), eras=ALL - ANTIQ - MEDV, rooms=("court_layout",))
def judge_bench(mb, x, y, z, rot, rng, era):
    """Raised panelled judge's bench on a dais with a tall-back chair behind, gavel + block."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s not in FUTSUB else "metal"
    box(mb, M, (0, -0.6, 0.15), (3.0, 1.2, 0.3), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.95, 0.85), (2.8, 0.3, 1.1), k)
    for i in range(5):
        box(mb, M, (-1.12 + i * 0.56, -1.105, 0.85), (0.44, 0.02, 0.8), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.9, 1.43), (3.0, 0.5, 0.06), "wood2" if k == "wood" else "dark")
    box(mb, M, (0, -0.45, 0.55), (0.7, 0.6, 0.06), "fabric")
    box(mb, M, (0, -0.25, 1.15), (0.8, 0.12, 1.4), "fabric")
    box(mb, M, (0, -0.25, 1.9), (0.9, 0.14, 0.12), k)
    if s in ("fut", "cyber", "space"):
        box(mb, M, (0.8, -0.95, 1.5), (0.5, 0.02, 0.3), "screen", r=(-0.3, 0, 0))
    box(mb, M, (0.5, -0.95, 1.47), (0.14, 0.1, 0.03), "wood2")
    rod(mb, M, (0.45, -0.95, 1.5), (0.6, -0.9, 1.5), 0.012, "wood")
    cyl(mb, M, (0.45, -0.95, 1.5), 0.025, 0.08, "wood", seg=8, axis="Y")
    box(mb, M, (0, -1.11, 1.15), (0.5, 0.02, 0.4), "metal")           # crest
    cyl(mb, M, (0, -1.125, 1.15), 0.15, 0.015, "accent", seg=12, axis="Y")
    return [surf(M, (-0.7, -0.9, 1.46), 0.4)]


@prop("witness_box", "floor", (1.1, 1.0, 1.3), eras=ALL - ANTIQ - MEDV, rooms=("court_layout",))
def witness_box(mb, x, y, z, rot, rng, era):
    """Railed, raised stand with a chair and microphone (faces -Y)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s not in FUTSUB else "metal"
    box(mb, M, (0, 0, 0.1), (1.1, 1.0, 0.2), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.48, 0.6), (1.1, 0.06, 0.8), k)
    for sx in (-0.52, 0.52):
        box(mb, M, (sx, 0, 0.6), (0.06, 1.0, 0.8), k)
    for i in range(3):
        box(mb, M, (-0.33 + i * 0.33, -0.515, 0.6), (0.26, 0.02, 0.58), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.48, 1.02), (1.16, 0.12, 0.05), "wood2" if k == "wood" else "dark")
    box(mb, M, (0, 0.15, 0.65), (0.45, 0.42, 0.05), "wood")
    box(mb, M, (0, 0.35, 0.95), (0.45, 0.05, 0.55), "wood")
    if s not in ("ren", "enl", "vic"):
        rod(mb, M, (0.2, -0.46, 1.05), (0.1, -0.35, 1.28), 0.008, "dark")
        sph(mb, M, (0.1, -0.33, 1.3), 0.025, "dark")
    return []


@prop("jury_bench", "floor", (3.0, 1.6, 1.3), eras=ALL - ANTIQ - MEDV, rooms=("court_layout",))
def jury_bench(mb, x, y, z, rot, rng, era):
    """Two tiers of six jury chairs behind a panelled rail (faces -Y)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s not in FUTSUB else "metal"
    box(mb, M, (0, 0.45, 0.15), (3.0, 0.7, 0.3), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.75, 0.45), (3.0, 0.08, 0.9), k)
    for i in range(6):
        box(mb, M, (-1.25 + i * 0.5, -0.8, 0.45), (0.4, 0.02, 0.66), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.75, 0.92), (3.06, 0.14, 0.05), "wood2" if k == "wood" else "dark")
    for row, (y0, z0) in enumerate(((-0.25, 0.0), (0.45, 0.3))):
        for i in range(6):
            cx = -1.25 + i * 0.5
            box(mb, M, (cx, y0, z0 + 0.46), (0.42, 0.42, 0.05), "fabric")
            box(mb, M, (cx, y0 + 0.2, z0 + 0.75), (0.42, 0.05, 0.55), "fabric" if s != "vic" else "wood")
            for sx in (-0.18, 0.18):
                box(mb, M, (cx + sx, y0, z0 + 0.22), (0.04, 0.38, 0.44), k)
    return []


@prop("pew", "floor", (2.6, 0.7, 1.0), eras=ALL - ANTIQ, rooms=("pews",))
def pew(mb, x, y, z, rot, rng, era):
    """Wooden pew / gallery bench with scrolled ends and a kneeler + book ledge (faces -Y)."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s not in FUTSUB else "metal"
    box(mb, M, (0, 0.0, 0.44), (2.5, 0.42, 0.05), k)
    box(mb, M, (0, 0.22, 0.72), (2.5, 0.05, 0.56), k, r=(-0.1, 0, 0))
    for sx in (-1.25, 1.25):
        box(mb, M, (sx, 0.05, 0.48), (0.07, 0.6, 0.96), "wood2" if k == "wood" else "metal2")
        cyl(mb, M, (sx, -0.2, 0.96), 0.12, 0.08, "wood2" if k == "wood" else "metal2", seg=10, axis="X")
    box(mb, M, (0, 0.28, 0.9), (2.5, 0.14, 0.03), k)                               # book ledge (for the pew behind)
    box(mb, M, (0, 0.3, 0.12), (2.4, 0.18, 0.08), "fabric")                         # kneeler
    if rng.random() < 0.5:
        box(mb, M, (rng.uniform(-0.8, 0.8), 0.28, 0.93), (0.14, 0.1, 0.04), "dark")
    return []


@prop("flag", "floor", (0.6, 0.6, 2.4), eras=ALL, rooms=COURT + ("court_layout", "civic", "classroom", "police", "bunker", "office"))
def flag(mb, x, y, z, rot, rng, era):
    """Flag on a pole with a weighted base and finial; draped cloth in folds."""
    M = frame(x, y, z, rot)
    cyl(mb, M, (0, 0, 0.05), 0.18, 0.1, "metal2", seg=12, r2=0.12)
    cyl(mb, M, (0, 0, 1.2), 0.02, 2.3, "wood2" if tier(era) <= 1 else "metal", seg=8)
    sph(mb, M, (0, 0, 2.38), 0.045, "metal")
    k1, k2 = rng.sample(("fabric", "accent", "trim", "paper", "leaf"), 2)
    for i in range(4):
        box(mb, M, (0.06 + i * 0.012, -0.03 + (i % 2) * 0.06, 1.82 - i * 0.06), (0.05, 0.08, 0.95 - i * 0.12), k1 if i % 2 == 0 else k2)
    box(mb, M, (0.05, 0.0, 2.25), (0.1, 0.16, 0.12), k1)
    return []


@prop("lectern", "floor", (0.6, 0.5, 1.3), eras=ALL, rooms=("church", "court", "classroom", "hall", "pews"))
def lectern(mb, x, y, z, rot, rng, era):
    """Reading stand with sloped top and an open book (faces -Y); eagle-less, chunky."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s not in FUTSUB else "metal"
    box(mb, M, (0, 0, 0.04), (0.55, 0.45, 0.08), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, 0, 0.55), (0.32, 0.3, 0.95), k)
    box(mb, M, (0, -0.02, 1.08), (0.6, 0.45, 0.06), k, r=(0.35, 0, 0))
    box(mb, M, (0, -0.04, 1.11), (0.44, 0.3, 0.03), "paper", r=(0.35, 0, 0))
    box(mb, M, (0, -0.04, 1.105), (0.02, 0.3, 0.035), "dark", r=(0.35, 0, 0))
    if s in ("med", "ren", "enl", "vic"):
        box(mb, M, (0, -0.16, 0.55), (0.14, 0.02, 0.5), "fabric")
    return []


@prop("altar", "wall", (2.2, 1.0, 1.0), eras=ALL, rooms=("church", "temple", "pews"))
def altar(mb, x, y, z, rot, rng, era):
    """Altar table with a long cloth, candlesticks, cross / emblem on a stand, kneeling step in front."""
    M, s = frame(x, y, z, rot), sub(era)
    box(mb, M, (0, -0.55, 0.06), (2.6, 1.1, 0.12), "stone")
    box(mb, M, (0, -0.5, 0.52), (2.0, 0.8, 0.84), "stone" if s in ("antiq", "med") else "wood")
    box(mb, M, (0, -0.5, 0.96), (2.1, 0.86, 0.04), "paper")
    box(mb, M, (0, -0.935, 0.7), (2.1, 0.02, 0.5), "paper")
    box(mb, M, (0, -0.945, 0.68), (0.4, 0.02, 0.46), "accent")
    for sx in (-0.75, 0.75):
        cyl(mb, M, (sx, -0.45, 1.0), 0.06, 0.04, "metal", seg=10)
        cyl(mb, M, (sx, -0.45, 1.12), 0.018, 0.2, "metal", seg=6)
        cyl(mb, M, (sx, -0.45, 1.32), 0.025, 0.22, "paper", seg=8)
        cyl(mb, M, (sx, -0.45, 1.45), 0.01, 0.04, "flame", seg=6)
    box(mb, M, (0, -0.25, 1.4), (0.07, 0.06, 0.8), "metal")
    box(mb, M, (0, -0.25, 1.55), (0.42, 0.06, 0.07), "metal")
    box(mb, M, (0, -0.02, 1.4), (1.6, 0.04, 2.2), "fabric2")                          # dossal hanging
    box(mb, M, (0, -1.3, 0.1), (2.0, 0.35, 0.2), "fabric")                            # kneeling step
    return []


# ============================================================================ waiting room
WAIT = ("waiting", "reception", "station", "lobby")


@prop("waiting_chairs", "floor", (2.0, 0.6, 0.85), eras=INTER | COLD | ANALOG | NOWS | FUTS | VIC, rooms=("waiting_row",))
def waiting_chairs(mb, x, y, z, rot, rng, era):
    """Beam of three or four linked seats (faces -Y); a coat or magazine left on one."""
    M, s = frame(x, y, z, rot), sub(era)
    n = 4 if rng.random() < 0.5 else 3
    w = 0.52
    k = {"vic": "wood", "inter": "wood", "cold": "accent", "analog": "fabric2"}.get(s, "fabric")
    box(mb, M, (0, 0.0, 0.3), (n * w, 0.08, 0.06), "metal2")
    for sx in (-(n * w) / 2 + 0.1, (n * w) / 2 - 0.1):
        box(mb, M, (sx, 0.0, 0.15), (0.06, 0.4, 0.3), "metal2")
        box(mb, M, (sx, 0.0, 0.02), (0.08, 0.5, 0.04), "metal2")
    for i in range(n):
        cx = -(n * w) / 2 + w * (i + 0.5)
        box(mb, M, (cx, -0.03, 0.44), (w - 0.06, 0.46, 0.07), k)
        box(mb, M, (cx, 0.22, 0.7), (w - 0.06, 0.06, 0.46), k, r=(-0.12, 0, 0))
        box(mb, M, (cx + w / 2, 0.02, 0.6), (0.04, 0.4, 0.04), "dark")
    i = rng.randrange(n)
    cx = -(n * w) / 2 + w * (i + 0.5)
    if rng.random() < 0.5:
        box(mb, M, (cx, -0.05, 0.49), (0.22, 0.3, 0.02), "paper", r=(0, 0, 0.3))
    else:
        box(mb, M, (cx, 0.0, 0.55), (0.4, 0.4, 0.1), rng.choice(("fabric2", "dark")), r=(0.2, 0, 0.2))
    return []


@prop("magazine_table", "floor", (0.8, 0.6, 0.5), eras=INTER | COLD | ANALOG | NOWS | FUTS | VIC, rooms=WAIT + ("hospital",))
def magazine_table(mb, x, y, z, rot, rng, era):
    M, t = frame(x, y, z, rot), tier(era)
    k = "wood" if t <= 2 else ("metal" if t == 4 else "wood")
    box(mb, M, (0, 0, 0.45), (0.8, 0.6, 0.04), k)
    legs4(mb, M, 0.76, 0.56, 0.43, 0.04, "metal2" if t >= 2 else "wood2")
    for i in range(rng.randint(3, 5)):
        box(mb, M, (rng.uniform(-0.2, 0.2), rng.uniform(-0.12, 0.12), 0.475 + i * 0.008), (0.21, 0.28, 0.006),
            rng.choice(("paper", "accent", "fabric", "glass")), r=(0, 0, rng.uniform(-0.6, 0.6)))
    return []


@prop("reception_desk", "wall", (2.2, 0.9, 1.15), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=("reception_x",))
def reception_desk(mb, x, y, z, rot, rng, era):
    """Front desk with a raised transaction ledge, bell / sign-in book, monitor or ledger, and bins behind."""
    M, s = frame(x, y, z, rot), sub(era)
    k = "wood" if s in ("vic", "inter", "cold") else ("metal" if s in FUTSUB else "wood")
    box(mb, M, (0, -0.55, 0.55), (2.2, 0.12, 1.1), k)
    box(mb, M, (0, -0.58, 1.12), (2.3, 0.3, 0.05), "wood2" if k == "wood" else "metal2")
    box(mb, M, (0, -0.32, 0.74), (2.1, 0.5, 0.04), "wood2" if k == "wood" else "metal2")
    for sx in (-1.05, 1.05):
        box(mb, M, (sx, -0.32, 0.37), (0.06, 0.5, 0.74), k)
    for i in range(4):
        box(mb, M, (-0.8 + i * 0.53, -0.615, 0.5), (0.4, 0.02, 0.7), "wood2" if k == "wood" else "accent" if s in FUTSUB else "trim")
    if s in ("vic", "inter"):
        cyl(mb, M, (0.6, -0.6, 1.17), 0.05, 0.05, "metal", seg=10, r2=0.02)
        box(mb, M, (-0.4, -0.58, 1.16), (0.4, 0.26, 0.03), "paper")
        box(mb, M, (-0.4, -0.58, 1.17), (0.02, 0.26, 0.03), "dark")
    box(mb, M, (0, -0.02, 1.8), (1.2, 0.04, 0.3), "trim")                            # name sign on the wall
    box(mb, M, (0, -0.045, 1.8), (1.0, 0.01, 0.12), "paper" if s not in FUTSUB else "accent")
    return [surf(M, (0.3, -0.3, 0.76), 0.4)]


# ============================================================================ hanging
@prop("industrial_lamp", "hanging", (0.5, 0.5, 0.9), eras=VIC | MIDC | ANALOG | NOWS | FUTS, rooms=FACTORY + ("warehouse", "garage", "bunker", "lab", "kitchen", "cafe"))
def industrial_lamp(mb, x, y, z, rot, rng, era):
    """Enamel dome pendant on a chain/cable (origin at the ceiling)."""
    M, s = frame(x, y, z, rot), sub(era)
    L = 0.7
    cyl(mb, M, (0, 0, -0.02), 0.06, 0.04, "metal2", seg=8)
    cyl(mb, M, (0, 0, -L / 2), 0.008, L, "dark", seg=6)
    k = "leaf" if s in ("cold", "analog") else ("metal2" if s != "vic" else "dark")
    cyl(mb, M, (0, 0, -L - 0.06), 0.05, 0.12, k, seg=10)
    cyl(mb, M, (0, 0, -L - 0.17), 0.08, 0.12, k, seg=14, r2=0.25)
    cyl(mb, M, (0, 0, -L - 0.215), 0.24, 0.02, "lampshade", seg=14)
    return []


@prop("ceiling_fan", "hanging", (1.3, 1.3, 0.6), eras=MIDC | ANALOG | NOWS | VIC, rooms=("cafe", "office", "saloon", "waiting", "tropical", "hotel", "police"))
def ceiling_fan(mb, x, y, z, rot, rng, era):
    M = frame(x, y, z, rot + rng.uniform(0, 1.5))
    cyl(mb, M, (0, 0, -0.03), 0.07, 0.06, "metal2", seg=10)
    cyl(mb, M, (0, 0, -0.2), 0.015, 0.3, "metal2", seg=6)
    cyl(mb, M, (0, 0, -0.38), 0.1, 0.12, "metal", seg=12)
    for a in range(4):
        ang = a * math.tau / 4
        box(mb, M, (math.cos(ang) * 0.38, math.sin(ang) * 0.38, -0.4), (0.55, 0.13, 0.015), "wood", r=(0.08, 0, ang))
    sph(mb, M, (0, 0, -0.5), 0.07, "lampshade")
    return []

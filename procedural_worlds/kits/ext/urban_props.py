"""Urban asset pack, part 2: street furniture, construction, rail / transit parts, maritime and space
transit props for every era. Tags (rooms): street, plaza, station, rail, construction, dock, ship,
space, parking, canal, forum. Front of every prop is local -Y (faces the viewer at rot=0)."""
import math
from mathutils import Vector, Matrix
from ..props import prop, _box, _cyl, OLD, MID, NOW, FUT
from .urban_vehicles import (M_at, cylx, rbox, tbox, rod, spoked, _ring, ALL, ANC, MED, PREIND, STEAM, INTER, COLD,
                             EIGHTIES, NOWISH, NEAR, FAR, RAIL, acc, body_key, hull_shell)

MODERNISH = MID | NOW | FUT
ELECTRIC = MID | NOW | FUT                         # electric street light / signals
LATE = NOW | FUT


# ============================================================================= street furniture
@prop("fire_hydrant", "floor", (0.4, 0.4, 0.8), eras=STEAM | MODERNISH, rooms=("street", "plaza", "parking", "construction"))
def fire_hydrant(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = "fabric" if era not in FUT else "accent"
    _cyl(mb, M, (0, 0, 0.04), 0.17, 0.08, k, seg=10)
    _cyl(mb, M, (0, 0, 0.32), 0.12, 0.5, k, seg=10)
    _cyl(mb, M, (0, 0, 0.6), 0.14, 0.06, k, seg=10)
    _cyl(mb, M, (0, 0, 0.68), 0.1, 0.12, k, seg=10, r2=0.05)
    for sx in (-1, 1):
        cylx(mb, M, (sx * 0.15, 0, 0.42), 0.05, 0.1, "metal", seg=8)
    cylx(mb, M, (0, -0.15, 0.4), 0.07, 0.1, "metal", seg=8, axis="Y")


@prop("mailbox", "floor", (0.6, 0.6, 1.5), eras=STEAM | MODERNISH, rooms=("street", "plaza", "station"))
def mailbox(mb, x, y, z, rot, rng, era):
    """Victorian pillar box / US blue mailbox / modern parcel locker."""
    M = M_at(x, y, z, rot)
    if era in STEAM or (era in INTER and rng.random() < 0.5):
        _cyl(mb, M, (0, 0, 0.05), 0.3, 0.1, "dark", seg=14)
        _cyl(mb, M, (0, 0, 0.75), 0.26, 1.3, "fabric", seg=14)
        _cyl(mb, M, (0, 0, 1.45), 0.29, 0.1, "fabric", seg=14)
        _cyl(mb, M, (0, 0, 1.55), 0.24, 0.12, "fabric", seg=14, r2=0.12)
        _box(mb, M, (0, -0.25, 1.2), (0.26, 0.04, 0.05), "dark")                    # slot
        _box(mb, M, (0, -0.25, 0.85), (0.2, 0.03, 0.2), "paper")
    elif era in FUT:
        _box(mb, M, (0, 0, 0.9), (0.9, 0.5, 1.8), "metal2")
        for i in range(3):
            for j in range(4):
                _box(mb, M, (-0.28 + i * 0.28, -0.26, 0.3 + j * 0.4), (0.24, 0.02, 0.34), "metal")
        _box(mb, M, (0, -0.27, 1.62), (0.6, 0.02, 0.12), "accent")
    else:
        for sx in (-0.18, 0.18):
            _box(mb, M, (sx, 0, 0.2), (0.05, 0.4, 0.4), "accent" if era in NOW else "trim")
        _box(mb, M, (0, 0, 0.75), (0.5, 0.45, 0.7), "accent" if era in NOW else "trim")
        cylx(mb, M, (0, 0, 1.1), 0.25, 0.45, "accent" if era in NOW else "trim", seg=12, axis="Y")
        _box(mb, M, (0, -0.24, 1.0), (0.3, 0.04, 0.12), "metal")
        _box(mb, M, (0, -0.235, 0.7), (0.3, 0.02, 0.2), "paper")


@prop("phone_booth", "floor", (1.0, 1.0, 2.6), eras=INTER | COLD | NOW | FUT, rooms=("street", "plaza", "station"))
def phone_booth(mb, x, y, z, rot, rng, era):
    """Red glazed kiosk (interwar/cold war), open payphone hood (80s/modern), holo pillar (future)."""
    M = M_at(x, y, z, rot)
    if era in MID:
        k = "fabric"
        _box(mb, M, (0, 0, 0.06), (1.0, 1.0, 0.12), k)
        for sx in (-0.45, 0.45):
            for sy in (-0.45, 0.45):
                _box(mb, M, (sx, sy, 1.25), (0.1, 0.1, 2.3), k)
        for side in ((0, -0.46), (0, 0.46), (-0.46, 0), (0.46, 0)):
            sz = (0.8, 0.04, 1.7) if side[0] == 0 else (0.04, 0.8, 1.7)
            _box(mb, M, (side[0], side[1], 1.25), sz, "glass")
            for k2 in range(1, 6):                                                   # glazing bars
                _box(mb, M, (side[0] * 1.02, side[1] * 1.02, 0.4 + k2 * 0.28), (sz[0] + 0.01, sz[1] + 0.01, 0.03), k)
        _box(mb, M, (0, 0, 2.42), (1.05, 1.05, 0.2), k)
        tbox(mb, M, (0, 0, 2.6), (1.0, 1.0, 0.18), k, top=(0.6, 0.6))
        for sy in (-0.53, 0.53):
            _box(mb, M, (0, sy, 2.42), (0.7, 0.02, 0.12), "lampshade")                # TELEPHONE strip
    elif era in FUT:
        _cyl(mb, M, (0, 0, 1.2), 0.18, 2.4, "metal2", seg=10)
        _box(mb, M, (0, -0.19, 1.5), (0.3, 0.02, 0.5), "screen")
        _cyl(mb, M, (0, 0, 2.42), 0.22, 0.05, "accent", seg=12)
    else:
        _box(mb, M, (0, 0.1, 1.1), (0.1, 0.1, 2.2), "metal2")
        tbox(mb, M, (0, -0.1, 1.55), (0.8, 0.5, 0.9), "metal", top=(1.0, 1.0))
        _box(mb, M, (0, -0.1, 1.55), (0.7, 0.4, 0.8), "dark")
        _box(mb, M, (0, -0.25, 1.5), (0.3, 0.12, 0.4), "metal2")                    # handset unit
        _box(mb, M, (0, -0.1, 2.05), (0.84, 0.54, 0.1), "accent")
        _box(mb, M, (0, -0.36, 1.25), (0.5, 0.04, 0.12), "accent")


@prop("payphone", "wall", (0.4, 0.3, 0.8), eras=COLD | NOW, rooms=("street", "station", "bar", "diner"))
def payphone(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 1.4), (0.3, 0.18, 0.55), "metal")
    _box(mb, M, (-0.08, -0.1, 1.45), (0.07, 0.04, 0.3), "dark")                       # handset
    for i in range(3):
        for j in range(4):
            _box(mb, M, (0.04 + i * 0.04, -0.095, 1.3 + j * 0.05), (0.025, 0.02, 0.03), "paper")
    _box(mb, M, (0, -0.1, 1.65), (0.32, 0.06, 0.06), "accent")


@prop("newspaper_stand", "floor", (2.2, 1.4, 2.6), eras=STEAM | MID | NOW, rooms=("street", "plaza", "station"))
def newspaper_stand(mb, x, y, z, rot, rng, era):
    """Kiosk: counter, magazine racks, awning roof, papers stacked in front."""
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("wall2", "trim", "accent"))
    _box(mb, M, (0, 0.15, 1.15), (2.0, 1.1, 2.3), k)
    _box(mb, M, (0, -0.42, 1.55), (1.6, 0.04, 0.9), "dark")                             # hatch
    _box(mb, M, (0, -0.55, 1.0), (1.9, 0.3, 0.08), "wood")
    tbox(mb, M, (0, 0.0, 2.42), (2.3, 1.6, 0.25), k, top=(0.9, 0.8))
    _box(mb, M, (0, -0.6, 2.3), (2.2, 0.04, 0.3), "signcol" if era in STEAM | MID else "paper")
    for i in range(6):                                                                # magazines
        _box(mb, M, (-0.75 + i * 0.3, -0.45, 1.5 + (i % 2) * 0.3), (0.22, 0.02, 0.28), rng.choice(("accent", "paper", "fabric", "glass")))
    for i in range(3):
        _box(mb, M, (-0.6 + i * 0.6, -0.95, 0.35), (0.45, 0.32, 0.7), "wood2")
        _box(mb, M, (-0.6 + i * 0.6, -0.95, 0.75), (0.42, 0.3, 0.1), "paper")


@prop("bus_shelter", "floor", (3.4, 1.6, 2.6), eras=MODERNISH, rooms=("street", "station"))
def bus_shelter(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = "metal2" if era not in INTER else "wood"
    for sx in (-1.6, 1.6):
        for sy in (-0.65, 0.65):
            _box(mb, M, (sx, sy, 1.2), (0.08, 0.08, 2.4), k)
    _box(mb, M, (0, 0.68, 1.3), (3.2, 0.04, 2.0), "glass")
    _box(mb, M, (1.6, 0, 1.3), (0.04, 1.3, 2.0), "glass")
    _box(mb, M, (1.62, 0, 1.3), (0.02, 1.0, 1.4), "paper" if era not in FUT else "screen")   # ad panel
    tbox(mb, M, (0, 0, 2.48), (3.5, 1.6, 0.12), k, top=(1.0, 0.95), shift=(0, 0.04))
    _box(mb, M, (0, 0.45, 0.48), (2.4, 0.35, 0.06), "wood" if era not in FUT else "metal")
    _box(mb, M, (0, -0.82, 2.35), (1.0, 0.04, 0.22), "accent")                          # route sign
    rod(mb, M, (-1.9, -0.6, 0), (-1.9, -0.6, 2.8), 0.04, "metal2")
    cylx(mb, M, (-1.9, -0.6, 2.7), 0.22, 0.03, "accent", seg=12, axis="Y")


@prop("street_bench", "floor", (1.8, 0.7, 0.9), eras=ALL, rooms=("street", "plaza", "station", "dock"))
def street_bench(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    if era in ANC | MED:
        _box(mb, M, (0, 0, 0.42), (1.8, 0.5, 0.12), "stone")
        for sx in (-0.7, 0.7):
            _box(mb, M, (sx, 0, 0.18), (0.3, 0.45, 0.36), "stone")
        return
    leg = "metal2" if era not in FUT else "metal"
    slat = "wood" if era not in FUT else "metal"
    for sx in (-0.8, 0.8):
        _box(mb, M, (sx, 0, 0.22), (0.07, 0.55, 0.44), leg)
        _box(mb, M, (sx, 0.24, 0.62), (0.06, 0.06, 0.55), leg)
        if era in STEAM | INTER:
            _box(mb, M, (sx, -0.05, 0.62), (0.07, 0.35, 0.05), leg)                  # armrest
    for k in range(3):
        _box(mb, M, (0, -0.18 + k * 0.15, 0.45), (1.8, 0.12, 0.04), slat)
    for k in range(2):
        _box(mb, M, (0, 0.27, 0.62 + k * 0.17), (1.8, 0.04, 0.12), slat)


@prop("trash_bin", "floor", (0.6, 0.6, 1.0), eras=STEAM | MODERNISH, rooms=("street", "plaza", "station", "parking", "dock"))
def trash_bin(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    if era in STEAM | INTER:
        _cyl(mb, M, (0, 0, 0.42), 0.28, 0.84, "metal2", seg=12)
        _cyl(mb, M, (0, 0, 0.88), 0.3, 0.08, "metal2", seg=12, r2=0.15)
        for zz in (0.2, 0.62):
            _cyl(mb, M, (0, 0, zz), 0.29, 0.03, "dark", seg=12)
    elif era in COLD | EIGHTIES:
        _cyl(mb, M, (0, 0, 0.45), 0.26, 0.9, "metal", seg=12, r2=0.3)                # wire basket
        _cyl(mb, M, (0, 0, 0.88), 0.31, 0.04, "dark", seg=12)
        mb.sphere(M @ Vector((0, 0, 0.92)), 0.2, "paper", sub=1, squash=0.6)
    elif era in FUT:
        _cyl(mb, M, (0, 0, 0.5), 0.25, 1.0, "metal2", seg=8, r2=0.2)
        _cyl(mb, M, (0, 0, 0.8), 0.255, 0.05, "accent", seg=8)
    else:                                                                            # wheelie bin
        tbox(mb, M, (0, 0, 0.5), (0.58, 0.7, 0.95), body_key(rng, era, ("wall2", "dark", "accent")), top=(1.06, 1.06))
        _box(mb, M, (0, 0.03, 1.0), (0.64, 0.78, 0.06), "dark")
        for sx in (-0.26, 0.26):
            cylx(mb, M, (sx, 0.35, 0.1), 0.1, 0.06, "dark", seg=8)


@prop("bollard", "floor", (0.3, 0.3, 1.0), eras=ALL, rooms=("street", "plaza", "dock", "parking", "station"))
def bollard(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    if era in OLD:
        tbox(mb, M, (0, 0, 0.4), (0.3, 0.3, 0.8), "stone", top=(0.8, 0.8))
        _cyl(mb, M, (0, 0, 0.85), 0.12, 0.1, "stone", seg=8)
    elif era in MID:
        _cyl(mb, M, (0, 0, 0.45), 0.12, 0.9, "dark", seg=10)
        _cyl(mb, M, (0, 0, 0.93), 0.14, 0.08, "dark", seg=10, r2=0.06)
        _cyl(mb, M, (0, 0, 0.1), 0.16, 0.2, "dark", seg=10)
    else:
        _cyl(mb, M, (0, 0, 0.5), 0.11, 1.0, "metal2" if era in NOW else "metal", seg=10)
        _cyl(mb, M, (0, 0, 0.82), 0.115, 0.08, "paper" if era in NOW else "accent", seg=10)


@prop("traffic_light", "floor", (0.5, 0.5, 3.6), eras=ELECTRIC, rooms=("street", "parking"))
def traffic_light(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 1.6), 0.06, 3.2, "metal2", seg=8)
    _cyl(mb, M, (0, 0, 0.1), 0.12, 0.2, "metal2", seg=8)
    if era in FUT:
        _box(mb, M, (0, -0.08, 2.9), (0.18, 0.08, 0.9), "dark")
        _box(mb, M, (0, -0.125, 2.9), (0.12, 0.02, 0.8), "accent")
        return
    _box(mb, M, (0, -0.15, 2.75), (0.32, 0.22, 0.95), "dark" if era not in INTER else "trim")
    for i, kk in enumerate(("fabric", "lampshade", "leaf")):
        cylx(mb, M, (0, -0.27, 3.05 - i * 0.3), 0.09, 0.03, kk, seg=10, axis="Y")
        _box(mb, M, (0, -0.32, 3.12 - i * 0.3), (0.22, 0.12, 0.03), "dark")           # visors
    _box(mb, M, (0.15, -0.1, 1.15), (0.14, 0.12, 0.2), "dark")                         # push button


@prop("street_sign", "floor", (0.9, 0.2, 2.8), eras=STEAM | MODERNISH, rooms=("street", "plaza", "parking", "station"))
def street_sign(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 1.35), 0.04, 2.7, "metal2", seg=6)
    k = "leaf" if era in NOW else "paper" if era in STEAM | MID else "accent"
    _box(mb, M, (0.25, 0, 2.55), (0.8, 0.03, 0.18), k)
    _box(mb, M, (0, 0.25, 2.35), (0.03, 0.8, 0.18), k)
    for i in range(4):
        _box(mb, M, (0.05 + i * 0.12, -0.02, 2.55), (0.07, 0.01, 0.07), "dark")
    if era in COLD | NOW and rng.random() < 0.6:                                      # stop / warning plate
        cylx(mb, M, (0, -0.04, 1.85), 0.3, 0.03, "fabric", seg=8, axis="Y")
        _box(mb, M, (0, -0.06, 1.85), (0.32, 0.01, 0.08), "paper")


@prop("parking_meter", "floor", (0.3, 0.3, 1.4), eras=COLD | NOW, rooms=("street", "parking"))
def parking_meter(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.6), 0.04, 1.2, "metal2", seg=6)
    if era in COLD:
        tbox(mb, M, (0, 0, 1.3), (0.22, 0.18, 0.25), "metal", top=(0.9, 0.9))
        cylx(mb, M, (0, 0, 1.45), 0.11, 0.18, "metal", seg=10, axis="Y")
        cylx(mb, M, (0, -0.06, 1.45), 0.08, 0.08, "glass", seg=10, axis="Y")
    else:
        _box(mb, M, (0, 0, 1.4), (0.25, 0.18, 0.45), "metal2")
        _box(mb, M, (0, -0.092, 1.5), (0.16, 0.01, 0.1), "screen")
        _box(mb, M, (0, -0.1, 1.32), (0.12, 0.02, 0.06), "dark")


@prop("manhole", "floor", (0.8, 0.8, 0.03), eras=STEAM | MODERNISH, rooms=("street", "parking", "plaza"))
def manhole(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.012), 0.36, 0.024, "metal2", seg=16)
    for k in range(4):
        _box(mb, M, (0, -0.2 + k * 0.13, 0.026), (0.55 - abs(k - 1.5) * 0.12, 0.03, 0.01), "dark")


@prop("gas_lamp", "floor", (0.5, 0.5, 3.6), eras=STEAM | {"1700s-1800s", "enlightenment_piracy"} | INTER, rooms=("street", "plaza", "station", "dock"))
def gas_lamp(mb, x, y, z, rot, rng, era):
    """Cast-iron gas lamp: fluted post, ladder bar, glazed lantern with a crown."""
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.3), 0.16, 0.6, "dark", seg=10, r2=0.1)
    _cyl(mb, M, (0, 0, 1.6), 0.06, 2.4, "dark", seg=8)
    _box(mb, M, (0, 0, 2.6), (0.6, 0.05, 0.05), "dark")                                  # ladder bar
    _cyl(mb, M, (0, 0, 2.85), 0.13, 0.12, "dark", seg=8, r2=0.18)
    tbox(mb, M, (0, 0, 3.12), (0.32, 0.32, 0.42), "lampshade", top=(1.3, 1.3))
    for sx in (-1, 1):
        for sy in (-1, 1):
            rod(mb, M, (sx * 0.16, sy * 0.16, 2.92), (sx * 0.21, sy * 0.21, 3.33), 0.012, "dark", seg=4)
    tbox(mb, M, (0, 0, 3.42), (0.48, 0.48, 0.18), "dark", top=(0.2, 0.2))
    _cyl(mb, M, (0, 0, 3.56), 0.03, 0.12, "dark", seg=6)


@prop("torch_post", "floor", (0.4, 0.4, 2.4), eras=ANC | MED | PREIND, rooms=("street", "plaza", "dock", "forum"))
def torch_post(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 1.0), 0.07, 2.0, "wood2", seg=6)
    _cyl(mb, M, (0, 0, 2.05), 0.14, 0.18, "metal", seg=8, r2=0.2)
    for k in range(3):
        _cyl(mb, M, (0, 0, 2.2 + k * 0.12), 0.13 - k * 0.04, 0.16, "flame", seg=7, r2=0.03)


@prop("electric_lamp", "floor", (1.4, 0.4, 5.2), eras=INTER | COLD, rooms=("street", "plaza", "station", "parking", "dock"))
def electric_lamp(mb, x, y, z, rot, rng, era):
    """1920s-50s street light: tapering post, swan-neck arm, enamel shade."""
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.35), 0.15, 0.7, "dark", seg=10)
    _cyl(mb, M, (0, 0, 2.6), 0.07, 4.0, "dark", seg=8, r2=0.05)
    rod(mb, M, (0, 0, 4.5), (0, -0.5, 4.95), 0.04, "dark")
    rod(mb, M, (0, -0.5, 4.95), (0, -1.0, 4.85), 0.04, "dark")
    _cyl(mb, M, (0, -1.05, 4.7), 0.3, 0.2, "metal", seg=12, r2=0.08)
    _cyl(mb, M, (0, -1.05, 4.58), 0.12, 0.08, "lampshade", seg=10)


@prop("led_pole", "floor", (1.8, 0.4, 7.0), eras=NOW | FUT, rooms=("street", "plaza", "parking", "station", "dock"))
def led_pole(mb, x, y, z, rot, rng, era):
    """Modern street light: tall galvanised pole, flat LED head (future: glowing ring)."""
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 3.3), 0.09, 6.6, "metal2", seg=8, r2=0.06)
    if era in FUT:
        _cyl(mb, M, (0, 0, 6.7), 0.45, 0.06, "accent", seg=16)
        _cyl(mb, M, (0, 0, 6.65), 0.5, 0.04, "metal2", seg=16)
        return
    rod(mb, M, (0, 0, 6.5), (0, -1.5, 6.75), 0.05, "metal2")
    _box(mb, M, (0, -1.7, 6.75), (0.3, 0.7, 0.08), "metal2")
    _box(mb, M, (0, -1.7, 6.7), (0.22, 0.6, 0.02), "lampshade")
    if rng.random() < 0.5:                                                            # CCTV / sign
        _box(mb, M, (0.12, -0.15, 4.0), (0.12, 0.3, 0.12), "paper")


@prop("cctv_camera", "wall", (0.3, 0.5, 0.3), eras=EIGHTIES | NOW | FUT | COLD, rooms=("street", "station", "parking", "construction", "checkpoint"))
def cctv_camera(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    zz = 3.0 if z < 0.5 else 0.0
    _box(mb, M, (0, 0.05, zz), (0.12, 0.1, 0.12), "metal2")
    rod(mb, M, (0, 0.05, zz), (0, -0.15, zz - 0.1), 0.025, "metal2")
    rbox(mb, M, (0, -0.3, zz - 0.15), (0.16, 0.38, 0.16), "paper", rx=-0.35)
    cylx(mb, M, (0, -0.5, zz - 0.22), 0.05, 0.03, "dark", seg=10, axis="Y")


@prop("billboard", "floor", (6.0, 0.8, 6.5), eras=MODERNISH, rooms=("street", "parking", "construction"))
def billboard(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for sx in (-1.8, 1.8):
        _box(mb, M, (sx, 0.2, 2.0), (0.2, 0.2, 4.0), "metal2" if era not in INTER else "wood2")
    face = "screen" if era in FUT else rng.choice(("accent", "paper", "wall2"))
    _box(mb, M, (0, 0.1, 5.0), (6.0, 0.15, 2.8), "trim")
    _box(mb, M, (0, 0.0, 5.0), (5.7, 0.05, 2.5), face)
    for i in range(rng.randint(2, 4)):                                                # big painted shapes + a slogan
        mb.sphere(M @ Vector((rng.uniform(-2, 2), -0.05, rng.uniform(4.4, 5.6))), rng.uniform(0.4, 0.8),
                  rng.choice(("fabric", "paper", "glass2", "dark")), sub=1, squash=1.0)
    for k in range(rng.randint(3, 6)):
        _box(mb, M, (-2.4 + k * 0.6, -0.04, 4.0), (0.4, 0.02, 0.25), "dark")
    _box(mb, M, (0, -0.4, 3.55), (6.0, 0.6, 0.06), "metal2")                           # catwalk
    for k in range(3):
        _box(mb, M, (-2 + k * 2, -0.55, 3.75), (0.1, 0.25, 0.25), "dark")              # flood lamps


@prop("awning", "wall", (2.4, 1.2, 0.6), eras=ALL, rooms=("street", "market", "plaza", "dock"))
def awning(mb, x, y, z, rot, rng, era):
    """Striped canvas awning on a shopfront (wall prop; hangs at ~2.6 m)."""
    M = M_at(x, y, z, rot)
    zz = 2.6 if z < 0.5 else 0.0
    n = 8
    for k in range(n):
        rbox(mb, M, (-1.2 + 2.4 * (k + 0.5) / n, -0.55, zz), (2.4 / n + 0.005, 1.2, 0.04), "fabric" if k % 2 else "paper", rx=-0.38)
    for k in range(n):                                                                # scalloped valance
        _box(mb, M, (-1.2 + 2.4 * (k + 0.5) / n, -1.1, zz - 0.32), (2.4 / n - 0.03, 0.03, 0.18), "fabric" if k % 2 else "paper")
    for sx in (-1.2, 1.2):
        rod(mb, M, (sx, 0, zz + 0.2), (sx, -1.1, zz - 0.22), 0.02, "metal2")


@prop("market_crates", "floor", (1.4, 0.9, 1.0), eras=ALL, rooms=("street", "market", "dock", "plaza"))
def market_crates(mb, x, y, z, rot, rng, era):
    """Stacked open produce crates, fruit and veg spilling over."""
    M = M_at(x, y, z, rot)
    for i in range(rng.randint(2, 4)):
        cx = -0.4 + (i % 2) * 0.75
        cz = 0.17 + (i // 2) * 0.36
        _box(mb, M, (cx, 0, cz), (0.65, 0.45, 0.32), "wood")
        _box(mb, M, (cx, -0.23, cz + 0.05), (0.6, 0.02, 0.06), "wood2")
        if i // 2 == 0 or i == 3:
            k = rng.choice(("fabric", "accent", "leaf", "glass2", "lampshade"))
            for j in range(5):
                mb.sphere(M @ Vector((cx + rng.uniform(-0.22, 0.22), rng.uniform(-0.14, 0.14), cz + 0.18)), 0.07, k, sub=1)


@prop("market_stall", "floor", (2.4, 1.6, 2.6), eras=ALL, rooms=("market", "street", "plaza", "forum"))
def market_stall(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 0.45), (2.2, 1.1, 0.9), "wood")
    for sx in (-1.05, 1.05):
        for sy in (-0.5, 0.5):
            _box(mb, M, (sx, sy, 1.25), (0.07, 0.07, 2.5), "wood2")
    tbox(mb, M, (0, 0, 2.5), (2.5, 1.6, 0.25), "fabric" if rng.random() < 0.5 else "fabric2", top=(0.4, 1.0))
    for i in range(rng.randint(6, 12)):
        mb.sphere(M @ Vector((rng.uniform(-0.9, 0.9), rng.uniform(-0.4, 0.4), 0.98)), rng.uniform(0.07, 0.14),
                  rng.choice(("accent", "fabric", "leaf", "glass2", "paper")), sub=1)


@prop("street_clock", "floor", (0.7, 0.4, 4.0), eras=STEAM | INTER, rooms=("street", "plaza", "station"))
def street_clock(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.3), 0.2, 0.6, "dark", seg=10)
    _cyl(mb, M, (0, 0, 1.8), 0.08, 2.6, "dark", seg=8)
    cylx(mb, M, (0, 0, 3.4), 0.36, 0.22, "dark", seg=16, axis="Y")
    for sy in (-0.115, 0.115):
        cylx(mb, M, (0, sy, 3.4), 0.3, 0.02, "paper", seg=16, axis="Y")
    _box(mb, M, (0.06, -0.13, 3.47), (0.03, 0.01, 0.18), "dark")
    _box(mb, M, (-0.06, -0.13, 3.38), (0.14, 0.01, 0.03), "dark")


@prop("fountain", "floor", (4.0, 4.0, 2.6), eras=ALL, rooms=("plaza", "forum", "street"))
def fountain(mb, x, y, z, rot, rng, era):
    """Round basin with a central column and a top bowl (water in glass)."""
    M = M_at(x, y, z, rot)
    st = "stone" if era not in FUT else "metal"
    _cyl(mb, M, (0, 0, 0.3), 1.9, 0.6, st, seg=20)
    _cyl(mb, M, (0, 0, 0.62), 1.95, 0.08, "trim" if era in FUT else st, seg=20)
    _cyl(mb, M, (0, 0, 0.55), 1.7, 0.04, "glass", seg=20)
    _cyl(mb, M, (0, 0, 1.1), 0.25, 1.1, st, seg=10)
    _cyl(mb, M, (0, 0, 1.75), 0.8, 0.2, st, seg=14, r2=0.3)
    _cyl(mb, M, (0, 0, 1.86), 0.7, 0.03, "glass", seg=14)
    _cyl(mb, M, (0, 0, 2.15), 0.12, 0.6, st, seg=8, r2=0.05)
    for k in range(6):                                                                # spouts of water
        a = k / 6 * math.tau
        rod(mb, M, (math.cos(a) * 0.6, math.sin(a) * 0.6, 1.84), (math.cos(a) * 1.3, math.sin(a) * 1.3, 0.6), 0.03, "glass", seg=4)


@prop("monument", "floor", (2.0, 2.0, 6.0), eras=ALL, rooms=("plaza", "forum"))
def monument(mb, x, y, z, rot, rng, era):
    """Stepped plinth with an obelisk / column / (future) a floating ring."""
    M = M_at(x, y, z, rot)
    st = "stone"
    _box(mb, M, (0, 0, 0.2), (2.4, 2.4, 0.4), st)
    _box(mb, M, (0, 0, 0.6), (1.8, 1.8, 0.4), st)
    _box(mb, M, (0, 0, 1.4), (1.2, 1.2, 1.2), st)
    _box(mb, M, (0, -0.61, 1.4), (0.8, 0.02, 0.5), "metal")                              # plaque
    if era in FUT:
        _cyl(mb, M, (0, 0, 3.0), 0.12, 2.0, "metal", seg=8)
        cylx(mb, M, (0, 0, 4.5), 1.0, 0.1, "accent", seg=20, axis="Y")
    elif era in ANC | PREIND and rng.random() < 0.6:
        _cyl(mb, M, (0, 0, 3.8), 0.32, 3.6, st, seg=12)                                  # column
        _box(mb, M, (0, 0, 5.7), (0.9, 0.9, 0.2), st)
    else:
        tbox(mb, M, (0, 0, 4.0), (0.8, 0.8, 4.0), st, top=(0.55, 0.55))                  # obelisk
        tbox(mb, M, (0, 0, 6.2), (0.44, 0.44, 0.4), st, top=(0.02, 0.02))


@prop("street_tree", "floor", (2.4, 2.4, 6.0), eras=ALL, rooms=("street", "plaza", "parking"))
def street_tree(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 0.03), (1.2, 1.2, 0.06), "metal2" if era in MODERNISH else "stone")
    h = rng.uniform(3.0, 4.2)
    _cyl(mb, M, (0, 0, h / 2), 0.13, h, "wood2", seg=8, r2=0.09)
    for k in range(rng.randint(4, 7)):
        a = rng.uniform(0, math.tau)
        mb.sphere(M @ Vector((math.cos(a) * rng.uniform(0.3, 0.9), math.sin(a) * rng.uniform(0.3, 0.9), h + rng.uniform(-0.4, 0.9))),
                  rng.uniform(0.7, 1.1), "leaf", sub=1, squash=0.85)
    if era in STEAM | MID:
        for k in range(6):                                                            # iron tree guard
            a = k / 6 * math.tau
            rod(mb, M, (math.cos(a) * 0.35, math.sin(a) * 0.35, 0), (math.cos(a) * 0.3, math.sin(a) * 0.3, 1.5), 0.015, "dark", seg=4)


@prop("bike_rack", "floor", (2.0, 0.6, 0.9), eras=NOW | FUT, rooms=("street", "station", "parking"))
def bike_rack(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for k in range(4):
        xx = -0.75 + k * 0.5
        rod(mb, M, (xx, -0.25, 0), (xx, -0.25, 0.8), 0.025, "metal2")
        rod(mb, M, (xx, 0.25, 0), (xx, 0.25, 0.8), 0.025, "metal2")
        rod(mb, M, (xx, -0.25, 0.8), (xx, 0.25, 0.8), 0.025, "metal2")


@prop("vending_machine", "floor", (1.0, 0.8, 1.9), eras=COLD | NOW | FUT, rooms=("street", "station", "parking", "space"))
def vending_machine(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("fabric", "accent", "wall2", "paper"))
    _box(mb, M, (0, 0, 0.95), (0.95, 0.75, 1.9), k)
    _box(mb, M, (-0.12, -0.38, 1.15), (0.6, 0.02, 1.2), "glass" if era not in FUT else "screen")
    for i in range(3):
        for j in range(4):
            _box(mb, M, (-0.3 + i * 0.18, -0.39, 0.7 + j * 0.28), (0.1, 0.02, 0.16), rng.choice(("fabric", "accent", "paper", "glass2")))
    _box(mb, M, (0.32, -0.38, 1.3), (0.18, 0.02, 0.4), "dark")
    _box(mb, M, (-0.12, -0.39, 0.3), (0.5, 0.03, 0.15), "dark")
    _box(mb, M, (0, -0.39, 1.8), (0.85, 0.02, 0.12), "lampshade")


@prop("advertising_column", "floor", (1.2, 1.2, 3.4), eras=STEAM | INTER | COLD, rooms=("street", "plaza", "station"))
def advertising_column(mb, x, y, z, rot, rng, era):
    """Morris column: round pillar plastered with posters, little domed cap."""
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.12), 0.62, 0.24, "dark", seg=16)
    _cyl(mb, M, (0, 0, 1.5), 0.55, 2.6, "wall2", seg=16)
    for k in range(7):                                                                # posters
        a = k / 7 * math.tau + rng.uniform(-0.1, 0.1)
        rbox(mb, M, (math.cos(a) * 0.56, math.sin(a) * 0.56, rng.uniform(1.0, 2.0)), (0.02, 0.4, rng.uniform(0.5, 0.9)),
             rng.choice(("paper", "accent", "fabric", "glass2")), rz=a)
    _cyl(mb, M, (0, 0, 2.86), 0.65, 0.12, "dark", seg=16)
    _cyl(mb, M, (0, 0, 3.05), 0.55, 0.3, "dark", seg=16, r2=0.15)
    _cyl(mb, M, (0, 0, 3.3), 0.05, 0.2, "dark", seg=6)


@prop("telegraph_pole", "floor", (2.0, 0.4, 8.0), eras=STEAM | MID | {"modern", "analog_digital", "post_apocalyptic"}, rooms=("street", "rail", "farm"))
def telegraph_pole(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 3.9), 0.12, 7.8, "wood2", seg=8, r2=0.09)
    for zz, w in ((7.3, 1.8), (6.8, 1.3)):
        _box(mb, M, (0, -0.12, zz), (w, 0.1, 0.1), "wood2")
        for k in range(4):
            _cyl(mb, M, (-w / 2 + 0.1 + k * (w - 0.2) / 3, -0.12, zz + 0.1), 0.035, 0.12, "glass", seg=6)
    if era in MID | NOW and rng.random() < 0.6:
        cylx(mb, M, (0.25, 0.15, 6.0), 0.22, 0.6, "metal2", seg=10, axis="Z")          # transformer


@prop("hitching_post", "floor", (2.2, 0.3, 1.1), eras=PREIND | STEAM, rooms=("street", "saloon"))
def hitching_post(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for sx in (-1.0, 1.0):
        _box(mb, M, (sx, 0, 0.5), (0.12, 0.12, 1.0), "wood2")
    _box(mb, M, (0, 0, 0.98), (2.2, 0.1, 0.1), "wood2")


@prop("water_trough", "floor", (2.0, 0.7, 0.7), eras=ANC | MED | PREIND | STEAM, rooms=("street", "saloon", "farm", "market"))
def water_trough(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = "stone" if era in ANC | MED else "wood"
    _box(mb, M, (0, 0, 0.25), (1.9, 0.6, 0.5), k)
    _box(mb, M, (0, 0, 0.48), (1.75, 0.45, 0.04), "glass")
    for sx in (-0.95, 0.95):
        _box(mb, M, (sx, 0, 0.3), (0.06, 0.66, 0.6), "wood2" if k == "wood" else k)


@prop("well", "floor", (2.0, 2.0, 2.8), eras=ANC | MED | PREIND, rooms=("street", "plaza", "farm", "forum"))
def well(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.4), 0.8, 0.8, "stone", seg=14)
    _cyl(mb, M, (0, 0, 0.78), 0.62, 0.04, "dark", seg=14)
    for sx in (-0.75, 0.75):
        _box(mb, M, (sx, 0, 1.4), (0.12, 0.12, 1.4), "wood2")
    cylx(mb, M, (0, 0, 1.75), 0.08, 1.6, "wood2", seg=8)
    tbox(mb, M, (0, 0, 2.3), (1.8, 1.5, 0.5), "wood", top=(1.0, 0.05))
    _cyl(mb, M, (0, 0, 1.2), 0.15, 0.22, "wood", seg=8)
    rod(mb, M, (0, 0, 1.31), (0, 0, 1.72), 0.01, "fabric2", seg=4)


@prop("lantern_string", "hanging", (6.0, 0.4, 0.6), eras=ALL, rooms=("street", "market", "plaza", "canal"))
def lantern_string(mb, x, y, z, rot, rng, era):
    """Paper lanterns / bulbs strung on a sagging line (hanging prop, z = the line height)."""
    M = M_at(x, y, z, rot)
    n = 8
    pts = [(-3 + 6 * k / n, 0, -0.5 * math.sin(math.pi * k / n)) for k in range(n + 1)]
    for a, b in zip(pts, pts[1:]):
        rod(mb, M, a, b, 0.01, "dark", seg=4)
    for p in pts[1:-1]:
        if era in OLD | INTER:
            _cyl(mb, M, (p[0], 0, p[2] - 0.2), 0.12, 0.26, "lampshade", seg=8)
            _cyl(mb, M, (p[0], 0, p[2] - 0.05), 0.06, 0.04, "dark", seg=8)
        else:
            mb.sphere(M @ Vector((p[0], 0, p[2] - 0.08)), 0.05, "lampshade", sub=1)


@prop("vertical_sign", "wall", (0.5, 0.15, 2.4), eras=ALL, rooms=("street", "market"))
def vertical_sign(mb, x, y, z, rot, rng, era):
    """Tall blade sign with stacked glyph strokes (kanji-like for East-Asian cultures, used by features)."""
    M = M_at(x, y, z, rot)
    zz = 3.2 if z < 0.5 else 0.0
    k = "signcol" if era in FUT | EIGHTIES else rng.choice(("paper", "fabric", "accent", "wood"))
    _box(mb, M, (0, -0.3, zz), (0.08, 0.5, 2.2), k)
    _box(mb, M, (0, -0.06, zz + 1.0), (0.05, 0.5, 0.05), "metal2")
    _box(mb, M, (0, -0.06, zz - 1.0), (0.05, 0.5, 0.05), "metal2")
    glyphs(mb, M, (0, -0.3, zz), 2.0, 0.35, rng, axis="X")


def glyphs(mb, M, c, h, w, rng, n=4, axis="X", key="dark"):
    """Stacked square glyphs made of short horizontal / vertical / slanted strokes (kanji-like)."""
    cx, cy, cz = c
    cell = h / n
    for i in range(n):
        gz = cz + h / 2 - cell * (i + 0.5)
        for s in range(rng.randint(3, 5)):
            kind = rng.random()
            u = rng.uniform(-w * 0.35, w * 0.35)
            v = rng.uniform(-cell * 0.3, cell * 0.3)
            if kind < 0.45:
                su, sv = rng.uniform(w * 0.3, w * 0.8), cell * 0.07
            elif kind < 0.85:
                su, sv = w * 0.07, rng.uniform(cell * 0.3, cell * 0.75)
            else:
                su, sv = w * 0.07, cell * 0.5
            rx = rng.uniform(-0.6, 0.6) if kind >= 0.85 else 0.0
            if axis == "X":                                                           # sign plane is YZ, viewed from -X/+X
                for sxs in (-1, 1):
                    rbox(mb, M, (cx + sxs * 0.045, cy + u, gz + v), (0.01, su, sv), key, rx=rx)
            else:                                                                     # sign plane is XZ, viewed from -Y
                rbox(mb, M, (cx + u, cy - 0.03, gz + v), (su, 0.01, sv), key, ry=rx)


@prop("noren_shopfront", "wall", (2.4, 0.4, 2.6), eras=ALL, rooms=("street", "market"))
def noren_shopfront(mb, x, y, z, rot, rng, era):
    """Japanese shop entrance: split noren curtain under a tiled hood, paper lantern, name board."""
    M = M_at(x, y, z, rot)
    for k in range(4):
        _box(mb, M, (-0.75 + k * 0.5, -0.12, 1.85), (0.46, 0.02, 0.7), "fabric" if k % 2 == 0 else "fabric2")
    _box(mb, M, (0, -0.12, 2.22), (2.1, 0.05, 0.05), "wood2")
    tbox(mb, M, (0, -0.35, 2.55), (2.6, 0.8, 0.15), "dark", top=(1.0, 0.4), shift=(0, 0.2))
    _box(mb, M, (0, -0.05, 2.95), (1.6, 0.06, 0.4), "wood")
    glyphs(mb, M, (0, -0.1, 2.95), 0.36, 1.4, rng, n=1, axis="Y")
    _cyl(mb, M, (1.15, -0.4, 1.7), 0.18, 0.5, "lampshade", seg=10)
    _cyl(mb, M, (1.15, -0.4, 1.98), 0.1, 0.06, "dark", seg=8)


# ============================================================================= construction
@prop("scaffolding", "floor", (3.2, 1.4, 6.5), eras=ALL, rooms=("construction", "street"))
def scaffolding(mb, x, y, z, rot, rng, era):
    """Two-bay, three-lift scaffold: standards, ledgers, diagonal braces, plank decks, a ladder."""
    M = M_at(x, y, z, rot)
    k = "wood2" if era in OLD else "metal2"
    r = 0.05 if era in OLD else 0.03
    H, W, D = 6.0, 3.0, 1.2
    for sx in (-W / 2, 0, W / 2):
        for sy in (-D / 2, D / 2):
            rod(mb, M, (sx, sy, 0), (sx, sy, H), r, k)
    for lz in (2.0, 4.0, 6.0):
        for sy in (-D / 2, D / 2):
            rod(mb, M, (-W / 2, sy, lz), (W / 2, sy, lz), r, k)
        for sx in (-W / 2, 0, W / 2):
            rod(mb, M, (sx, -D / 2, lz), (sx, D / 2, lz), r, k)
        _box(mb, M, (0, 0, lz + 0.04), (W, D - 0.1, 0.05), "wood")
        _box(mb, M, (0, -D / 2, lz + 0.15), (W, 0.03, 0.2), "wood2")                   # toe board
    rod(mb, M, (-W / 2, -D / 2, 0), (0, -D / 2, 2.0), r, k)
    rod(mb, M, (0, -D / 2, 2.0), (W / 2, -D / 2, 4.0), r, k)
    rod(mb, M, (W / 2, -D / 2, 4.0), (0, -D / 2, 6.0), r, k)
    for sx in (-0.15, 0.15):                                                          # ladder
        rod(mb, M, (W / 2 - 0.4 + sx, 0, 0), (W / 2 - 0.4 + sx, 0.1, 2.0), 0.02, "wood2")
    for j in range(6):
        _box(mb, M, (W / 2 - 0.4, 0.02, 0.3 + j * 0.3), (0.3, 0.03, 0.03), "wood2")
    if era in NOW | FUT and rng.random() < 0.6:                                       # debris netting
        _box(mb, M, (0, -D / 2 - 0.05, 4.5), (W, 0.01, 3.0), "glass")


@prop("traffic_cone", "floor", (0.4, 0.4, 0.75), eras=COLD | NOW | FUT, rooms=("construction", "street", "parking"))
def traffic_cone(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 0.02), (0.4, 0.4, 0.04), "accent" if era not in FUT else "dark")
    _cyl(mb, M, (0, 0, 0.37), 0.15, 0.66, "accent", seg=10, r2=0.025)
    _cyl(mb, M, (0, 0, 0.38), 0.105, 0.1, "paper", seg=10, r2=0.088)


@prop("road_barrier", "floor", (2.0, 0.6, 1.1), eras=INTER | COLD | NOW | FUT, rooms=("construction", "street", "checkpoint"))
def road_barrier(mb, x, y, z, rot, rng, era):
    """A-frame barrier with a red/white striped plank and a warning lamp."""
    M = M_at(x, y, z, rot)
    for sx in (-0.9, 0.9):
        rod(mb, M, (sx, -0.25, 0), (sx, 0, 1.0), 0.03, "metal2")
        rod(mb, M, (sx, 0.25, 0), (sx, 0, 1.0), 0.03, "metal2")
    n = 6
    for k in range(n):
        _box(mb, M, (-0.95 + 1.9 * (k + 0.5) / n, -0.02, 0.85), (1.9 / n, 0.04, 0.22), "fabric" if k % 2 else "paper")
    _cyl(mb, M, (0.85, -0.02, 1.08), 0.07, 0.12, "lampshade", seg=8)


@prop("jersey_barrier", "floor", (2.0, 0.6, 0.85), eras=NOW | FUT | COLD, rooms=("construction", "street", "checkpoint", "parking"))
def jersey_barrier(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    tbox(mb, M, (0, 0, 0.15), (2.0, 0.6, 0.3), "stone", top=(1.0, 0.55))
    tbox(mb, M, (0, 0, 0.55), (2.0, 0.33, 0.5), "stone", top=(1.0, 0.7))
    if rng.random() < 0.5:
        _box(mb, M, (0, -0.15, 0.55), (0.6, 0.02, 0.15), "accent")


@prop("cement_mixer", "floor", (1.4, 1.6, 1.6), eras=INTER | COLD | NOW, rooms=("construction",))
def cement_mixer(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 0.45), (0.9, 1.2, 0.1), "metal2")
    for sx in (-0.5, 0.5):
        cylx(mb, M, (sx, 0.3, 0.25), 0.25, 0.12, "dark", seg=12)
    _box(mb, M, (0, -0.65, 0.3), (0.08, 0.08, 0.6), "metal2")
    _box(mb, M, (0, 0.35, 0.7), (0.5, 0.4, 0.4), "metal2")                              # motor
    drum = acc(era)
    vs = mb.cyl((0, 0, 0), 0.45, 0.8, drum, seg=12, r2=0.2)
    from mathutils import Matrix
    import bmesh
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation((0, -0.15, 1.05)) @ Matrix.Rotation(-0.9, 4, "X"), verts=vs)
    vs = mb.cyl((0, 0, 0), 0.45, 0.35, drum, seg=12, r2=0.3)
    bmesh.ops.transform(mb.bm, matrix=M @ Matrix.Translation((0, 0.12, 0.88)) @ Matrix.Rotation(math.pi - 0.9, 4, "X"), verts=vs)
    rod(mb, M, (0.3, 0.1, 0.5), (0.3, -0.3, 1.3), 0.03, "metal2")


@prop("pallet", "floor", (1.2, 1.0, 0.9), eras=COLD | NOW | FUT, rooms=("construction", "dock", "storage", "factory"))
def pallet(mb, x, y, z, rot, rng, era):
    """Wooden pallet loaded with shrink-wrapped boxes / sacks / bricks."""
    M = M_at(x, y, z, rot)
    for k in range(5):
        _box(mb, M, (-0.5 + k * 0.25, 0, 0.13), (0.12, 1.0, 0.025), "wood")
    for sy in (-0.42, 0, 0.42):
        _box(mb, M, (0, sy, 0.06), (1.2, 0.1, 0.1), "wood2")
    load = rng.random()
    if load < 0.4:
        for i in range(rng.randint(2, 4)):
            _box(mb, M, (rng.uniform(-0.2, 0.2), rng.uniform(-0.15, 0.15), 0.32 + i * 0.36), (0.9, 0.75, 0.34), "paper" if i % 2 else "wood2")
    elif load < 0.7:
        for i in range(3):
            for j in range(2):
                mb.sphere(M @ Vector((-0.3 + j * 0.6, -0.2 + (i % 2) * 0.4, 0.3 + i * 0.2)), 0.27, "fabric2", sub=1, squash=0.45)
    else:
        for i in range(4):
            _box(mb, M, (0, 0, 0.26 + i * 0.14), (1.0, 0.8, 0.13), "fabric" if i % 2 else "accent")


@prop("rebar_bundle", "floor", (3.0, 0.6, 0.4), eras=COLD | NOW | FUT, rooms=("construction",))
def rebar_bundle(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for sx in (-1.2, 1.2):
        _box(mb, M, (sx, 0, 0.06), (0.12, 0.6, 0.12), "wood2")
    for i in range(14):
        cylx(mb, M, (rng.uniform(-0.1, 0.1), -0.22 + (i % 7) * 0.075, 0.16 + (i // 7) * 0.06), 0.015, 3.0, "fabric2", seg=5)


@prop("portable_toilet", "floor", (1.2, 1.2, 2.4), eras=NOW | FUT | {"cold_war"}, rooms=("construction", "parking"))
def portable_toilet(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("leaf", "wall2", "accent"))
    _box(mb, M, (0, 0, 0.05), (1.15, 1.15, 0.1), "dark")
    _box(mb, M, (0, 0, 1.15), (1.1, 1.1, 2.1), k)
    _box(mb, M, (0, -0.56, 1.1), (0.85, 0.02, 1.9), k)
    _box(mb, M, (0.3, -0.58, 1.15), (0.06, 0.03, 0.2), "dark")
    _box(mb, M, (0, -0.57, 1.9), (0.3, 0.02, 0.12), "paper")
    tbox(mb, M, (0, 0, 2.3), (1.15, 1.15, 0.15), "paper", top=(0.85, 0.85))


@prop("excavator", "floor", (3.2, 7.5, 4.5), eras=COLD | NOW | FUT, rooms=("construction",))
def excavator(mb, x, y, z, rot, rng, era):
    """Blocky tracked excavator: tracks, slewing cab, boom + stick + bucket (landmark)."""
    M = M_at(x, y, z, rot)
    k = acc(era)
    for sx in (-1.15, 1.15):
        _box(mb, M, (sx, 0.6, 0.45), (0.7, 4.2, 0.9), "dark")
        for k2 in range(9):
            _box(mb, M, (sx * 1.01, -1.4 + k2 * 0.5, 0.45), (0.72, 0.08, 0.92), "metal2")
    _box(mb, M, (0, 0.6, 1.05), (1.4, 1.4, 0.3), "dark")
    _box(mb, M, (0, 1.0, 1.75), (2.8, 3.0, 1.1), k)                                    # upper body
    _box(mb, M, (0, 2.3, 1.8), (2.6, 0.5, 1.0), "metal2")                              # counterweight
    _box(mb, M, (-0.75, -0.1, 2.85), (1.1, 1.2, 1.3), k)                               # cab
    _box(mb, M, (-0.75, -0.71, 2.95), (0.95, 0.02, 1.0), "glass")
    _box(mb, M, (-1.31, -0.1, 2.95), (0.02, 1.0, 0.9), "glass")
    _cyl(mb, M, (0.9, 1.8, 2.7), 0.08, 0.8, "dark", seg=6)                             # exhaust
    b0, b1, b2 = (0.45, -0.3, 2.0), (0.45, -3.0, 4.3), (0.45, -4.6, 1.6)
    for a, b, w in ((b0, b1, 0.45), (b1, b2, 0.32)):
        d = Vector(b) - Vector(a)
        ang = math.atan2(d.z, -d.y)
        rbox(mb, M, (Vector(a) + Vector(b)) / 2, (w, d.length, w), k, rx=-ang)
    rod(mb, M, (0.45, -0.8, 2.6), (0.45, -2.6, 4.0), 0.07, "metal")                    # ram
    tbox(mb, M, (0.45, -4.75, 1.1), (0.9, 0.8, 0.8), "metal2", top=(1.0, 0.4), shift=(0, 0.25))
    for i in range(4):
        _box(mb, M, (0.1 + i * 0.23, -5.1, 0.72), (0.08, 0.15, 0.12), "metal2")


@prop("tower_crane", "floor", (4.0, 30.0, 32.0), eras=COLD | NOW | FUT, rooms=("construction", "dock"))
def tower_crane(mb, x, y, z, rot, rng, era):
    """Lattice tower crane: mast, slewing unit + cab, jib with hook, counter-jib with weights."""
    M = M_at(x, y, z, rot)
    k = acc(era) if era not in FUT else "paper"
    H = 26.0
    _box(mb, M, (0, 0, 0.5), (4.0, 4.0, 1.0), "stone")
    s = 0.9
    for sx in (-s, s):
        for sy in (-s, s):
            rod(mb, M, (sx, sy, 1.0), (sx, sy, H), 0.08, k)
    for j in range(int((H - 1) / 2.5)):
        z0, z1 = 1.0 + j * 2.5, 1.0 + (j + 1) * 2.5
        for a, b in (((-s, -s), (s, -s)), ((s, -s), (s, s)), ((s, s), (-s, s)), ((-s, s), (-s, -s))):
            rod(mb, M, (a[0], a[1], z0), (b[0], b[1], z1), 0.04, k, seg=4)
    _box(mb, M, (0, 0, H + 0.6), (2.2, 2.2, 1.2), k)
    _box(mb, M, (1.4, -1.0, H + 0.4), (1.0, 1.2, 1.2), "paper")                         # cab
    _box(mb, M, (1.4, -1.61, H + 0.5), (0.9, 0.02, 0.8), "glass")
    tbox(mb, M, (0, 0, H + 3.0), (1.0, 1.0, 3.6), k, top=(0.1, 0.1))                   # apex
    J = 24.0
    for sx in (-0.5, 0.5):                                                            # jib (triangular lattice)
        rod(mb, M, (sx, -0.5, H + 1.2), (sx, -J, H + 1.2), 0.07, k)
    rod(mb, M, (0, -0.5, H + 2.3), (0, -J, H + 1.6), 0.07, k)
    for j in range(int(J / 2)):
        y0, y1 = -0.5 - j * 2, -0.5 - (j + 1) * 2
        for sx in (-0.5, 0.5):
            rod(mb, M, (sx, y0, H + 1.2), (0, y1, H + 2.3 - 0.7 * (j + 1) / (J / 2)), 0.035, k, seg=4)
    rod(mb, M, (0, 0, H + 4.8), (0, -J * 0.6, H + 2.0), 0.03, "metal2", seg=4)        # tie bar
    rod(mb, M, (0, 0, H + 4.8), (0, 8.0, H + 1.6), 0.03, "metal2", seg=4)
    _box(mb, M, (0, 4.5, H + 1.2), (1.2, 8.0, 0.35), k)                                # counter-jib
    _box(mb, M, (0, 7.6, H + 0.3), (1.6, 1.6, 1.8), "stone")
    hy = -J * rng.uniform(0.45, 0.85)
    hz = rng.uniform(4.0, H - 6.0)
    _box(mb, M, (0, hy, H + 0.95), (1.0, 1.2, 0.3), "metal2")                          # trolley
    rod(mb, M, (0, hy, H + 0.8), (0, hy, hz + 0.5), 0.015, "dark", seg=4)
    _box(mb, M, (0, hy, hz + 0.3), (0.5, 0.3, 0.5), "accent")
    rod(mb, M, (0, hy, hz), (0, hy - 0.15, hz - 0.5), 0.04, "dark", seg=4)


@prop("brick_pile", "floor", (1.2, 1.0, 0.8), eras=ALL, rooms=("construction", "street"))
def brick_pile(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for layer in range(rng.randint(3, 6)):
        for i in range(4):
            for j in range(3):
                if layer > 3 and rng.random() < 0.4:
                    continue
                rbox(mb, M, (-0.36 + i * 0.24, -0.28 + j * 0.28, 0.04 + layer * 0.08), (0.22, 0.1, 0.07),
                     "fabric" if era not in FUT else "stone", rz=(layer % 2) * math.pi / 2 + rng.uniform(-0.05, 0.05))


@prop("sandbags", "floor", (2.0, 0.8, 0.9), eras=MED | PREIND | STEAM | MID | NOW | FUT, rooms=("construction", "checkpoint", "dock", "street"))
def sandbags(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for layer in range(3):
        for i in range(5 - layer):
            mb.sphere(M @ Vector((-0.8 + (i + layer * 0.5) * 0.4, rng.uniform(-0.04, 0.04), 0.13 + layer * 0.24)), 0.24,
                      "fabric2", sub=1, squash=0.55)


@prop("dumpster", "floor", (2.0, 1.4, 1.4), eras=COLD | NOW | FUT, rooms=("construction", "street", "parking"))
def dumpster(mb, x, y, z, rot, rng, era):
    """Builder's skip: tapered steel box with lifting lugs, overflowing rubble."""
    M = M_at(x, y, z, rot)
    tbox(mb, M, (0, 0, 0.55), (2.6, 1.4, 1.0), body_key(rng, era, ("accent", "leaf", "wall2")), top=(1.25, 1.1))
    for sx in (-1.45, 1.45):
        cylx(mb, M, (sx, 0, 0.75), 0.1, 0.12, "metal2", seg=8)
    for i in range(8):
        mb.sphere(M @ Vector((rng.uniform(-1.1, 1.1), rng.uniform(-0.5, 0.5), 1.05)), rng.uniform(0.15, 0.32),
                  rng.choice(("stone", "wood2", "fabric2", "paper")), sub=1, squash=0.6)


@prop("lumber_stack", "floor", (3.0, 1.0, 0.8), eras=ALL, rooms=("construction", "dock", "street"))
def lumber_stack(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for layer in range(rng.randint(3, 6)):
        for i in range(5):
            rbox(mb, M, (rng.uniform(-0.08, 0.08), -0.4 + i * 0.2, 0.06 + layer * 0.12), (3.0, 0.18, 0.1), "wood", rz=rng.uniform(-0.02, 0.02))
    for sx in (-1.2, 0, 1.2):
        _box(mb, M, (sx, 0, 0.0), (0.1, 1.0, 0.04), "wood2")


@prop("site_hoarding", "floor", (6.0, 0.3, 2.4), eras=STEAM | MID | NOW | FUT, rooms=("construction", "street"))
def site_hoarding(mb, x, y, z, rot, rng, era):
    """Plywood / mesh site fence with posters and a DANGER board."""
    M = M_at(x, y, z, rot)
    mesh = era in NOW | FUT and rng.random() < 0.5
    for k in range(4):
        _box(mb, M, (-3 + 1.5 * (k + 0.5), 0, 1.15), (1.48, 0.04 if not mesh else 0.02, 2.2), "wood" if not mesh else "glass")
        _box(mb, M, (-3 + 1.5 * k, 0.05, 1.15), (0.08, 0.08, 2.3), "wood2" if not mesh else "metal2")
        if mesh:
            _box(mb, M, (-3 + 1.5 * k, 0.05, 0.08), (0.5, 0.2, 0.16), "stone")
    for i in range(rng.randint(1, 3)):
        _box(mb, M, (rng.uniform(-2.4, 2.4), -0.04, rng.uniform(1.0, 1.6)), (0.6, 0.02, 0.85), rng.choice(("paper", "accent", "fabric")))
    _box(mb, M, (1.6, -0.045, 1.8), (0.8, 0.02, 0.5), "lampshade")
    _box(mb, M, (1.6, -0.05, 1.8), (0.6, 0.01, 0.12), "fabric")


@prop("generator", "floor", (1.4, 0.8, 1.0), eras=COLD | NOW | FUT, rooms=("construction", "dock", "street"))
def generator(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 0.5), (1.4, 0.8, 0.85), body_key(rng, era, ("accent", "leaf", "wall2")))
    for k in range(6):
        _box(mb, M, (-0.5 + k * 0.2, -0.41, 0.6), (0.1, 0.02, 0.45), "dark")
    _cyl(mb, M, (0.5, 0.2, 1.05), 0.06, 0.25, "dark", seg=6)
    for sx in (-0.5, 0.5):
        cylx(mb, M, (sx, 0, 0.06), 0.06, 0.8, "dark", seg=6, axis="Y")


@prop("site_cabin", "floor", (6.0, 2.5, 2.8), eras=COLD | NOW | FUT, rooms=("construction", "dock", "parking"))
def site_cabin(mb, x, y, z, rot, rng, era):
    """Portakabin office: corrugated box on blocks, window, door, steps."""
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("paper", "wall2", "accent"))
    for sx in (-2.6, 2.6):
        _box(mb, M, (sx, 0, 0.15), (0.4, 2.2, 0.3), "stone")
    _box(mb, M, (0, 0, 1.55), (6.0, 2.4, 2.5), k)
    for i in range(14):
        _box(mb, M, (-2.8 + i * 0.43, -1.21, 1.55), (0.05, 0.02, 2.4), "trim")
    _box(mb, M, (-1.2, -1.23, 1.8), (1.6, 0.03, 0.9), "glass")
    _box(mb, M, (1.6, -1.23, 1.35), (0.9, 0.03, 2.0), "dark")
    _box(mb, M, (1.6, -1.6, 0.25), (1.0, 0.7, 0.5), "metal2")


# ============================================================================= rail / transit parts
@prop("train_seats", "floor", (1.4, 1.9, 1.3), eras=RAIL, rooms=("rail", "carriage", "station"))
def train_seats(mb, x, y, z, rot, rng, era):
    """Facing seat pair (bay of four): two double seats facing each other + a little table."""
    M = M_at(x, y, z, rot)
    fab = "fabric" if era not in OLD else "fabric2"
    frame = "wood" if era in OLD else "metal2" if era in NOW else "metal" if era in FUT else "wood2"
    for s in (-1, 1):
        _box(mb, M, (0, s * 0.75, 0.25), (1.3, 0.5, 0.5), frame)
        _box(mb, M, (0, s * 0.72, 0.53), (1.3, 0.52, 0.12), fab)
        tbox(mb, M, (0, s * 0.97, 0.95), (1.3, 0.14, 0.8), fab, top=(1.0, 0.8))
        if era not in FUT:
            for sx in (-0.33, 0.33):                                                   # head rests
                _box(mb, M, (sx, s * 0.97, 1.32), (0.44, 0.16, 0.14), "paper" if era in MID | NOW else fab)
    _box(mb, M, (0.2, 0, 0.75), (0.75, 0.5, 0.04), "wood" if era not in FUT else "metal2")
    _box(mb, M, (0.55, 0, 0.4), (0.05, 0.06, 0.7), "metal2")
    return [(Vector((x, y, z + 0.78)), 0.2)]


@prop("bus_seats", "floor", (1.1, 0.7, 1.15), eras=MODERNISH, rooms=("carriage", "bus", "station"))
def bus_seats(mb, x, y, z, rot, rng, era):
    """Forward-facing double seat (front at -Y) with a grab handle on the back."""
    M = M_at(x, y, z, rot)
    fab = rng.choice(("fabric", "fabric2"))
    _box(mb, M, (0, 0, 0.22), (0.9, 0.3, 0.44), "metal2")
    _box(mb, M, (0, -0.05, 0.5), (1.0, 0.48, 0.12), fab)
    tbox(mb, M, (0, 0.22, 0.85), (1.0, 0.12, 0.62), fab, top=(0.96, 0.8))
    rod(mb, M, (-0.45, 0.28, 1.12), (0.45, 0.28, 1.12), 0.02, "metal")


@prop("luggage_rack", "wall", (2.0, 0.5, 0.3), eras=RAIL, rooms=("rail", "carriage", "bus"))
def luggage_rack(mb, x, y, z, rot, rng, era):
    """Overhead rack (wall prop at ~2.0 m): brackets, rails / net, a couple of bags."""
    M = M_at(x, y, z, rot)
    zz = 2.0 if z < 0.5 else 0.0
    k = "metal" if era not in OLD else "metal"
    for sx in (-0.9, 0, 0.9):
        _box(mb, M, (sx, -0.2, zz), (0.04, 0.45, 0.04), k)
        rod(mb, M, (sx, 0.0, zz - 0.3), (sx, -0.3, zz), 0.015, k, seg=4)
    for k2 in range(4):
        rod(mb, M, (-1, -0.05 - k2 * 0.11, zz + 0.02), (1, -0.05 - k2 * 0.11, zz + 0.02), 0.012, "metal2" if era in OLD else k, seg=4)
    for i in range(rng.randint(0, 3)):
        _box(mb, M, (rng.uniform(-0.7, 0.7), -0.2, zz + 0.16), (rng.uniform(0.35, 0.6), 0.32, rng.uniform(0.2, 0.3)),
             rng.choice(("fabric2", "wood2", "dark", "accent")))


@prop("train_door", "wall", (1.4, 0.2, 2.2), eras=RAIL, rooms=("rail", "carriage", "station"))
def train_door(mb, x, y, z, rot, rng, era):
    """Sliding double door (modern) / panelled door with drop window (old)."""
    M = M_at(x, y, z, rot)
    if era in OLD | INTER:
        _box(mb, M, (0, 0, 1.05), (0.75, 0.06, 2.1), "wood2")
        _box(mb, M, (0, -0.035, 1.55), (0.5, 0.02, 0.55), "glass")
        _box(mb, M, (0, -0.04, 0.7), (0.5, 0.02, 0.6), "wood")
        cylx(mb, M, (0.28, -0.07, 1.1), 0.03, 0.06, "metal", axis="Y")
        return
    for sx in (-0.33, 0.33):
        _box(mb, M, (sx, 0, 1.05), (0.64, 0.06, 2.1), "metal2" if era in NOW else "metal")
        _box(mb, M, (sx, -0.035, 1.4), (0.42, 0.02, 0.9), "glass")
    _box(mb, M, (0, -0.04, 1.05), (0.02, 0.03, 2.1), "dark")
    _box(mb, M, (0, -0.05, 2.2), (1.4, 0.06, 0.12), "accent" if era in FUT else "metal2")
    _box(mb, M, (0.75, -0.04, 1.3), (0.1, 0.03, 0.14), "accent")                         # door button


@prop("ticket_barrier", "floor", (1.8, 1.2, 1.1), eras=COLD | NOW | FUT, rooms=("station", "rail"))
def ticket_barrier(mb, x, y, z, rot, rng, era):
    """Ticket gate: two cabinets with paddles (or a turnstile for the cold war)."""
    M = M_at(x, y, z, rot)
    for sx in (-0.6, 0.6):
        tbox(mb, M, (sx, 0, 0.5), (0.3, 1.2, 1.0), "metal2" if era not in FUT else "metal", top=(1.0, 0.9))
        _box(mb, M, (sx, -0.45, 1.01), (0.25, 0.2, 0.02), "screen" if era in FUT else "accent")
    if era in COLD:
        for k in range(3):
            a = k / 3 * math.tau
            rod(mb, M, (-0.45, 0, 0.9), (-0.45 + math.cos(a) * 0.5, math.sin(a) * 0.3, 0.9 - 0.2), 0.025, "metal")
    else:
        for sx in (-0.3, 0.3):
            _box(mb, M, (sx, 0.05, 0.75), (0.32, 0.03, 0.45), "fabric" if era in NOW else "accent")


@prop("platform_bench", "floor", (2.2, 0.7, 1.0), eras=RAIL, rooms=("station", "rail"))
def platform_bench(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    if era in FUT:
        tbox(mb, M, (0, 0, 0.22), (2.0, 0.5, 0.44), "metal", top=(0.9, 0.8))
        _box(mb, M, (0, 0, 0.47), (2.1, 0.55, 0.06), "trim")
        _box(mb, M, (0, 0, 0.02), (1.8, 0.4, 0.04), "accent")
        return
    k = "wood" if era not in NOW else "metal2"
    for sx in (-0.95, 0, 0.95):
        _box(mb, M, (sx, 0.02, 0.24), (0.07, 0.5, 0.48), "dark")
        _box(mb, M, (sx, 0.26, 0.72), (0.06, 0.05, 0.5), "dark")
    for kk in range(4):
        _box(mb, M, (0, -0.2 + kk * 0.13, 0.48), (2.2, 0.1, 0.04), k)
    for kk in range(2):
        _box(mb, M, (0, 0.28, 0.66 + kk * 0.16), (2.2, 0.04, 0.12), k)


@prop("departure_board", "hanging", (2.6, 0.3, 1.2), eras=RAIL, rooms=("station", "rail"))
def departure_board(mb, x, y, z, rot, rng, era):
    """Hanging board (z = ceiling hook height): painted slats / split flaps / LED / holo."""
    M = M_at(x, y, z, rot)
    zz = -1.0
    for sx in (-1.0, 1.0):
        rod(mb, M, (sx, 0, 0), (sx, 0, zz + 0.5), 0.015, "metal2", seg=4)
    if era in FUT:
        _box(mb, M, (0, 0, zz), (2.6, 0.06, 1.0), "metal2")
        _box(mb, M, (0, -0.035, zz), (2.4, 0.01, 0.85), "screen")
        for r in range(4):
            _box(mb, M, (-0.4, -0.045, zz + 0.3 - r * 0.2), (1.2, 0.01, 0.06), "accent")
        return
    face = "dark" if era in COLD | NOW else "wood"
    _box(mb, M, (0, 0, zz), (2.6, 0.12, 1.0), "trim")
    _box(mb, M, (0, -0.065, zz), (2.45, 0.01, 0.88), face)
    ink = "lampshade" if era in COLD | NOW else "paper"
    for r in range(5):
        for c in range(rng.randint(4, 9)):
            _box(mb, M, (-1.1 + c * 0.14, -0.075, zz + 0.32 - r * 0.16), (0.1, 0.01, 0.1), ink)
        _box(mb, M, (0.9, -0.075, zz + 0.32 - r * 0.16), (0.4, 0.01, 0.1), ink)
    if era in OLD | INTER:
        cylx(mb, M, (0, -0.05, zz + 0.75), 0.28, 0.1, "paper", seg=14, axis="Y")       # clock on top
        cylx(mb, M, (0, -0.02, zz + 0.75), 0.31, 0.06, "trim", seg=14, axis="Y")


@prop("track_section", "floor", (3.0, 6.0, 0.3), eras=RAIL, rooms=("rail", "station"))
def track_section(mb, x, y, z, rot, rng, era):
    """6 m of railway: ballast bed, sleepers, two rails (gauge 1.435 m)."""
    M = M_at(x, y, z, rot)
    track(mb, M, 0, 6.0, era, rng)


def track(mb, M, y0, L, era, rng, ballast=True):
    """Rails along local Y from y0 to y0+L (sleepers every 0.65 m)."""
    if ballast:
        tbox(mb, M, (0, y0 + L / 2, 0.08), (3.2, L, 0.16), "stone", top=(0.85, 1.0))
    sk = "wood2" if era not in NOW | FUT else "stone"
    for k in range(int(L / 0.65)):
        rbox(mb, M, (rng.uniform(-0.03, 0.03), y0 + 0.3 + k * 0.65, 0.2), (2.5, 0.24, 0.12), sk, rz=rng.uniform(-0.03, 0.03))
    for sx in (-0.72, 0.72):
        _box(mb, M, (sx, y0 + L / 2, 0.32), (0.07, L, 0.12), "metal")
        _box(mb, M, (sx, y0 + L / 2, 0.27), (0.14, L, 0.03), "metal2")


@prop("sleepers_stack", "floor", (2.6, 1.2, 0.8), eras=RAIL, rooms=("rail", "construction", "station"))
def sleepers_stack(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for layer in range(rng.randint(3, 5)):
        for i in range(4):
            if layer % 2 == 0:
                rbox(mb, M, (0, -0.45 + i * 0.3, 0.07 + layer * 0.15), (2.5, 0.24, 0.14), "wood2", rz=rng.uniform(-0.03, 0.03))
            else:
                rbox(mb, M, (-1.0 + i * 0.66, 0, 0.07 + layer * 0.15), (0.24, 1.2, 0.14), "wood2", rz=rng.uniform(-0.03, 0.03))


@prop("buffer_stop", "floor", (3.0, 1.4, 1.6), eras=RAIL, rooms=("rail", "station"))
def buffer_stop(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0.3, 0.6), (2.6, 0.6, 1.2), "fabric" if era not in OLD else "wood2")
    for sx in (-0.85, 0.85):
        cylx(mb, M, (sx, -0.15, 1.0), 0.12, 0.5, "dark", seg=10, axis="Y")
        cylx(mb, M, (sx, -0.42, 1.0), 0.22, 0.05, "metal", seg=12, axis="Y")
    rod(mb, M, (-1.2, 0.5, 0), (-0.8, 0.0, 1.2), 0.06, "dark")
    rod(mb, M, (1.2, 0.5, 0), (0.8, 0.0, 1.2), 0.06, "dark")
    _cyl(mb, M, (0, 0.3, 1.32), 0.1, 0.2, "fabric", seg=8)


@prop("rail_signal", "floor", (0.8, 0.5, 5.0), eras=RAIL, rooms=("rail", "station"))
def rail_signal(mb, x, y, z, rot, rng, era):
    """Semaphore arm on a lattice post (steam/interwar) or a colour-light head (later)."""
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 2.3), 0.08, 4.6, "dark" if era in OLD | INTER else "metal2", seg=8)
    if era in OLD | INTER:
        rbox(mb, M, (0.6, -0.1, 4.2), (1.2, 0.04, 0.2), "fabric", ry=-0.6 if rng.random() < 0.5 else 0.0)
        _box(mb, M, (1.0, -0.12, 4.2), (0.12, 0.02, 0.22), "paper")
        cylx(mb, M, (0.15, -0.12, 4.0), 0.1, 0.06, "lampshade", seg=8, axis="Y")
        _box(mb, M, (0, 0, 4.7), (0.2, 0.2, 0.1), "dark")
    else:
        tbox(mb, M, (0, -0.1, 4.0), (0.4, 0.25, 1.0), "dark", top=(0.9, 0.9))
        for i, kk in enumerate(("fabric", "lampshade", "leaf")):
            cylx(mb, M, (0, -0.24, 4.3 - i * 0.28), 0.08, 0.03, kk, seg=10, axis="Y")


@prop("grab_pole", "floor", (0.2, 0.2, 2.3), eras=MODERNISH, rooms=("carriage", "bus"))
def grab_pole(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 1.15), 0.025, 2.3, "accent" if era in NOW else "metal", seg=8)


@prop("strap_rail", "hanging", (3.0, 0.2, 0.5), eras=INTER | COLD | NOW | FUT, rooms=("carriage", "bus"))
def strap_rail(mb, x, y, z, rot, rng, era):
    """Overhead grab rail with hanging straps (hanging prop, z = rail height)."""
    M = M_at(x, y, z, rot)
    rod(mb, M, (-1.5, 0, 0), (1.5, 0, 0), 0.02, "metal")
    for k in range(6):
        sx = -1.25 + k * 0.5
        _box(mb, M, (sx, 0, -0.14), (0.02, 0.03, 0.26), "dark" if era in INTER | COLD else "paper")
        cylx(mb, M, (sx, 0, -0.32), 0.06, 0.02, "dark" if era in INTER | COLD else "accent", seg=8)


@prop("suitcase_pile", "floor", (1.0, 0.7, 1.0), eras=PREIND | STEAM | MID | NOW | FUT, rooms=("station", "rail", "carriage", "dock", "ship", "space"))
def suitcase_pile(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    zz = 0.0
    for i in range(rng.randint(2, 4)):
        w, d, h = rng.uniform(0.5, 0.8), rng.uniform(0.3, 0.45), rng.uniform(0.18, 0.28)
        k = rng.choice(("wood2", "fabric2", "dark", "accent", "fabric")) if era not in FUT else rng.choice(("metal", "accent", "trim"))
        rbox(mb, M, (rng.uniform(-0.05, 0.05), 0, zz + h / 2), (w, d, h), k, rz=rng.uniform(-0.3, 0.3))
        _box(mb, M, (0, 0, zz + h + 0.02), (0.15, 0.03, 0.04), "dark")
        zz += h
    if era in OLD | INTER and rng.random() < 0.5:                                    # hat box
        _cyl(mb, M, (0.1, 0, zz + 0.12), 0.18, 0.24, "paper", seg=10)


@prop("steamer_trunk", "floor", (1.0, 0.6, 0.7), eras=PREIND | STEAM | INTER, rooms=("station", "rail", "carriage", "dock", "ship"))
def steamer_trunk(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = rng.choice(("wood", "fabric2", "dark"))
    _box(mb, M, (0, 0, 0.3), (0.95, 0.55, 0.6), k)
    cylx(mb, M, (0, 0, 0.6), 0.27, 0.95, k, seg=10, axis="X")
    for sx in (-0.3, 0.3):
        _box(mb, M, (sx, 0, 0.45), (0.06, 0.57, 0.9), "wood2")
    _box(mb, M, (0, -0.28, 0.55), (0.1, 0.03, 0.1), "metal")


@prop("ticket_machine", "floor", (0.8, 0.6, 1.8), eras=COLD | NOW | FUT, rooms=("station", "rail", "parking"))
def ticket_machine(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("accent", "wall2", "metal"))
    tbox(mb, M, (0, 0, 0.85), (0.75, 0.55, 1.7), k, top=(1.0, 0.85), shift=(0, 0.04))
    rbox(mb, M, (0, -0.24, 1.3), (0.5, 0.02, 0.4), "screen", rx=0.25)
    _box(mb, M, (0, -0.28, 0.95), (0.4, 0.06, 0.15), "dark")
    _box(mb, M, (0, -0.28, 0.45), (0.3, 0.04, 0.12), "dark")
    _box(mb, M, (0, -0.25, 1.65), (0.7, 0.02, 0.12), "paper")


@prop("station_sign", "hanging", (2.6, 0.2, 0.7), eras=RAIL, rooms=("station", "rail"))
def station_sign(mb, x, y, z, rot, rng, era):
    """Name board / roundel (hanging, z = hook height)."""
    M = M_at(x, y, z, rot)
    for sx in (-0.9, 0.9):
        rod(mb, M, (sx, 0, 0), (sx, 0, -0.5), 0.015, "metal2", seg=4)
    if era in INTER | COLD and rng.random() < 0.7:                                   # roundel
        cylx(mb, M, (0, 0, -0.85), 0.42, 0.06, "fabric", seg=18, axis="Y")
        cylx(mb, M, (0, 0, -0.85), 0.28, 0.07, "paper", seg=18, axis="Y")
        _box(mb, M, (0, 0, -0.85), (1.3, 0.08, 0.2), "accent")
        for k in range(5):
            _box(mb, M, (-0.45 + k * 0.22, -0.045, -0.85), (0.12, 0.01, 0.1), "paper")
        return
    _box(mb, M, (0, 0, -0.8), (2.4, 0.06, 0.55), "trim" if era in OLD else "accent")
    _box(mb, M, (0, -0.035, -0.8), (2.25, 0.01, 0.42), "paper")
    for k in range(rng.randint(5, 9)):
        _box(mb, M, (-0.9 + k * 0.22, -0.045, -0.8), (0.13, 0.01, 0.2), "dark")


# ============================================================================= maritime
@prop("mooring_bollard", "floor", (0.6, 0.6, 0.8), eras=ALL, rooms=("dock", "ship", "canal"))
def mooring_bollard(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    if era in ANC | MED:
        _cyl(mb, M, (0, 0, 0.45), 0.18, 0.9, "wood2", seg=8)
        return
    _cyl(mb, M, (0, 0, 0.05), 0.32, 0.1, "dark", seg=12)
    _cyl(mb, M, (0, 0, 0.38), 0.2, 0.6, "dark", seg=12, r2=0.17)
    _cyl(mb, M, (0, 0, 0.72), 0.27, 0.1, "dark", seg=12)


@prop("rope_coil", "floor", (0.8, 0.8, 0.25), eras=ALL, rooms=("dock", "ship", "canal"))
def rope_coil(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for k in range(4):
        r = 0.36 - k * 0.07
        n = 12
        for i in range(n):
            a = i / n * math.tau
            rbox(mb, M, (math.cos(a) * r, math.sin(a) * r, 0.04 + k * 0.045), (0.07, r * math.tau / n * 1.15, 0.06), "paper" if era not in FUT else "accent", rz=a)


@prop("cargo_stack", "floor", (1.8, 1.4, 1.6), eras=ALL, rooms=("dock", "ship", "storage"))
def cargo_stack(mb, x, y, z, rot, rng, era):
    """Netted crates, bales and barrels heaped on the quay."""
    M = M_at(x, y, z, rot)
    for i in range(rng.randint(3, 6)):
        cx, cy = rng.uniform(-0.55, 0.55), rng.uniform(-0.35, 0.35)
        if rng.random() < 0.35 and era in OLD | MID:
            _cyl(mb, M, (cx, cy, 0.42), 0.27, 0.84, "wood", seg=12)
            _cyl(mb, M, (cx, cy, 0.2), 0.285, 0.05, "metal", seg=12)
            _cyl(mb, M, (cx, cy, 0.65), 0.285, 0.05, "metal", seg=12)
        else:
            s = rng.uniform(0.5, 0.75)
            zz = s / 2 + (0 if i < 3 else 0.6)
            rbox(mb, M, (cx, cy, zz), (s, s, s), rng.choice(("wood", "wood2", "fabric2", "paper")), rz=rng.uniform(-0.3, 0.3))
            _box(mb, M, (cx, cy - s / 2 - 0.01, zz), (s * 0.9, 0.02, 0.06), "trim")


@prop("life_ring", "wall", (0.8, 0.1, 0.8), eras=STEAM | MID | NOW | FUT, rooms=("dock", "ship", "canal"))
def life_ring(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    zz = 1.4 if z < 0.5 else 0.0
    n = 12
    for i in range(n):
        a = i / n * math.tau
        from mathutils import Matrix as _Mx
        rbox(mb, M @ _Mx.Rotation(math.pi / 2, 4, "Z"), (0, math.cos(a) * 0.3, zz + math.sin(a) * 0.3), (0.1, 0.17, 0.12),
             "fabric" if (i // 3) % 2 else "paper", rx=a + math.pi / 2)
    _box(mb, M, (0, 0.05, zz + 0.4), (0.06, 0.06, 0.12), "metal2")


@prop("lifeboat", "floor", (2.0, 6.5, 2.4), eras=STEAM | MID | NOW, rooms=("ship", "dock"))
def lifeboat(mb, x, y, z, rot, rng, era):
    """Lifeboat hung on two davits (floor prop: davits stand on the deck)."""
    M = M_at(x, y, z, rot)
    Mb = M @ Matrix.Translation((0, 0, 1.4))
    hull_shell(mb, Mb, 5.8, 1.8, 0.7, "paper" if era not in NOW else "accent", inner="wood", bow_lift=0.15, stern_w=0.35)
    if era in NOW:
        tbox(mb, Mb, (0, 0.3, 1.05), (1.7, 4.2, 0.7), "accent", top=(0.7, 0.85))
    for sy in (-2.6, 2.6):
        rod(mb, M, (0.9, sy, 0), (0.9, sy, 2.8), 0.06, "metal2")
        rod(mb, M, (0.9, sy, 2.8), (0.0, sy * 0.95, 3.0), 0.06, "metal2")
        rod(mb, M, (0.0, sy * 0.95, 3.0), (0, sy * 0.95, 1.95), 0.012, "dark", seg=4)


@prop("cargo_container", "floor", (2.5, 6.1, 2.6), eras=COLD | NOW | FUT, rooms=("dock", "ship", "construction", "storage"))
def cargo_container(mb, x, y, z, rot, rng, era):
    """20 ft shipping container: corrugated sides, corner castings, door end with locking bars."""
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("fabric", "accent", "wall2", "leaf", "trim", "metal"))
    _box(mb, M, (0, 0, 1.3), (2.44, 6.06, 2.59), k)
    for sx in (-1, 1):
        for i in range(24):
            _box(mb, M, (sx * 1.23, -2.9 + i * 0.25, 1.3), (0.03, 0.1, 2.4), k)
    for sx in (-1.17, 1.17):
        for sy in (-2.98, 2.98):
            for sz in (0.08, 2.52):
                _box(mb, M, (sx, sy, sz), (0.16, 0.16, 0.16), "dark")
    for sx in (-0.85, -0.35, 0.35, 0.85):                                            # door locking bars
        _box(mb, M, (sx, -3.04, 1.3), (0.05, 0.04, 2.4), "metal2")
    _box(mb, M, (0, -3.04, 1.3), (0.02, 0.03, 2.4), "dark")
    for k2 in range(3):
        _box(mb, M, (1.24, -1.5 + k2 * 0.3, 2.1), (0.01, 0.2, 0.25), "paper")


@prop("mast", "floor", (4.0, 1.0, 14.0), eras=ANC | MED | PREIND | STEAM, rooms=("ship", "dock"))
def mast(mb, x, y, z, rot, rng, era):
    """Wooden mast with yards, furled sails, a crow's nest and shrouds."""
    M = M_at(x, y, z, rot)
    H = 13.0
    _cyl(mb, M, (0, 0, H / 2), 0.2, H, "wood", seg=10, r2=0.12)
    for zz, w in ((H * 0.42, 7.0), (H * 0.7, 5.4), (H * 0.92, 3.6)):
        cylx(mb, M, (0, 0.25, zz), 0.08, w, "wood2", seg=8)
        cylx(mb, M, (0, 0.25, zz - 0.15), 0.18, w * 0.9, "paper", seg=8)                 # furled sail bundle
        if era in ANC | MED and zz < H * 0.5:
            tbox(mb, M, (0, 0.35, zz - 2.2), (w * 0.95, 0.08, 4.2), "paper", top=(1.0, 1.0))
    _cyl(mb, M, (0, 0, H * 0.78), 0.65, 0.5, "wood2", seg=12)                          # crow's nest
    for sx in (-1, 1):
        for k in range(4):
            rod(mb, M, (sx * 1.7, -0.6 + k * 0.4, 0.2), (sx * 0.2, 0, H * 0.75), 0.02, "dark", seg=4)
        for j in range(6):
            zj = 1.2 + j * 1.3
            f = zj / (H * 0.75)
            rod(mb, M, (sx * (1.7 - 1.5 * f), -0.6 + 0.6 * f, zj), (sx * (1.7 - 1.5 * f), 0.6 - 0.6 * f, zj), 0.012, "dark", seg=4)
    _box(mb, M, (0, 0, H + 0.4), (0.04, 0.6, 0.4), "fabric")                             # pennant


@prop("ship_wheel", "floor", (1.4, 0.8, 1.9), eras=PREIND | STEAM | INTER, rooms=("ship",))
def ship_wheel(mb, x, y, z, rot, rng, era):
    """Helm: spoked wheel with handles on a pedestal."""
    M = M_at(x, y, z, rot)
    tbox(mb, M, (0, 0.2, 0.55), (0.5, 0.5, 1.1), "wood2", top=(0.7, 0.7))
    from mathutils import Matrix as _Mx
    Mw = M @ _Mx.Translation((0, -0.1, 1.25)) @ _Mx.Rotation(math.pi / 2, 4, "Z")
    _ring(mb, Mw, (0, 0, 0), 0.5, 0.06, "wood", n=16)
    for i in range(8):
        a = i / 8 * math.tau
        rbox(mb, Mw, (0, math.cos(a) * 0.4, math.sin(a) * 0.4), (0.04, 0.04, 0.8), "wood", rx=a + math.pi / 2)
        rbox(mb, Mw, (0, math.cos(a) * 0.62, math.sin(a) * 0.62), (0.045, 0.045, 0.2), "wood2", rx=a + math.pi / 2)
    cylx(mb, Mw, (0, 0, 0), 0.1, 0.12, "metal", seg=10)


@prop("cannon", "floor", (1.2, 2.6, 1.0), eras=MED | PREIND | STEAM, rooms=("ship", "dock", "fort"))
def cannon(mb, x, y, z, rot, rng, era):
    """Naval gun on a truck carriage, muzzle at -Y."""
    M = M_at(x, y, z, rot)
    for sx in (-0.38, 0.38):
        tbox(mb, M, (sx, 0.3, 0.35), (0.12, 1.2, 0.5), "wood2", top=(1.0, 0.7), shift=(0, 0.2))
        for sy in (-0.2, 0.7):
            cylx(mb, M, (sx * 1.15, sy, 0.16), 0.16, 0.1, "wood2", seg=10)
    _box(mb, M, (0, 0.3, 0.15), (0.7, 1.1, 0.1), "wood2")
    cylx(mb, M, (0, -0.25, 0.65), 0.2, 2.2, "dark", seg=12, axis="Y", r2=0.15)
    cylx(mb, M, (0, -1.32, 0.65), 0.19, 0.12, "dark", seg=12, axis="Y")
    cylx(mb, M, (0, 0.88, 0.65), 0.12, 0.2, "dark", seg=10, axis="Y")
    for i in range(3):
        mb.sphere(M @ Vector((0.7 + (i % 2) * 0.2, 0.6 + i * 0.15, 0.1)), 0.1, "dark", sub=1)


@prop("anchor", "floor", (1.4, 0.4, 2.0), eras=ALL, rooms=("dock", "ship", "beach"))
def anchor(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = "dark"
    _box(mb, M, (0, 0, 1.0), (0.12, 0.12, 1.7), k)
    _box(mb, M, (0, 0, 1.75), (0.9, 0.1, 0.1), "wood2" if era in OLD else k)          # stock
    cylx(mb, M, (0, 0, 1.95), 0.12, 0.04, k, seg=10, axis="Y")
    n = 8
    for i in range(n + 1):
        a = math.pi + i / n * math.pi
        rbox(mb, M, (math.cos(a) * 0.6, 0, 0.75 + math.sin(a) * 0.6), (0.24, 0.1, 0.1), k, ry=-a + math.pi / 2)
    for sx in (-1, 1):
        tbox(mb, M, (sx * 0.62, 0, 0.85), (0.25, 0.08, 0.3), k, top=(0.1, 1.0), shift=(sx * 0.1, 0))


@prop("capstan", "floor", (1.6, 1.6, 1.1), eras=MED | PREIND | STEAM, rooms=("ship", "dock"))
def capstan(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.1), 0.55, 0.2, "wood2", seg=12)
    _cyl(mb, M, (0, 0, 0.55), 0.3, 0.7, "wood", seg=10, r2=0.38)
    _cyl(mb, M, (0, 0, 0.95), 0.42, 0.15, "wood2", seg=12)
    for i in range(4):
        a = i / 4 * math.pi
        rbox(mb, M, (0, 0, 0.95), (1.6, 0.06, 0.06), "wood", rz=a)


@prop("buoy", "floor", (1.0, 1.0, 2.0), eras=STEAM | MID | NOW | FUT, rooms=("dock", "ship", "canal"))
def buoy(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = body_key(rng, era, ("fabric", "leaf", "accent"))
    _cyl(mb, M, (0, 0, 0.35), 0.5, 0.7, k, seg=12, r2=0.35)
    _cyl(mb, M, (0, 0, 1.1), 0.12, 0.8, k, seg=8)
    for sx in (-1, 1):
        rod(mb, M, (sx * 0.3, 0, 0.7), (0, 0, 1.6), 0.03, k)
    _cyl(mb, M, (0, 0, 1.65), 0.1, 0.2, "lampshade", seg=8)
    _cyl(mb, M, (0, 0, 0.36), 0.51, 0.08, "paper", seg=12)


@prop("deck_vent", "floor", (0.8, 0.8, 2.0), eras=STEAM | MID | NOW, rooms=("ship",))
def deck_vent(mb, x, y, z, rot, rng, era):
    """Cowl ventilator: tall pipe with a flared mouth turned toward -Y."""
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0, 0.8), 0.15, 1.6, "paper", seg=10)
    cylx(mb, M, (0, -0.15, 1.75), 0.32, 0.45, "paper", seg=12, axis="Y", r2=0.16)
    cylx(mb, M, (0, -0.38, 1.75), 0.27, 0.02, "dark", seg=12, axis="Y")


@prop("fishing_nets", "floor", (1.6, 1.2, 0.5), eras=ALL, rooms=("dock", "ship", "beach"))
def fishing_nets(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for i in range(4):
        mb.sphere(M @ Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3), 0.15)), rng.uniform(0.3, 0.45), "leaf" if i % 2 else "fabric2", sub=1, squash=0.35)
    for i in range(5):
        mb.sphere(M @ Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.4, 0.4), 0.3)), 0.07, "accent", sub=1)       # floats


@prop("lobster_pots", "floor", (1.4, 0.8, 1.0), eras=PREIND | STEAM | MID | NOW, rooms=("dock", "beach"))
def lobster_pots(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for i in range(rng.randint(2, 4)):
        px, pz = -0.4 + (i % 2) * 0.75, 0.25 + (i // 2) * 0.5
        _box(mb, M, (px, 0, pz - 0.23), (0.7, 0.5, 0.04), "wood2")
        cylx(mb, M, (px, 0, pz - 0.05), 0.25, 0.7, "glass", seg=8, r2=None)
        for k in range(3):
            cylx(mb, M, (px - 0.3 + k * 0.3, 0, pz - 0.05), 0.26, 0.02, "wood2", seg=8)


# ============================================================================= space transit
@prop("hull_ribs", "floor", (4.0, 0.6, 3.6), eras=FUT | {"cold_war"}, rooms=("space",))
def hull_ribs(mb, x, y, z, rot, rng, era):
    """Structural ring frame of a corridor (an arch of segments across X)."""
    M = M_at(x, y, z, rot)
    n = 9
    for i in range(n):
        a0, a1 = math.pi * i / n, math.pi * (i + 1) / n
        p0 = Vector((math.cos(a0) * 1.9, 0, 0.2 + math.sin(a0) * 2.9))
        p1 = Vector((math.cos(a1) * 1.9, 0, 0.2 + math.sin(a1) * 2.9))
        d = p1 - p0
        rbox(mb, M, (p0 + p1) / 2, (d.length + 0.06, 0.3, 0.22), "metal2", ry=-math.atan2(d.z, d.x))
    for sx in (-1.9, 1.9):
        _box(mb, M, (sx, 0, 0.1), (0.3, 0.32, 0.2), "metal2")
    _box(mb, M, (0, -0.16, 3.08), (0.6, 0.02, 0.06), "accent")


@prop("conduits", "wall", (3.0, 0.4, 1.2), eras=FUT | COLD | NOW, rooms=("space", "factory", "lab", "carriage"))
def conduits(mb, x, y, z, rot, rng, era):
    """Bundle of pipes and cable trays along a wall (wall prop, runs along local X)."""
    M = M_at(x, y, z, rot)
    zz = 1.8 if z < 0.5 else 0.0
    for i in range(rng.randint(3, 5)):
        r = rng.uniform(0.04, 0.1)
        cylx(mb, M, (0, -0.1 - (i % 2) * 0.1, zz + i * 0.2), r, 3.0, rng.choice(("metal", "metal2", "accent", "fabric")) if i else "accent", seg=8)
    for sx in (-1.2, 0, 1.2):
        _box(mb, M, (sx, -0.06, zz + 0.4), (0.06, 0.16, 1.0), "dark")
    _box(mb, M, (0.6, -0.12, zz - 0.3), (0.4, 0.12, 0.3), "metal2")                      # junction box
    _box(mb, M, (0.6, -0.185, zz - 0.25), (0.1, 0.01, 0.06), "accent")


@prop("airlock_door", "wall", (2.4, 0.4, 2.8), eras=FUT | {"cold_war"}, rooms=("space",))
def airlock_door(mb, x, y, z, rot, rng, era):
    """Hexagonal pressure door with a striped frame, wheel lock and status lamp."""
    M = M_at(x, y, z, rot)
    from mathutils import Matrix as _Mx
    Mr = M @ _Mx.Translation((0, 0, 1.3)) @ _Mx.Rotation(math.pi / 2, 4, "X")
    for r, h, k, seg in ((1.25, 0.2, "metal2", 6), (1.05, 0.26, "metal", 6), (0.4, 0.34, "metal2", 12)):
        vs = mb.cyl((0, 0, 0), r, h, k, seg=seg)
        import bmesh
        bmesh.ops.transform(mb.bm, matrix=Mr @ _Mx.Rotation(math.pi / 6 if seg == 6 else 0, 4, "Z"), verts=vs)
    for i in range(10):                                                               # hazard stripes on the frame
        a = i / 10 * math.tau
        rbox(mb, M, (math.cos(a) * 1.15, -0.11, 1.3 + math.sin(a) * 1.15), (0.14, 0.02, 0.3), "accent" if i % 2 else "dark", ry=-a)
    _box(mb, M, (0, -0.15, 1.3), (1.9, 0.02, 0.06), "dark")                              # split seam
    _box(mb, M, (1.4, -0.08, 2.0), (0.2, 0.1, 0.3), "screen")


@prop("cockpit_seat", "floor", (0.9, 1.0, 1.5), eras=FUT | {"cold_war"}, rooms=("space", "cockpit"))
def cockpit_seat(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _cyl(mb, M, (0, 0.1, 0.2), 0.12, 0.4, "metal2", seg=8)
    _box(mb, M, (0, 0.1, 0.02), (0.6, 0.6, 0.04), "metal2")
    tbox(mb, M, (0, 0.0, 0.5), (0.65, 0.6, 0.18), "fabric", top=(0.95, 0.95))
    rbox(mb, M, (0, 0.33, 1.0), (0.62, 0.16, 0.95), "fabric", rx=0.18)
    _box(mb, M, (0, 0.42, 1.55), (0.36, 0.14, 0.22), "fabric")                         # head rest
    for sx in (-0.38, 0.38):
        _box(mb, M, (sx, 0.05, 0.72), (0.1, 0.5, 0.08), "metal2")
        _box(mb, M, (sx, -0.15, 0.78), (0.08, 0.1, 0.08), "accent")
    for sx in (-0.15, 0.15):                                                          # harness
        rbox(mb, M, (sx, 0.24, 1.0), (0.06, 0.02, 0.8), "accent", rx=0.18)


@prop("console", "floor", (1.6, 0.9, 1.3), eras=FUT | COLD | NOW, rooms=("space", "cockpit", "lab", "ship", "station"))
def console(mb, x, y, z, rot, rng, era):
    """Control desk: sloped panel with screens/dials, button rows, a raised display."""
    M = M_at(x, y, z, rot)
    tbox(mb, M, (0, 0.1, 0.45), (1.5, 0.7, 0.9), "metal2", top=(1.0, 0.75), shift=(0, 0.08))
    rbox(mb, M, (0, -0.05, 0.98), (1.45, 0.55, 0.06), "metal", rx=0.45)
    if era in COLD:
        for i in range(5):
            cylx(mb, M, (-0.55 + i * 0.27, -0.12, 1.0), 0.08, 0.03, "paper", seg=10, axis="Z")
        for i in range(8):
            _box(mb, M, (-0.6 + i * 0.17, 0.08, 1.12), (0.06, 0.04, 0.04), rng.choice(("fabric", "lampshade", "leaf")))
    else:
        for i in range(3):
            rbox(mb, M, (-0.45 + i * 0.45, -0.06, 1.01), (0.38, 0.28, 0.02), "screen", rx=0.45)
        for i in range(10):
            _box(mb, M, (-0.6 + i * 0.13, -0.27, 0.9), (0.07, 0.05, 0.03), rng.choice(("accent", "screen", "paper")))
    _box(mb, M, (0, 0.38, 1.3), (1.2, 0.06, 0.55), "metal2")
    _box(mb, M, (0, 0.345, 1.3), (1.1, 0.01, 0.45), "screen")


@prop("cargo_pod", "floor", (1.4, 1.4, 1.4), eras=FUT, rooms=("space", "dock", "storage"))
def cargo_pod(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    k = rng.choice(("paper", "metal", "trim"))
    _cyl(mb, M, (0, 0, 0.65), 0.62, 1.2, k, seg=8)
    for zz in (0.15, 1.15):
        _cyl(mb, M, (0, 0, zz), 0.66, 0.12, "metal2", seg=8)
    _box(mb, M, (0, -0.6, 0.65), (0.4, 0.06, 0.25), "accent")


@prop("space_locker", "wall", (1.6, 0.5, 2.0), eras=FUT, rooms=("space",))
def space_locker(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    for i in range(3):
        _box(mb, M, (-0.52 + i * 0.52, 0, 1.0), (0.5, 0.45, 1.95), "metal2")
        _box(mb, M, (-0.52 + i * 0.52, -0.23, 1.3), (0.3, 0.02, 0.06), "accent")
        _box(mb, M, (-0.52 + i * 0.52, -0.23, 1.7), (0.3, 0.02, 0.2), "screen" if i == 1 else "dark")


@prop("cryo_pod", "floor", (1.2, 2.4, 1.3), eras=FAR | {"cyberpunk", "near-future"}, rooms=("space", "lab"))
def cryo_pod(mb, x, y, z, rot, rng, era):
    M = M_at(x, y, z, rot)
    _box(mb, M, (0, 0, 0.3), (1.0, 2.2, 0.6), "metal2")
    cylx(mb, M, (0, 0, 0.62), 0.48, 2.0, "glass", seg=12, axis="Y")
    _box(mb, M, (0, 0, 0.62), (1.0, 2.05, 0.04), "metal")
    _box(mb, M, (0, -1.12, 0.5), (0.6, 0.04, 0.4), "screen")
    _box(mb, M, (0, 0, 0.05), (0.8, 2.0, 0.06), "accent")

"""Room kit: any interior from data (presets/settings.json entry + era + conditions).

Room spans x in [0, W], y in [0, D]; the camera stands near the FRONT wall (y = 0) looking toward the
back-left. Walls: front (y=0), back (y=D), left (x=0), right (x=W). Features are functions in FEATURES,
named by the setting's "features" list; each reserves wall spans / floor areas, adds geometry to a
MeshBuilder and registers focus points + surfaces for clutter."""
import math, random
import bpy
from mathutils import Vector
from .mb import MB
from . import props as P
from .. import core, shots
from ..ink import srgb

T = 0.15        # wall thickness
WIN_SILL, WIN_TOP = 0.95, 2.25


def _c(rgb):
    return srgb(*rgb) if isinstance(rgb, (list, tuple)) else rgb


def era_palette(era_def, mood, state):
    pal = {}
    for k, v in era_def["palette"].items():
        pal[k] = {"color": _c(v["color"]), "emission": _c(v["emission"]), "strength": v["strength"]} if isinstance(v, dict) else _c(v)
    def darker(c, f):
        c = c["color"] if isinstance(c, dict) else c
        return tuple(x * f for x in c)
    pal.setdefault("wood2", darker(pal["wood"], 0.72))
    pal.setdefault("metal2", darker(pal["metal"], 0.55))
    pal.setdefault("fabric2", darker(pal["fabric"], 0.8))
    pal.setdefault("paper", srgb(0.93, 0.90, 0.80))
    pal.setdefault("glass", srgb(0.45, 0.62, 0.58))
    pal.setdefault("glass2", srgb(0.62, 0.40, 0.16))
    pal.setdefault("leaf", srgb(0.36, 0.50, 0.30))
    pal.setdefault("rug", darker(pal["fabric"], 0.65))
    pal.setdefault("stone", srgb(0.55, 0.53, 0.50))
    pal.setdefault("dark", srgb(0.10, 0.10, 0.11))
    lit = mood in ("DUSK", "NIGHT") and not state.get("lights_off")
    lc = _c(era_def["light"]["color"])
    pal["flame"] = {"color": srgb(1.0, 0.78, 0.35), "emission": srgb(1.0, 0.70, 0.30), "strength": 3.0}
    pal["lampshade"] = {"color": lc, "emission": lc, "strength": 2.0} if lit else srgb(0.88, 0.84, 0.72)
    pal["screen"] = {"color": srgb(0.55, 0.85, 0.80), "emission": srgb(0.45, 0.85, 0.80), "strength": 1.5} if lit else srgb(0.20, 0.26, 0.28)
    sky = {"DAY": srgb(0.80, 0.88, 0.90), "GOLDEN": srgb(0.98, 0.84, 0.60), "DUSK": srgb(0.80, 0.52, 0.50), "NIGHT": srgb(0.12, 0.16, 0.26)}[mood]
    pal["sky"] = {"color": sky, "flat": True}
    pal["outside"] = {"color": srgb(0.10, 0.10, 0.12), "flat": True}
    pal["fire"] = {"color": srgb(1.0, 0.55, 0.15), "emission": srgb(1.0, 0.55, 0.15), "strength": 4.0}
    pal["fire2"] = {"color": srgb(1.0, 0.85, 0.35), "emission": srgb(1.0, 0.85, 0.35), "strength": 4.0}
    pal["water"] = srgb(0.30, 0.40, 0.42)
    return pal


class Room:
    def __init__(self, col, entry, layers, seed, mood):
        self.col, self.E, self.L, self.mood = col, entry, layers, mood
        self.rng = random.Random(f"room:{entry['_name']}:{seed}")
        self.era = layers.get("era") if layers.get("era") in core.load_preset("era") else entry["eras"][0]
        self.era_def = core.load_preset("era")[self.era]
        cond = core.load_preset("conditions")
        self.state = cond["state"].get(layers.get("state", "lived-in"), cond["state"]["lived-in"])
        self.weather = cond["weather"].get(layers.get("weather", "clear"), cond["weather"]["clear"])
        self.pal = era_palette(self.era_def, mood, self.state)
        r = self.rng
        self.W = r.uniform(*entry["w"])
        self.D = r.uniform(*entry["d"])
        self.H = r.uniform(*entry["h"])
        self.mb = {k: MB(f"PW_Room{k}") for k in ("Shell", "Trim", "Floor", "Furniture", "Props", "Glow")}
        self.used = {"back": [], "left": [], "right": [], "front": []}
        self.avoid = []                      # floor circles (x, y, r)
        self.surfaces = []
        self.focus = {}
        self.lamps = []                      # (pos, color, energy, radius)
        self.openings = {"back": [], "left": [], "right": [], "front": []}
        # keep the camera corner clear (front-right): nothing tall gets scattered in its face
        self.avoid += [(self.W - 0.9, 0.9, 1.9), (self.W - 2.2, 2.0, 1.3), (self.W - 3.4, 2.9, 1.0)]

    # ---------------------------------------------------------------- wall frames
    def wall(self, side):
        W, D = self.W, self.D
        return {"back": (Vector((0, D, 0)), Vector((1, 0, 0)), Vector((0, -1, 0)), W),
                "left": (Vector((0, 0, 0)), Vector((0, 1, 0)), Vector((1, 0, 0)), D),
                "right": (Vector((W, D, 0)), Vector((0, -1, 0)), Vector((-1, 0, 0)), D),
                "front": (Vector((W, 0, 0)), Vector((-1, 0, 0)), Vector((0, 1, 0)), W)}[side]

    def wp(self, side, u, z=0.0, inset=0.0):
        o, ud, n, _ = self.wall(side)
        return o + ud * u + n * inset + Vector((0, 0, z))

    def yaw(self, side):
        """Rotation so a prop's local -Y faces into the room from `side`'s wall."""
        _, _, n, _ = self.wall(side)
        return math.atan2(n.x, -n.y)

    def reserve(self, side, width, prefer=None, margin=0.3):
        """Find a free span of `width` on a wall (avoids openings + previous features)."""
        _, _, _, L = self.wall(side)
        taken = self.used[side] + [(a - 0.2, b + 0.2) for a, b in self.openings[side]]
        cands = []
        u = margin
        while u + width <= L - margin:
            if all(u + width <= a or u >= b for a, b in taken):
                cands.append(u)
            u += 0.1
        if not cands:
            return None
        u0 = min(cands, key=lambda c: abs(c - prefer)) if prefer is not None else self.rng.choice(cands)
        self.used[side].append((u0, u0 + width))
        return u0

    def add_focus(self, name, pos, size, view=None):
        if view is None:
            view = Vector((self.W * 0.75, self.D * 0.2, pos.z)) - pos
        view = Vector((view.x, view.y, 0))
        self.focus[name] = shots.focus_point(pos, view, size)

    # ---------------------------------------------------------------- shell
    def plan_openings(self):
        r = self.rng
        for side, n in self.E.get("windows", {}).items():
            _, _, _, L = self.wall(side)
            ww = 1.1 if self.era_def["window"] != "industrial" else 1.6
            for i in range(n):
                c = L * (i + 1) / (n + 1) + r.uniform(-0.2, 0.2)
                self.openings[side].append((c - ww / 2, c + ww / 2))
        ds = self.E.get("door", "front")
        _, _, _, L = self.wall(ds)
        u = r.uniform(0.8, L * 0.35) if ds != "front" else L * 0.25
        self.door = (ds, u, u + 1.0)
        self.openings[ds].append((u, u + 1.0))

    def shell(self):
        sh, tr, fl = self.mb["Shell"], self.mb["Trim"], self.mb["Floor"]
        W, D, H, r = self.W, self.D, self.H, self.rng
        pat = self.era_def["floor"]
        if pat == "checker":
            n = max(8, int(W / 0.5))
            fl.quad_grid(0, 0, W, D, n, int(D / W * n), lambda i, j: "floor_a" if (i + j) % 2 else "floor_b", jitter=0.03, rng=r)
        elif pat == "planks":
            n = int(W / 0.18)
            fl.quad_grid(0, 0, W, D, n, 3, lambda i, j: "floor_a" if (i * 7 + j * 3) % 5 else "floor_b", jitter=0.02, rng=r)
        elif pat == "stone":
            fl.quad_grid(0, 0, W, D, int(W / 0.7), int(D / 0.7), lambda i, j: r.choice(("floor_a", "floor_a", "floor_b")), jitter=0.12, rng=r)
        else:  # tiles
            fl.quad_grid(0, 0, W, D, int(W / 0.6), int(D / 0.6), lambda i, j: "floor_a" if (i + 2 * j) % 3 else "floor_b", jitter=0.01, rng=r)
        holes = self.state.get("holes")
        for side in ("back", "left", "right", "front"):
            o, ud, n, L = self.wall(side)
            cuts = sorted(self.openings[side])
            u = 0.0
            spans = []
            for a, b in cuts:
                spans.append((u, a, 0.0, H))
                lo = 0.0 if (side, a) == (self.door[0], self.door[1]) else WIN_SILL
                hi = 2.1 if lo == 0.0 else WIN_TOP
                if lo > 0:
                    spans.append((a, b, 0.0, lo))
                spans.append((a, b, hi, H))
                u = b
            spans.append((u, L, 0.0, H))
            for a, b, z0, z1 in spans:
                if b - a < 0.02 or z1 - z0 < 0.02:
                    continue
                if holes and z0 == 0.0 and z1 == H and b - a > 2.5 and r.random() < 0.35:
                    m = (a + b) / 2                       # ruined: a ragged gap in the wall
                    spans_ = [(a, m - 0.6, z0, z1), (m - 0.6, m + 0.6, z0, z0 + r.uniform(0.4, 1.2)), (m + 0.6, b, z0, z1)]
                else:
                    spans_ = [(a, b, z0, z1)]
                for a2, b2, za, zb in spans_:
                    c = o + ud * ((a2 + b2) / 2) - n * (T / 2) + Vector((0, 0, (za + zb) / 2))
                    size = Vector((abs(ud.x) * (b2 - a2) + abs(n.x) * T, abs(ud.y) * (b2 - a2) + abs(n.y) * T, zb - za))
                    sh.box(c, size, "wall")
                    if za == 0.0:                          # two-tone lower wall skin up to the rail
                        zt = min(zb, 1.0)
                        c2 = o + ud * ((a2 + b2) / 2) + n * 0.006 + Vector((0, 0, zt / 2))
                        sh.box(c2, Vector((abs(ud.x) * (b2 - a2) + abs(n.x) * 0.012, abs(ud.y) * (b2 - a2) + abs(n.y) * 0.012, zt)), "wall2")
            # trim: baseboard + crown + dado rail
            for z, hh in ((0.06, 0.12), (H - 0.06, 0.12), (1.0, 0.05)):
                c = o + ud * (L / 2) + n * 0.01 + Vector((0, 0, z))
                tr.box(c, Vector((abs(ud.x) * L + abs(n.x) * 0.04, abs(ud.y) * L + abs(n.y) * 0.04, hh)), "trim")
        # lower wall band (two-tone) as a thin skin up to the rail
        sh.box((W / 2, D / 2, H + 0.08), (W + 2 * T, D + 2 * T, 0.16), "ceiling")
        self.windows_and_door()

    def windows_and_door(self):
        tr, gl = self.mb["Trim"], self.mb["Glow"]
        style = self.era_def["window"]
        for side, cuts in self.openings.items():
            o, ud, n, L = self.wall(side)
            for a, b in cuts:
                is_door = (side, a) == (self.door[0], self.door[1])
                lo, hi = (0.0, 2.1) if is_door else (WIN_SILL, WIN_TOP)
                mid = (a + b) / 2
                # frame
                for u in (a, b):
                    tr.box(o + ud * u + n * 0.02 + Vector((0, 0, (lo + hi) / 2)),
                           Vector((abs(ud.x) * 0.1 + abs(n.x) * 0.2, abs(ud.y) * 0.1 + abs(n.y) * 0.2, hi - lo)), "trim")
                tr.box(o + ud * mid + n * 0.02 + Vector((0, 0, hi)),
                       Vector((abs(ud.x) * (b - a + 0.1) + abs(n.x) * 0.2, abs(ud.y) * (b - a + 0.1) + abs(n.y) * 0.2, 0.1)), "trim")
                card = o + ud * mid - n * (T + 0.6) + Vector((0, 0, (lo + hi) / 2))
                csz = Vector((abs(ud.x) * (b - a + 1.0) + abs(n.x) * 0.02, abs(ud.y) * (b - a + 1.0) + abs(n.y) * 0.02, hi - lo + 1.0))
                gl.box(card, csz, "outside" if is_door else "sky")
                if not is_door:
                    tr.box(o + ud * mid + n * 0.06 + Vector((0, 0, lo)),
                           Vector((abs(ud.x) * (b - a + 0.2) + abs(n.x) * 0.22, abs(ud.y) * (b - a + 0.2) + abs(n.y) * 0.22, 0.06)), "trim")
                    bars = {"arched": 1, "sash": 2, "industrial": 3, "sleek": 0, "porthole": 0}.get(style, 1)
                    for k in range(bars):
                        u = a + (b - a) * (k + 1) / (bars + 1)
                        tr.box(o + ud * u - n * (T / 2) + Vector((0, 0, (lo + hi) / 2)),
                               Vector((abs(ud.x) * 0.05 + abs(n.x) * 0.05, abs(ud.y) * 0.05 + abs(n.y) * 0.05, hi - lo)), "trim")
                    tr.box(o + ud * mid - n * (T / 2) + Vector((0, 0, (lo + hi) / 2 + 0.15)),
                           Vector((abs(ud.x) * (b - a) + abs(n.x) * 0.05, abs(ud.y) * (b - a) + abs(n.y) * 0.05, 0.05)), "trim")
                    self.add_focus("window", o + ud * mid + Vector((0, 0, (lo + hi) / 2)), max(b - a, hi - lo) * 1.2, view=n)
                else:
                    self.add_focus("door", o + ud * mid + Vector((0, 0, 1.05)), 2.2, view=n)

    # ---------------------------------------------------------------- lights
    def lights(self):
        lt = self.era_def["light"]["type"]
        lc = _c(self.era_def["light"]["color"])
        F = self.mb["Furniture"]
        night = self.mood in ("DUSK", "NIGHT")
        on = not self.state.get("lights_off")
        k = {"DAY": 0.25, "GOLDEN": 0.5, "DUSK": 1.0, "NIGHT": 1.25}[self.mood] if on else 0.0
        if lt in ("bulb", "pendant", "strip"):
            n = max(1, int(self.W * self.D / 22))
            for i in range(n):
                x = self.W * (i + 1) / (n + 1)
                y = self.D * self.rng.uniform(0.4, 0.6)
                if lt == "strip":
                    F.box((x, y, self.H - 0.03), (1.6, 0.18, 0.05), "accent" if night else "metal")
                else:
                    F.cyl((x, y, self.H - 0.35), 0.008, 0.7, "metal", seg=6)
                    F.cyl((x, y, self.H - 0.75), 0.22, 0.2, "lampshade", r2=0.06)
                self.lamps.append((Vector((x, y, self.H - (0.9 if lt != "strip" else 0.2))), lc, 220 * k, 0.15))
            self.add_focus("lamp", Vector((self.W / (n + 1), self.D * 0.5, self.H - 0.7)), 0.9)
        else:                                   # candles / oil lamps / braziers: sconces every ~3 m
            for side in ("left", "back", "right"):
                _, _, _, L = self.wall(side)
                for i in range(max(1, int(L / 3.2))):
                    u0 = self.reserve(side, 0.3, prefer=L * (i + 0.5) / max(1, int(L / 3.2)))
                    if u0 is None:
                        continue
                    zl = min(2.2, self.H * 0.6)
                    p = self.wp(side, u0 + 0.15, zl, 0.08)
                    P.place_prop(F, "sconce", p.x, p.y, zl, self.yaw(side), self.rng, self.era)
                    self.lamps.append((self.wp(side, u0 + 0.15, zl + 0.1, 0.35), lc, 90 * k, 0.05))
        if night and on:                         # big rooms: a soft overhead fill so they never go black
            vol = self.W * self.D * max(1.0, self.H / 3.0) ** 2
            self.lamps.append((Vector((self.W / 2, self.D / 2, self.H * 0.8)), lc, 25.0 * vol / 30.0, 1.5))
        if self.state.get("fire"):
            for _ in range(3):
                x, y = self.rng.uniform(1, self.W - 1), self.rng.uniform(1, self.D - 1)
                self.lamps.append((Vector((x, y, 0.8)), srgb(1.0, 0.55, 0.2), 400, 0.3))

    def build_lights(self):
        for i, (p, c, e, r) in enumerate(self.lamps):
            if e <= 0:
                continue
            ld = bpy.data.lights.new(f"PW_RoomLamp{i}", "POINT")
            ld.energy, ld.color, ld.shadow_soft_size = e, c, r
            o = bpy.data.objects.new(f"PW_RoomLamp{i}", ld)
            o.location = p
            self.col.objects.link(o)
        wk = {"DAY": 160, "GOLDEN": 110, "DUSK": 40, "NIGHT": 12}[self.mood] * self.weather.get("sun_scale", 1.0)
        for side, cuts in self.openings.items():
            o, ud, n, L = self.wall(side)
            for j, (a, b) in enumerate(cuts):
                if (side, a) == (self.door[0], self.door[1]):
                    continue
                ld = bpy.data.lights.new(f"PW_RoomWin{side}{j}", "AREA")
                ld.shape, ld.size, ld.size_y = "RECTANGLE", b - a, WIN_TOP - WIN_SILL
                ld.energy = wk
                ld.color = (0.85, 0.92, 1.0) if self.mood != "GOLDEN" else (1.0, 0.85, 0.65)
                ob = bpy.data.objects.new(f"PW_RoomWin{side}{j}", ld)
                ob.location = o + ud * ((a + b) / 2) + n * 0.05 + Vector((0, 0, (WIN_SILL + WIN_TOP) / 2))
                ob.rotation_euler = (n.to_track_quat("-Z", "Y")).to_euler()
                self.col.objects.link(ob)

    # ---------------------------------------------------------------- run
    def run(self):
        self.plan_openings()
        self.shell()
        for f in self.E["features"]:
            FEATURES[f](self)
        self.lights()
        self.clutter()
        self.state_dressing()
        objs = []
        for k, m in self.mb.items():
            if not m.empty():
                o = m.build(self.col, self.pal)
                objs.append(o)
                if k in ("Shell", "Floor"):
                    o["pw_wonk"] = 0.0
                if k == "Glow":
                    o["pw_line"] = 0
                    o.visible_shadow = False
        self.build_lights()
        cx = self.W / 2
        self.add_focus("room", Vector((self.W * 0.45, self.D * 0.6, 1.1)), max(3.0, min(self.W, self.D) * 0.6),
                       view=Vector((self.W - 0.7, 0.8, 1.1)) - Vector((self.W * 0.45, self.D * 0.6, 1.1)))
        main = self.focus.get(self.E.get("focus", "room"), self.focus["room"])
        cam = Vector((self.W - 0.75 + self.rng.uniform(-0.1, 0.1), 0.85 + self.rng.uniform(-0.1, 0.1), 1.6))
        mp = Vector(main["pos"])
        tgt = cam.lerp(Vector((mp.x, mp.y, 0.9)), 1.0)
        tgt = (tgt + Vector((self.W * 0.3, self.D * 0.85, 0.9))) / 2
        win = [s for s in ("back", "left", "right") if any((s, a) != (self.door[0], self.door[1]) for a, b in self.openings[s])]
        az = {"back": 180.0, "left": 270.0, "right": 90.0, "front": 0.0}[win[0]] if win else 180.0
        return {"objects": len(self.col.objects), "focus_points": self.focus, "spawn": {"focus": "room"},
                "camera": {"location": tuple(cam), "target": tuple(tgt), "lens": 18 if self.W < 9 else 20, "clip_end": 200.0},
                "sun_dir": (34.0, az + self.rng.uniform(-15, 15)), "sun_scale": 1.0 if win else 0.0, "sky_scale": 0.6,
                "ink": self.ink_hints()}

    def ink_hints(self):
        h = {"grime": self.state.get("grime", 1.0), "base_height": 0.25}
        if self.mood in ("DUSK", "NIGHT") and not self.state.get("lights_off"):
            h["light_tint"] = srgb(0.98, 0.88, 0.72)        # lamp-lit room, not moonlight
            h["shadow_tint"] = srgb(0.46, 0.43, 0.58)
        return h

    # ---------------------------------------------------------------- clutter + state
    def clutter(self):
        r = self.rng
        rooms = list(self.E.get("props", [])) + [self.E["_name"]]
        dens = self.state.get("clutter", 1.0)
        F, Pm = self.mb["Furniture"], self.mb["Props"]
        self.surfaces += P.scatter_floor(F, (0.4, 1.6, self.W - 0.4, self.D - 0.4), self.era, rooms, r,
                                         int(self.W * self.D / 8 * dens), self.avoid)
        P.scatter_surfaces(Pm, self.surfaces, self.era, rooms, r, density=dens * 1.8)
        walls = P.candidates("wall", self.era, rooms)
        for side in ("back", "left", "right"):
            for _ in range(int(4 * dens)):
                u0 = self.reserve(side, 0.7)
                if u0 is None:
                    break
                name = r.choice([w for w in ("frame", "clock", "frame") if w in walls] or ["frame"])
                p = self.wp(side, u0 + 0.35, 0, 0.03)
                P.place_prop(Pm, name, p.x, p.y, r.uniform(1.5, 2.0), self.yaw(side), r, self.era)

    def state_dressing(self):
        r = self.rng
        Pm = self.mb["Props"]
        deb = self.state.get("debris", 0.0)
        for _ in range(int(deb * self.W * self.D / 3)):
            x, y = r.uniform(0.5, self.W - 0.5), r.uniform(1.2, self.D - 0.5)
            k = r.choice(("papers", "papers", "crate", "sack")) if self.era != "far-future" else "papers"
            if k in P.PROPS and (P.PROPS[k]["eras"] is None or self.era in P.PROPS[k]["eras"]):
                P.place_prop(Pm, k, x, y, 0.0, r.uniform(0, math.tau), r, self.era)
            Pm.box((x + r.uniform(-0.4, 0.4), y + r.uniform(-0.4, 0.4), 0.03), (r.uniform(0.1, 0.5), r.uniform(0.05, 0.3), 0.05),
                   r.choice(("wood2", "stone", "trim")), rot_z=r.uniform(0, math.tau))
        wl = self.state.get("water_level")
        if wl:
            g = self.mb["Glow"]
            g.box((self.W / 2, self.D / 2, wl / 2), (self.W, self.D, wl), "water")
        if self.state.get("fire"):
            g = self.mb["Glow"]
            for _ in range(5):
                x, y = r.uniform(0.6, self.W - 0.6), r.uniform(1.5, self.D - 0.4)
                for k in range(3):
                    g.cyl((x + r.uniform(-0.2, 0.2), y + r.uniform(-0.2, 0.2), 0.35 + 0.15 * k), 0.3 - 0.08 * k, 0.6, "fire" if k < 2 else "fire2", seg=7, r2=0.02)


# ============================================================================ features
def f_counter_run(R):
    side = "back"
    w = min(R.W * 0.55, 6.0)
    u0 = R.reserve(side, w, prefer=R.W * 0.1)
    if u0 is None:
        return
    F = R.mb["Furniture"]
    y = R.D - 1.6
    n = max(1, int(w / 2.0))
    for i in range(n):
        x = u0 + w * (i + 0.5) / n
        R.surfaces += P.place_prop(F, "counter", x, y, 0, 0.0, R.rng, R.era)
    stools = P.candidates("floor", R.era, ["diner", "bar"])
    for i in range(int(w / 0.75)):
        x = u0 + 0.4 + i * 0.75
        P.place_prop(F, "stool", x, y - 0.75, 0, R.rng.uniform(0, 6.28), R.rng, R.era)
    R.avoid += [(u0 + w / 2, y - 0.3, w / 2 + 0.4)]
    R.counter = (u0, u0 + w, y)
    R.add_focus("counter", Vector((u0 + w / 2, y, 1.1)), max(2.0, w * 0.5))


def f_bar_back(R):
    F = R.mb["Furniture"]
    u = getattr(R, "counter", None)
    u0, u1 = (u[0], u[1]) if u else (R.W * 0.2, R.W * 0.6)
    for x in [u0 + 0.6 + i * 1.05 for i in range(int((u1 - u0 - 0.4) / 1.05))]:
        P.place_prop(F, "shelf_unit", x, R.D - 0.22, 0.6, 0.0, R.rng, R.era)
        for k in range(R.rng.randint(4, 8)):
            P.place_prop(R.mb["Props"], "bottle", x + R.rng.uniform(-0.4, 0.4), R.D - 0.25, 1.1 + 0.45 * R.rng.randint(0, 2), 0, R.rng, R.era)
    R.add_focus("bar_back", Vector(((u0 + u1) / 2, R.D - 0.3, 1.7)), max(1.8, (u1 - u0) * 0.5))
    R.add_focus("bottles", Vector(((u0 + u1) / 2, R.D - 0.3, 1.6)), 1.0)


def f_booths(R):
    side = "left"
    F = R.mb["Furniture"]
    for i in range(3):
        u0 = R.reserve(side, 1.9, prefer=1.6 + i * 2.0)
        if u0 is None:
            break
        y = u0 + 0.95
        R.surfaces += P.place_prop(F, "table", 0.75, y, 0, math.pi / 2, R.rng, R.era)
        for dy in (-0.75, 0.75):
            F.box((0.75, y + dy, 0.25), (1.2, 0.45, 0.5), "fabric")
            F.box((0.75, y + dy * 1.25, 0.75), (1.2, 0.12, 0.6), "fabric")
        R.avoid.append((0.75, y, 1.1))
        if i == 0:
            R.add_focus("booth", Vector((0.75, y, 0.9)), 1.6)


def f_tables(R):
    F = R.mb["Furniture"]
    for i in range(R.rng.randint(3, 5)):
        for _ in range(20):
            x, y = R.rng.uniform(1.5, R.W - 1.5), R.rng.uniform(2.2, R.D - 2.5)
            if any((x - ax) ** 2 + (y - ay) ** 2 < (ar + 1.0) ** 2 for ax, ay, ar in R.avoid):
                continue
            a = R.rng.uniform(-0.3, 0.3)
            R.surfaces += P.place_prop(F, "table", x, y, 0, a, R.rng, R.era)
            for k in range(R.rng.randint(2, 4)):
                ang = a + k * math.pi / 2
                P.place_prop(F, "chair", x + math.cos(ang) * 0.75, y + math.sin(ang) * 0.75, 0, ang - math.pi / 2, R.rng, R.era)
            R.avoid.append((x, y, 1.0))
            if "table" not in R.focus:
                R.add_focus("table", Vector((x, y, 0.85)), 1.4)
            break


def f_beams(R):
    F = R.mb["Furniture"]
    for i in range(int(R.D / 1.6)):
        y = 0.8 + i * 1.6
        F.box((R.W / 2, y, R.H - 0.15), (R.W, 0.22, 0.25), "wood2")
    for x in (R.W * 0.33, R.W * 0.66):
        F.box((x, R.D / 2, R.H - 0.32), (0.2, R.D, 0.12), "wood2")


def f_fireplace(R):
    for side in ("left", "right", "back"):
        u0 = R.reserve(side, 2.0)
        if u0 is not None:
            break
    else:
        return
    F, G = R.mb["Furniture"], R.mb["Glow"]
    c = R.wp(side, u0 + 1.0, 0, 0.0)
    _, ud, n, _ = R.wall(side)
    def box(off_u, off_n, z, su, sn, sz, key):
        p = c + ud * off_u + n * off_n + Vector((0, 0, z))
        F.box(p, Vector((abs(ud.x) * su + abs(n.x) * sn, abs(ud.y) * su + abs(n.y) * sn, sz)), key)
    box(0, 0.25, 0.7, 2.0, 0.5, 1.4, "stone")
    box(0, 0.35, 1.45, 2.2, 0.7, 0.12, "wood2")
    box(0, 0.45, 0.45, 1.1, 0.12, 0.8, "dark")
    lit = R.mood in ("DUSK", "NIGHT", "GOLDEN") and not R.state.get("lights_off")
    if lit:
        p = c + n * 0.55 + Vector((0, 0, 0.25))
        for k in range(3):
            G.cyl(p + ud * (k - 1) * 0.22, 0.14, 0.4, "fire" if k != 1 else "fire2", seg=6, r2=0.01)
        R.lamps.append((c + n * 1.0 + Vector((0, 0, 0.6)), srgb(1.0, 0.6, 0.3), 180.0, 0.2))
    R.surfaces.append((c + n * 0.35 + Vector((0, 0, 1.52)), 0.8))
    R.avoid.append((c.x + n.x, c.y + n.y, 1.2))
    R.add_focus("fireplace", c + n * 0.3 + Vector((0, 0, 0.8)), 2.2, view=n)


def f_crates_pile(R):
    F = R.mb["Furniture"]
    corner = R.rng.choice([(0.8, R.D - 0.8), (R.W - 0.8, R.D - 0.8)])
    for i in range(R.rng.randint(3, 6)):
        name = R.rng.choice(P.candidates("floor", R.era, ["storage"]) or ["crate"])
        if name not in ("crate", "barrel", "sack"):
            name = "crate"
        P.place_prop(F, name, corner[0] + R.rng.uniform(-0.6, 0.6), corner[1] + R.rng.uniform(-0.6, 0.6), 0, R.rng.uniform(0, 6.28), R.rng, R.era)
    R.avoid.append((corner[0], corner[1], 1.2))
    R.add_focus("crates", Vector((corner[0], corner[1], 0.6)), 1.6)


def f_desks_rows(R):
    F = R.mb["Furniture"]
    rows, cols = (3, max(2, int(R.W / 2.6)))
    first = None
    for i in range(rows):
        for j in range(cols):
            x = 1.4 + j * (R.W - 2.8) / max(1, cols - 1)
            y = 2.4 + i * 1.6
            if y > R.D - 1.2 or any((x - ax) ** 2 + (y - ay) ** 2 < (ar + 0.8) ** 2 for ax, ay, ar in R.avoid):
                continue
            R.surfaces += P.place_prop(F, "desk", x, y, 0, 0.0, R.rng, R.era)
            P.place_prop(F, "chair", x, y - 0.7, 0, math.pi + R.rng.uniform(-0.4, 0.4), R.rng, R.era)
            R.avoid.append((x, y, 0.9))
            first = first or Vector((x, y, 0.95))
    if first:
        R.add_focus("desk", first, 1.4)


def f_desk_single(R):
    F = R.mb["Furniture"]
    x, y = R.W * R.rng.uniform(0.35, 0.55), R.D - 1.4
    R.surfaces += P.place_prop(F, "desk", x, y, 0, math.pi, R.rng, R.era)
    P.place_prop(F, "chair", x - 0.2, y + 0.7, 0, R.rng.uniform(-0.3, 0.3), R.rng, R.era)
    P.place_prop(R.mb["Props"], "lamp", x + 0.5, y + 0.1, 0.765, 0, R.rng, R.era)
    R.avoid.append((x, y, 1.0))
    R.add_focus("desk", Vector((x, y, 0.95)), 1.4)


def f_shelves_walls(R):
    F = R.mb["Furniture"]
    first = None
    for side in ("left", "back", "right"):
        for k in range(R.rng.randint(1, 3)):
            u0 = R.reserve(side, 1.25)
            if u0 is None:
                break
            p = R.wp(side, u0 + 0.62, 0, 0.22)
            name = "bookcase" if "bookcase" in P.candidates("wall", R.era, R.E.get("props", []) + ["library"]) and R.rng.random() < 0.6 else "shelf_unit"
            P.place_prop(F, name, p.x, p.y, 0.0, R.yaw(side), R.rng, R.era)
            R.avoid.append((p.x, p.y, 0.6))
            first = first or (p, side)
    if first:
        p, side = first
        R.add_focus("shelves", p + Vector((0, 0, 1.2)), 2.2, view=R.wall(side)[2])


def f_shelves_rows(R):
    F = R.mb["Furniture"]
    for i in range(3):
        x = 2.0 + i * (R.W - 4.0) / 2
        for k in range(2):
            y = R.D * 0.45 + k * 1.25
            P.place_prop(F, "bookcase", x, y, 0, 0.0, R.rng, R.era)
            P.place_prop(F, "bookcase", x, y + 0.42, 0, math.pi, R.rng, R.era)
        R.avoid.append((x, R.D * 0.45 + 0.8, 1.6))


def f_cabinets_wall(R):
    F = R.mb["Furniture"]
    for side in ("right", "left"):
        u0 = R.reserve(side, 1.0)
        if u0 is not None:
            p = R.wp(side, u0 + 0.5, 0, 0.24)
            R.surfaces += P.place_prop(F, "cabinet", p.x, p.y, 0, R.yaw(side), R.rng, R.era)
            R.avoid.append((p.x, p.y, 0.6))


def f_sofa_set(R):
    F = R.mb["Furniture"]
    x, y = R.W * 0.45, R.D * 0.55
    P.place_prop(F, "rug", x, y - 0.4, 0, 0, R.rng, R.era)
    P.place_prop(F, "sofa", x, y + 0.6, 0, 0.0, R.rng, R.era)
    F.box((x, y - 0.4, 0.22), (1.1, 0.6, 0.06), "wood")
    for sx in (-0.5, 0.5):
        for sy in (-0.25, 0.25):
            F.box((x + sx, y - 0.4 + sy, 0.1), (0.05, 0.05, 0.2), "wood")
    R.surfaces.append((Vector((x, y - 0.4, 0.25)), 0.4))
    R.avoid.append((x, y, 1.5))
    R.add_focus("sofa", Vector((x, y + 0.5, 0.6)), 2.0)


def f_rug(R):
    x, y = R.rng.uniform(R.W * 0.3, R.W * 0.7), R.rng.uniform(R.D * 0.3, R.D * 0.6)
    P.place_prop(R.mb["Furniture"], "rug", x, y, 0.0, R.rng.uniform(-0.2, 0.2), R.rng, R.era)


def f_bed_single(R):
    F = R.mb["Furniture"]
    side = "back"
    u0 = R.reserve(side, 1.6, prefer=R.W * 0.3)
    if u0 is None:
        return
    x, y = u0 + 0.8, R.D - 1.05
    P.place_prop(F, "bed", x, y, 0, math.pi, R.rng, R.era)
    R.surfaces += P.place_prop(F, "cabinet", x + 0.95, R.D - 0.3, 0, 0.0, R.rng, R.era)[:1]
    R.avoid.append((x, y, 1.3))
    R.add_focus("bed", Vector((x, y, 0.6)), 2.0)


def f_beds_row(R):
    F = R.mb["Furniture"]
    n = max(2, int(R.W / 1.9))
    for i in range(n):
        x = 1.0 + i * (R.W - 2.0) / max(1, n - 1)
        if R.reserve("back", 1.2, prefer=x - 0.6) is None:
            continue
        P.place_prop(F, "bed", x, R.D - 1.05, 0, math.pi, R.rng, R.era)
        R.avoid.append((x, R.D - 1.05, 1.1))
    R.add_focus("beds", Vector((R.W * 0.4, R.D - 1.0, 0.7)), 3.0)


def f_cells(R):
    F = R.mb["Furniture"]
    side = "right"
    _, _, _, L = R.wall(side)
    x0 = R.W - 1.8
    n = max(2, int((R.D - 2.5) / 2.0))
    for i in range(n):
        y0 = R.D - 0.2 - (i + 1) * 2.0
        F.box((x0 + 0.9, y0, 1.2), (1.8, 0.12, 2.4), "stone" if R.era in P.OLD else "wall2")
        for k in range(9):
            F.box((x0, y0 + 0.2 + k * 0.2, 1.2), (0.05, 0.05, 2.4), "metal2")
        F.box((x0, y0 + 1.0, 2.35), (0.08, 2.0, 0.08), "metal2")
        F.box((x0 + 1.2, y0 + 1.0, 0.25), (0.7, 1.8, 0.1), "wood2")
    F.box((x0 + 0.9, R.D - 0.2 - n * 2.0, 1.2), (1.8, 0.12, 2.4), "wall2")
    R.avoid.append((x0 + 0.9, R.D - n, n))
    R.add_focus("cells", Vector((x0, R.D - 2.2, 1.2)), 2.4, view=Vector((-1, -0.4, 0)))


def f_blackboard(R):
    F = R.mb["Furniture"]
    u0 = R.reserve("back", 3.2, prefer=R.W / 2 - 1.6)
    if u0 is None:
        return
    p = R.wp("back", u0 + 1.6, 1.5, 0.03)
    F.box(p, (3.2, 0.04, 1.2), "trim")
    F.box(p + Vector((0, -0.02, 0)), (3.0, 0.02, 1.05), "dark")
    for k in range(4):                                    # chalk scribbles
        F.box(p + Vector((R.rng.uniform(-1.1, 0.9), -0.035, 0.35 - k * 0.2)), (R.rng.uniform(0.4, 1.2), 0.005, 0.03), "paper")
    F.box(p + Vector((0, -0.08, -0.6)), (3.0, 0.12, 0.04), "trim")
    R.add_focus("blackboard", p, 2.6, view=Vector((0, -1, 0)))


def f_pillars(R):
    F = R.mb["Furniture"]
    nx = 2
    ny = max(2, int(R.D / 4))
    for i in range(nx):
        for j in range(ny):
            x = R.W * (0.25 if i == 0 else 0.75)
            y = 2.5 + j * (R.D - 4) / max(1, ny - 1)
            if any((x - ax) ** 2 + (y - ay) ** 2 < ar ** 2 for ax, ay, ar in R.avoid[:3]):
                continue                                          # never in the camera's face
            F.cyl((x, y, R.H / 2), 0.35, R.H, "stone", seg=10)
            F.box((x, y, 0.15), (0.95, 0.95, 0.3), "stone")
            F.box((x, y, R.H - 0.15), (0.95, 0.95, 0.3), "stone")
            R.avoid.append((x, y, 0.6))
    R.add_focus("pillars", Vector((R.W * 0.25, R.D * 0.5, R.H * 0.4)), R.H * 0.6)


def f_dais(R):
    F = R.mb["Furniture"]
    x, y = R.W / 2, R.D - 2.0
    F.box((x, y, 0.2), (5.0, 3.0, 0.4), "stone")
    F.box((x, y + 0.6, 0.6), (3.5, 1.6, 0.4), "stone")
    F.box((x, y + 0.6, 1.3), (1.0, 0.8, 1.0), "wood2")         # throne
    F.box((x, y + 0.95, 2.2), (1.1, 0.15, 1.9), "wood2")
    F.box((x, y + 0.6, 0.85), (1.2, 0.9, 0.12), "fabric")
    for sx in (-2.2, 2.2):                                    # banners
        F.box((x + sx, R.D - 0.2, R.H * 0.55), (1.2, 0.04, R.H * 0.5), "fabric")
    R.avoid.append((x, y, 2.8))
    R.add_focus("dais", Vector((x, y + 0.5, 1.5)), 4.0)
    R.add_focus("throne", Vector((x, y + 0.6, 1.4)), 1.8)


def f_banquet(R):
    F = R.mb["Furniture"]
    x0, y0 = R.W / 2, R.D * 0.4
    L = R.D * 0.4
    F.box((x0, y0, 0.78), (1.4, L, 0.08), "wood")
    for k in range(int(L / 1.2)):
        y = y0 - L / 2 + 0.6 + k * 1.2
        F.box((x0, y, 0.38), (0.12, 0.12, 0.74), "wood2")
        for sx in (-1.0, 1.0):
            F.box((x0 + sx, y, 0.45), (0.4, 1.0, 0.06), "wood2")
    R.surfaces += [(Vector((x0, y0 - L / 4, 0.82)), 0.6), (Vector((x0, y0 + L / 4, 0.82)), 0.6)]
    R.avoid.append((x0, y0, L / 2 + 0.5))
    R.add_focus("banquet", Vector((x0, y0, 1.0)), L * 0.6)


def f_machines(R):
    F = R.mb["Furniture"]
    for k in range(2):
        u0 = R.reserve("back", 1.8)
        if u0 is None:
            break
        p = R.wp("back", u0 + 0.9, 0, 0.8)
        h = R.rng.uniform(1.4, 2.0)
        F.box(p + Vector((0, 0, h / 2)), (1.6, 1.2, h), "metal2")
        F.cyl(p + Vector((0.4, -0.61, h * 0.6)), 0.18, 0.06, "metal", axis="Y")
        F.cyl(p + Vector((-0.3, 0.0, h + 0.4)), 0.1, 0.8, "metal")
        F.cyl(p + Vector((-0.3, 0.0, R.H - 0.2)), 0.1, R.W, "metal", axis="X")
        R.avoid.append((p.x, p.y, 1.2))
        if k == 0:
            R.add_focus("machines", p + Vector((0, 0, h * 0.6)), 2.4, view=Vector((0, -1, 0)))


FEATURES = {"counter_run": f_counter_run, "bar_back": f_bar_back, "booths": f_booths, "tables": f_tables,
            "beams": f_beams, "fireplace": f_fireplace, "crates_pile": f_crates_pile, "desks_rows": f_desks_rows,
            "desk_single": f_desk_single, "shelves_walls": f_shelves_walls, "shelves_rows": f_shelves_rows,
            "cabinets_wall": f_cabinets_wall, "sofa_set": f_sofa_set, "rug": f_rug, "bed_single": f_bed_single,
            "beds_row": f_beds_row, "cells": f_cells, "blackboard": f_blackboard, "pillars": f_pillars,
            "dais": f_dais, "banquet": f_banquet, "machines": f_machines}

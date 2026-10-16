"""Street kit: a street block from data. Street runs along +Y; buildings line both sides with era-dressed
facades (ground-floor shopfronts with door, display window, awning and sign; upper floors with era
windows; gabled roofs for old eras, cornices / antennas for newer ones). Variants via entry flags:
"stalls" (market), "small" (village), "water_end" (harbour), "elevated" (rooftop camera).
Camera at eye level near y=0 looking down the street."""
import math, random
import bpy
from mathutils import Vector
from .mb import MB
from . import props as P
from .room import era_palette, _c
from .. import core, shots
from ..ink import srgb


FEATURES = {}        # name -> fn(street): extra dressing listed in a setting's "features"


class Street:
    def __init__(self, col, entry, layers, seed, mood):
        self.col, self.E, self.L, self.mood = col, entry, layers, mood
        self.rng = random.Random(f"street:{entry['_name']}:{seed}")
        eras = core.load_preset("era")
        self.era = layers.get("era") if layers.get("era") in eras else entry["eras"][0]
        self.era_def = eras[self.era]
        cond = core.load_preset("conditions")
        self.state = cond["state"].get(layers.get("state", "lived-in"), cond["state"]["lived-in"])
        self.weather = cond["weather"].get(layers.get("weather", "clear"), cond["weather"]["clear"])
        self.pal = era_palette(self.era_def, mood, self.state)
        r = self.rng
        old = self.era in P.OLD
        self.road = r.uniform(*entry.get("road", (6.0, 9.0)))
        self.walk = 2.2 if not old else 1.0
        self.len = r.uniform(*entry.get("length", (55.0, 75.0)))
        self.floors = entry.get("floors", (2, 3) if old else ((3, 5) if self.era in P.MID | P.NOW else (5, 11)))
        if entry.get("small"):
            self.floors = (1, 2)
        for i, c in enumerate(("wallA", "wallB", "wallC")):        # per-building facade colours
            base = self.pal["wall"] if i == 0 else self.pal["wall2"] if i == 1 else self.pal["accent"]
            base = base["color"] if isinstance(base, dict) else base
            self.pal[c] = tuple(min(1.0, x * r.uniform(0.75, 1.05)) for x in base)
        self.pal["signcol"] = {"color": srgb(0.95, 0.35, 0.55), "emission": srgb(0.95, 0.35, 0.55), "strength": 3.0} \
            if self.era_def["signage"] in ("neon", "holo") else srgb(0.82, 0.70, 0.40)
        self.pal["asphalt"] = srgb(0.30, 0.31, 0.33) if not old else srgb(0.50, 0.44, 0.36)
        self.pal["awning"] = self.pal["fabric"]
        self.mb = {k: MB(f"PW_Street{k}") for k in ("Ground", "Facades", "Detail", "Props", "Glow")}
        self.focus, self.lamps, self.shopfronts = {}, [], []

    def run(self):
        r, E = self.rng, self.E
        G = self.mb["Ground"]
        half = self.road / 2
        old = self.era in P.OLD
        # road + pavements (cobbles for old eras via a jittered grid)
        if old:
            G.quad_grid(-half, -10, half, self.len, int(self.road / 0.6), int((self.len + 10) / 0.6),
                        lambda i, j: r.choice(("floor_a", "floor_b", "floor_a")), jitter=0.1, rng=r)
        else:
            G.box((0, self.len / 2 - 5, -0.05), (self.road, self.len + 10, 0.1), "asphalt")
            for k in range(int(self.len / 6)):            # lane dashes
                G.box((0, k * 6.0, 0.005), (0.15, 2.5, 0.01), "paper")
        for s in (-1, 1):
            G.box((s * (half + self.walk / 2), self.len / 2 - 5, 0.08), (self.walk, self.len + 10, 0.16), "floor_b" if old else "stone")
        for s in (-1, 1):
            self.side(s)
        self.street_props()
        if E.get("stalls"):
            self.stalls()
        for f in E.get("features", []):            # extension street features (kits/ext/*)
            FEATURES[f](self)
        if E.get("water_end"):
            self.pal["water"] = srgb(0.28, 0.42, 0.46)
            G.box((0, self.len + 30, -0.4), (80, 60, 0.2), "water")
        # far end: a closing building so the street doesn't end in void
        far = self.mb["Facades"]
        if not E.get("water_end"):
            far.box((0, self.len + 6, 9), (self.road + 2 * self.walk + 20, 4, 18), "wallB")
            self.focus["far_end"] = shots.focus_point(Vector((0, self.len, 3.5)), Vector((0, -1, 0)), 12.0)
        else:
            self.focus["far_end"] = shots.focus_point(Vector((0, self.len + 20, 2.0)), Vector((0, -1, 0)), 14.0)
        objs = []
        for k, m in self.mb.items():
            if not m.empty():
                o = m.build(self.col, self.pal)
                if k == "Ground":
                    o["pw_wonk"] = 0.3
                if k == "Glow":
                    o["pw_line"] = 0
        self.build_lamps()
        cam_h = 1.65 if not E.get("elevated") else 9.0
        cam = Vector((r.uniform(-0.3, 0.3) * half, -3.0, cam_h))
        tgt = Vector((r.uniform(-0.5, 0.5), self.len * 0.6, cam_h * (0.9 if E.get("elevated") else 1.0) + 1.0))
        tgt = cam + (tgt - cam).normalized() * 12.0          # focus distance drives line weight
        self.focus["street"] = shots.focus_point(Vector((0, 14.0, 2.5)), cam - Vector((0, 14, 2.5)), 8.0)
        sun = {"DAY": (45, 200), "GOLDEN": (14, 120), "DUSK": (5, 100), "NIGHT": (30, 60)}[self.mood]
        return {"objects": len(self.col.objects), "focus_points": self.focus, "spawn": {"focus": "street"},
                "camera": {"location": tuple(cam), "target": tuple(tgt), "lens": 24, "clip_end": 600.0},
                "sun_dir": sun, "sun_scale": self.weather.get("sun_scale", 1.0), "sky_scale": self.weather.get("sky_scale", 1.0),
                "ink": {"grime": self.state.get("grime", 1.0), "base_height": 0.8, "line_scale": 1.2}}

    # ------------------------------------------------------------------ buildings
    def side(self, s):
        r = self.rng
        x0 = s * (self.road / 2 + self.walk)
        y = -8.0
        F, D = self.mb["Facades"], self.mb["Detail"]
        old = self.era in P.OLD
        while y < self.len:
            w = r.uniform(4.5, 9.0)
            nf = r.randint(*self.floors)
            fh = 3.2 if not old else 2.8
            H = nf * fh + 0.6
            depth = 10.0
            wall = r.choice(("wallA", "wallB", "wallC"))
            cx = x0 + s * depth / 2
            F.box((cx, y + w / 2, H / 2), (depth, w - 0.05, H), wall)
            face = x0 - s * 0.01                              # facade plane (street side)
            # ground floor shopfront
            door_y = y + r.uniform(0.6, w * 0.35)
            D.box((face, door_y + 0.5, 1.1), (0.12, 1.0, 2.2), "dark")
            D.box((face - s * 0.03, door_y + 0.5, 2.3), (0.1, 1.3, 0.12), "trim")
            win_y0, win_y1 = door_y + 1.3, y + w - 0.5
            if win_y1 - win_y0 > 1.0:
                lit = self.mood in ("DUSK", "NIGHT")
                D.box((face, (win_y0 + win_y1) / 2, 1.5), (0.1, win_y1 - win_y0, 1.6), "lampshade" if lit else "glass")
                D.box((face - s * 0.04, (win_y0 + win_y1) / 2, 0.55), (0.12, win_y1 - win_y0 + 0.1, 0.3), "trim")
                if r.random() < 0.7:                          # awning
                    D.box((face - s * 0.6, (win_y0 + win_y1) / 2, 2.55), (1.2, win_y1 - win_y0 + 0.3, 0.08), "awning",
                          rot=None)
                if r.random() < 0.85:                         # shop sign board
                    sy = (win_y0 + win_y1) / 2
                    D.box((face - s * 0.06, sy, 2.95), (0.08, min(3.0, win_y1 - win_y0), 0.55), "signcol")
                    for k in range(r.randint(2, 4)):          # pseudo-lettering strokes
                        D.box((face - s * 0.11, sy - 0.8 + k * 0.5 + r.uniform(-0.1, 0.1), 2.95), (0.02, 0.3, 0.12), "dark")
                self.shopfronts.append(Vector((face - s * 0.3, (win_y0 + win_y1) / 2, 1.6)))
            # upper floors: window grid
            nwin = max(1, int(w / 2.0))
            for f in range(1, nf):
                z = f * fh + 1.4
                for k in range(nwin):
                    wy = y + w * (k + 0.5) / nwin
                    lit = self.mood in ("DUSK", "NIGHT") and r.random() < 0.45
                    style = self.era_def["window"]
                    ww, wh = (0.8, 1.4) if style in ("sash", "arched") else (1.4, 1.2) if style == "industrial" else (1.6, 1.0)
                    D.box((face, wy, z), (0.1, ww, wh), "lampshade" if lit else "dark")
                    D.box((face - s * 0.05, wy, z - wh / 2 - 0.05), (0.15, ww + 0.2, 0.08), "trim")
                    if style == "arched":
                        D.box((face - s * 0.03, wy, z + wh / 2 + 0.1), (0.1, ww + 0.15, 0.2), "trim")
                    if old and r.random() < 0.5:              # timber framing
                        D.box((face - s * 0.04, wy - ww, z), (0.08, 0.15, fh), "wood2")
                F.box((face - s * 0.06, y + w / 2, f * fh), (0.14, w, 0.15), "trim")      # floor ledge
            # roof
            if old:
                ridge = H + w * 0.35
                xb = x0 + s * depth
                F.poly([(x0, y, H), (x0, y + w, H), (x0, y + w / 2, ridge)], wall)            # gable end
                F.poly([(x0, y - 0.2, H - 0.1), (xb, y - 0.2, H - 0.1), (xb, y + w / 2, ridge), (x0, y + w / 2, ridge)], "wood2")
                F.poly([(x0, y + w + 0.2, H - 0.1), (x0, y + w / 2, ridge), (xb, y + w / 2, ridge), (xb, y + w + 0.2, H - 0.1)], "wood2")
                F.box((cx, y + w / 2, H + 0.05), (depth + 0.4, w + 0.3, 0.1), "trim")
                for yy in (y + w * 0.25, y + w * 0.75):
                    D.box((cx, yy, (H + ridge) / 2), (depth, 0.25, ridge - H), "wood2")
                D.box((cx + s * 1.5, y + w * 0.7, ridge + 0.3), (0.6, 0.6, 1.4), "stone")    # chimney
            else:
                F.box((face - s * 0.15, y + w / 2, H - 0.1), (0.4, w, 0.35), "trim")         # cornice
                if self.era in P.FUT or r.random() < 0.3:
                    D.cyl((cx, y + w / 2, H + 1.2), 0.04, 2.4, "metal", seg=6)
                    D.box((cx + s * 2, y + w * 0.3, H + 0.6), (1.6, 1.2, 1.2), "metal2")
            if self.era in P.FUT and r.random() < 0.6:        # vertical neon blade sign
                D.box((face - s * 0.7, y + w * 0.5, fh * 1.8), (1.2, 0.15, 3.5), "signcol")
            y += w

    def street_props(self):
        r = self.rng
        D, Pm = self.mb["Detail"], self.mb["Props"]
        half = self.road / 2
        lt = self.era_def["light"]["type"]
        lc = _c(self.era_def["light"]["color"])
        on = self.mood in ("DUSK", "NIGHT", "GOLDEN") and not self.state.get("lights_off")
        for k in range(int(self.len / 12)):
            for s in (-1, 1):
                y = 4 + k * 12 + (6 if s > 0 else 0)
                x = s * (half + 0.4)
                h = 3.0 if self.era in P.OLD else 4.5
                D.cyl((x, y, h / 2), 0.06, h, "metal2", seg=6)
                if self.era in P.OLD:
                    D.box((x, y, h + 0.2), (0.3, 0.3, 0.4), "lampshade")
                else:
                    D.box((x - s * 0.5, y, h), (1.0, 0.1, 0.08), "metal2")
                    D.box((x - s * 0.9, y, h - 0.12), (0.4, 0.3, 0.15), "lampshade")
                if on:
                    self.lamps.append((Vector((x - s * 0.8, y, h - 0.4)), lc, 350.0))
                if k == 1 and s == 1:
                    self.focus["street_lamp"] = shots.focus_point(Vector((x, y, h * 0.7)), Vector((-s, -0.6, 0)), 3.0)
        # vehicles / carts and clutter
        n = int(self.len / 15)
        for k in range(n):
            y = r.uniform(6, self.len - 8)
            s = r.choice((-1, 1))
            x = s * (half - 1.2)
            if self.era in P.OLD:
                D.box((x, y, 0.7), (1.2, 2.2, 0.4), "wood")
                for dy in (-0.7, 0.7):
                    D.cyl((x + s * 0.65, y + dy, 0.5), 0.45, 0.08, "wood2", seg=12, axis="X")
                D.box((x, y + 1.6, 0.6), (0.08, 1.4, 0.08), "wood2")
            else:
                body = r.choice(("fabric", "accent", "wall2", "metal"))
                D.box((x, y, 0.6), (1.8, 4.2, 0.7), body)
                D.box((x, y - 0.2, 1.25), (1.6, 2.2, 0.6), body)
                D.box((x, y - 0.2, 1.25), (1.62, 1.9, 0.45), "glass")
                for dy in (-1.3, 1.3):
                    for dx in (-0.85, 0.85):
                        D.cyl((x + dx, y + dy, 0.35), 0.35, 0.25, "dark", seg=12, axis="X")
            if k == 0:
                self.focus["vehicle"] = shots.focus_point(Vector((x, y, 0.9)), Vector((-s, -1, 0)), 4.0)
        for k in range(int(self.len / 5)):
            s = r.choice((-1, 1))
            y = r.uniform(0, self.len)
            x = s * (half + self.walk * r.uniform(0.3, 0.8))
            name = r.choice(P.candidates("floor", self.era, ["outdoor", "storage", "shop"]) or ["crate"])
            if name in ("crate", "barrel", "sack", "plant"):
                P.place_prop(Pm, name, x, y, 0.16, r.uniform(0, 6.28), r, self.era)
        if self.shopfronts:
            sf = min(self.shopfronts[2:] or self.shopfronts, key=lambda p: p.y)
            self.focus["shopfront"] = shots.focus_point(sf, Vector((-math.copysign(1, sf.x), -0.5, 0)), 4.0)
            self.focus["sign"] = shots.focus_point(sf + Vector((0, 0, 1.35)), Vector((-math.copysign(1, sf.x), -0.6, 0)), 2.5)

    def stalls(self):
        r = self.rng
        D = self.mb["Detail"]
        for k in range(int(self.len / 7)):
            s = 1 if k % 2 else -1
            y = 5 + k * 7 + r.uniform(-1, 1)
            x = s * (self.road / 2 - 1.6)
            D.box((x, y, 0.45), (1.6, 2.6, 0.9), "wood")
            for dx in (-0.75, 0.75):
                for dy in (-1.25, 1.25):
                    D.cyl((x + dx, y + dy, 1.2), 0.04, 2.4, "wood2", seg=6)
            D.box((x, y, 2.45), (2.0, 3.0, 0.08), "awning")
            for i in range(r.randint(4, 9)):                # goods
                D.sphere((x + r.uniform(-0.6, 0.6), y + r.uniform(-1.1, 1.1), 0.98), r.uniform(0.08, 0.16),
                         r.choice(("accent", "fabric", "leaf", "glass2")), sub=1)
            if k == 1:
                self.focus["stall"] = shots.focus_point(Vector((x, y, 1.1)), Vector((-s, -0.8, 0)), 3.2)

    def build_lamps(self):
        for i, (p, c, e) in enumerate(self.lamps):
            ld = bpy.data.lights.new(f"PW_StreetLamp{i}", "POINT")
            ld.energy, ld.color, ld.shadow_soft_size = e, c, 0.2
            o = bpy.data.objects.new(f"PW_StreetLamp{i}", ld)
            o.location = p
            self.col.objects.link(o)

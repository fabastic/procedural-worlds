"""Terrain kit: open landscapes from biome data (presets/settings.json entry "biome").
A heightfield (amplitude/roughness per biome, optional valley path and water), scattered vegetation /
rocks by biome rules, and an optional landmark (cabin, ruin, tent camp, gravestones, craters, barn).
Camera at eye level looking across toward the landmark with the horizon in frame."""
import math, random
import bpy, bmesh
from mathutils import Vector, noise
from .mb import MB
from . import props as P
from .room import era_palette, _c
from .. import core, shots
from ..ink import srgb

BIOMES = {
    #           ground A / B (sRGB)                   amp  rough  scatter: (kind, density per 100 m2)
    "forest":   dict(ga=(0.40, 0.50, 0.30), gb=(0.32, 0.40, 0.26), amp=2.5, rough=0.06, scatter=[("conifer", 2.2), ("tree", 1.2), ("rock", 0.3), ("bush", 1.0)]),
    "jungle":   dict(ga=(0.30, 0.48, 0.28), gb=(0.24, 0.38, 0.22), amp=2.0, rough=0.08, scatter=[("palm", 1.4), ("tree", 2.0), ("bush", 3.0)]),
    "desert":   dict(ga=(0.88, 0.74, 0.52), gb=(0.80, 0.64, 0.44), amp=4.0, rough=0.03, scatter=[("cactus", 0.35), ("rock", 0.25)]),
    "snowfield": dict(ga=(0.94, 0.95, 0.96), gb=(0.82, 0.86, 0.90), amp=3.0, rough=0.04, scatter=[("conifer_snow", 0.8), ("rock", 0.2)]),
    "mountain": dict(ga=(0.58, 0.56, 0.52), gb=(0.45, 0.50, 0.40), amp=14.0, rough=0.035, scatter=[("rock", 0.8), ("conifer", 0.5)]),
    "swamp":    dict(ga=(0.38, 0.40, 0.28), gb=(0.30, 0.32, 0.24), amp=0.8, rough=0.08, water=0.15, scatter=[("dead_tree", 0.6), ("tree", 0.6), ("reed", 3.0)]),
    "field":    dict(ga=(0.62, 0.66, 0.40), gb=(0.70, 0.62, 0.36), amp=1.6, rough=0.03, scatter=[("tree", 0.1), ("bush", 0.3), ("reed", 1.5)]),
    "wasteland": dict(ga=(0.48, 0.42, 0.36), gb=(0.38, 0.34, 0.30), amp=1.5, rough=0.05, scatter=[("dead_tree", 0.3), ("rock", 0.6), ("debris", 1.5)]),
    "alien":    dict(ga=(0.55, 0.40, 0.58), gb=(0.38, 0.50, 0.55), amp=6.0, rough=0.05, scatter=[("crystal", 0.8), ("rock", 0.5)]),
}


SCATTER = {}         # biome scatter kind -> fn(terrain, x, y, z, scale)
LANDMARKS = {}       # name -> fn(terrain, x, y, z): add geometry to terrain.mb[...] and set terrain.focus["landmark"]


class Terrain:
    def __init__(self, col, entry, layers, seed, mood):
        self.col, self.E, self.L, self.mood, self.seed = col, entry, layers, mood, seed
        self.rng = random.Random(f"terrain:{entry['_name']}:{seed}")
        eras = core.load_preset("era")
        self.era = layers.get("era") if layers.get("era") in eras else entry["eras"][0]
        cond = core.load_preset("conditions")
        self.state = cond["state"].get(layers.get("state", "lived-in"), cond["state"]["lived-in"])
        self.weather = cond["weather"].get(layers.get("weather", "clear"), cond["weather"]["clear"])
        self.B = dict(BIOMES[entry.get("biome", "forest")])
        if self.weather.get("snow_cover"):
            self.B["ga"], self.B["gb"] = BIOMES["snowfield"]["ga"], BIOMES["snowfield"]["gb"]
        self.pal = era_palette(eras[self.era], mood, self.state)
        self.pal.update({"groundA": srgb(*self.B["ga"]), "groundB": srgb(*self.B["gb"]),
                         "bark": srgb(0.36, 0.27, 0.20), "foliage": srgb(0.30, 0.44, 0.28), "foliage2": srgb(0.38, 0.52, 0.30),
                         "snow": srgb(0.95, 0.96, 0.97), "cactus": srgb(0.40, 0.55, 0.36), "crystal": {"color": srgb(0.60, 0.90, 0.85), "emission": srgb(0.5, 0.9, 0.85), "strength": 2.0},
                         "water": srgb(0.30, 0.42, 0.44), "rock": srgb(0.55, 0.53, 0.50), "reed": srgb(0.55, 0.55, 0.32)})
        self.mb = {k: MB(f"PW_Land{k}") for k in ("Veg", "Rocks", "Landmark", "Glow")}
        self.focus, self.lamps = {}, []
        self.size = entry.get("size", 120.0)

    def h(self, x, y):
        B = self.B
        n = core.fbm(x * B["rough"], y * B["rough"], self.seed, 4)
        z = n * B["amp"]
        if self.E.get("valley", True):                  # a flat walkable lane toward the landmark
            z *= min(1.0, abs(x) / 12.0 + 0.25)
        return z

    def run(self):
        r = self.rng
        S = self.size
        n = 110
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=S / 2)
        for v in bm.verts:
            v.co.y += S / 2 - 10
            v.co.z = self.h(v.co.x, v.co.y)
        me = bpy.data.meshes.new("PW_LandGround")
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        m = bpy.data.materials.get("PW_LandGround") or bpy.data.materials.new("PW_LandGround")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out, bsdf = nt.nodes.new("ShaderNodeOutputMaterial"), nt.nodes.new("ShaderNodeBsdfPrincipled")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 0.08
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.interpolation = "CONSTANT"
        ramp.color_ramp.elements[0].color = (*self.pal["groundA"], 1)
        ramp.color_ramp.elements[1].position = 0.55
        ramp.color_ramp.elements[1].color = (*self.pal["groundB"], 1)
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        me.materials.append(m)
        g = bpy.data.objects.new("PW_LandGround", me)
        self.col.objects.link(g)
        g["pw_wonk"] = 0.0
        if self.B.get("water") is not None or self.E.get("water"):
            wl = self.E.get("water", self.B.get("water", 0.0))
            self.mb["Glow"].box((0, S / 2 - 10, wl - 0.05), (S, S, 0.1), "water")
        self.landmark()
        self.scatter()
        for k, mbk in self.mb.items():
            if not mbk.empty():
                o = mbk.build(self.col, self.pal)
                if k == "Glow":
                    o["pw_line"] = 0 if not self.E.get("water") else 1
        for i, (p, c, e) in enumerate(self.lamps):
            ld = bpy.data.lights.new(f"PW_LandLamp{i}", "POINT")
            ld.energy, ld.color, ld.shadow_soft_size = e, c, 0.3
            o = bpy.data.objects.new(f"PW_LandLamp{i}", ld)
            o.location = p
            self.col.objects.link(o)
        lm = Vector(self.focus.get("landmark", {"pos": (0, 30, 2)})["pos"])
        cam = Vector((r.uniform(-2, 2), -6.0, 0.0))
        cam.z = self.h(cam.x, cam.y) + (1.7 if self.B["amp"] < 8 else 3.0)
        tgt = Vector((lm.x * 0.6, lm.y, max(lm.z, cam.z) + 0.5))
        tgt = cam + (tgt - cam).normalized() * min(18.0, (tgt - cam).length)
        self.focus["horizon"] = shots.focus_point(Vector((0, S * 0.9, self.h(0, S * 0.9) + 4)), Vector((0, -1, 0)), 40.0)
        self.focus["path"] = shots.focus_point(Vector((0, 8, self.h(0, 8) + 1.0)), Vector((0.2, -1, 0)), 4.0)
        sun = {"DAY": (50, 200), "GOLDEN": (14, 140), "DUSK": (11, 125), "NIGHT": (38, 150)}[self.mood]
        return {"objects": len(self.col.objects), "focus_points": self.focus, "spawn": {"focus": "path"},
                "camera": {"location": tuple(cam), "target": tuple(tgt), "lens": 32, "clip_end": 2000.0},
                "sun_dir": sun, "sun_scale": self.weather.get("sun_scale", 1.0), "sky_scale": self.weather.get("sky_scale", 1.0),
                "ink": {"grime": self.state.get("grime", 1.0) * 0.6, "base_height": 0.6, "line_scale": 1.15,
                        "sea_color": self.pal["groundB"]}}

    # ------------------------------------------------------------------ vegetation / rocks
    def tree(self, V, x, y, z, s, kind):
        r = self.rng
        if kind in ("conifer", "conifer_snow"):
            V.cyl((x, y, z + 0.8 * s), 0.18 * s, 1.6 * s, "bark", seg=6)
            for k in range(3):
                V.cyl((x, y, z + (1.6 + k * 1.3) * s), (1.6 - k * 0.4) * s, 2.2 * s, "foliage" if kind == "conifer" else "snow", seg=7, r2=0.05)
        elif kind == "palm":
            V.cyl((x, y, z + 2.5 * s), 0.15 * s, 5 * s, "bark", seg=6, r2=0.1 * s)
            for k in range(6):
                a = k / 6 * math.tau
                V.box((x + math.cos(a) * 1.0 * s, y + math.sin(a) * 1.0 * s, z + 5.0 * s), (2.2 * s, 0.5 * s, 0.08), "foliage", rot_z=a)
        elif kind == "dead_tree":
            V.cyl((x, y, z + 1.5 * s), 0.16 * s, 3 * s, "bark", seg=6, r2=0.05)
            for k in range(3):
                a = r.uniform(0, math.tau)
                V.box((x + math.cos(a) * 0.6 * s, y + math.sin(a) * 0.6 * s, z + (2 + k * 0.5) * s), (1.4 * s, 0.08, 0.08), "bark", rot_z=a)
        else:
            V.cyl((x, y, z + 1.2 * s), 0.2 * s, 2.4 * s, "bark", seg=6)
            for k in range(3):
                V.sphere((x + r.uniform(-0.7, 0.7) * s, y + r.uniform(-0.7, 0.7) * s, z + (2.6 + r.uniform(0, 0.9)) * s),
                         r.uniform(1.0, 1.5) * s, r.choice(("foliage", "foliage2")), sub=1)

    def scatter(self):
        r = self.rng
        V, Rk = self.mb["Veg"], self.mb["Rocks"]
        S = self.size
        area = S * S / 100.0
        lm = Vector(self.focus.get("landmark", {"pos": (0, 30, 0)})["pos"])
        for kind, dens in self.B["scatter"]:
            for _ in range(int(dens * area * 0.25)):
                x, y = r.uniform(-S / 2, S / 2), r.uniform(-8, S - 12)
                if abs(x) < 3.5 and y < S * 0.5 or (Vector((x, y, 0)) - Vector((lm.x, lm.y, 0))).length < 8:
                    continue                                     # keep the lane + landmark clear
                if abs(x) < 6 and y < 4:
                    continue
                z = self.h(x, y)
                s = r.uniform(0.7, 1.4)
                if kind in ("conifer", "conifer_snow", "tree", "palm", "dead_tree"):
                    self.tree(V, x, y, z, s, kind)
                elif kind == "rock":
                    Rk.sphere((x, y, z + 0.2 * s), r.uniform(0.4, 1.2) * s, "rock", sub=1, squash=0.6)
                elif kind == "bush":
                    V.sphere((x, y, z + 0.3), r.uniform(0.4, 0.8), "foliage2", sub=1, squash=0.7)
                elif kind == "cactus":
                    V.cyl((x, y, z + 1.2 * s), 0.22 * s, 2.4 * s, "cactus", seg=8)
                    V.cyl((x + 0.45 * s, y, z + 1.5 * s), 0.14 * s, 0.9 * s, "cactus", seg=8)
                    V.cyl((x + 0.45 * s, y, z + 1.0 * s), 0.14 * s, 0.4 * s, "cactus", seg=8, axis="X")
                elif kind == "reed":
                    for k in range(4):
                        V.box((x + r.uniform(-0.2, 0.2), y + r.uniform(-0.2, 0.2), z + 0.4), (0.04, 0.04, 0.8 * s), "reed",
                              rot_z=r.uniform(0, 3))
                elif kind == "crystal":
                    V.cyl((x, y, z + 1.0 * s), 0.4 * s, 2.0 * s, "crystal", seg=5, r2=0.0)
                elif kind in SCATTER:
                    SCATTER[kind](self, x, y, z, s)
                elif kind == "debris":
                    Rk.box((x, y, z + 0.1), (r.uniform(0.3, 1.5), r.uniform(0.2, 0.6), 0.2), r.choice(("wood2", "metal2", "rock")),
                           rot_z=r.uniform(0, 6.28))

    # ------------------------------------------------------------------ landmarks
    def landmark(self):
        r = self.rng
        kind = self.E.get("landmark")
        Lm = self.mb["Landmark"]
        x, y = r.uniform(-4, 4), r.uniform(17, 23)
        z = self.h(x, y)
        night = self.mood in ("DUSK", "NIGHT")
        if kind in LANDMARKS:                       # extension landmarks (kits/ext/*)
            return LANDMARKS[kind](self, x, y, z)
        if kind == "cabin":
            Lm.box((x, y, z + 1.4), (6, 4.5, 2.8), "wood")
            Lm.poly([(x - 3.3, y - 2.6, z + 2.8), (x + 3.3, y - 2.6, z + 2.8), (x + 3.3, y, z + 4.6), (x - 3.3, y, z + 4.6)], "wood2")
            Lm.poly([(x - 3.3, y + 2.6, z + 2.8), (x - 3.3, y, z + 4.6), (x + 3.3, y, z + 4.6), (x + 3.3, y + 2.6, z + 2.8)], "wood2")
            Lm.box((x - 0.8, y - 2.27, z + 1.0), (0.9, 0.06, 2.0), "dark")
            Lm.box((x + 1.5, y - 2.27, z + 1.6), (1.0, 0.06, 0.8), "lampshade")
            Lm.box((x + 2.0, y + 1.0, z + 4.6), (0.6, 0.6, 1.6), "stone")
            if night:
                self.lamps.append((Vector((x + 1.5, y - 3.0, z + 1.6)), srgb(1, 0.75, 0.45), 300))
            self.focus["landmark"] = self.focus["cabin"] = shots.focus_point(Vector((x, y, z + 2.0)), Vector((0, -1, 0)), 7.0)
        elif kind == "ruins":
            for k in range(7):
                a = k / 7 * math.pi
                px, py = x + math.cos(a) * 6, y + math.sin(a) * 3
                hh = r.uniform(1.0, 5.0)
                Lm.box((px, py, self.h(px, py) + hh / 2), (1.2, 1.2, hh), "stone", rot_z=r.uniform(-0.1, 0.1))
            Lm.box((x, y + 3.0, z + 4.4), (9, 1.0, 0.8), "stone")
            for k in range(8):
                Lm.box((x + r.uniform(-7, 7), y + r.uniform(-5, 5), z + 0.2), (r.uniform(0.4, 1.4), r.uniform(0.4, 1.0), 0.4), "stone",
                       rot_z=r.uniform(0, 6.28))
            self.focus["landmark"] = self.focus["ruins"] = shots.focus_point(Vector((x, y, z + 2.5)), Vector((0, -1, 0)), 9.0)
        elif kind == "camp":
            for k in range(3):
                a = k / 3 * math.tau + 0.4
                px, py = x + math.cos(a) * 4, y + math.sin(a) * 4
                pz = self.h(px, py)
                Lm.cyl((px, py, pz + 1.0), 1.4, 2.0, "fabric", seg=4, r2=0.02)
            Lm.cyl((x, y, z + 0.1), 0.6, 0.2, "stone", seg=8)
            if night or self.mood == "GOLDEN":
                g = self.mb["Glow"]
                for k in range(3):
                    g.cyl((x + r.uniform(-0.15, 0.15), y + r.uniform(-0.15, 0.15), z + 0.45), 0.25, 0.7, "fire" if k else "fire2", seg=6, r2=0.0)
                self.lamps.append((Vector((x, y, z + 1.0)), srgb(1, 0.6, 0.3), 500))
            self.focus["landmark"] = self.focus["campfire"] = shots.focus_point(Vector((x, y, z + 0.6)), Vector((0, -1, 0)), 3.0)
        elif kind == "graveyard":
            for i in range(5):
                for j in range(4):
                    px, py = x - 6 + i * 3 + r.uniform(-0.4, 0.4), y - 4 + j * 2.6
                    pz = self.h(px, py)
                    Lm.box((px, py, pz + 0.6), (0.8, 0.2, 1.2), "stone", rot_z=r.uniform(-0.15, 0.15))
                    if r.random() < 0.3:
                        Lm.box((px, py, pz + 1.05), (0.12, 0.12, 0.9), "stone")
                        Lm.box((px, py, pz + 1.25), (0.5, 0.12, 0.12), "stone")
            for k in range(14):
                Lm.box((x - 9 + k * 1.4, y - 7, z + 0.6), (0.08, 0.08, 1.2), "metal2")
            Lm.box((x, y - 7, z + 1.1), (19, 0.06, 0.06), "metal2")
            self.focus["landmark"] = self.focus["graves"] = shots.focus_point(Vector((x, y - 3, z + 0.8)), Vector((0, -1, 0)), 6.0)
        elif kind == "battlefield":
            for k in range(12):
                px, py = x + r.uniform(-14, 14), y + r.uniform(-14, 10)
                Lm.cyl((px, py, self.h(px, py) + 0.05), r.uniform(1.5, 3.0), 0.12, "dark", seg=10)
            for k in range(10):
                px = x - 12 + k * 2.6
                Lm.box((px, y - 8, z + 0.5), (0.1, 0.1, 1.0), "wood2", rot_z=r.uniform(-0.3, 0.3))
            Lm.box((x, y - 8, z + 0.7), (26, 0.04, 0.04), "metal2")
            Lm.box((x + 4, y, z + 0.6), (4, 1.2, 1.2), "fabric2")             # sandbag line
            self.focus["landmark"] = self.focus["trench"] = shots.focus_point(Vector((x + 4, y, z + 0.8)), Vector((0, -1, 0)), 6.0)
        elif kind == "barn":
            Lm.box((x, y, z + 2.5), (8, 6, 5), "accent")
            Lm.poly([(x - 4.3, y - 3.2, z + 5), (x + 4.3, y - 3.2, z + 5), (x + 4.3, y, z + 7.5), (x - 4.3, y, z + 7.5)], "wood2")
            Lm.poly([(x - 4.3, y + 3.2, z + 5), (x - 4.3, y, z + 7.5), (x + 4.3, y, z + 7.5), (x + 4.3, y + 3.2, z + 5)], "wood2")
            Lm.box((x, y - 3.02, z + 1.6), (3, 0.06, 3.2), "wood2")
            for k in range(16):
                Lm.box((x - 12 + k * 1.5, y - 9, z + 0.5), (0.1, 0.1, 1.0), "wood")
            Lm.box((x - 0.75, y - 9, z + 0.8), (24, 0.06, 0.12), "wood")
            self.focus["landmark"] = self.focus["barn"] = shots.focus_point(Vector((x, y, z + 3)), Vector((0, -1, 0)), 9.0)
        else:  # a lone big tree as landmark
            self.tree(self.mb["Veg"], x, y, z, 2.0, "tree" if self.B["scatter"][0][0] != "cactus" else "dead_tree")
            self.focus["landmark"] = self.focus["tree"] = shots.focus_point(Vector((x, y, z + 4)), Vector((0, -1, 0)), 8.0)

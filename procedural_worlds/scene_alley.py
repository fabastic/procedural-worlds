"""Cyberpunk alley: a narrow neon back alley between tall modular buildings.

Built for the ink / graphic-novel look: this module only makes geometry, composition, base colours
and lights. ink.py later turns materials into cel shading, draws Line Art and adds wobble.
Geometry is accumulated with a small mesh builder (MB) and emitted as one mesh per building /
prop, so the scene stays at ~100-140 objects and builds in a couple of seconds.

Ink hints set here:
  PW_Reflect_*  road reflection decals   pw_line=0, pw_wonk=0 (emissive, lower strength)
  PW_Steam_*    steam puffs              pw_wonk=1 (extra wobble)
  camera target is placed FOCUS m along the view ray (ink.py sizes lines from that distance)
  emissive materials (Emission Strength > 0): PW_Alley_Neon_*, PW_Alley_Box_*, PW_Alley_Lit_*,
  PW_Alley_Lantern*, PW_Alley_Reflect_*, PW_Alley_Bulb, PW_Alley_FarLit, PW_Alley_Vend*
"""
import math, random
import bpy
from mathutils import Vector
from . import core

Z = Vector((0.0, 0.0, 1.0))
Y_OFF = 5.0
FOCUS = 9.0


# ----------------------------------------------------------------------------------- colours
def srgb(c):
    """'#rrggbb' (sRGB) -> linear RGB tuple."""
    c = c.lstrip("#")
    v = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in v)


def mixc(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


WALLS = {"concrete": "#66756f", "teal": "#4f6763", "terracotta": "#8e4c36", "ochre": "#9c7a3c",
         "sage": "#6c7858", "cream": "#a2977b", "brick": "#6e3226", "soot": "#3e3530"}
GRIME = "#1d1814"
NEON = {"magenta": "#ff2fb5", "cyan": "#19ecff", "yellow": "#d4ff1e", "orange": "#ff4818",
        "mint": "#45ffa2"}
LIT = {"warm": "#ffbb66", "cyan": "#86e6ff", "pink": "#ff92d2"}
POSTER = ["#cbb98d", "#b0452f", "#3f7f7a", "#d9b23b", "#e6dfca", "#7d3f6b", "#1f2a33"]
GRAFFITI = ["#c23a8a", "#d8c23a", "#3aa59a", "#e6e2d6", "#d0552c"]

# per mood: emission factor, practical-light factor, lit-window fraction, haze, sky (bottom, top)
MOOD = {
    "NIGHT":  (1.00, 1.00, 0.42, "#2a1f3a", ("#4a2b5c", "#07070f")),
    "DUSK":   (0.90, 0.75, 0.34, "#6a4a72", ("#e0727a", "#2c2452")),
    "GOLDEN": (0.70, 0.40, 0.20, "#b89070", ("#f2b77a", "#8a7d80")),
    "DAY":    (0.62, 0.30, 0.12, "#a7a8a0", ("#cfcfc4", "#8e9aa0")),
}
# sun_scale, sky_scale, sun_dir(elevation, azimuth) -- sun rakes down the alley onto the right side
SUN = {"NIGHT": (1.0, 4.0, (38, 28)), "DUSK": (1.0, 2.2, (14, 24)),
       "GOLDEN": (0.75, 1.6, (20, 26)), "DAY": (0.6, 1.5, (52, 28))}


def _grime_mat(name, color, dark, amount=0.55):
    """Wall material: base colour mixed toward a soot colour by streaky noise + a soot band at
    street level. The chain feeds Base Color, which the ink module reads for its cel tones."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    b = N("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.85
    tc = N("ShaderNodeTexCoord")
    mp = N("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.2, 2.2, 0.22)
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.9
    nz.inputs["Detail"].default_value = 4.0
    ramp = N("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.48
    ramp.color_ramp.elements[1].position = 0.78
    mul = N("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = amount
    sep = N("ShaderNodeSeparateXYZ")
    mr = N("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 2.2
    mr.inputs["To Min"].default_value = 0.5
    mr.inputs["To Max"].default_value = 0.0
    mx = N("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    mix = N("ShaderNodeMix")
    mix.data_type = "RGBA"

    def sk(coll, ident):
        return next(x for x in coll if x.identifier == ident)
    sk(mix.inputs, "A_Color").default_value = (*color, 1)
    sk(mix.inputs, "B_Color").default_value = (*dark, 1)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    L(nz.outputs["Fac"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], mul.inputs[0])
    L(tc.outputs["Object"], sep.inputs[0])
    L(sep.outputs["Z"], mr.inputs["Value"])
    L(mul.outputs["Value"], mx.inputs[0])
    L(mr.outputs["Result"], mx.inputs[1])
    L(mx.outputs["Value"], sk(mix.inputs, "Factor_Float"))
    L(sk(mix.outputs, "Result_Color"), b.inputs["Base Color"])
    L(b.outputs["BSDF"], out.inputs["Surface"])
    return m


class Mats:
    """All PW_Alley_* materials for one build (reused by name across regenerations)."""

    def __init__(self, mood):
        ef, lk, self.lit_frac, haze, sky = MOOD[mood]
        self.ef, self.lk = ef, lk
        self.haze = srgb(haze)
        # NIGHT: the ink palette multiplies lit tones by a dark blue tint, so lift the
        # non-emissive base colours a little to keep walls/props legible (road/glass stay dark).
        lift = 1.7 if mood == "NIGHT" else 1.0
        nb = lambda c: tuple(min(.85, x * lift) for x in c)
        keep = ("Road", "RoadPatch", "Puddle", "Glass", "GlassFar", "Metal", "SignBoard")

        def mk(name, color, emission=None, **kw):
            if emission is None and name[len("PW_Alley_"):] not in keep:
                color = nb(color)
            return core.make_material(name, color, emission=emission, **kw)
        g = nb(srgb(GRIME))
        self.walls = {k: _grime_mat(f"PW_Alley_Wall_{k}", nb(srgb(c)), g) for k, c in WALLS.items()}
        self.far_walls = {k: _grime_mat(f"PW_Alley_WallFar_{k}", mixc(srgb(c), self.haze, .5),
                                        mixc(g, self.haze, .5), amount=.3) for k, c in WALLS.items()}
        self.trim_dark = mk("PW_Alley_TrimDark", srgb("#2b2622"), rough=.8)
        self.trim_light = mk("PW_Alley_TrimLight", srgb("#8f8a78"), rough=.8)
        self.metal = mk("PW_Alley_Metal", srgb("#1b1817"), rough=.6, metallic=.3)
        self.rust = mk("PW_Alley_Rust", srgb("#6a3520"), rough=.8)
        self.glass = mk("PW_Alley_Glass", srgb("#141b20"), rough=.15)
        self.glass_far = mk("PW_Alley_GlassFar", mixc(srgb("#141b20"), self.haze, .45), rough=.3)
        self.lit = {k: mk(f"PW_Alley_Lit_{k}", srgb(c), rough=.4, emission=srgb(c), strength=2.6 * ef)
                    for k, c in LIT.items()}
        self.far_lit = mk("PW_Alley_FarLit", srgb("#ffc77a"), emission=srgb("#ffc77a"),
                          strength=1.6 * ef)
        self.shutter = mk("PW_Alley_Shutter", srgb("#5b5e5a"), rough=.5, metallic=.4)
        self.road = mk("PW_Alley_Road", srgb("#2c333c"), rough=.15)
        self.patch = mk("PW_Alley_RoadPatch", srgb("#373e46"), rough=.25)
        self.pave = mk("PW_Alley_Pavement", srgb("#4a4f4c"), rough=.7)
        self.puddle = mk("PW_Alley_Puddle", srgb("#41566b"), rough=.04)
        self.board = mk("PW_Alley_SignBoard", srgb("#221e24"), rough=.6)
        self.neon = {k: mk(f"PW_Alley_Neon_{k}", srgb(c), rough=.3, emission=srgb(c),
                           strength=6.5 * ef) for k, c in NEON.items()}
        self.box = {k: mk(f"PW_Alley_Box_{k}", mixc(srgb(c), (1, 1, 1), .45), rough=.4,
                          emission=mixc(srgb(c), (1, 1, 1), .45), strength=3.2 * ef)
                    for k, c in NEON.items()}
        rcols = dict(NEON, warm=LIT["warm"])
        self.reflect = {k: mk(f"PW_Alley_Reflect_{k}", mixc(srgb(c), srgb("#17191b"), .25), rough=.1,
                              emission=srgb(c), strength=1.0 * ef) for k, c in rcols.items()}
        self.lantern = mk("PW_Alley_Lantern", srgb("#ff4a26"), emission=srgb("#ff4a26"),
                          strength=4.5 * ef)
        self.lantern2 = mk("PW_Alley_LanternGold", srgb("#ffb433"), emission=srgb("#ffb433"),
                           strength=4.5 * ef)
        self.bulb = mk("PW_Alley_Bulb", srgb("#ffc070"), emission=srgb("#ffc070"), strength=8 * ef)
        self.vend = mk("PW_Alley_VendPanel", srgb("#bff6ff"), emission=srgb("#bff6ff"),
                       strength=3.0 * ef)
        self.awn_a = mk("PW_Alley_AwningRed", srgb("#9c2a22"), rough=.8)
        self.awn_b = mk("PW_Alley_AwningCream", srgb("#d6cba8"), rough=.8)
        self.noren = mk("PW_Alley_Noren", srgb("#24304f"), rough=.9)
        self.wood = mk("PW_Alley_Wood", srgb("#5e3f28"), rough=.8)
        self.steam = mk("PW_Alley_Steam", srgb("#cfcfc8"), rough=1.0)
        self.cardboard = mk("PW_Alley_Cardboard", srgb("#8b6a44"), rough=.9)
        self.tape = mk("PW_Alley_Tape", srgb("#b59a6a"), rough=.6)
        self.bag = [mk("PW_Alley_Bag0", srgb("#151517"), rough=.3),
                    mk("PW_Alley_Bag1", srgb("#24302a"), rough=.3),
                    mk("PW_Alley_Bag2", srgb("#2c3644"), rough=.3)]
        self.dumpster = [mk("PW_Alley_Dumpster0", srgb("#3c5a48"), rough=.6),
                         mk("PW_Alley_Dumpster1", srgb("#2e4a5e"), rough=.6),
                         mk("PW_Alley_Dumpster2", srgb("#6a3a26"), rough=.6)]
        self.plastic = [mk("PW_Alley_Crate0", srgb("#8f2f2a"), rough=.5),
                        mk("PW_Alley_Crate1", srgb("#2f5f8a"), rough=.5),
                        mk("PW_Alley_Crate2", srgb("#c79a2a"), rough=.5)]
        self.cone = mk("PW_Alley_Cone", srgb("#e0571c"), rough=.5)
        self.white = mk("PW_Alley_White", srgb("#dedbd0"), rough=.6)
        self.ac = mk("PW_Alley_AC", srgb("#8d8f87"), rough=.6)
        self.tank = mk("PW_Alley_Tank", srgb("#4a3a2c"), rough=.8)
        self.poster = [mk(f"PW_Alley_Poster{i}", srgb(c), rough=.8) for i, c in enumerate(POSTER)]
        self.graffiti = [mk(f"PW_Alley_Graffiti{i}", srgb(c), rough=.7)
                         for i, c in enumerate(GRAFFITI)]
        self.scooter = [mk("PW_Alley_Scooter0", srgb("#b8b2a0"), rough=.4),
                        mk("PW_Alley_Scooter1", srgb("#a33a2c"), rough=.4),
                        mk("PW_Alley_Scooter2", srgb("#3e6e6a"), rough=.4)]
        self.skyline = mk("PW_Alley_Skyline", mixc(srgb("#3b4448"), self.haze, .7), rough=.9)
        self.skyline2 = mk("PW_Alley_Skyline2", mixc(srgb("#2c3134"), self.haze, .55), rough=.9)


# ----------------------------------------------------------------------------- mesh builder
class MB:
    """Accumulates polygons with per-face material + smooth flag; emits one mesh object."""

    def __init__(self):
        self.v, self.f, self.fm, self.fs = [], [], [], []
        self.mats, self._mi = [], {}

    def _m(self, mat):
        i = self._mi.get(mat.name)
        if i is None:
            i = self._mi[mat.name] = len(self.mats)
            self.mats.append(mat)
        return i

    def add(self, pts, faces, mat, smooth=False):
        b = len(self.v)
        self.v.extend((p[0], p[1], p[2]) for p in pts)
        mi = self._m(mat)
        for fc in faces:
            self.f.append(tuple(b + i for i in fc))
            self.fm.append(mi)
            self.fs.append(smooth)

    def poly(self, pts, mat, normal=None, smooth=False):
        pts = [Vector(p) for p in pts]
        if normal is not None:
            nn = Vector((0.0, 0.0, 0.0))
            for i, a in enumerate(pts):
                b = pts[(i + 1) % len(pts)]
                nn.x += (a.y - b.y) * (a.z + b.z)
                nn.y += (a.z - b.z) * (a.x + b.x)
                nn.z += (a.x - b.x) * (a.y + b.y)
            if nn.dot(Vector(normal)) < 0:
                pts.reverse()
        self.add(pts, [tuple(range(len(pts)))], mat, smooth)

    def box_axes(self, c, u, v, w, hu, hv, hw, mat):
        c, u, v, w = Vector(c), Vector(u), Vector(v), Vector(w)
        if u.cross(v).dot(w) < 0:
            w = -w
        pts = [c + u * (hu if i & 1 else -hu) + v * (hv if i & 2 else -hv) + w * (hw if i & 4 else -hw)
               for i in range(8)]
        self.add(pts, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2),
                       (1, 3, 7, 5)], mat)

    def box(self, c, size, mat, rz=0.0):
        cz, sz = math.cos(rz), math.sin(rz)
        self.box_axes(c, (cz, sz, 0), (-sz, cz, 0), Z, size[0] / 2, size[1] / 2, size[2] / 2, mat)

    def box_mm(self, x0, x1, y0, y1, z0, z1, mat):
        self.box_axes(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (1, 0, 0), (0, 1, 0), Z,
                      abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2, mat)

    def seg_box(self, p0, p1, w, h, mat, up=Z):
        """Thin beam from p0 to p1 (stringers, rails, braces)."""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        u = d.normalized()
        v = Vector(up).cross(u)
        if v.length < 1e-4:
            v = Vector((1, 0, 0)).cross(u)
        v.normalize()
        w_ = u.cross(v)
        self.box_axes((p0 + p1) / 2, u, v, w_, d.length / 2, w / 2, h / 2, mat)

    def cyl(self, base, r, h, mat, sides=10, axis=Z, caps=True, smooth=True, r2=None):
        axis = Vector(axis).normalized()
        base = Vector(base)
        ref = Vector((1, 0, 0)) if abs(axis.z) > 0.9 else Vector((0, 0, 1))
        e1 = axis.cross(ref).normalized()
        e2 = axis.cross(e1)
        r2 = r if r2 is None else r2
        ang = [math.tau * k / sides for k in range(sides)]
        pts = [base + (e1 * math.cos(a) + e2 * math.sin(a)) * r for a in ang]
        pts += [base + axis * h + (e1 * math.cos(a) + e2 * math.sin(a)) * r2 for a in ang]
        s = sides
        self.add(pts, [(k, (k + 1) % s, s + (k + 1) % s, s + k) for k in range(s)], mat, smooth)
        if caps:
            b = len(self.v) - 2 * s
            mi = self._m(mat)
            self.f.append(tuple(b + k for k in reversed(range(s))))
            self.f.append(tuple(b + s + k for k in range(s)))
            self.fm += [mi, mi]
            self.fs += [False, False]

    def cone(self, base, r, h, mat, sides=10, smooth=True):
        base = Vector(base)
        pts = [base + Vector((math.cos(a) * r, math.sin(a) * r, 0))
               for a in (math.tau * k / sides for k in range(sides))]
        pts.append(base + Vector((0, 0, h)))
        s = sides
        self.add(pts, [(k, (k + 1) % s, s) for k in range(s)], mat, smooth)
        self.add(pts[:s], [tuple(reversed(range(s)))], mat, False)

    def tube(self, pts, r, mat, sides=6, closed=False, smooth=True):
        pts = [Vector(p) for p in pts]
        n = len(pts)
        if n < 2:
            return
        tans = []
        for i in range(n):
            if closed:
                t = pts[(i + 1) % n] - pts[i - 1]
            else:
                t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
            tans.append(t.normalized())
        ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
        nrm = tans[0].cross(ref).normalized()
        ring_pts = []
        ang = [math.tau * k / sides for k in range(sides)]
        for i in range(n):
            t = tans[i]
            nrm = nrm - t * nrm.dot(t)
            if nrm.length < 1e-6:
                nrm = t.orthogonal()
            nrm.normalize()
            bn = t.cross(nrm)
            ring_pts += [pts[i] + (nrm * math.cos(a) + bn * math.sin(a)) * r for a in ang]
        s = sides
        faces = []
        segs = n if closed else n - 1
        for j in range(segs):
            j1 = (j + 1) % n
            for k in range(s):
                k1 = (k + 1) % s
                faces.append((j * s + k, j * s + k1, j1 * s + k1, j1 * s + k))
        self.add(ring_pts, faces, mat, smooth)

    def blob(self, c, rad, mat, rng, segs=8, rings=5, jit=0.15, floor=None):
        c = Vector(c)
        pts = [c + Vector((0, 0, rad[2]))]
        for i in range(1, rings):
            ph = math.pi * i / rings
            for j in range(segs):
                th = math.tau * j / segs
                f = 1 + rng.uniform(-jit, jit)
                p = c + Vector((math.sin(ph) * math.cos(th) * rad[0] * f,
                                math.sin(ph) * math.sin(th) * rad[1] * f, math.cos(ph) * rad[2] * f))
                if floor is not None:
                    p.z = max(p.z, floor)
                pts.append(p)
        bot = c - Vector((0, 0, rad[2]))
        if floor is not None:
            bot.z = max(bot.z, floor)
        pts.append(bot)
        S = len(pts) - 1
        faces = [(0, 1 + j, 1 + (j + 1) % segs) for j in range(segs)]
        for i in range(rings - 2):
            r0, r1 = 1 + i * segs, 1 + (i + 1) * segs
            faces += [(r0 + j, r1 + j, r1 + (j + 1) % segs, r0 + (j + 1) % segs) for j in range(segs)]
        rl = 1 + (rings - 2) * segs
        faces += [(S, rl + (j + 1) % segs, rl + j) for j in range(segs)]
        self.add(pts, faces, mat, True)

    def slab_poly(self, pts2, z0, z1, mat):
        """Extruded flat polygon (puddles, patches)."""
        a = sum(pts2[i][0] * pts2[(i + 1) % len(pts2)][1] - pts2[(i + 1) % len(pts2)][0] * pts2[i][1]
                for i in range(len(pts2)))
        if a < 0:
            pts2 = list(reversed(pts2))
        n = len(pts2)
        pts = [(x, y, z0) for x, y in pts2] + [(x, y, z1) for x, y in pts2]
        faces = [tuple(range(n, 2 * n)), tuple(reversed(range(n)))]
        faces += [(k, (k + 1) % n, n + (k + 1) % n, n + k) for k in range(n)]
        self.add(pts, faces, mat)

    def build(self, name, col, **props):
        if not self.f:
            return None
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        for m in self.mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", self.fm)
        me.polygons.foreach_set("use_smooth", self.fs)
        me.update()
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        for k, v in props.items():
            ob[k] = v
        return ob


class Frame:
    """Facade coordinates: a along the facade, z up, d out of the wall (toward the alley)."""

    def __init__(self, o, u, n):
        self.o, self.u, self.n = Vector(o), Vector(u), Vector(n)

    def P(self, a, z, d=0.0):
        return self.o + self.u * a + self.n * d + Z * z

    def box(self, mb, a0, a1, z0, z1, d0, d1, mat):
        mb.box_axes(self.P((a0 + a1) / 2, (z0 + z1) / 2, (d0 + d1) / 2), self.u, Z, self.n,
                    abs(a1 - a0) / 2, abs(z1 - z0) / 2, abs(d1 - d0) / 2, mat)

    def quad(self, mb, a0, a1, z0, z1, d, mat, normal=None):
        mb.poly([self.P(a0, z0, d), self.P(a1, z0, d), self.P(a1, z1, d), self.P(a0, z1, d)], mat,
                normal=self.n if normal is None else normal)


# ------------------------------------------------------------------------------------ glyphs
STROKES = [(0, .84, 1, 1), (0, .42, 1, .58), (0, 0, 1, .16), (0, 0, .16, 1), (.42, 0, .58, 1),
           (.84, 0, 1, 1), (0, .42, .5, .58), (.5, .42, 1, .58), (.42, .5, .58, 1), (.42, 0, .58, .5),
           (0, .6, .16, 1), (.84, 0, 1, .4), (.2, .2, .8, .3), (.2, .66, .36, .9), (.64, .1, .8, .34)]


def glyph(rng):
    """Pseudo-kanji: 3-5 strokes from a stroke library (always one full-length spine)."""
    spine = rng.choice([STROKES[1], STROKES[4], STROKES[0], STROKES[3]])
    rest = rng.sample([s for s in STROKES if s != spine], rng.randint(2, 4))
    return [spine] + rest


def glyph_boxes(mb, origin, pv, qv, nv, cw, ch, rects, depth, mat):
    for (x0, y0, x1, y1) in rects:
        c = origin + pv * ((x0 + x1) / 2 * cw) + qv * ((y0 + y1) / 2 * ch) + nv * (depth / 2)
        mb.box_axes(c, pv, qv, nv, (x1 - x0) / 2 * cw, (y1 - y0) / 2 * ch, depth / 2, mat)


# -------------------------------------------------------------------------------- the scene
class CyberpunkAlley:
    """A narrow neon-lit alley between tall buildings, seen from eye level."""
    LABEL = "Cyberpunk alley"

    @staticmethod
    def build(col, seed, size, detail, height, mood="NIGHT", **kw):
        if mood not in MOOD:
            mood = "NIGHT"
        return _Alley(col, seed, mood, height).run()


class _Alley:
    def __init__(self, col, seed, mood, height):
        self.col, self.seed, self.mood = col, seed, mood
        self.hk = max(0.6, min(1.6, height or 1.0))
        self.M = Mats(mood)
        self.signs = []          # dicts: x0,x1,y,zb,zt,key  (for reflections + lights)
        self.lights = []         # (name, type, loc, color, energy, radius)
        self.R = lambda k: random.Random(seed * 7919 + k * 104729)

    # ---------------------------------------------------------------------------- top level
    def run(self):
        R = self.R(0)
        self.W = R.uniform(5.2, 6.8)
        self.L = R.uniform(46.0, 58.0)
        self.cam = Vector((R.uniform(-.55, .55), -2.6, R.uniform(1.5, 1.75)))
        self.y_start = -9.0
        self.sides = {-1: [], 1: []}
        stall_side = R.choice((-1, 1))
        self.stall = (stall_side, R.uniform(11.0, 20.0))

        self._ground()
        self.cables = MB()
        for s in (-1, 1):
            self._side(s)
        self._far_end()
        self._blade_signs()
        self._extra_neon()
        self._overhead()
        self._clutter()
        self._reflections()
        self._make_lights()
        self.cables.build("PW_Cables", self.col)

        # Shift the whole set so the world origin (where a stray default cube usually sits) is
        # behind the camera and out of shot.
        for o in self.col.objects:
            o.location.y += Y_OFF
        # aim down the alley (vanishing point ~0.85 L away, slight upward tilt) but put the target
        # only FOCUS m out along that ray: ink.py sizes lines/wobble from camera->target distance.
        far = Vector((self.cam.x * 0.25 + R.uniform(-.3, .3), self.L * 0.85, R.uniform(5.0, 6.2)))
        cam = self.cam + Vector((0, Y_OFF, 0))
        tgt = tuple(cam + (far + Vector((0, Y_OFF, 0)) - cam).normalized() * FOCUS)
        cam = tuple(cam)
        sun_scale, sky_scale, sun_dir = SUN[self.mood]
        focus = self._focus_points(Vector(cam))
        return {"focus_points": focus, "spawn": {"focus": "alley"},
                "objects": len(self.col.objects),
                "camera": {"location": cam, "target": tgt, "lens": round(R.uniform(21.0, 25.0), 1),
                           "clip_end": 500.0},
                "sun_scale": sun_scale, "sky_scale": sky_scale, "sun_dir": sun_dir,
                "ink": {"line_scale": 1.45}}

    def _focus_points(self, cam):
        """Named story focus points (see shots.py contract)."""
        from . import shots
        col, W, Y = self.col, self.W, Y_OFF

        def axis(p, back=4.0):
            return Vector((0.0, p[1] - back, 1.7))

        bpy.context.view_layer.update()

        def cy(o):                      # joined meshes keep their origin at 0: use the bbox centre
            lo, hi = shots._world_bbox([o])
            return (lo.y + hi.y) / 2

        def nearest(prefix, ymin=4.0):
            objs = [o for o in shots.objects_named(col, prefix) if cy(o) > cam.y + ymin]
            return min(objs, key=cy, default=None)

        fp = {}
        blades = [g for g in self.signs if g.get("kind") == "blade" and (g["y0"] + g["y1"]) / 2 + Y > cam.y + 6]
        if blades:
            g = min(blades, key=lambda g: g["y0"])
            p = Vector(((g["x0"] + g["x1"]) / 2, (g["y0"] + g["y1"]) / 2 + Y, (g["zb"] + g["zt"]) / 2))
            fp["neon_sign"] = shots.focus_point(p, axis(p, 6.0) - p, max(2.0, g["zt"] - g["zb"]))
        side, sy = self.stall
        p = Vector((side * (W / 2 - 1.3), sy + Y, 1.5))
        fp["stall"] = shots.focus_point(p, axis(p, 5.0) - p, 3.5)
        p = Vector((0.0, self.L * 0.85 + Y, 3.5))
        fp["far_end"] = shots.focus_point(p, cam - p, 12.0)
        p = Vector((cam.x, cam.y + 7.0, 0.05))
        fp["puddle"] = shots.focus_point(p, cam - p, 2.4)
        p = Vector((0.0, cam.y + 16.0, 3.5))
        fp["alley"] = shots.focus_point(p, cam - p, 9.0)
        p = Vector((-W / 2 + 0.3, cam.y + 13.0, 8.0))
        fp["fire_escape"] = shots.focus_point(p, axis(p, 6.0) - p, 7.0)
        for name, prefix in (("vending", "PW_Vending"), ("dumpster", "PW_Dumpster"), ("steam", "PW_Steam"),
                             ("scooter", "PW_Scooter"), ("trash", "PW_TrashBags")):
            o = nearest(prefix)
            if o is not None:
                lo, hi = shots._world_bbox([o])
                c = shots.focus_from_objects([o], axis((lo + hi) / 2), z_frac=0.5)
                fp[name] = c
        for name, oname in (("lanterns", "PW_LanternString"), ("street_lamp", "PW_StreetLamp")):
            o = col.objects.get(oname)
            if o is not None:
                fp[name] = shots.focus_from_objects([o], cam, size=3.0, z_frac=0.5)
        return {k: v for k, v in fp.items() if v}

    # ------------------------------------------------------------------------------ helpers
    def facade_x(self, s, y):
        for b in self.sides[s]:
            if b["y0"] <= y <= b["y1"]:
                return s * (self.W / 2 + b["sb"]), b
        return s * self.W / 2, None

    def _light(self, name, loc, color, energy, kind="POINT", radius=0.4):
        self.lights.append((name, kind, tuple(loc), color, energy, radius))

    # ------------------------------------------------------------------------------- ground
    def _ground(self):
        M, W, L, R = self.M, self.W, self.L, self.R(1)
        mb = MB()
        y0, y1 = self.y_start - 2, L + 16
        # road strip subdivided along y so the ink wobble has vertices to work with
        xs = [-60, -W / 2 - 1.5, W / 2 + 1.5, 60]
        ys = [y0 + (y1 - y0) * i / 24 for i in range(25)]
        for j in range(24):
            for i in range(3):
                mb.poly([(xs[i], ys[j], 0), (xs[i + 1], ys[j], 0), (xs[i + 1], ys[j + 1], 0),
                         (xs[i], ys[j + 1], 0)], M.road, normal=Z)
        road = mb.build("PW_Road", self.col)
        road["pw_wonk"] = 0.2

        pv = MB()
        # raised pavement strips along both walls -> strong perspective lines
        for s in (-1, 1):
            pv.box_mm(s * (W / 2 - .55), s * (W / 2 + 1.2), y0, L + .3, 0, .09, M.pave)
            # kerb stones every ~1.5 m give rhythm
            y = y0
            while y < L:
                pv.box_mm(s * (W / 2 - .58), s * (W / 2 - .5), y + .02, y + 1.48, 0, .1, M.pave)
                y += 1.5
        # centre gutter strip
        pv.box_mm(-.18, .18, y0, L + 12, 0, .012, M.trim_dark)
        # drain grates in the gutter
        y = R.uniform(2, 6)
        while y < L:
            pv.box_mm(-.26, .26, y, y + .45, 0, .02, M.metal)
            for k in range(4):
                pv.box_mm(-.2, .2, y + .06 + k * .1, y + .1 + k * .1, .02, .028, M.trim_dark)
            y += R.uniform(7, 11)
        pv.build("PW_Pavement", self.col)

        # asphalt patches (slightly raised irregular shapes keep ink outlines)
        pa = MB()
        for _ in range(R.randint(5, 8)):
            cx, cy = R.uniform(-W / 2 + .8, W / 2 - .8), R.uniform(0, L)
            pts = []
            n = R.randint(5, 7)
            rx, ry = R.uniform(.5, 1.4), R.uniform(.8, 2.5)
            for k in range(n):
                a = math.tau * k / n + R.uniform(-.2, .2)
                pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
            pa.slab_poly(pts, 0, .003, M.patch)
        # manhole
        mx, my = R.uniform(-W / 2 + 1.2, W / 2 - 1.2), R.uniform(6, 16)
        pa.cyl((mx, my, 0), .38, .02, M.metal, sides=16, smooth=False)
        pa.cyl((mx, my, .02), .3, .006, M.trim_dark, sides=16, smooth=False)
        for k in range(-2, 3):
            pa.box((mx, my + k * .1, .028), (.44 - abs(k) * .08, .025, .006), M.metal)
        self.manhole = (mx, my)
        pa.build("PW_RoadDetail", self.col)

        # puddles: flat dark-blue-grey irregular shapes, slightly raised (keep outlines)
        pu = MB()
        self.puddles = []
        for _ in range(R.randint(5, 8)):
            cx, cy = R.uniform(-W / 2 + .7, W / 2 - .7), R.uniform(1.5, L * .8)
            rx, ry = R.uniform(.4, 1.2), R.uniform(.7, 2.2)
            n = R.randint(9, 13)
            pts = []
            for k in range(n):
                a = math.tau * k / n
                f = R.uniform(.65, 1.15)
                pts.append((cx + math.cos(a) * rx * f, cy + math.sin(a) * ry * f))
            pu.slab_poly(pts, 0, .004, M.puddle)
            self.puddles.append((cx, cy, rx, ry))
        pu.build("PW_Puddles", self.col)


    # ------------------------------------------------------------------------- side blocks
    def _side(self, s):
        R = self.R(10 + (s + 1))
        W, L = self.W, self.L
        y, i = self.y_start, 0
        while y < L - .5:
            bw = R.uniform(6.0, 13.0)
            y1 = min(y + bw, L)
            if L - y1 < 4:
                y1 = L
            H = R.uniform(12.0, 35.0) * self.hk
            if i == 0:
                H = max(H, 18.0 * self.hk)
            sb = 0.0 if i == 0 else R.choice((0.0, 0.0, 0.3, 0.6, 0.9))
            F = Frame((s * (W / 2 + sb), 0, 0), (0, 1, 0), (-s, 0, 0))
            b = {"y0": y, "y1": y1, "sb": sb, "F": F, "s": s}
            self.sides[s].append(b)
            mb = MB()
            stall_y = self.stall[1] if self.stall[0] == s and y + 1 < self.stall[1] < y1 - 1 else None
            info = self._building(F, y, y1, H, R, mb, far=False, stall_y=stall_y,
                                  name=f"{'L' if s < 0 else 'R'}{i}")
            b.update(info)
            mb.build(f"PW_Bldg_{'L' if s < 0 else 'R'}{i}", self.col)
            y, i = y1, i + 1

    def _wall_holes(self, F, mb, a0, a1, z0, z1, holes, wall):
        holes = sorted(holes, key=lambda h: h[0])
        cuts = [a0]
        for h in holes:
            cuts += [h[0], h[1]]
        cuts.append(a1)
        for i in range(len(cuts) - 1):
            ca, cb = cuts[i], cuts[i + 1]
            if cb - ca < 1e-4:
                continue
            if i % 2 == 0:
                F.quad(mb, ca, cb, z0, z1, 0, wall)
            else:
                h = holes[i // 2]
                if h[2] > z0 + 1e-4:
                    F.quad(mb, ca, cb, z0, h[2], 0, wall)
                if h[3] < z1 - 1e-4:
                    F.quad(mb, ca, cb, h[3], z1, 0, wall)
        for (ha0, ha1, hz0, hz1, gm, dep) in holes:
            P = F.P
            mb.poly([P(ha0, hz0, 0), P(ha1, hz0, 0), P(ha1, hz0, -dep), P(ha0, hz0, -dep)], wall, Z)
            mb.poly([P(ha0, hz1, 0), P(ha1, hz1, 0), P(ha1, hz1, -dep), P(ha0, hz1, -dep)], wall, -Z)
            mb.poly([P(ha0, hz0, 0), P(ha0, hz1, 0), P(ha0, hz1, -dep), P(ha0, hz0, -dep)], wall, F.u)
            mb.poly([P(ha1, hz0, 0), P(ha1, hz1, 0), P(ha1, hz1, -dep), P(ha1, hz0, -dep)], wall, -F.u)
            F.quad(mb, ha0, ha1, hz0, hz1, -dep, gm)

    def _building(self, F, a0, a1, H, R, mb, far, stall_y=None, name=""):
        M = self.M
        BW = a1 - a0
        gf = R.uniform(3.9, 4.5)
        fh = R.uniform(2.9, 3.4)
        nfl = max(2, int((H - gf) / fh))
        H = gf + nfl * fh
        wkey = R.choice(list(WALLS))
        wall = (M.far_walls if far else M.walls)[wkey]
        trim = M.trim_light if wkey in ("soot", "brick", "teal") and R.random() < .6 else M.trim_dark
        glass_dark = M.glass_far if far else M.glass
        ribbon = R.random() < .22
        ww, wh, gap = R.uniform(.9, 1.5), R.uniform(1.3, 1.75), R.uniform(.7, 1.5)
        rd = R.uniform(.2, .32)
        balc_p, ac_p = R.uniform(0, .3), R.uniform(.1, .4)
        fire = (not far) and BW > 6 and R.random() < .5
        ledges = R.random() < .7
        lit_frac = self.M.lit_frac * (1.3 if far else 1.0)
        D = 12.0

        # body: end walls + roof
        P = F.P
        for a, nrm in ((a0, -F.u), (a1, F.u)):
            mb.poly([P(a, 0, 0), P(a, 0, -D), P(a, H, -D), P(a, H, 0)], wall, nrm)
        mb.poly([P(a0, H, 0), P(a1, H, 0), P(a1, H, -D), P(a0, H, -D)], wall, Z)

        pitch = ww + gap
        ncol = max(1, int((BW - .6) / pitch))
        m0 = a0 + (BW - ncol * pitch) / 2
        cols = [m0 + pitch * (i + .5) for i in range(ncol)]
        fe = None
        if fire and ncol >= 2:
            k = R.randrange(ncol - 1)
            c = (cols[k] + cols[k + 1]) / 2
            fe = (max(a0 + .3, c - 1.9), min(a1 - .3, c + 1.9))

        def lit_mat():
            r, k = R.random(), R.random()     # always two draws: layout identical across moods
            if r < lit_frac:
                if far:
                    return M.far_lit, True
                return M.lit["warm" if k < .62 else "cyan" if k < .84 else "pink"], True
            return glass_dark, False

        # ---- upper floors
        for f in range(nfl):
            z0 = gf + f * fh
            z1 = z0 + fh
            sill = z0 + .85
            top = min(sill + wh, z1 - .35)
            holes = []
            if ribbon:
                ra0, ra1 = a0 + .7, a1 - .7
                gm, lit = lit_mat()
                holes.append((ra0, ra1, sill, top, gm, rd))
            else:
                for c in cols:
                    gm, lit = lit_mat()
                    holes.append((c - ww / 2, c + ww / 2, sill, top, gm, rd))
            self._wall_holes(F, mb, a0, a1, z0, z1, holes, wall)
            for (ha0, ha1, hz0, hz1, gm, dep) in holes:
                F.box(mb, ha0 - .08, ha1 + .08, hz0 - .09, hz0, 0, .1, trim)          # sill
                # mullions
                nm = max(1, int((ha1 - ha0) / 1.1))
                for m in range(1, nm + (0 if ribbon else 0)):
                    am = ha0 + (ha1 - ha0) * m / nm
                    F.box(mb, am - .03, am + .03, hz0, hz1, -dep, -dep + .05, trim)
                if not ribbon and ha1 - ha0 > .8:
                    am = (ha0 + ha1) / 2
                    F.box(mb, am - .025, am + .025, hz0, hz1, -dep, -dep + .04, trim)
                rb = R.random()
                if gm is not glass_dark and rb < .45:                              # blind
                    zb = hz1 - (hz1 - hz0) * (.25 + .35 * rb / .45)
                    F.box(mb, ha0, ha1, zb, hz1, -dep, -dep + .03, M.trim_dark)
            if ledges or f == 0:
                F.box(mb, a0, a1, z0 - .1, z0 + .08, 0, .14 if f else .22, trim)
            # balconies / AC units per column
            if far:
                continue
            for c in cols:
                in_fe = fe is not None and fe[0] - .4 < c < fe[1] + .4
                r = R.random()
                if not ribbon and not in_fe and r < balc_p and f < nfl - 1:
                    self._balcony(F, mb, c - ww / 2 - .3, c + ww / 2 + .3, z0, R, wall, trim)
                elif not in_fe and r < balc_p + ac_p:
                    side = R.choice((-1, 0, 1)) if not ribbon else 0
                    ac_a = c + side * (ww / 2 + .55) if side else c
                    zz = sill - .72 if side == 0 else sill + .1
                    if a0 + .5 < ac_a < a1 - .5:
                        F.box(mb, ac_a - .4, ac_a + .4, zz, zz + .55, 0, .5, M.ac)
                        F.quad(mb, ac_a - .32, ac_a + .32, zz + .07, zz + .48, .505, M.metal)
                        F.box(mb, ac_a - .35, ac_a - .31, zz - .12, zz, 0, .45, M.metal)
                        F.box(mb, ac_a + .31, ac_a + .35, zz - .12, zz, 0, .45, M.metal)

        # ---- ground floor
        self._ground_floor(F, mb, a0, a1, gf, wall, trim, R, far, stall_y)
        # roof edge, parapet, rooftop stuff
        F.box(mb, a0, a1, H - .35, H, 0, .32, trim)
        F.box(mb, a0, a1, H, H + .9, -.3, 0, wall)
        if not far:
            if fe:
                self._fire_escape(F, mb, fe[0], fe[1], [gf + f * fh for f in range(nfl)], R)
            self._pipes(F, mb, a0, a1, cols, pitch, H, gf, fh, R)
            self._rooftop(F, mb, a0, a1, H, R)
        return {"H": H, "gf": gf, "fh": fh, "cols": cols, "fe": fe}

    def _balcony(self, F, mb, a0, a1, z, R, wall, trim):
        M = self.M
        dep = R.uniform(.8, 1.1)
        F.box(mb, a0, a1, z - .14, z, 0, dep, trim)
        if R.random() < .5:   # solid parapet
            F.box(mb, a0, a1, z, z + 1.0, dep - .08, dep, wall)
            F.box(mb, a0, a0 + .08, z, z + 1.0, 0, dep, wall)
            F.box(mb, a1 - .08, a1, z, z + 1.0, 0, dep, wall)
        else:                 # bars
            mb.tube([F.P(a0, z + 1, 0), F.P(a0, z + 1, dep), F.P(a1, z + 1, dep), F.P(a1, z + 1, 0)],
                    .03, M.metal, sides=4, smooth=False)
            n = max(3, int((a1 - a0) / .25))
            for k in range(n + 1):
                a = a0 + (a1 - a0) * k / n
                F.box(mb, a - .015, a + .015, z, z + 1, dep - .03, dep, M.metal)
        if R.random() < .4:   # laundry line
            zl = z + 1.9
            mb.tube([F.P(a0 + .05, zl, dep - .05), F.P(a1 - .05, zl, dep - .05)], .01, M.metal, 3)
            a = a0 + .2
            while a < a1 - .5:
                w = R.uniform(.3, .6)
                cm = R.choice(M.poster + [M.white, M.awn_a])
                F.box(mb, a, a + w, zl - R.uniform(.5, .9), zl, dep - .07, dep - .04, cm)
                a += w + R.uniform(.05, .3)

    def _ground_floor(self, F, mb, a0, a1, gf, wall, trim, R, far, stall_y):
        M = self.M
        BW = a1 - a0
        n_u = 1 if BW < 7.5 else 2 if BW < 11.5 else 3
        slot = BW / n_u
        holes, extra = [], []
        for k in range(n_u):
            sa0 = a0 + k * slot
            pier = R.uniform(.45, .8)
            oa0, oa1 = sa0 + pier, sa0 + slot - pier
            oh = R.uniform(2.6, min(3.2, gf - .6))
            is_stall = stall_y is not None and sa0 <= stall_y <= sa0 + slot
            kind = "shop" if is_stall else R.choices(("shutter", "shop", "door"), (.45, .35, .2))[0]
            dep = .4
            if kind == "door":
                da0 = oa0 if R.random() < .5 else oa1 - 1.1
                holes.append((da0, da0 + 1.1, 0, 2.3, M.trim_dark, .3))
                wa0, wa1 = (da0 + 1.6, oa1) if da0 == oa0 else (oa0, da0 - .5)
                if wa1 - wa0 > .7:
                    gm = M.lit["warm"] if R.random() < .5 and not far else (M.glass_far if far else M.glass)
                    holes.append((wa0, wa1, 1.0, 2.3, gm, .25))
                extra.append(("door", da0, da0 + 1.1))
            else:
                if kind == "shutter":
                    gm = M.shutter
                else:
                    gm = M.lit["warm"] if is_stall else M.lit[R.choice(("warm", "cyan", "warm", "pink"))]
                    if far:
                        gm = M.far_lit
                holes.append((oa0, oa1, 0, oh, gm, dep))
                extra.append((kind, oa0, oa1, oh, is_stall))
        self._wall_holes(F, mb, a0, a1, 0, gf, holes, wall)
        # posters on piers between openings
        cuts = sorted(holes, key=lambda h: h[0])
        gaps, prev = [], a0
        for h in cuts:
            if h[0] - prev > .6:
                gaps.append((prev + .08, h[0] - .08))
            prev = h[1]
        if a1 - prev > .6:
            gaps.append((prev + .08, a1 - .08))
        if not far:
            self._posters(F, mb, gaps, R)
        for e in extra:
            kind = e[0]
            if kind == "door":
                F.box(mb, e[1] - .08, e[2] + .08, 2.3, 2.42, 0, .1, trim)
                if not far and R.random() < .6:     # little door lamp
                    am = (e[1] + e[2]) / 2
                    F.box(mb, am - .1, am + .1, 2.55, 2.75, 0, .18, M.bulb)
                continue
            _, oa0, oa1, oh, is_stall = e
            if kind == "shutter":
                z = .32
                while z < oh - .4:
                    F.box(mb, oa0, oa1, z, z + .045, -.4, -.37, M.trim_dark)
                    z += R.uniform(.3, .36)
                F.box(mb, oa0 - .05, oa1 + .05, oh - .38, oh, -.4, .06, M.shutter)
                if not far:
                    for _ in range(R.randint(0, 3)):    # graffiti tags
                        ca, cz = R.uniform(oa0 + .4, oa1 - .4), R.uniform(.5, oh - .8)
                        gm = R.choice(M.graffiti)
                        a = ca - R.uniform(.3, .7)
                        zz = cz
                        for j in range(R.randint(3, 6)):      # zigzag tag strokes
                            a2 = a + R.uniform(.12, .3)
                            z2 = cz + R.uniform(-.25, .25)
                            th = R.uniform(.04, .08)
                            mb.poly([F.P(a, zz - th, -.355), F.P(a2, z2 - th, -.355), F.P(a2, z2 + th, -.355),
                                     F.P(a, zz + th, -.355)], gm, normal=F.n)
                            a, zz = a2, z2
            else:   # lit shop window: frame + silhouettes of shelves and goods
                d = -.4
                n = max(2, int((oa1 - oa0) / 1.2))
                for m in range(1, n):
                    am = oa0 + (oa1 - oa0) * m / n
                    F.box(mb, am - .04, am + .04, 0, oh, d, d + .08, M.trim_dark)
                F.box(mb, oa0, oa1, 2.2, 2.27, d, d + .08, M.trim_dark)
                if not far and not is_stall:
                    for zs in (.9, 1.6):
                        F.box(mb, oa0 + .1, oa1 - .1, zs, zs + .04, d + .1, d + .3, M.trim_dark)
                        a = oa0 + .2
                        while a < oa1 - .4:
                            w = R.uniform(.12, .35)
                            F.box(mb, a, a + w, zs + .04, zs + .04 + R.uniform(.15, .45), d + .12, d + .26,
                                  M.metal)
                            a += w + R.uniform(.05, .3)
                    if self.Fside(F):
                        self.signs.append(self._sign_info(F, oa0, oa1, .3, oh - .3, .05, .1, "warm",
                                                          kind="shop"))
            # shop sign above the opening
            sh = R.uniform(.6, .95)
            zs0 = oh + .12
            if not is_stall and R.random() < (.8 if not far else .6) and zs0 + sh < gf - .15:
                self._hsign(F, oa0 - .1, oa1 + .1, zs0, zs0 + sh, R, far)
            if is_stall:
                self._stall(F, oa0, oa1, oh, R)
                self._hsign(F, oa0 - .1, oa1 + .1, zs0 + .25, min(gf - .1, zs0 + .25 + sh), R, far,
                            force_light=True)

    def Fside(self, F):
        return abs(F.u.y) > .5

    def _posters(self, F, mb, gaps, R):
        M = self.M
        for g0, g1 in gaps:
            if R.random() < .25:
                continue
            for k in range(R.randint(1, 4)):
                w, h = R.uniform(.35, .65), R.uniform(.5, .9)
                if g1 - g0 < w + .05:
                    break
                ca, cz = R.uniform(g0 + w / 2, g1 - w / 2), R.uniform(1.0, 2.0)
                ang = R.uniform(-.12, .12)
                cu, cz_ = math.cos(ang), math.sin(ang)
                d = .012 + k * .006

                def pt(x, z):
                    return F.P(ca + x * cu - z * cz_, cz + x * cz_ + z * cu, d)
                mb.poly([pt(-w / 2, -h / 2), pt(w / 2, -h / 2), pt(w / 2, h / 2), pt(-w / 2, h / 2)],
                        R.choice(M.poster), normal=F.n)
                # a dark title band / block on the sheet
                bh = R.uniform(.12, .3)
                y0 = R.uniform(-h / 2 + .05, h / 2 - bh - .05)
                mb.poly([pt(-w / 2 + .05, y0), pt(w / 2 - .05, y0), pt(w / 2 - .05, y0 + bh),
                         pt(-w / 2 + .05, y0 + bh)], R.choice((M.trim_dark, M.poster[1], M.poster[6])),
                        normal=F.n)
                mb.v[-4:] = [(p[0] + F.n.x * .003, p[1] + F.n.y * .003, p[2]) for p in mb.v[-4:]]

    def _fire_escape(self, F, mb, a0, a1, levels, R):
        M = self.M
        dep = 1.25
        met = M.metal
        for i, z in enumerate(levels):
            F.box(mb, a0, a1, z - .07, z, 0, dep, met)
            for zr in (z + 1.0, z + .5):
                mb.tube([F.P(a0, zr, .05), F.P(a0, zr, dep), F.P(a1, zr, dep), F.P(a1, zr, .05)], .022,
                        met, sides=4, smooth=False)
            n = int((a1 - a0) / .32)
            for k in range(n + 1):
                a = a0 + (a1 - a0) * k / n
                F.box(mb, a - .014, a + .014, z, z + 1.0, dep - .03, dep, met)
            for a in (a0, a1):
                for dd in (.4, .8):
                    F.box(mb, a - .014, a + .014, z, z + 1.0, dd - .014, dd + .014, met)
            # diagonal brace to the wall
            mb.seg_box(F.P(a0 + .2, z - .07, dep - .05), F.P(a0 + .2, z - .9, .02), .04, .04, met)
            mb.seg_box(F.P(a1 - .2, z - .07, dep - .05), F.P(a1 - .2, z - .9, .02), .04, .04, met)
            if i < len(levels) - 1:
                z2 = levels[i + 1]
                run = min(a1 - a0 - .5, (z2 - z) * .95)
                if i % 2 == 0:
                    sa, ea = a0 + .25, a0 + .25 + run
                else:
                    sa, ea = a1 - .25, a1 - .25 - run
                for dd in (dep * .45, dep - .06):
                    mb.seg_box(F.P(sa, z, dd), F.P(ea, z2, dd), .03, .16, met)
                mb.seg_box(F.P(sa, z + .9, dep - .06), F.P(ea, z2 + .9, dep - .06), .03, .03, met)
                ns = int((z2 - z) / .24)
                for k in range(1, ns):
                    t = k / ns
                    a = sa + (ea - sa) * t
                    zz = z + (z2 - z) * t
                    F.box(mb, a - .1, a + .1, zz - .03, zz, dep * .45, dep - .06, met)
        # drop ladder below the first platform
        z = levels[0]
        la = a1 - .55
        for a in (la, la + .42):
            F.box(mb, a - .02, a + .02, 2.2, z, dep - .12, dep - .08, met)
        zz = 2.35
        while zz < z - .1:
            F.box(mb, la, la + .42, zz - .015, zz + .015, dep - .12, dep - .08, met)
            zz += .3

    def _pipes(self, F, mb, a0, a1, cols, pitch, H, gf, fh, R):
        M = self.M
        cand = [a0 + .22, a1 - .22] + [c + pitch / 2 for c in cols[:-1]]
        for _ in range(R.randint(1, 3)):
            a = R.choice(cand)
            r = R.uniform(.05, .09)
            mat = R.choice((M.metal, M.rust, M.trim_dark))
            d = .12 + r
            pts = [F.P(a, .05, d)]
            if R.random() < .45:
                zj = R.uniform(gf, H - 3)
                da = R.choice((-.5, .5))
                pts += [F.P(a, zj, d), F.P(a + da, zj + .5, d), F.P(a + da, H - .2, d)]
                a_top = a + da
            else:
                pts.append(F.P(a, H - .2, d))
                a_top = a
            mb.tube(pts, r, mat, sides=6)
            F.box(mb, a_top - .18, a_top + .18, H - .5, H - .15, 0, .38, mat)       # hopper
            z = gf
            while z < H - 1:
                F.box(mb, a - .03, a + .03, z, z + .08, 0, d, M.metal)
                z += fh
        # small louvred vents just above the shop level
        for _ in range(R.randint(0, 2)):
            a = R.uniform(a0 + .6, a1 - .6)
            z = gf - .2 - R.uniform(0, .3)
            F.box(mb, a - .3, a + .3, z - .5, z, 0, .18, M.ac)
            for k in range(4):
                F.box(mb, a - .26, a + .26, z - .45 + k * .11, z - .41 + k * .11, .18, .2, M.metal)

    def _rooftop(self, F, mb, a0, a1, H, R):
        M = self.M
        BW = a1 - a0
        if R.random() < .6 and BW > 4:                         # water tank on legs
            a = R.uniform(a0 + 1.8, a1 - 1.8)
            d = -R.uniform(1.8, 3.0)
            r = R.uniform(1.0, 1.4)
            lh = R.uniform(1.2, 2.2)
            c = F.P(a, H, d)
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                mb.box((c.x + dx * r * .6, c.y + dy * r * .6, H + lh / 2), (.12, .12, lh), M.metal)
            mb.box((c.x, c.y, H + lh * .55), (r * 1.3, .06, .06), M.metal, rz=.78)
            mb.cyl((c.x, c.y, H + lh), r, R.uniform(1.8, 2.6), M.tank, sides=14)
            top = H + lh + 2.6
            mb.cyl((c.x, c.y, H + lh + 2.0), r + .05, .08, M.metal, sides=14)
            mb.cone((c.x, c.y, top - .45), r + .08, .7, M.tank, sides=14)
        for _ in range(R.randint(0, 3)):                       # antennas
            a = R.uniform(a0 + .5, a1 - .5)
            d = -R.uniform(.4, 1.6)
            h = R.uniform(2.5, 7.0)
            mb.tube([F.P(a, H + .9, d), F.P(a, H + .9 + h, d)], .035, M.metal, 4, smooth=False)
            for k in range(R.randint(1, 3)):
                zz = H + .9 + h * (.55 + .14 * k)
                w = R.uniform(.4, 1.2)
                mb.seg_box(F.P(a - w / 2, zz, d), F.P(a + w / 2, zz, d), .03, .03, M.metal)
        if R.random() < .35:                                   # satellite dish
            a = R.uniform(a0 + .6, a1 - .6)
            c = F.P(a, H + 1.3, -.4)
            mb.cyl(c, .45, .12, M.white, sides=10, axis=(F.n * .7 + Z * .7), r2=.55)
            mb.box((c.x, c.y, H + 1.05), (.06, .06, .5), M.metal)
        if R.random() < .5:                                    # stair housing
            aa = R.uniform(a0 + .5, a1 - 3)
            F.box(mb, aa, aa + 2.5, H, H + 2.6, -5.5, -3.0, M.trim_dark)

    # ---------------------------------------------------------------------------- signs
    def _sname(self):
        self.n_sign = getattr(self, "n_sign", 0) + 1
        return f"PW_Sign_{self.n_sign:02d}"

    def _sign_info(self, F, a0, a1, z0, z1, d0, d1, key, kind="blade"):
        pts = [F.P(a, 0, d) for a in (a0, a1) for d in (d0, d1)]
        return {"x0": min(p.x for p in pts), "x1": max(p.x for p in pts),
                "y0": min(p.y for p in pts), "y1": max(p.y for p in pts),
                "zb": z0, "zt": z1, "key": key, "kind": kind}

    def _hsign(self, F, a0, a1, z0, z1, R, far, force_light=False):
        """Horizontal shop sign flat on the facade with a row of glyphs."""
        M = self.M
        mb = MB()
        key = R.choice(list(NEON))
        light = force_light or R.random() < .45
        bmat = M.box[key] if light else M.board
        gmat = M.board if light else M.neon[key]
        F.box(mb, a0, a1, z0, z1, 0, .18, bmat)
        F.box(mb, a0 - .04, a1 + .04, z0 - .04, z0, 0, .2, M.metal)
        h = z1 - z0
        ch = h * .62
        n = max(1, int((a1 - a0 - .3) / (ch * 1.25)))
        n = min(n, R.randint(2, 6))
        total = n * ch * 1.25 - ch * .25
        st = (a0 + a1) / 2 - total / 2
        for k in range(n):
            o = F.P(st + k * ch * 1.25, z0 + h * .19, .18)
            glyph_boxes(mb, o, F.u, Z, F.n, ch, ch, glyph(R), .035, gmat)
        if not light and R.random() < .6:
            mb.tube([F.P(a0 + .06, z0 + .06, .22), F.P(a1 - .06, z0 + .06, .22),
                     F.P(a1 - .06, z1 - .06, .22), F.P(a0 + .06, z1 - .06, .22)], .022,
                    M.neon[R.choice(list(NEON))], sides=5, closed=True)
        mb.build(self._sname(), self.col)
        if not far:
            self.signs.append(self._sign_info(F, a0, a1, z0, z1, 0, .2, key, kind="h"))

    def _blade(self, F, a, z0, h, proj, R, key=None, light=None):
        """Vertical blade sign projecting from the wall, glyphs stacked on the camera-facing face."""
        M = self.M
        mb = MB()
        key = key or R.choice(list(NEON))
        light = (R.random() < .4) if light is None else light
        t = R.uniform(.16, .24)
        d0, d1 = .35, .35 + proj
        bmat = M.box[key] if light else M.board
        gmat = M.board if light else M.neon[key]
        # board + brackets
        F.box(mb, a - t / 2, a + t / 2, z0, z0 + h, d0, d1, bmat)
        for zb in (z0 + .25, z0 + h - .25):
            F.box(mb, a - .03, a + .03, zb - .04, zb + .04, 0, d0 + .05, M.metal)
        F.box(mb, a - t / 2 - .02, a + t / 2 + .02, z0 + h, z0 + h + .1, d0 - .02, d1 + .02, M.metal)
        # camera-facing face is the one at -u (camera looks toward +y)
        sgn = -1 if F.u.y > 0 else 1
        fa = a + sgn * t / 2
        nv = F.u * sgn
        cw = proj * .72
        n = max(1, int((h - .3) / (cw * 1.18)))
        zs = z0 + h / 2 + (n * cw * 1.18 - cw * .18) / 2 - cw
        pv = F.n
        for k in range(n):
            o = F.P(fa, zs - k * cw * 1.18, (d0 + d1) / 2 - cw / 2)
            o = o + nv * 0.0
            glyph_boxes(mb, o, pv, Z, nv, cw, cw, glyph(R), .04, gmat)
        # neon tube outline around the face
        tk = key if R.random() < .6 else R.choice(list(NEON))
        off = .06
        lp = [F.P(fa, z0 + off, d0 + off), F.P(fa, z0 + off, d1 - off), F.P(fa, z0 + h - off, d1 - off),
              F.P(fa, z0 + h - off, d0 + off)]
        lp = [p + nv * .06 for p in lp]
        mb.tube(lp, .028, M.neon[tk], sides=5, closed=True)
        mb.build(self._sname(), self.col)
        info = self._sign_info(F, a - t / 2, a + t / 2, z0, z0 + h, d0, d1, key)
        info["power"] = h * proj
        self.signs.append(info)
        return info

    def _blade_signs(self):
        R = self.R(30)
        L = self.L
        plan = [(-1, R.uniform(5.5, 9.0)), (1, R.uniform(7.0, 12.0))]
        n = R.randint(5, 8)
        for k in range(n):
            s = -1 if k % 2 == 0 else 1
            if R.random() < .3:
                s = -s
            plan.append((s, R.uniform(10.0, L - 5)))
        used = {-1: [], 1: []}
        keys = list(NEON)
        R.shuffle(keys)
        for i, (s, y) in enumerate(plan):
            x, b = self.facade_x(s, y)
            if b is None or y < b["y0"] + .5 or y > b["y1"] - .5:
                continue
            if any(abs(y - u) < 2.2 for u in used[s]):
                continue
            if b.get("fe") and b["fe"][0] - .5 < y < b["fe"][1] + .5:
                continue
            if self.stall[0] == s and abs(y - self.stall[1]) < 2.5:
                continue
            used[s].append(y)
            z0 = R.uniform(b["gf"] - .2, b["gf"] + .4) if i < 2 else R.uniform(b["gf"] + .2, b["gf"] + 2.0)
            hmax = b["H"] - z0 - .6
            if hmax < 2.0:
                continue
            h = min(hmax, R.uniform(3.2, 4.6) if i < 2 else R.uniform(2.2, 6.5))
            proj = R.uniform(.85, 1.25) if i < 2 else R.uniform(.65, 1.15)
            self._blade(b["F"], y, z0, h, proj, R, key=keys[i % len(keys)])
        # a rooftop sign facing the camera on one of the mid-distance buildings
        cands = [b for s in (-1, 1) for b in self.sides[s] if 14 < b["y0"] < L - 8]
        if cands and R.random() < .8:
            b = R.choice(cands)
            M = self.M
            mb = MB()
            s = b["s"]
            key = R.choice(list(NEON))
            xw = s * (self.W / 2 + b["sb"])
            x0, x1 = xw + s * .3, xw + s * R.uniform(3.5, 5.5)
            y = b["y0"] + .6
            z0 = b["H"] + 1.6
            z1 = z0 + R.uniform(2.0, 3.0)
            xa, xb = min(x0, x1), max(x0, x1)
            mb.box_mm(xa, xb, y, y + .25, z0, z1, M.board)
            for xx in (xa + .3, xb - .3):
                mb.box_mm(xx - .06, xx + .06, y + .1, y + .22, b["H"], z0, M.metal)
                mb.seg_box((xx, y + .2, z0), (xx, y + 1.6, b["H"] + .9), .05, .05, M.metal)
            ch = (z1 - z0) * .66
            n = max(1, int((xb - xa - .3) / (ch * 1.2)))
            st = (xa + xb) / 2 - (n * ch * 1.2 - ch * .2) / 2
            for k in range(n):
                o = Vector((st + k * ch * 1.2, y, z0 + (z1 - z0) * .17))
                glyph_boxes(mb, o, Vector((1, 0, 0)), Z, Vector((0, -1, 0)), ch, ch, glyph(R), .05,
                            M.neon[key])
            mb.tube([(xa + .08, y - .06, z0 + .08), (xb - .08, y - .06, z0 + .08),
                     (xb - .08, y - .06, z1 - .08), (xa + .08, y - .06, z1 - .08)], .04, M.neon[key], 5,
                    closed=True)
            mb.build(self._sname(), self.col)
            self.roof_sign = ((xa + xb) / 2, y - .5, (z0 + z1) / 2, key)

    def _extra_neon(self):
        """Free neon tube shapes on the walls (arrows, rings, zigzags)."""
        R = self.R(40)
        M = self.M
        mb = MB()
        for k in range(R.randint(2, 4)):
            s = R.choice((-1, 1))
            y = R.uniform(4, self.L - 8)
            x, b = self.facade_x(s, y)
            if b is None:
                continue
            F = b["F"]
            z = R.uniform(b["gf"] + .5, min(b["H"] - 2, b["gf"] + 5))
            key = R.choice(list(NEON))
            mat = M.neon[key]
            d = .1
            shape = R.choice(("arrow", "ring", "zig", "tri"))
            sz = R.uniform(.6, 1.2)
            if shape == "arrow":
                pts = [F.P(y - sz, z, d), F.P(y + sz, z, d)]
                mb.tube(pts, .035, mat, 5)
                mb.tube([F.P(y + sz - .35, z + .3, d), F.P(y + sz, z, d), F.P(y + sz - .35, z - .3, d)], .035,
                        mat, 5)
            elif shape == "ring":
                pts = [F.P(y + math.cos(a) * sz, z + math.sin(a) * sz, d)
                       for a in (math.tau * j / 16 for j in range(16))]
                mb.tube(pts, .035, mat, 5, closed=True)
                mb.tube([F.P(y + math.cos(a) * sz * .6, z + math.sin(a) * sz * .6, d)
                         for a in (math.tau * j / 12 for j in range(12))], .03,
                        M.neon[R.choice(list(NEON))], 5, closed=True)
            elif shape == "zig":
                pts = [F.P(y - sz * 1.5 + j * sz * .5, z + (.3 if j % 2 else -.3), d) for j in range(7)]
                mb.tube(pts, .035, mat, 5)
            else:
                pts = [F.P(y - sz, z + sz, d), F.P(y + sz, z + sz, d), F.P(y, z - sz * .2, d)]
                mb.tube(pts, .035, mat, 5, closed=True)
                mb.tube([F.P(y, z - sz * .2, d), F.P(y, z - sz, d)], .035, mat, 5)
                mb.tube([F.P(y - sz * .5, z - sz, d), F.P(y + sz * .5, z - sz, d)], .035, mat, 5)
            info = self._sign_info(F, y - sz, y + sz, z - sz, z + sz, 0, .15, key, kind="tube")
            self.signs.append(info)
        mb.build("PW_NeonTubes", self.col)

    # ---------------------------------------------------------------------------- stall
    def _stall(self, F, a0, a1, oh, R):
        M = self.M
        mb = MB()
        zi = min(oh - .05, 2.85)
        dout, zo = R.uniform(1.5, 1.9), zi - .45
        n = max(4, int((a1 - a0) / .38))
        sv = (F.P(0, zo, dout) - F.P(0, zi, 0))
        ln = sv.length
        sv.normalize()
        nrm = F.u.cross(sv)
        if nrm.z < 0:
            nrm = -nrm
        for k in range(n):
            sa0 = a0 - .2 + (a1 - a0 + .4) * k / n
            sa1 = a0 - .2 + (a1 - a0 + .4) * (k + 1) / n
            mat = M.awn_a if k % 2 == 0 else M.awn_b
            c = (F.P((sa0 + sa1) / 2, zi, 0) + F.P((sa0 + sa1) / 2, zo, dout)) / 2
            mb.box_axes(c, F.u, sv, nrm, (sa1 - sa0) / 2, ln / 2, .03, mat)
            F.box(mb, sa0, sa1, zo - .32, zo, dout - .03, dout, mat)                 # valance
        # noren curtain panels
        a = a0 + .1
        while a < a1 - .45:
            F.box(mb, a, a + .42, zo - 1.0, zo - .32, dout - .08, dout - .05, M.noren)
            F.box(mb, a + .12, a + .3, zo - .8, zo - .6, dout - .045, dout - .035, M.white)
            a += .46
        # counter, stools, pot + steam
        F.box(mb, a0 + .1, a1 - .1, 0, .95, 0, .65, M.wood)
        F.box(mb, a0, a1, .95, 1.02, -.05, .78, M.trim_dark)
        k = 0
        a = a0 + .5
        while a < a1 - .3:
            p = F.P(a, 0, 1.15)
            mb.cyl(p, .05, .68, M.metal, sides=6)
            mb.cyl((p.x, p.y, .68), .2, .07, M.awn_a, sides=12)
            a += R.uniform(.7, .9)
            k += 1
        pa = R.uniform(a0 + .4, a1 - .4)
        p = F.P(pa, 1.02, .35)
        mb.cyl(p, .22, .3, M.metal, sides=12)
        st = MB()
        for j in range(4):
            q = p + Vector((R.uniform(-.06, .06), R.uniform(-.06, .06), .4 + j * .26))
            r = .1 + j * .05
            st.blob(q, (r, r, r * .7), M.steam, R, segs=8, rings=5, jit=.2)
        st.build("PW_Steam_Stall", self.col, pw_wonk=1.0)
        # lanterns hanging off the awning edge
        nl = R.randint(3, 5)
        for j in range(nl):
            la = a0 + (a1 - a0) * (j + .5) / nl
            top = F.P(la, zo - .02, dout + .12)
            mb.tube([top + Z * .02, top - Z * .25], .008, M.metal, 3, smooth=False)
            mat = M.lantern if j % 2 == 0 else M.lantern2
            mb.cyl(top - Z * .7, .17, .45, mat, sides=10)
            mb.cyl(top - Z * .76, .1, .06, M.trim_dark, sides=8)
            mb.cyl(top - Z * .25, .1, .05, M.trim_dark, sides=8)
        mb.build("PW_NoodleStall", self.col)
        self.stall_light = F.P((a0 + a1) / 2, 2.0, 1.2)
        self.signs.append(self._sign_info(F, a0, a1, zo - .9, zo, dout - .1, dout + .2, "warm",
                                          kind="stall"))

    # -------------------------------------------------------------------------- far end
    def _far_end(self):
        R = self.R(50)
        M, L, W = self.M, self.L, self.W
        yf = L + 12
        F0 = Frame((0, yf, 0), (1, 0, 0), (0, -1, 0))
        mb = MB()
        x = -R.uniform(20, 26)
        i = 0
        while x < 24:
            bw = R.uniform(7, 13)
            H = R.uniform(14, 38)
            sb = R.uniform(0, 1.5)
            F = Frame((0, yf + sb, 0), (1, 0, 0), (0, -1, 0))
            self._building(F, x, x + bw, H, R, mb, far=True)
            x += bw
            i += 1
        mb.build("PW_FarBlock", self.col)
        # a big lightbox billboard right at the vanishing point (the hazy focal glow)
        sb = MB()
        key = R.choice(("cyan", "magenta", "yellow", "mint"))
        bx = self.cam.x * .5 + R.uniform(-2.5, 2.5)
        z0 = R.uniform(7, 11)
        w, h = R.uniform(4, 7), R.uniform(2.2, 3.5)
        sb.box_mm(bx - w / 2, bx + w / 2, yf - .9, yf - .6, z0, z0 + h, M.box[key])
        for xx in (bx - w / 2 + .5, bx + w / 2 - .5):
            sb.box_mm(xx - .07, xx + .07, yf - .6, yf, z0 + .3, z0 + .5, M.metal)
        ch = h * .6
        n = max(1, int((w - .4) / (ch * 1.2)))
        st = bx - (n * ch * 1.2 - ch * .2) / 2
        for k in range(n):
            glyph_boxes(sb, Vector((st + k * ch * 1.2, yf - .9, z0 + h * .2)), Vector((1, 0, 0)), Z,
                        Vector((0, -1, 0)), ch, ch, glyph(R), .06, M.board)
        sb.build(f"PW_Sign_Far", self.col)
        self.far_sign = (bx, yf - 2.0, z0 + h / 2, key)
        self.signs.append({"x0": bx - w / 2, "x1": bx + w / 2, "y0": yf - .9, "y1": yf - .6,
                           "zb": z0, "zt": z0 + h, "key": key, "kind": "far"})
        # skyline towers far beyond: hazy silhouettes with a few lit window bands
        sk = MB()
        for k in range(R.randint(9, 13)):
            cx = R.uniform(-90, 90)
            cy = R.uniform(L + 45, L + 160)
            w, d, h = R.uniform(14, 30), R.uniform(14, 30), R.uniform(45, 140)
            mat = M.skyline if cy > L + 95 else M.skyline2
            sk.box_mm(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, -1, h, mat)
            if R.random() < .5:   # setback crown
                sk.box_mm(cx - w * .3, cx + w * .3, cy - d * .3, cy + d * .3, h, h + R.uniform(8, 20), mat)
            sk.tube([(cx, cy, h), (cx, cy, h + R.uniform(10, 25))], .4, M.metal, 4, smooth=False)
            nb = int(h / 3.5)
            for j in range(nb):
                r, xa, xb = R.random(), R.uniform(cx - w / 2 + 1, cx), R.uniform(cx + 1, cx + w / 2 - 1)
                if r < M.lit_frac * .8:
                    zb = 4 + j * 3.5
                    sk.box_mm(xa, xb, cy - d / 2 - .2, cy - d / 2, zb, zb + 1.2, M.far_lit)
        sk.build("PW_Skyline", self.col, pw_wonk=0.3)

    # ------------------------------------------------------------------------- overhead
    def _cable(self, mb, p0, p1, sag, r, segs=18):
        p0, p1 = Vector(p0), Vector(p1)
        pts = []
        for k in range(segs + 1):
            t = k / segs
            p = p0.lerp(p1, t)
            p.z -= sag * 4 * t * (1 - t)
            pts.append(p)
        mb.tube(pts, r, self.M.metal, sides=5)
        return pts

    def _overhead(self):
        R = self.R(60)
        M, L = self.M, self.L
        mb = self.cables
        n = R.randint(12, 18)
        for k in range(n):
            y = R.uniform(-1, L - 2)
            ya = y + R.uniform(-3, 3)
            xa, ba = self.facade_x(-1, y)
            xb, bb = self.facade_x(1, ya)
            if not ba or not bb:
                continue
            za = R.uniform(4.5, min(ba["H"] - .5, 17))
            zb = za + R.uniform(-2.5, 2.5)
            zb = max(4.5, min(bb["H"] - .5, zb))
            bundle = R.choice((1, 1, 1, 2, 3))
            for j in range(bundle):
                off = j * .14
                self._cable(mb, (xa, y + off, za - off), (xb, ya + off, zb + off * .5),
                            R.uniform(.4, 1.6) + j * .2, R.uniform(.018, .035))
            if R.random() < .15:   # junction box on a cable
                mb.box(((xa + xb) / 2, (y + ya) / 2, (za + zb) / 2 - .9), (.3, .25, .35), M.trim_dark)
        # runs along the facades with sags between hooks
        for s in (-1, 1):
            for _ in range(R.randint(1, 3)):
                z = R.uniform(3.6, 7.5)
                y = R.uniform(-2, 8)
                while y < L - 4:
                    y2 = y + R.uniform(3, 7)
                    x1, _ = self.facade_x(s, y)
                    x2, _ = self.facade_x(s, y2)
                    self._cable(mb, (x1 - s * .15, y, z), (x2 - s * .15, y2, z), R.uniform(.15, .45), .02, 8)
                    y = y2
        # lantern string across the alley near the stall
        ss, sy = self.stall
        xa, ba = self.facade_x(-1, sy + 1.5)
        xb, bb = self.facade_x(1, sy + 2.5)
        if ba and bb:
            z = R.uniform(4.6, 5.6)
            sag = R.uniform(.5, .9)
            pts = self._cable(mb, (xa, sy + 1.5, z), (xb, sy + 2.5, z + .2), sag, .015, 20)
            lm = MB()
            for k in range(2, 19, 2):
                p = pts[k]
                lm.tube([p, p - Z * .2], .008, M.metal, 3, smooth=False)
                lm.cyl(p - Z * .55, .14, .35, M.lantern if k % 4 else M.lantern2, sides=10)
                lm.cyl(p - Z * .6, .08, .05, M.trim_dark, sides=8)
                lm.cyl(p - Z * .2, .08, .04, M.trim_dark, sides=8)
            lm.build("PW_LanternString", self.col)
            self.lantern_mid = (pts[10] - Z * .8)
        # wall street lamp
        s = R.choice((-1, 1))
        y = R.uniform(16, min(30, L - 6))
        x, b = self.facade_x(s, y)
        if b:
            F = b["F"]
            lm = MB()
            z = 4.8
            lm.tube([F.P(y, z - .6, .02), F.P(y, z, .4), F.P(y, z + .1, 1.1)], .04, M.metal, 5)
            F.box(lm, y - .18, y + .18, z - .05, z + .2, .9, 1.4, M.metal)
            F.box(lm, y - .14, y + .14, z - .1, z - .05, .95, 1.35, M.bulb)
            lm.build("PW_StreetLamp", self.col)
            self.lamp = F.P(y, z - .4, 1.15)

    # -------------------------------------------------------------------------- clutter
    def _clutter(self):
        R = self.R(70)
        M, W, L = self.M, self.W, self.L
        self.n_cl = 0
        items = ["dumpster", "bags", "crates", "boxes", "barrels", "scooter", "cones", "vending", "bags"]
        wts = [1.3, 2.0, 1.0, 1.4, .9, .7, .6, .6, .6]
        for s in (-1, 1):
            y = R.uniform(-.5, 1.5)
            while y < L - 6:
                it = R.choices(items, wts)[0]
                ln = {"dumpster": 2.0, "bags": 1.3, "crates": .9, "boxes": 1.1, "barrels": 1.0,
                      "scooter": 1.8, "cones": .6, "vending": 1.0}[it]
                yc = y + ln / 2
                if self.stall[0] == s and abs(yc - self.stall[1]) < 3.2:
                    y += 1.0
                    continue
                xw, b = self.facade_x(s, yc)
                getattr(self, "_c_" + it)(s, xw, yc, R)
                self.n_cl += 1
                y += ln + R.uniform(.4, 3.0) * (1 if y < 25 else 1.6)
        # steam vents in the road
        for k in range(R.randint(1, 2)):
            x, y = R.choice((-1, 1)) * R.uniform(.9, W / 2 - .9), R.uniform(8, L * .6)
            mb = MB()
            mb.box_mm(x - .35, x + .35, y - .35, y + .35, 0, .05, M.metal)
            for j in range(5):
                mb.box_mm(x - .3, x + .3, y - .28 + j * .13, y - .22 + j * .13, .05, .06, M.trim_dark)
            mb.build(f"PW_SteamVent_{k}", self.col)
            st = MB()
            drift = R.uniform(-.12, .12)
            z = .12
            for j in range(R.randint(4, 6)):
                r = .12 + j * .07
                for q in range(2 if j > 1 else 1):
                    off = (q - .5) * r * .9 if j > 1 else 0
                    st.blob((x + off + R.uniform(-.06, .06) + j * drift, y + R.uniform(-.08, .08), z + r * .4),
                            (r * 1.25, r * 1.1, r * .62), M.steam, R, jit=.2)
                z += r * .75
            st.build(f"PW_Steam_{k}", self.col, pw_wonk=1.0)

    def _put(self, mb, name):
        mb.build(f"PW_{name}_{self.n_cl}", self.col)

    def _c_dumpster(self, s, xw, y, R):
        M = self.M
        mb = MB()
        dx = 1.0
        x = xw - s * (.12 + dx / 2)
        mat = R.choice(M.dumpster)
        mb.box_mm(x - dx / 2, x + dx / 2, y - .85, y + .85, .16, 1.25, mat)
        mb.box_mm(x - dx / 2 - .04, x + dx / 2 + .04, y - .88, y + .88, 1.1, 1.2, mat)        # rim
        ang = R.uniform(0, .5)
        hinge = Vector((x + s * dx / 2, y, 1.25))
        u = Vector((0, 1, 0))
        v = Vector((-s * math.cos(ang), 0, math.sin(ang)))
        mb.box_axes(hinge + v * (dx / 2), u, v, u.cross(v), .88, dx / 2 + .02, .03, M.metal)
        for dxx in (-1, 1):
            for dyy in (-1, 1):
                mb.cyl((x + dxx * .35 - .04, y + dyy * .7, .08), .08, .08, M.metal, sides=8,
                       axis=(1, 0, 0))
        mb.box_mm(x - s * (dx / 2 + .01), x - s * (dx / 2 + .012), y - .5, y - .1, .55, .85,
                  R.choice(M.poster))
        self._put(mb, "Dumpster")

    def _c_bags(self, s, xw, y, R):
        M = self.M
        mb = MB()
        for k in range(R.randint(3, 7)):
            r = R.uniform(.24, .4)
            x = xw - s * (.25 + R.uniform(0, .8))
            yy = y + R.uniform(-.55, .55)
            z = r * .5 + (R.uniform(.15, .3) if k > 3 else 0)
            mat = R.choice(M.bag)
            mb.blob((x, yy, z), (r * 1.15, r * R.uniform(.9, 1.2), r * .62), mat, R, segs=9, rings=6,
                    jit=.22, floor=max(0, z - r * .45))
            mb.blob((x, yy, z + r * .62), (r * .22, r * .22, r * .16), mat, R, segs=6, rings=4, jit=.3)
        self._put(mb, "TrashBags")

    def _c_crates(self, s, xw, y, R):
        M = self.M
        mb = MB()
        x = xw - s * .45
        z = 0
        for k in range(R.randint(1, 4)):
            mat = R.choice(M.plastic)
            rz = R.uniform(-.15, .15)
            mb.box((x + R.uniform(-.04, .04), y, z + .16), (.55, .75, .32), mat, rz)
            mb.box((x, y, z + .3), (.57, .77, .03), M.trim_dark, rz)
            z += .32
        self._put(mb, "Crates")

    def _c_boxes(self, s, xw, y, R):
        M = self.M
        mb = MB()
        z = 0
        x = xw - s * .5
        for k in range(R.randint(2, 5)):
            sx, sy, sz = R.uniform(.4, .7), R.uniform(.4, .8), R.uniform(.3, .55)
            rz = R.uniform(-.3, .3)
            xx = x + R.uniform(-.1, .1)
            yy = y + R.uniform(-.25, .25)
            mb.box((xx, yy, z + sz / 2), (sx, sy, sz), M.cardboard, rz)
            mb.box((xx, yy, z + sz + .002), (sx * .15, sy * 1.01, .006), M.tape, rz)
            z += sz
            if z > 1.4:
                break
        self._put(mb, "Boxes")

    def _c_barrels(self, s, xw, y, R):
        M = self.M
        mb = MB()
        for k in range(R.randint(1, 3)):
            x = xw - s * (.4 + (k % 2) * .6)
            yy = y - .3 + k * .35
            mat = R.choice((M.rust, M.dumpster[1], M.plastic[0]))
            mb.cyl((x, yy, 0), .3, .9, mat, sides=12)
            for zz in (.28, .62):
                mb.cyl((x, yy, zz), .315, .04, M.trim_dark, sides=12)
        self._put(mb, "Barrels")

    def _c_scooter(self, s, xw, y, R):
        M = self.M
        mb = MB()
        x = xw - s * .6
        mat = R.choice(M.scooter)
        d = R.choice((-1, 1))
        for yy in (y - .65 * d, y + .6 * d):
            mb.cyl((x - .06, yy, .26), .26, .12, M.trim_dark, sides=12, axis=(1, 0, 0))
        mb.box((x, y, .38), (.3, .9, .12), mat)                       # deck
        mb.blob((x, y - .45 * d, .62), (.2, .4, .28), mat, R, jit=.05)    # rear body
        mb.box((x, y - .4 * d, .9), (.28, .55, .1), M.trim_dark)       # seat
        mb.seg_box((x, y + .55 * d, .35), (x, y + .42 * d, 1.05), .16, .1, mat)   # front column
        mb.seg_box((x - .32, y + .42 * d, 1.08), (x + .32, y + .42 * d, 1.08), .04, .04, M.metal)
        mb.box((x, y + .5 * d, .95), (.14, .06, .1), M.bulb)
        self._put(mb, "Scooter")

    def _c_cones(self, s, xw, y, R):
        M = self.M
        mb = MB()
        for k in range(R.randint(1, 3)):
            x = xw - s * R.uniform(.5, 1.4)
            yy = y + R.uniform(-.25, .25)
            mb.box((x, yy, .02), (.36, .36, .04), M.cone)
            mb.cone((x, yy, .04), .16, .55, M.cone, sides=10)
            mb.cyl((x, yy, .25), .105, .07, M.white, sides=10, caps=False)
        self._put(mb, "Cones")

    def _c_vending(self, s, xw, y, R):
        M = self.M
        mb = MB()
        dx = .75
        x = xw - s * (.05 + dx / 2)
        body = R.choice((M.plastic[0], M.plastic[1], M.white))
        mb.box_mm(x - dx / 2, x + dx / 2, y - .45, y + .45, 0, 1.85, body)
        fx = x - s * dx / 2
        mb.box_mm(fx - s * .01, fx - s * .02, y - .38, y + .3, .75, 1.75, M.vend)
        for r in range(4):
            for c in range(4):
                mb.box_mm(fx - s * .02, fx - s * .06, y - .34 + c * .16, y - .24 + c * .16,
                          .85 + r * .22, .97 + r * .22, R.choice(M.plastic + M.poster[:4]))
        mb.box_mm(fx - s * .01, fx - s * .03, y - .38, y + .3, .2, .5, M.trim_dark)
        self._put(mb, "Vending")

    # ---------------------------------------------------------------------- reflections
    def _reflections(self):
        """Comic-style broken streak reflections on the wet road below each light source."""
        R = self.R(80)
        M, W = self.M, self.W
        cy = self.cam.y
        xlim = W / 2 - .62
        for i, sg in enumerate(self.signs):
            key = sg["key"]
            y_src = (sg["y0"] + sg["y1"]) / 2
            if y_src < cy + 4.0:
                continue
            x0, x1 = max(-xlim, sg["x0"]), min(xlim, sg["x1"])
            xc = (sg["x0"] + sg["x1"]) / 2
            # pull the streak inward a little (mirror image sits below the source, nearer centre)
            if x1 - x0 < .9:
                xc = max(-xlim + .5, min(xlim - .5, xc - math.copysign(.45, xc)))
                x0, x1 = xc - .45, xc + .45
            hsrc = sg["zt"] - sg["zb"]
            ln = min(9.0, max(1.5, hsrc * 1.1 + .06 * (y_src - cy)))
            if sg["kind"] in ("shop", "stall"):
                ln = min(ln, 3.0)
            y_far = y_src + .2
            y_near = max(cy + 4.2, y_src - ln)
            s_far, s_near = 1 / (y_far - cy), 1 / (y_near - cy)
            n = max(4, min(16, int(ln / .32) + 3))
            mb = MB()
            for k in range(n):
                t0 = (k + R.uniform(0, .12)) / n
                t1 = (k + R.uniform(.6, .92)) / n
                ya = cy + 1 / (s_far + (s_near - s_far) * t0)
                yb = cy + 1 / (s_far + (s_near - s_far) * t1)
                fade = 1 - .45 * (k / n)
                w = (x1 - x0) * R.uniform(.7, 1.15) * fade
                xm = (x0 + x1) / 2 + R.uniform(-.12, .12) * (x1 - x0)
                xa_, xb_ = max(-xlim, xm - w / 2), min(xlim, xm + w / 2)
                if xb_ - xa_ < .05:
                    continue
                ym = (ya + yb) / 2
                hd = abs(yb - ya) / 2
                m = 4
                top = [(xa_ + (xb_ - xa_) * j / m, ym + hd * R.uniform(.6, 1.2)) for j in range(1, m)]
                bot = [(xa_ + (xb_ - xa_) * j / m, ym - hd * R.uniform(.6, 1.2)) for j in range(m - 1, 0, -1)]
                pts = [(xa_, ym + R.uniform(-.3, .3) * hd)] + top + \
                      [(xb_, ym + R.uniform(-.3, .3) * hd)] + bot
                mb.poly([(x, y, .007) for x, y in pts], M.reflect[key], normal=Z)
            mb.build(f"PW_Reflect_{i}", self.col, pw_line=0, pw_wonk=0)

    # --------------------------------------------------------------------------- lights
    def _make_lights(self):
        lk = self.M.lk
        cy = self.cam.y
        blades = [s for s in self.signs if s["kind"] == "blade"]
        blades.sort(key=lambda s: -(s.get("power", 1) / (1 + .04 * max(0, (s["y0"] - cy) - 6))))
        for i, sg in enumerate(blades[:5]):
            xc = (sg["x0"] + sg["x1"]) / 2
            loc = (xc * .7, (sg["y0"] + sg["y1"]) / 2 - .6, (sg["zb"] + sg["zt"]) / 2 - .5)
            col = srgb(NEON[sg["key"]])
            e = min(2600, 1000 + 300 * sg.get("power", 3)) * lk
            self._light(f"PW_Light_Neon_{i}", loc, col, e, radius=.6)
        if hasattr(self, "stall_light"):
            self._light("PW_Light_Stall", self.stall_light, srgb("#ffa85a"), 650 * lk, radius=.5)
        if hasattr(self, "lamp"):
            self._light("PW_Light_Lamp", self.lamp, srgb("#ffb56b"), 1000 * lk, radius=.3)
        shops = [s for s in self.signs if s["kind"] == "shop" and s["y0"] > cy + 4]
        if shops:      # nearest lit shop window spills light onto the street
            sg = min(shops, key=lambda s: s["y0"])
            xc = (sg["x0"] + sg["x1"]) / 2
            loc = (xc - math.copysign(1.3, xc), (sg["y0"] + sg["y1"]) / 2, 1.6)
            self._light("PW_Light_Shop", loc, srgb(LIT["warm"]), 450 * lk, radius=.8)
        elif hasattr(self, "lantern_mid"):
            self._light("PW_Light_Lanterns", self.lantern_mid, srgb("#ff6a3a"), 450 * lk, radius=1.0)
        fx, fy, fz, fk = self.far_sign
        self._light("PW_Light_Far", (fx, fy - 2, fz), srgb(NEON[fk]), 2500 * lk, radius=1.5)
        for name, kind, loc, color, energy, radius in self.lights:
            ld = bpy.data.lights.new(name, kind)
            ld.color = color
            ld.energy = energy
            if hasattr(ld, "shadow_soft_size"):
                ld.shadow_soft_size = radius
            ob = bpy.data.objects.new(name, ld)
            ob.location = loc
            self.col.objects.link(ob)

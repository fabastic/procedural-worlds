"""Lived-in kitchen interior, modelled for the hand-inked graphic-novel look
(reference/ink_style_ref.png): chunky hard-edged geometry that produces good ink lines,
a muted slightly dirty palette, a sun patch through a real window opening and mood lamps.

Everything is built with bmesh into a few dozen joined objects (fast, few draw calls).
Structure and props vary per seed through random.Random(seed) only."""
import math
import random
import bpy
import bmesh
from mathutils import Vector, Matrix
from . import core

H = 2.7          # ceiling height
OFF = Vector((1.5, 1.5, 0.0))  # room offset: keeps the world origin (default cube) outside the walls
T = 0.15         # wall thickness
TAU = math.tau
I4 = Matrix.Identity(4)


def Tr(x, y, z):
    return Matrix.Translation((x, y, z))


def Rx(a):
    return Matrix.Rotation(a, 4, "X")


def Ry(a):
    return Matrix.Rotation(a, 4, "Y")


def Rz(a):
    return Matrix.Rotation(a, 4, "Z")


def Sc(x, y, z):
    return Matrix.Diagonal((x, y, z, 1.0))


# --------------------------------------------------------------------------- materials

def _sock(coll, ident):
    return next(s for s in coll if s.identifier == ident)


def _grime(name, color, amount=0.2, scale=1.5, floor=0.0, rough=0.8):
    """Principled material whose Base Color is colour * blotchy world-space noise grime
    (* darker towards the floor). The ink module cel-shades from this Base Color chain."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    L = nt.links.new
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = rough
    b.inputs["Base Color"].default_value = (*color, 1)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    e0, e1 = ramp.color_ramp.elements
    e0.position, e0.color = 0.42, (1 - amount, 1 - amount, 1 - amount, 1)
    e1.position, e1.color = 0.62, (1, 1, 1, 1)
    L(geo.outputs["Position"], nz.inputs["Vector"])
    L(nz.outputs["Fac"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    _sock(mix.inputs, "Factor_Float").default_value = 1.0
    _sock(mix.inputs, "A_Color").default_value = (*color, 1)
    L(ramp.outputs["Color"], _sock(mix.inputs, "B_Color"))
    res = _sock(mix.outputs, "Result_Color")
    if floor > 0:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 0.7
        r2 = nt.nodes.new("ShaderNodeValToRGB")
        a0, a1 = r2.color_ramp.elements
        a0.color = (1 - floor, 1 - floor, 1 - floor, 1)
        a1.color = (1, 1, 1, 1)
        m2 = nt.nodes.new("ShaderNodeMix")
        m2.data_type, m2.blend_type = "RGBA", "MULTIPLY"
        _sock(m2.inputs, "Factor_Float").default_value = 1.0
        L(geo.outputs["Position"], sep.inputs[0])
        L(sep.outputs["Z"], mr.inputs["Value"])
        L(mr.outputs["Result"], r2.inputs["Fac"])
        L(res, _sock(m2.inputs, "A_Color"))
        L(r2.outputs["Color"], _sock(m2.inputs, "B_Color"))
        res = _sock(m2.outputs, "Result_Color")
    L(res, b.inputs["Base Color"])
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = (*color, 1)
    return m


MOOD_K = {
    # sun elevation, sun_scale, sky_scale, lamp W, fill W, fill colour, hall lamp W,
    # sky card colour, skyline colour, lit-window strength
    "DAY":    dict(el=48, sun=2.2, sky=0.12, lamp=0, fill=40, fcol=(1.0, 0.95, 0.86), hall=0,
                   win=170, wcol=(0.85, 0.92, 1.0),
                   card=(0.62, 0.78, 0.92), city=(0.42, 0.44, 0.46), lit=0.0),
    "GOLDEN": dict(el=33, sun=1.8, sky=0.35, lamp=25, fill=16, fcol=(1.0, 0.9, 0.78), hall=6,
                   win=110, wcol=(1.0, 0.75, 0.5),
                   card=(0.95, 0.66, 0.38), city=(0.42, 0.28, 0.22), lit=0.0),
    "DUSK":   dict(el=17, sun=0.9, sky=0.9, lamp=110, fill=26, fcol=(0.75, 0.72, 0.95), hall=18,
                   win=45, wcol=(0.7, 0.6, 1.0),
                   card=(0.42, 0.30, 0.52), city=(0.16, 0.12, 0.20), lit=2.0),
    "NIGHT":  dict(el=40, sun=0.7, sky=1.0, lamp=170, fill=22, fcol=(0.6, 0.7, 1.0), hall=25,
                   win=18, wcol=(0.5, 0.6, 1.0),
                   card=(0.03, 0.045, 0.11), city=(0.015, 0.018, 0.035), lit=4.0),
}


def _materials(rng, mood):
    def m(n, c, r=0.7):
        return core.make_material("PW_Kitchen_" + n, c, rough=r)

    g = _grime
    k = MOOD_K[mood]
    wall = rng.choice([(0.60, 0.42, 0.17), (0.64, 0.50, 0.25), (0.68, 0.58, 0.38)])
    wall_lo = rng.choice([(0.25, 0.32, 0.22), (0.50, 0.29, 0.14), tuple(c * 0.75 for c in wall)])
    cab = rng.choice([(0.40, 0.37, 0.28), (0.50, 0.46, 0.34), (0.30, 0.36, 0.28)])
    trim = rng.choice([(0.045, 0.13, 0.11), (0.06, 0.16, 0.13), (0.09, 0.19, 0.14)])
    upanel = rng.choice([(0.64, 0.56, 0.38), (0.52, 0.48, 0.35), (0.40, 0.48, 0.36)])
    counter = rng.choice([(0.48, 0.55, 0.37), (0.34, 0.18, 0.07), (0.64, 0.60, 0.48)])
    fridge = rng.choice([(0.62, 0.62, 0.52), (0.38, 0.48, 0.40), (0.66, 0.58, 0.40)])
    enamel = rng.choice([(0.70, 0.67, 0.58), (0.60, 0.56, 0.44), (0.30, 0.40, 0.32)])
    P = dict(
        wall=g("PW_Kitchen_Wall", wall, 0.28, 1.1, floor=0.3),
        wall_lo=g("PW_Kitchen_WallLow", wall_lo, 0.22, 1.4, floor=0.3),
        ceiling=g("PW_Kitchen_Ceiling", (0.70, 0.64, 0.50), 0.18, 0.8),
        tile_a=m("FloorDark", (0.03, 0.03, 0.028)),
        tile_b=g("PW_Kitchen_FloorLight", (0.70, 0.63, 0.47), 0.25, 1.8),
        trim=m("Trim", trim, 0.6),
        lower=g("PW_Kitchen_Cabinet", cab, 0.18, 2.2),
        upanel=g("PW_Kitchen_UpperPanel", upanel, 0.15, 2.0),
        counter=g("PW_Kitchen_Counter", counter, 0.2, 2.5),
        tile=m("Backsplash", (0.74, 0.72, 0.62), 0.4),
        grout=m("Grout", (0.13, 0.12, 0.10), 0.9),
        dark=m("Shadow", (0.035, 0.03, 0.028), 0.9),
        steel=m("Steel", (0.38, 0.39, 0.37), 0.35),
        black=m("Black", (0.03, 0.03, 0.03), 0.5),
        copper=m("Copper", (0.50, 0.17, 0.06), 0.35),
        brass=m("Brass", (0.50, 0.36, 0.10), 0.4),
        wood=m("Wood", (0.30, 0.15, 0.06), 0.7),
        wood_dk=m("WoodDark", (0.12, 0.06, 0.025), 0.7),
        wood_lt=m("WoodLight", (0.48, 0.30, 0.13), 0.7),
        cork=g("PW_Kitchen_Cork", (0.44, 0.21, 0.07), 0.2, 9.0),
        paper=m("Paper", (0.80, 0.77, 0.66), 0.9),
        paper_y=m("PaperYellow", (0.78, 0.66, 0.36), 0.9),
        paper_b=m("PaperBlue", (0.52, 0.60, 0.64), 0.9),
        ink=m("Ink", (0.05, 0.05, 0.06), 0.9),
        terracotta=m("Terracotta", (0.45, 0.13, 0.07), 0.8),
        sage=m("Sage", (0.24, 0.34, 0.24), 0.7),
        teal=m("Teal", (0.05, 0.16, 0.14), 0.7),
        mustard=m("Mustard", (0.55, 0.40, 0.08), 0.7),
        dustyblue=m("DustyBlue", (0.17, 0.25, 0.32), 0.7),
        cream=m("Cream", (0.72, 0.66, 0.50), 0.6),
        offwhite=m("OffWhite", (0.78, 0.76, 0.68), 0.5),
        red=m("FadedRed", (0.42, 0.08, 0.05), 0.7),
        glass_g=m("GlassGreen", (0.33, 0.44, 0.34), 0.2),
        glass_a=m("GlassAmber", (0.32, 0.13, 0.03), 0.2),
        glass_c=m("GlassClear", (0.55, 0.62, 0.60), 0.2),
        enamel=m("Enamel", enamel, 0.4),
        fridge=m("Fridge", fridge, 0.4),
        curtain=g("PW_Kitchen_Curtain", (0.74, 0.70, 0.58), 0.25, 3.0),
        curtain_h=g("PW_Kitchen_HallCurtain", (0.42, 0.16, 0.10), 0.2, 3.0),
        towel=m("Towel", rng.choice([(0.17, 0.25, 0.32), (0.45, 0.13, 0.07), (0.55, 0.40, 0.08)])),
        rug=g("PW_Kitchen_Rug", rng.choice([(0.42, 0.15, 0.08), (0.20, 0.27, 0.30)]), 0.2, 3.0),
        rug_b=m("RugBorder", (0.62, 0.52, 0.32)),
        leaf=m("Leaf", (0.12, 0.24, 0.10), 0.7),
        leaf2=m("Leaf2", (0.22, 0.34, 0.14), 0.7),
        hall=g("PW_Kitchen_HallWall", (0.16, 0.20, 0.14), 0.25, 1.2, floor=0.3),
        hall_lo=g("PW_Kitchen_HallWallLow", (0.20, 0.10, 0.06), 0.2, 1.2),
        hall_floor=m("HallFloorA", (0.14, 0.07, 0.03)),
        hall_floor2=m("HallFloorB", (0.10, 0.05, 0.02)),
        picture=m("Picture", rng.choice([(0.38, 0.42, 0.26), (0.55, 0.36, 0.16)])),
        shade=m("LampShade", rng.choice([(0.24, 0.34, 0.24), (0.70, 0.66, 0.54), (0.50, 0.17, 0.06)])),
        bulb=core.make_material("PW_Kitchen_Bulb", (0.95, 0.85, 0.6), rough=0.5,
                                emission=(1.0, 0.78, 0.45), strength=8.0 if k["lamp"] else 0.0),
        lampshade_h=core.make_material("PW_Kitchen_HallLamp", (0.75, 0.62, 0.38), rough=0.6,
                                       emission=(1.0, 0.7, 0.4), strength=2.0 if k["hall"] > 10 else 0.0),
        card=core.make_material("PW_Kitchen_SkyCard", k["card"], rough=1.0,
                                emission=k["card"], strength=1.0),
        city=core.make_material("PW_Kitchen_Skyline", k["city"], rough=1.0,
                                emission=k["city"], strength=1.0),
        lit=core.make_material("PW_Kitchen_LitWindow", (0.9, 0.7, 0.4) if k["lit"] else k["city"],
                               rough=1.0, emission=(1.0, 0.72, 0.4), strength=k["lit"]),
    )
    for key in ("card", "city", "lit"):
        P[key]["pw_flat"] = 1
    return P


# --------------------------------------------------------------------------- mesh builder

class MB:
    """Accumulates primitives (with per-face materials) into one bmesh -> one object."""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.mats = []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def face(self, vs, m, smooth=False):
        f = self.bm.faces.new(vs)
        f.material_index = self.mi(m)
        f.smooth = smooth
        return f

    def box(self, lo, hi, m, M=I4, inset=None):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        co = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        v = [self.bm.verts.new(M @ Vector(c)) for c in co]
        F = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4),
             "+x": (1, 2, 6, 5), "+y": (2, 3, 7, 6), "-x": (3, 0, 4, 7)}
        faces = {k: self.face([v[i] for i in idx], m) for k, idx in F.items()}
        for side, w, d, pm in (inset or ()):
            self.inset(faces[side], w, d, pm)
        return faces

    def inset(self, f, w, d, m=None):
        f.normal_update()
        bmesh.ops.inset_individual(self.bm, faces=[f], thickness=w, depth=d, use_even_offset=True)
        if m is not None:
            f.material_index = self.mi(m)
        return f

    def lathe(self, prof, m, M=I4, segs=14, smooth=True, cap0=True, cap1=True):
        angs = [TAU * i / segs for i in range(segs)]
        rings = []
        for r, z in prof:
            if r < 1e-5:
                rings.append([self.bm.verts.new(M @ Vector((0, 0, z)))])
            else:
                rings.append([self.bm.verts.new(M @ Vector((r * math.cos(a), r * math.sin(a), z)))
                              for a in angs])
        for A, B in zip(rings, rings[1:]):
            if len(A) == 1 and len(B) == 1:
                continue
            for i in range(segs):
                j = (i + 1) % segs
                if len(A) == 1:
                    vs = [A[0], B[j], B[i]]
                elif len(B) == 1:
                    vs = [A[i], A[j], B[0]]
                else:
                    vs = [A[i], A[j], B[j], B[i]]
                self.face(vs, m, smooth)
        if smooth:  # keep profile corners crisp
            for k in range(1, len(prof) - 1):
                if len(rings[k]) == 1:
                    continue
                a = Vector(prof[k]) - Vector(prof[k - 1])
                b = Vector(prof[k + 1]) - Vector(prof[k])
                if a.length > 1e-6 and b.length > 1e-6 and a.angle(b) > math.radians(35):
                    ring = rings[k]
                    for i in range(segs):
                        e = self.bm.edges.get((ring[i], ring[(i + 1) % segs]))
                        if e:
                            e.smooth = False
        if cap0 and len(rings[0]) > 1:
            self.face(rings[0][::-1], m)
        if cap1 and len(rings[-1]) > 1:
            self.face(rings[-1], m)

    def cyl(self, r, h, m, M=I4, segs=12, smooth=True):
        self.lathe([(r, 0), (r, h)], m, M, segs, smooth)

    def sphere(self, r, m, M=I4, segs=10, rings=6):
        self.lathe([(r * math.sin(math.pi * k / rings), -r * math.cos(math.pi * k / rings))
                    for k in range(rings + 1)], m, M, segs)

    def torus(self, R, r, m, M=I4, a0=0.0, a1=TAU, seg=12, rseg=6):
        closed = abs(a1 - a0 - TAU) < 1e-6
        n = seg if closed else seg + 1
        rings = []
        for i in range(n):
            a = a0 + (a1 - a0) * i / seg
            c = Vector((math.cos(a), math.sin(a), 0))
            rings.append([self.bm.verts.new(M @ (c * (R + r * math.cos(TAU * q / rseg))
                                                 + Vector((0, 0, r * math.sin(TAU * q / rseg)))))
                          for q in range(rseg)])
        for i in range(seg):
            A, B = rings[i], rings[(i + 1) % n]
            for q in range(rseg):
                p = (q + 1) % rseg
                self.face([A[q], B[q], B[p], A[p]], m, True)

    def grid(self, nu, nv, fn, m, smooth=True):
        vs = [[self.bm.verts.new(fn(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
        for i in range(nu):
            for j in range(nv):
                self.face([vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]], m, smooth)

    def slab(self, L, Ht, holes, thick, m, M=I4, zsplit=None, m_lo=None):
        """A thick panel in local XZ (u along x, v along z) with rectangular holes, extruded
        +y by `thick` as one manifold mesh (no seams -> no stray ink lines)."""
        us = sorted({0.0, L, *[min(max(h[0], 0), L) for h in holes],
                     *[min(max(h[1], 0), L) for h in holes]})
        zl = [0.0, Ht] + [h[2] for h in holes] + [h[3] for h in holes]
        if zsplit:
            zl.append(zsplit)
        zs = sorted({min(max(z, 0), Ht) for z in zl})
        V = {(i, j): self.bm.verts.new((us[i], 0.0, zs[j]))
             for i in range(len(us)) for j in range(len(zs))}
        faces = []
        for i in range(len(us) - 1):
            for j in range(len(zs) - 1):
                cu, cz = (us[i] + us[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
                if any(h[0] < cu < h[1] and h[2] < cz < h[3] for h in holes):
                    continue
                mat = m_lo if (zsplit and m_lo is not None and cz < zsplit) else m
                faces.append(self.face([V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]], mat))
        for v in list(V.values()):
            if not v.link_faces:
                self.bm.verts.remove(v)
        front = {v for f in faces for v in f.verts}
        ret = bmesh.ops.extrude_face_region(self.bm, geom=faces, use_keep_orig=True)
        nv = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
        for v in nv:
            v.co.y += thick
        allv = front | set(nv)
        for v in allv:
            v.co = M @ v.co
        fs = list({f for v in allv for f in v.link_faces})
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)

    def done(self, col):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.name, me)
        col.objects.link(ob)
        return ob


# --------------------------------------------------------------------------- props
# Local prop frame: base at z=0, centred on origin, front (towards the room) = -y.

def _pick(rng, P, *keys):
    return P[rng.choice(keys)]


def p_mug(mb, M, rng, P):
    c = _pick(rng, P, "cream", "terracotta", "sage", "dustyblue", "mustard", "offwhite")
    r, h = rng.uniform(0.036, 0.045), rng.uniform(0.085, 0.105)
    mb.lathe([(r * 0.9, 0), (r, 0.01), (r, h), (r * 0.85, h), (r * 0.85, 0.012), (0, 0.012)], c, M, 12)
    mb.torus(h * 0.27, 0.008, c, M @ Tr(r, 0, h * 0.52) @ Rx(math.pi / 2), -math.pi / 2, math.pi / 2, 8, 5)


def p_glass(mb, M, rng, P):
    r, h = rng.uniform(0.03, 0.035), rng.uniform(0.1, 0.13)
    mb.lathe([(r * 0.85, 0), (r, h), (r * 0.88, h), (r * 0.75, 0.008), (0, 0.008)], P["glass_c"], M, 12)


def p_jar(mb, M, rng, P, scale=1.0):
    r, h = rng.uniform(0.04, 0.055) * scale, rng.uniform(0.09, 0.16) * scale
    body = _pick(rng, P, "glass_g", "cream", "glass_a", "offwhite", "glass_c")
    lid = _pick(rng, P, "copper", "terracotta", "mustard", "black", "sage", "wood")
    mb.lathe([(r * 0.9, 0), (r, 0.015), (r, h * 0.92), (r * 0.82, h)], body, M, 12)
    mb.cyl(r * 0.88, 0.03 * scale, lid, M @ Tr(0, 0, h - 0.004), 12)
    if rng.random() < 0.6:
        mb.cyl(r * 1.01, h * 0.35, P["paper"], M @ Tr(0, 0, h * 0.3), 12)


def p_tin(mb, M, rng, P):
    r, h = rng.uniform(0.042, 0.06), rng.uniform(0.09, 0.18)
    c = _pick(rng, P, "mustard", "dustyblue", "terracotta", "sage", "red", "cream")
    mb.cyl(r, h, c, M, 14)
    mb.cyl(r * 1.04, 0.022, c, M @ Tr(0, 0, h - 0.012), 14)
    if rng.random() < 0.5:
        mb.cyl(r * 1.01, h * 0.3, _pick(rng, P, "cream", "offwhite", "black"), M @ Tr(0, 0, h * 0.3), 14)


def p_bottle(mb, M, rng, P, tall=1.0):
    r = rng.uniform(0.03, 0.04)
    h = rng.uniform(0.18, 0.24) * tall
    c = _pick(rng, P, "glass_g", "glass_a", "glass_c", "glass_g")
    mb.lathe([(r * 0.95, 0), (r, 0.01), (r, h), (r * 0.6, h + 0.03), (r * 0.38, h + 0.05),
              (r * 0.38, h + 0.1), (r * 0.42, h + 0.1), (r * 0.42, h + 0.115)], c, M, 12)
    if rng.random() < 0.7:
        mb.cyl(r * 1.01, h * 0.35, _pick(rng, P, "paper", "cream", "paper_y"), M @ Tr(0, 0, h * 0.3), 12)


def p_bowl(mb, M, rng, P, fruit=None):
    r = rng.uniform(0.08, 0.11)
    c = _pick(rng, P, "cream", "terracotta", "sage", "dustyblue", "offwhite")
    mb.lathe([(r * 0.45, 0), (r * 0.82, 0.03), (r, 0.065), (r * 0.92, 0.068), (r * 0.75, 0.032),
              (r * 0.4, 0.01), (0, 0.01)], c, M, 14)
    if fruit is None:
        fruit = rng.random() < 0.5
    if fruit:
        fr = rng.uniform(0.032, 0.04)
        for i in range(rng.randint(3, 5)):
            a = rng.uniform(0, TAU)
            d = 0.0 if i == 0 else r * 0.45
            z = 0.04 + (0.03 if i == 0 else 0)
            mb.sphere(fr, _pick(rng, P, "mustard", "terracotta", "sage", "red", "mustard"),
                      M @ Tr(math.cos(a) * d, math.sin(a) * d, z), 8, 5)


def p_plates(mb, M, rng, P):
    c = _pick(rng, P, "offwhite", "cream", "dustyblue")
    r = rng.uniform(0.1, 0.12)
    for i in range(rng.randint(3, 7)):
        mb.lathe([(r * 0.6, 0), (r * 0.68, 0.006), (r, 0.016), (r * 0.94, 0.018), (r * 0.62, 0.008), (0, 0.008)],
                 c, M @ Tr(0, 0, i * 0.017), 14)


def p_board(mb, M, rng, P):
    w, h = rng.uniform(0.26, 0.36), rng.uniform(0.32, 0.42)
    c = _pick(rng, P, "wood_lt", "wood", "wood_lt")
    B = M @ Tr(0, 0.06, 0) @ Rx(-rng.uniform(0.12, 0.25))
    mb.box((-w / 2, -0.02, 0), (w / 2, 0, h), c, B)
    mb.box((-0.04, -0.02, h - 0.01), (0.04, 0, h + 0.06), c, B)


def p_toaster(mb, M, rng, P):
    c = _pick(rng, P, "steel", "cream", "terracotta", "sage", "enamel")
    w, d, h = 0.26, 0.15, 0.18
    f = mb.box((-w / 2, -d / 2, 0.012), (w / 2, d / 2, h), c, M)
    edges = list({e for k in ("+z", "-y", "+y") for e in f[k].edges})
    bmesh.ops.bevel(mb.bm, geom=edges, offset=0.025, offset_type="OFFSET", segments=2,
                    profile=0.5, affect="EDGES", clamp_overlap=True)
    for s in (-0.035, 0.035):
        mb.box((-w * 0.36, s - 0.012, h - 0.001), (w * 0.36, s + 0.012, h + 0.004), P["black"], M)
    mb.box((w / 2, -0.02, h * 0.6), (w / 2 + 0.03, 0.02, h * 0.72), P["black"], M)
    mb.box((-w / 2 + 0.01, -d / 2 + 0.01, 0), (w / 2 - 0.01, d / 2 - 0.01, 0.012), P["black"], M)


def p_crock(mb, M, rng, P):
    c = _pick(rng, P, "terracotta", "cream", "sage", "steel")
    r, h = 0.06, rng.uniform(0.13, 0.17)
    mb.lathe([(r * 0.92, 0), (r, 0.01), (r, h), (r * 0.86, h), (r * 0.86, 0.02), (0, 0.02)], c, M, 12)
    for i in range(rng.randint(3, 6)):
        a = rng.uniform(0, TAU)
        tilt = rng.uniform(0.08, 0.3)
        L = rng.uniform(0.26, 0.34)
        U = M @ Tr(0, 0, 0.02) @ Rz(a) @ Rx(tilt)
        hc = _pick(rng, P, "wood", "black", "wood_lt", "steel")
        mb.cyl(0.007, L, hc, U, 6)
        kind = rng.random()
        if kind < 0.4:
            mb.box((-0.03, -0.004, L), (0.03, 0.004, L + 0.07), hc, U)
        elif kind < 0.8:
            mb.sphere(0.025, hc, U @ Tr(0, 0, L + 0.02) @ Sc(1, 0.5, 1.3), 8, 4)


def p_kettle(mb, M, rng, P, c=None):
    c = c or _pick(rng, P, "steel", "enamel", "copper", "cream", "dustyblue")
    r = rng.uniform(0.085, 0.1)
    mb.lathe([(r * 0.9, 0), (r, 0.012), (r * 1.02, 0.06), (r * 0.9, 0.13), (r * 0.55, 0.17),
              (r * 0.35, 0.18), (0, 0.18)], c, M, 14)
    mb.sphere(0.018, P["black"], M @ Tr(0, 0, 0.19), 8, 4)
    mb.lathe([(0.018, 0), (0.011, 0.13)], c, M @ Tr(-r * 0.75, 0, 0.05) @ Ry(-0.95), 8)
    mb.torus(r * 0.7, 0.011, P["black"], M @ Tr(0, 0, 0.17) @ Rx(math.pi / 2), 0.2, math.pi - 0.2, 10, 5)


def p_pot(mb, M, rng, P, c=None):
    c = c or _pick(rng, P, "copper", "steel", "terracotta", "enamel", "black")
    r, h = rng.uniform(0.09, 0.12), rng.uniform(0.1, 0.15)
    mb.lathe([(r * 0.95, 0), (r, 0.01), (r, h), (r * 0.94, h), (r * 0.94, 0.012), (0, 0.012)], c, M, 16)
    mb.lathe([(r * 1.02, h), (r * 1.02, h + 0.008), (r * 0.5, h + 0.03), (0, h + 0.035)], c, M, 16)
    mb.lathe([(0.012, h + 0.03), (0.02, h + 0.05), (0, h + 0.055)], P["black"], M, 8)
    for s in (-1, 1):
        mb.box((s * r, -0.02, h * 0.72), (s * (r + 0.04), 0.02, h * 0.82), P["black"], M)


def p_spices(mb, M, rng, P):
    for i in range(rng.randint(3, 5)):
        x = (i - 2) * 0.045
        h = rng.uniform(0.07, 0.1)
        c = _pick(rng, P, "glass_c", "glass_a", "red", "mustard", "glass_g")
        mb.cyl(0.02, h, c, M @ Tr(x, rng.uniform(-0.02, 0.02), 0), 8)
        mb.cyl(0.021, 0.018, _pick(rng, P, "black", "red", "offwhite"), M @ Tr(x, 0, h), 8)


def p_radio(mb, M, rng, P):
    c = _pick(rng, P, "terracotta", "cream", "sage", "wood")
    w, d, h = 0.28, 0.13, 0.17
    mb.box((-w / 2, -d / 2, 0), (w / 2, d / 2, h), c, M,
           inset=[("-y", 0.02, -0.006, P["dark"])])
    for x in (-0.07, 0.07):
        mb.cyl(0.018, 0.02, P["cream"], M @ Tr(x, -d / 2, h * 0.3) @ Rx(math.pi / 2), 10)
    mb.box((-w * 0.35, -0.012, h), (-w * 0.3, 0.012, h + 0.07), P["black"], M)
    mb.box((w * 0.3, -0.012, h), (w * 0.35, 0.012, h + 0.07), P["black"], M)
    mb.box((-w * 0.35, -0.012, h + 0.06), (w * 0.35, 0.012, h + 0.075), P["black"], M)


def p_books(mb, M, rng, P):
    z = 0.0
    for i in range(rng.randint(2, 4)):
        w, d, t = rng.uniform(0.17, 0.24), rng.uniform(0.12, 0.17), rng.uniform(0.025, 0.045)
        c = _pick(rng, P, "red", "dustyblue", "sage", "mustard", "terracotta", "cream", "teal")
        mb.box((-w / 2, -d / 2, z), (w / 2, d / 2, z + t), c, M @ Rz(rng.uniform(-0.2, 0.2)))
        z += t


def p_books_up(mb, M, rng, P):
    x = -0.1
    for i in range(rng.randint(4, 7)):
        w, h, d = rng.uniform(0.025, 0.045), rng.uniform(0.17, 0.25), rng.uniform(0.13, 0.17)
        c = _pick(rng, P, "red", "dustyblue", "sage", "mustard", "terracotta", "cream", "teal", "wood")
        tilt = rng.uniform(-0.25, 0) if i == 0 else 0.0
        mb.box((0, -d / 2, 0), (w, d / 2, h), c, M @ Tr(x, 0, 0) @ Ry(tilt))
        x += w + 0.002


def p_basket(mb, M, rng, P):
    c = _pick(rng, P, "wood_lt", "mustard", "wood")
    r, h = rng.uniform(0.11, 0.16), rng.uniform(0.09, 0.15)
    mb.lathe([(r * 0.8, 0), (r, h), (r * 0.94, h), (r * 0.75, 0.015), (0, 0.015)], c, M, 10, smooth=False)
    if rng.random() < 0.6:
        for i in range(rng.randint(2, 4)):
            a = rng.uniform(0, TAU)
            mb.sphere(0.04, _pick(rng, P, "mustard", "terracotta", "cream", "sage"),
                      M @ Tr(math.cos(a) * r * 0.4, math.sin(a) * r * 0.4, h * 0.8), 8, 5)


def p_plant(mb, M, rng, P):
    r = rng.uniform(0.055, 0.075)
    h = r * 1.4
    mb.lathe([(r * 0.7, 0), (r, h), (r * 1.12, h), (r * 1.12, h + 0.025), (r * 0.95, h + 0.025),
              (r * 0.95, h * 0.8), (0, h * 0.8)], P["terracotta"], M, 12)
    for i in range(rng.randint(5, 8)):
        a = rng.uniform(0, TAU)
        tilt = rng.uniform(0.25, 0.9)
        L = rng.uniform(0.1, 0.2)
        U = M @ Tr(0, 0, h * 0.85) @ Rz(a) @ Rx(tilt)
        mb.sphere(1.0, _pick(rng, P, "leaf", "leaf2"), U @ Tr(0, 0, L * 0.5) @ Sc(0.035, 0.012, L * 0.5), 6, 4)


def p_bread(mb, M, rng, P):
    mb.box((-0.18, -0.11, 0), (0.18, 0.11, 0.02), P["wood_lt"], M)
    mb.sphere(1.0, P["mustard"], M @ Tr(0.02, 0, 0.045) @ Sc(0.12, 0.06, 0.05), 10, 6)


def p_dishrack(mb, M, rng, P):
    w, d = 0.38, 0.26
    rc = _pick(rng, P, "steel", "sage", "cream")
    mb.box((-w / 2, -d / 2, 0), (w / 2, d / 2, 0.03), rc, M)
    for x in (-w / 2, w / 2 - 0.012):
        mb.box((x, -d / 2, 0.03), (x + 0.012, d / 2, 0.12), rc, M)
    pc = _pick(rng, P, "offwhite", "cream", "dustyblue")
    n = rng.randint(3, 6)
    for i in range(n):
        x = -w / 2 + 0.05 + i * (w - 0.1) / max(n - 1, 1)
        r = rng.uniform(0.1, 0.12)
        mb.lathe([(r * 0.6, 0), (r, 0.014), (r * 0.94, 0.016), (0, 0.006)], pc,
                 M @ Tr(x, 0.0, r + 0.02) @ Ry(math.pi / 2 + rng.uniform(-0.15, 0.15)), 14)
    if rng.random() < 0.6:
        p_mug(mb, M @ Tr(w / 2 - 0.06, -d / 2 + 0.05, 0.03) @ Rz(rng.uniform(0, TAU)), rng, P)


PROPS = {  # name: (footprint width, depth, fn)
    "mug": (0.11, 0.1, p_mug), "glass": (0.08, 0.08, p_glass), "jar": (0.12, 0.12, p_jar),
    "tin": (0.12, 0.12, p_tin), "bottle": (0.09, 0.09, p_bottle), "bowl": (0.22, 0.22, p_bowl),
    "plates": (0.25, 0.25, p_plates), "board": (0.38, 0.12, p_board),
    "toaster": (0.32, 0.18, p_toaster), "crock": (0.14, 0.14, p_crock),
    "kettle": (0.24, 0.22, p_kettle), "spices": (0.24, 0.08, p_spices),
    "radio": (0.34, 0.15, p_radio), "books": (0.25, 0.18, p_books), "books_up": (0.3, 0.17, p_books_up),
    "basket": (0.32, 0.32, p_basket), "plant": (0.2, 0.2, p_plant), "bread": (0.38, 0.24, p_bread),
    "pot": (0.3, 0.25, p_pot), "dishrack": (0.42, 0.28, p_dishrack),
}


UNIQUE = {"kettle", "toaster", "dishrack", "bread", "radio", "board", "crock"}


def scatter(mb, S, segs, depth, rng, P, kinds, gap=(0.02, 0.16), skip=0.12, rot=0.5, wall_bias=0.5,
            used=None):
    """Place props left-to-right along a surface frame S (x along, -y towards the room).
    Kinds in UNIQUE appear at most once per `used` set (one toaster per kitchen)."""
    used = set() if used is None else used
    for u0, u1 in segs:
        u = u0 + rng.uniform(0.01, 0.1)
        while True:
            pool = [k for k in kinds if k not in used] or ["mug"]
            kind = rng.choice(pool)
            w, d, fn = PROPS[kind]
            if u + w > u1:
                if w > 0.15:
                    continue_ok = [k for k in pool if PROPS[k][0] <= u1 - u]
                    if continue_ok:
                        kind = rng.choice(continue_ok)
                        w, d, fn = PROPS[kind]
                    else:
                        break
                else:
                    break
            if rng.random() < skip:
                u += rng.uniform(0.08, 0.25)
                continue
            lo, hi = d / 2 + 0.02, max(d / 2 + 0.02, depth - d / 2 - 0.02)
            if kind in ("board", "toaster", "dishrack", "bread", "radio", "books_up"):
                v = -lo - (hi - lo) * rng.uniform(0, 0.3)
            else:
                v = -lo - (hi - lo) * (rng.random() ** (1 + wall_bias))
            r = rng.uniform(-rot, rot) if kind not in ("board", "books_up") else rng.uniform(-0.08, 0.08)
            fn(mb, S @ Tr(u + w / 2, v, 0) @ Rz(r), rng, P)
            if kind in UNIQUE:
                used.add(kind)
            u += w + rng.uniform(*gap)


# --------------------------------------------------------------------------- kitchen

def _minus(segs, a, b):
    out = []
    for s0, s1 in segs:
        if b <= s0 or a >= s1:
            out.append((s0, s1))
        else:
            if a > s0:
                out.append((s0, a))
            if b < s1:
                out.append((b, s1))
    return out


def _split(length, rng, lo=0.42, hi=0.8):
    if length < 0.12:
        return []
    n = max(1, int(round(length / rng.uniform(0.55, 0.7))))
    while n > 1 and length / n < lo:
        n -= 1
    while length / n > hi:
        n += 1
    cuts = sorted(rng.uniform(-0.08, 0.08) + (i + 1) / n for i in range(n - 1))
    pts = [0.0] + [c * length for c in cuts] + [length]
    return [pts[i + 1] - pts[i] for i in range(n)]


class _Kitchen:
    def __init__(self, col, seed, mood):
        self.col = col
        self.rng = random.Random(seed)
        self.mood = mood if mood in MOOD_K else "GOLDEN"
        self.K = MOOD_K[self.mood]
        self.P = _materials(self.rng, self.mood)
        self.mbs = {}
        self.used = set()

    def mb(self, name):
        if name not in self.mbs:
            self.mbs[name] = MB("PW_" + name)
        return self.mbs[name]

    # ---- wall frames: local x = natural coordinate u along the wall, local y into the wall
    def wf(self, side):
        W, D = self.W, self.D
        return {"back": Tr(0, D, 0), "left": Rz(math.pi / 2),
                "right": Tr(W, D, 0) @ Rz(-math.pi / 2), "front": Tr(W, 0, 0) @ Rz(math.pi)}[side]

    def run(self):
        rng, P = self.rng, self.P
        self.W = W = rng.uniform(5.2, 5.9)
        self.D = D = rng.uniform(4.3, 4.9)
        self.layout = rng.choice(["back", "left"])  # which wall the doorway is on
        self.plan()
        self.camera()
        self.hall_dims()
        self.shell()
        self.trim()
        self.back_run()
        if self.layout == "back":
            self.left_run()
        else:
            self.sideboard()
        self.window(self.win_side, *self.win, self.wf(self.win_side))
        self.doorway()
        self.cork()
        self.fridge()
        self.lamp()
        self.floor_props()
        self.hall()
        self.lights()
        wonk = {"PW_Walls": 0.0, "PW_Floor": 0.0, "PW_HallShell": 0.0, "PW_HallFloor": 0.0,
                "PW_SkyCard": 0.0, "PW_Skyline": 0.0, "PW_HallSky": 0.0, "PW_Backsplash": 0.0,
                "PW_BacksplashGrout": 0.0, "PW_Trim": 0.3}
        for name, b in self.mbs.items():
            ob = b.done(self.col)
            ob.location = OFF
            if ob.name in wonk:
                ob["pw_wonk"] = wonk[ob.name]
            if ob.name == "PW_Backsplash":  # tiles: grout gaps read as fine pen lines, no outlines
                ob["pw_line"] = 0
            if ob.name in ("PW_SkyCard", "PW_Skyline"):
                ob.visible_shadow = False
                if ob.name == "PW_SkyCard":
                    ob["pw_line"] = 0
        cam = dict(self.cam)
        cam["location"] = tuple(Vector(cam["location"]) + OFF)
        cam["target"] = tuple(Vector(cam["target"]) + OFF)
        return {"objects": len(self.col.objects), "camera": cam,
                "sun_dir": (self.K["el"] + rng.uniform(-3, 3), self.sun_az),
                "sun_scale": self.K["sun"], "sky_scale": self.K["sky"],
                "layout": self.layout}

    # ---- layout plan
    def plan(self):
        rng, W, D = self.rng, self.W, self.D
        self.fw = rng.uniform(0.72, 0.8)
        self.fx = (W - 0.04 - self.fw, W - 0.04)          # fridge on the back wall, right end
        self.depth = 0.62
        if self.layout == "back":
            u0 = rng.uniform(0.35, 0.6)
            self.door = ("back", u0, u0 + 0.98)
            self.run_x = (u0 + 0.98 + 0.24, self.fx[0] - 0.03)
            L = self.run_x[1] - self.run_x[0]
            rest = L - 0.68
            left = rest * rng.uniform(0.25, 0.75)
            mods = [("cab", w) for w in _split(left, rng)] + [("stove", 0.68)] + \
                   [("cab", w) for w in _split(rest - left, rng)]
            wy0 = D - rng.uniform(1.0, 1.25) - rng.uniform(0.95, 1.1)
            self.win_side = "left"
            self.lr_start = rng.uniform(0.5, 0.75)
            self.lr_end = self.lr_start + rng.uniform(1.75, 2.0)
            wy0 = max(wy0, self.lr_end + 0.3)
            self.win = (wy0, min(wy0 + rng.uniform(0.95, 1.1), D - 0.3), rng.uniform(0.95, 1.05), 2.12)
            self.sun_az = -105 + rng.uniform(-10, 10)
        else:
            u1 = D - rng.uniform(0.85, 1.1)
            self.door = ("left", u1 - 0.92, u1)
            self.run_x = (0.0, self.fx[0] - 0.03)
            sx = rng.uniform(1.25, 1.75)
            a = sx - 0.43
            mods = [("cab", w) for w in _split(a, rng)] + [("sink", 0.86)]
            rest = self.run_x[1] - (a + 0.86)
            left = max(0.0, (rest - 0.68) * rng.uniform(0.0, 0.6))
            mods += [("cab", w) for w in _split(left, rng)] + [("stove", 0.68)] + \
                    [("cab", w) for w in _split(rest - 0.68 - left, rng)]
            ww = rng.uniform(0.95, 1.1)
            self.win_side = "back"
            self.win = (sx - ww / 2, sx + ww / 2, 1.12, 2.15)
            self.sun_az = 200 + rng.uniform(-8, 12)
        for i, (k, w) in enumerate(mods):
            if k == "cab" and rng.random() < 0.3:
                mods[i] = ("drawers", w)
        x = self.run_x[0]
        self.mods = []
        for k, w in mods:
            self.mods.append((k, x, x + w))
            x += w

    def camera(self):
        rng, W, D = self.rng, self.W, self.D
        loc = (W - 0.62 + rng.uniform(-0.12, 0.08), rng.uniform(0.4, 0.6), rng.uniform(1.58, 1.68))
        if self.layout == "back":
            dc = (self.door[1] + self.door[2]) / 2
            tgt = (dc + 0.9 + rng.uniform(-0.15, 0.2), D, 0.9)
        else:
            tgt = (1.3 + rng.uniform(-0.2, 0.2), D - 0.75, 0.9)
        self.cam = {"location": loc, "target": tgt, "lens": rng.choice((16, 17, 18)),
                    "clip_end": 60.0}

    def hall_dims(self):
        side, u0, u1 = self.door
        dc = (u0 + u1) / 2
        if side == "back":
            self.F = Tr(dc, self.D + T, 0)
        else:
            self.F = Tr(-T, dc, 0) @ Rz(math.pi / 2)
        self.hd = self.rng.uniform(2.3, 2.8)
        p = self.F.inverted() @ Vector(self.cam["location"])
        sx = p.x * self.hd / p.y if p.y < -0.1 else 0.0
        self.hwin = max(-1.9, min(1.9, sx))
        self.hw0 = max(1.3, -self.hwin + 1.2)
        self.hw1 = max(1.3, self.hwin + 1.2)

    # ---- room shell: walls with real openings, ceiling, checker floor
    def shell(self):
        P, W, D, rng = self.P, self.W, self.D, self.rng
        b = self.mb("Walls")
        dside, d0, d1 = self.door
        dc = (d0 + d1) / 2
        holes = {"back": [], "left": [], "right": [], "front": []}
        holes[dside].append((d0, d1, -1, 2.1))
        wu0, wu1, wz0, wz1 = self.win
        holes[self.win_side].append((wu0, wu1, wz0, wz1))
        ext = {"back": (-T, W + T), "left": (-T, D + T), "right": (-T, D + T), "front": (-T, W + T)}
        lo, hi = ext[dside]
        ext[dside] = (min(lo, dc - self.hw0 - T - 0.05), max(hi, dc + self.hw1 + T + 0.05))
        self.zsplit = rng.uniform(0.9, 1.0)
        for side, (a, c) in ext.items():
            M = self.wf(side) @ Tr(a, 0, 0)
            b.slab(c - a, H, [(h[0] - a, h[1] - a, h[2], h[3]) for h in holes[side]], T,
                   P["wall"], M, zsplit=self.zsplit, m_lo=P["wall_lo"])
        b.box((-T, -T, H), (W + T, D + T, H + 0.12), P["ceiling"])
        # checkered floor: jittered grid, alternating material per face
        f = self.mb("Floor")
        s = rng.uniform(0.3, 0.36)
        nx, ny = int(math.ceil(W / s)), int(math.ceil(D / s))
        V = {}
        for i in range(nx + 1):
            for j in range(ny + 1):
                x, y = min(i * s, W), min(j * s, D)
                if 0 < i < nx and 0 < j < ny:
                    x += rng.uniform(-0.022, 0.022)
                    y += rng.uniform(-0.022, 0.022)
                V[i, j] = f.bm.verts.new((x, y, rng.uniform(0.0, 0.004)))
        for i in range(nx):
            for j in range(ny):
                f.face([V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]],
                       P["tile_a"] if (i + j) % 2 else P["tile_b"])

    def trim(self):
        """Baseboards, chair rail and crown moulding around the kitchen."""
        P, W, D = self.P, self.W, self.D
        b = self.mb("Trim")
        lens = {"back": W, "left": D, "right": D, "front": W}
        for side, L in lens.items():
            M = self.wf(side)
            segs = [(0.0, L)]
            if self.door[0] == side:
                segs = _minus(segs, self.door[1] - 0.1, self.door[2] + 0.1)
            for a, c in segs:
                b.box((a, -0.02, 0), (c, 0, 0.13), P["trim"], M)
                b.box((a, -0.022, self.zsplit - 0.02), (c, 0, self.zsplit + 0.03), P["trim"], M)
            b.box((0, -0.05, H - 0.09), (L, 0, H), P["trim"], M)
            b.box((0, -0.028, H - 0.15), (L, 0, H - 0.09), P["trim"], M)

    # ---- cabinets
    def back_run(self):
        P, rng = self.P, self.rng
        R = self.wf("back")
        self.lower_run(R, self.mods, "Cabinets")
        x0, x1 = self.run_x
        # uppers
        zones = [(x0 + (0.0 if self.layout == "left" else 0.0), x1)]
        if self.win_side == "back":
            zones = _minus(zones, self.win[0] - 0.12, self.win[1] + 0.12)
        st = [m for m in self.mods if m[0] == "stove"][0]
        sc = (st[1] + st[2]) / 2
        ws = rng.uniform(0.95, 1.3)
        sh = None
        for a, c in zones:
            if a <= sc <= c:
                sh = (max(a, sc - ws / 2), min(c, sc + ws / 2))
        if sh is None or sh[1] - sh[0] < 0.6:
            big = max(zones, key=lambda z: z[1] - z[0])
            sh = (big[0], min(big[1], big[0] + ws))
        zones = _minus(zones, sh[0] - 0.02, sh[1] + 0.02)
        U = self.mb("Uppers")
        for a, c in zones:
            if c - a < 0.3:
                continue
            x = a
            for w in _split(c - a, rng, 0.35, 0.95):
                self.upper_cab(U, R, x, x + w)
                x += w
        if rng.random() < 0.6:  # cabinet over the fridge
            self.upper_cab(U, R, self.fx[0], self.fx[1], z0=1.98)
        self.shelf_zone(R, *sh)
        # backsplash tiles
        def ztop(x):
            if self.win_side == "back" and self.win[0] - 0.1 < x < self.win[1] + 0.1:
                return self.win[2] - 0.035
            return 1.48
        self.tiles(R, x0, x1, ztop)

    def lower_run(self, R, mods, name):
        P, rng = self.P, self.rng
        b = self.mb(name)
        d = self.depth
        knob = rng.choice(["knob", "bar"])
        kmat = _pick(rng, P, "brass", "black", "copper", "steel")
        self.knob, self.kmat = knob, kmat
        segs, cur = [], None
        for kind, a, c in mods:
            if kind == "stove":
                self.stove(R, a, c)
                if cur:
                    segs.append(cur)
                cur = None
                continue
            cur = [cur[0], c] if cur else [a, c]
            b.box((a + 0.02, -d + 0.07, 0), (c - 0.02, -0.02, 0.1), P["dark"], R)
            if kind == "sink":
                self.sink(R, a, c)
                continue
            b.box((a, -d + 0.02, 0.1), (c, 0, 0.86), P["lower"], R)
            g, fr = 0.004, -d
            if kind == "cab":
                self.panel(b, R, a + g, c - g, 0.69, 0.855, P["lower"], "bar" if knob == "bar" else "knob2")
                n = 2 if c - a > 0.62 else 1
                for i in range(n):
                    xa = a + (c - a) * i / n + g
                    xb = a + (c - a) * (i + 1) / n - g
                    hx = xb - 0.05 if (n == 1 and rng.random() < 0.5) or (n == 2 and i == 0) else xa + 0.05
                    self.panel(b, R, xa, xb, 0.105, 0.683, P["lower"], None)
                    self.knob_at(b, R, hx, fr - 0.02, 0.6)
            else:
                hs = rng.choice([[0.2, 0.24, 0.31], [0.18, 0.18, 0.18, 0.21], [0.25, 0.25, 0.25]])
                tot = sum(hs)
                z = 0.855
                for hgt in hs:
                    hh = hgt * 0.75 / tot
                    self.panel(b, R, a + g, c - g, z - hh + g, z, P["lower"], "bar" if knob == "bar" else "knob2")
                    z -= hh
        if cur:
            segs.append(cur)
        # countertops (one slab per segment between stoves, with a hole for the sink)
        for a, c in segs:
            holes = []
            for kind, ma, mc in mods:
                if kind == "sink" and ma >= a - 1e-6 and mc <= c + 1e-6:
                    holes.append((ma + 0.08 - a, mc - 0.08 - a, 0.13, d + 0.03 - 0.1))
            b.slab(c - a, d + 0.03, holes, 0.045, P["counter"],
                   R @ Tr(a, -d - 0.03, 0.91) @ Rx(-math.pi / 2))
        # props on the counter
        free = [tuple(s) for s in segs]
        for kind, ma, mc in mods:
            if kind == "sink":
                free = _minus(free, ma + 0.02, mc - 0.02)
        pm = self.mb("Props")
        for kind, ma, mc in mods:  # dish rack beside the sink
            if kind != "sink":
                continue
            for ra, rb in ((mc + 0.03, mc + 0.47), (ma - 0.47, ma - 0.03)):
                if any(s0 <= ra and rb <= s1 for s0, s1 in free):
                    p_dishrack(pm, R @ Tr((ra + rb) / 2, -0.2, 0.91) @ Rz(rng.uniform(-0.1, 0.1)), rng, P)
                    free = _minus(free, ra - 0.02, rb + 0.02)
                    break
        kinds = ["mug", "jar", "bottle", "bowl", "plates", "board", "toaster", "crock", "tin",
                 "kettle", "spices", "glass", "bread", "mug", "jar", "bottle"]
        scatter(pm, R @ Tr(0, 0, 0.91), free, d, rng, P, kinds, skip=0.04, used=self.used, gap=(0.0, 0.1))

    def panel(self, b, R, xa, xb, za, zb, mat, handle, inner=None, depth=None, M=None):
        """Door / drawer front with a recessed panel (inset geometry -> crease ink lines)."""
        d = self.depth if depth is None else depth
        M = R if M is None else M
        w = min(0.05, (xb - xa) * 0.18, (zb - za) * 0.22)
        f = b.box((xa, -d - 0.022, za), (xb, -d, zb), mat, M)
        b.inset(f["-y"], w, -0.012, inner)
        if inner is None:
            b.inset(f["-y"], 0.012, 0.005)
        cx, cz = (xa + xb) / 2, (za + zb) / 2
        if handle == "bar":
            hw = min(0.08, (xb - xa) * 0.25)
            b.box((cx - hw, -d - 0.05, cz - 0.009), (cx + hw, -d - 0.035, cz + 0.009), self.kmat, M)
            for s in (-1, 1):
                b.box((cx + s * hw * 0.8 - 0.006, -d - 0.04, cz - 0.006), (cx + s * hw * 0.8 + 0.006, -d - 0.02, cz + 0.006), self.kmat, M)
        elif handle == "knob2":
            if xb - xa > 0.6:
                for s in (-1, 1):
                    self.knob_at(b, R, cx + s * (xb - xa) * 0.25, -d - 0.02, cz, M)
            else:
                self.knob_at(b, R, cx, -d - 0.02, cz, M)

    def knob_at(self, b, R, x, y, z, M=None):
        M = R if M is None else M
        b.lathe([(0.009, 0), (0.009, 0.012), (0.019, 0.02), (0.019, 0.03), (0, 0.034)], self.kmat,
                M @ Tr(x, y, z) @ Rx(math.pi / 2), 10)

    def upper_cab(self, U, R, a, c, z0=1.48, z1=2.28, d=0.34):
        P, rng = self.P, self.rng
        f = U.box((a, -d + 0.02, z0), (c, 0, z1), P["trim"], R)
        U.inset(f["-y"], 0.02, -(d - 0.05), P["dark"])
        n = 2 if c - a > 0.6 else 1
        ajar = rng.random() < 0.25
        if ajar:  # something visible inside
            for k in range(rng.randint(2, 4)):
                x = a + 0.08 + k * 0.12
                if x < c - 0.08:
                    p_jar(U, R @ Tr(x, -0.15, z0 + 0.02 + (z1 - z0) * 0.5), rng, P)
            U.box((a + 0.02, -d + 0.03, (z0 + z1) / 2), (c - 0.02, -0.02, (z0 + z1) / 2 + 0.02), P["trim"], R)
        for i in range(n):
            xa = a + (c - a) * i / n + 0.004
            xb = a + (c - a) * (i + 1) / n - 0.004
            hinge_left = (i == 0) if n == 2 else rng.random() < 0.5
            M = R
            if ajar and i == n - 1:
                ang = rng.uniform(0.25, 0.6)
                if hinge_left:
                    M = R @ Tr(xa, -d, 0) @ Rz(-ang) @ Tr(-xa, d, 0)
                else:
                    M = R @ Tr(xb, -d, 0) @ Rz(ang) @ Tr(-xb, d, 0)
            self.panel(U, R, xa, xb, z0 + 0.004, z1 - 0.004, P["trim"], None, inner=P["upanel"], depth=d, M=M)
            hx = xb - 0.045 if hinge_left else xa + 0.045
            self.knob_at(U, R, hx, -d - 0.02, z0 + 0.06, M)
        # clutter on top
        if rng.random() < 0.7 and z1 < 2.4:
            pm = self.mb("Props")
            scatter(pm, R @ Tr(0, 0, z1), [(a, c)], d, rng, P, ["basket", "jar", "bottle", "plates", "bowl"],
                    skip=0.35, gap=(0.05, 0.3))

    def shelf_zone(self, R, a, c):
        P, rng = self.P, self.rng
        b = self.mb("Shelves")
        pm = self.mb("Props")
        hang = self.mb("Hanging")
        mat = _pick(rng, P, "wood", "trim", "wood_lt")
        zs = [rng.uniform(1.62, 1.7)]
        if rng.random() < 0.75:
            zs.append(zs[0] + rng.uniform(0.34, 0.4))
        sd = 0.24
        for z in zs:
            b.box((a, -sd, z - 0.035), (c, 0, z), mat, R)
            for x in (a + 0.1, c - 0.1):
                b.box((x - 0.015, -sd * 0.8, z - 0.17), (x + 0.015, 0, z - 0.035), P["black"], R)
            scatter(pm, R @ Tr(0, 0, z), [(a + 0.02, c - 0.02)], sd, rng, P,
                    ["jar", "tin", "bottle", "spices", "mug", "jar", "tin", "plates", "books_up"],
                    gap=(0.0, 0.08), skip=0.08, rot=1.5)
        # copper pot rail under the lowest shelf
        zr = zs[0] - 0.13
        rm = _pick(rng, P, "copper", "black", "brass")
        hang.cyl(0.011, c - a - 0.12, rm, R @ Tr(a + 0.06, -0.1, zr) @ Ry(math.pi / 2), 8)
        for x in (a + 0.06, c - 0.06):
            hang.box((x - 0.01, -0.1, zr - 0.01), (x + 0.01, 0, zr + 0.01), rm, R)
        x = a + 0.14
        while x < c - 0.12:
            kind = rng.choice(["pan", "pan", "saucepan", "ladle", "pan", "saucepan"])
            G = R @ Tr(x, -0.1, zr)
            hang.torus(0.016, 0.003, P["black"], G @ Tr(0, 0, -0.012) @ Rx(math.pi / 2) @ Rz(math.pi / 2), 0, TAU, 8, 4)
            c1 = _pick(rng, P, "copper", "copper", "black", "steel")
            hc = _pick(rng, P, "copper", "black", "wood")
            if kind == "ladle":
                hang.box((-0.008, -0.004, -0.36), (0.008, 0.004, -0.03), hc, G)
                hang.lathe([(0, -0.06), (0.04, -0.045), (0.05, 0), (0.045, 0), (0, -0.05)], c1, G @ Tr(0, 0, -0.38), 10)
                x += 0.11
                continue
            rp = rng.uniform(0.09, 0.13) if kind == "pan" else rng.uniform(0.07, 0.085)
            hp = 0.045 if kind == "pan" else 0.1
            Lh = rng.uniform(0.15, 0.2)
            hang.box((-0.013, 0.01, -0.03 - Lh), (0.013, 0.022, -0.025), hc, G)
            cz = -0.03 - Lh - rp * 1.08
            hang.lathe([(0, 0), (rp, 0), (rp * 1.1, hp), (rp * 1.04, hp), (rp * 0.95, 0.008), (0, 0.008)], c1,
                       G @ Tr(0, 0.07, cz) @ Rx(math.pi / 2), 16)
            x += rp * 2.3 + 0.03

    def tiles(self, R, x0, x1, ztop, zb=0.91):
        P, rng = self.P, self.rng
        b = self.mb("Backsplash")
        tw, th, g = rng.choice([(0.15, 0.075), (0.2, 0.1), (0.16, 0.08)]) + (0.007,)
        # grout backing per column region (handles the lower band under a window)
        xs = [x0]
        if self.win_side == "back":
            xs += [max(x0, self.win[0] - 0.1), min(x1, self.win[1] + 0.1)]
        xs.append(x1)
        xs = sorted(set(xs))
        gb = self.mb("BacksplashGrout")
        for a, c in zip(xs, xs[1:]):
            gb.box((a, -0.004, zb), (c, 0, ztop((a + c) / 2)), P["grout"], R)
        row = 0
        z = zb + g
        while z < 1.6:
            off = (tw / 2) * (row % 2)
            x = x0 - off
            while x < x1:
                xa, xb = max(x, x0), min(x + tw - g, x1)
                zt = min(z + th - g, ztop((xa + xb) / 2) - 0.002)
                if xb - xa > 0.02 and zt - z > 0.02:
                    b.box((xa, -0.014, z), (xb, -0.004, zt), P["tile"], R)
                x += tw
            z += th
            row += 1

    def stove(self, R, a, c):
        P, rng = self.P, self.rng
        b = self.mb("Stove")
        d = 0.64
        w = c - a
        b.box((a + 0.03, -d + 0.04, 0), (c - 0.03, -0.02, 0.08), P["dark"], R)
        b.box((a, -d, 0.08), (c, 0, 0.88), P["enamel"], R)
        f = b.box((a + 0.04, -d - 0.025, 0.15), (c - 0.04, -d, 0.62), P["enamel"], R)
        b.inset(f["-y"], 0.07, -0.01, P["dark"])
        b.cyl(0.012, w - 0.16, P["steel"], R @ Tr(a + 0.08, -d - 0.06, 0.66) @ Ry(math.pi / 2), 8)
        for x in (a + 0.1, c - 0.1):
            b.box((x - 0.008, -d - 0.06, 0.655), (x + 0.008, -d, 0.668), P["steel"], R)
        f = b.box((a + 0.04, -d - 0.02, 0.09), (c - 0.04, -d, 0.135), P["enamel"], R)
        b.inset(f["-y"], 0.012, -0.006)
        for i in range(4):
            x = a + w * (0.2 + 0.2 * i)
            b.lathe([(0.02, 0), (0.02, 0.018), (0.012, 0.03), (0, 0.032)], P["black"],
                    R @ Tr(x, -d, 0.77) @ Rx(math.pi / 2), 10)
        b.box((a, -d, 0.88), (c, 0, 0.905), P["black"], R)
        b.box((a, -0.07, 0.905), (c, 0, 1.12), P["enamel"], R, inset=[("-y", 0.025, -0.008, None)])
        burners = []
        for fx in (0.27, 0.73):
            for fy in (0.3, 0.68):
                x, y = a + w * fx, -d * fy
                burners.append((x, y))
                b.lathe([(0.085, 0), (0.085, 0.015), (0.075, 0.022), (0.03, 0.022), (0.03, 0.03), (0, 0.03)],
                        P["dark"], R @ Tr(x, y, 0.905), 12)
        pm = self.mb("Props")
        rng.shuffle(burners)
        x, y = burners[0]
        if rng.random() < 0.55:
            p_kettle(pm, R @ Tr(x, y, 0.935) @ Rz(rng.uniform(-0.6, 0.6) + math.pi * 0.5), rng, P)
            self.used.add("kettle")
        else:
            p_pot(pm, R @ Tr(x, y, 0.935) @ Rz(rng.uniform(0, TAU)), rng, P)
        if rng.random() < 0.6:
            x, y = burners[1]
            p_pot(pm, R @ Tr(x, y, 0.935) @ Rz(rng.uniform(0, TAU)), rng, P)
        if rng.random() < 0.8:  # towel over the oven handle
            tw = rng.uniform(0.18, 0.26)
            tx = a + rng.uniform(0.12, w - 0.12 - tw)
            tl = rng.uniform(0.25, 0.35)
            tc = P["towel"]
            for yy, ln in ((-d - 0.075, tl), (-d - 0.045, tl * 0.6)):
                def fn(s, t, yy=yy, ln=ln):
                    return R @ Vector((tx + s * tw, yy - 0.01 * math.sin(s * TAU * 1.5 + t) * t,
                                       0.67 - t * ln))
                b.grid(6, 4, fn, tc)
            b.box((tx, -d - 0.078, 0.66), (tx + tw, -d - 0.042, 0.685), tc, R)

    def sink(self, R, a, c):
        P, rng = self.P, self.rng
        b = self.mb("Sink")
        d = self.depth
        b.box((a, -d + 0.1, 0.1), (c, 0, 0.86), P["dark"], R)
        b.box((a, -d, 0.8), (c, -d + 0.1, 0.86), P["lower"], R)
        bm = _pick(rng, P, "steel", "offwhite")
        f = b.box((a + 0.08, -d - 0.03 + 0.13, 0.7), (c - 0.08, -0.1, 0.906), bm, R)
        bmesh.ops.delete(b.bm, geom=[f["+z"]], context="FACES_ONLY")
        cx = (a + c) / 2
        b.cyl(0.025, 0.005, P["black"], R @ Tr(cx, -d / 2, 0.701), 10)
        tm = _pick(rng, P, "steel", "brass", "copper")
        b.cyl(0.024, 0.22, tm, R @ Tr(cx, -0.055, 0.91), 10)
        b.cyl(0.013, 0.2, tm, R @ Tr(cx, -0.055, 1.11) @ Rx(math.pi / 2 - 0.15), 8)
        b.cyl(0.011, 0.06, tm, R @ Tr(cx, -0.25, 1.14) @ Rx(math.pi), 8)
        for s in (-1, 1):
            b.cyl(0.018, 0.06, tm, R @ Tr(cx + s * 0.1, -0.055, 0.91), 8)
            b.box((cx + s * 0.1 - 0.035, -0.062, 0.965), (cx + s * 0.1 + 0.035, -0.048, 0.98), tm, R)
        # curtain on a rod instead of doors (like the reference)
        b.cyl(0.009, c - a, P["black"], R @ Tr(a, -d - 0.02, 0.84) @ Ry(math.pi / 2), 8)
        cm = P["curtain"]
        split = rng.uniform(0.4, 0.6)
        gap = rng.uniform(0.04, 0.16)
        ph = rng.uniform(0, TAU)
        for s0, s1 in ((0.0, split - gap / 2), (split + gap / 2, 1.0)):
            def fn(s, t, s0=s0, s1=s1):
                u = s0 + (s1 - s0) * s
                x = a + 0.01 + u * (c - a - 0.02)
                fold = math.sin(u * TAU * (c - a) * 9 + ph)
                y = -d - 0.035 - 0.022 * fold * (0.6 + 0.4 * t)
                z = 0.835 - t * (0.835 - 0.04 - 0.02 * math.sin(u * 23 + ph))
                return R @ Vector((x, y, z))
            b.grid(max(6, int((s1 - s0) * (c - a) * 40)), 5, fn, cm)
        # dish rack and soap beside the sink
        pm = self.mb("Props")
        self.sink_x = (a, c)

    def left_run(self):
        """L-shaped short run on the left wall (foreground) with the sink and cork board above."""
        rng = self.rng
        R = self.wf("left")
        a = self.lr_start
        w0 = rng.uniform(0.42, 0.6)
        mods = [("cab", a, a + w0), ("sink", a + w0, a + w0 + 0.86)]
        x = a + w0 + 0.86
        rest = self.lr_end - x
        for w in _split(rest, rng, 0.35, 0.8):
            mods.append(("drawers" if rng.random() < 0.5 else "cab", x, x + w))
            x += w
        self.lower_run(R, mods, "LeftRun")
        self.tiles(R, a, x, lambda _x: 1.12)
        self.cork_span = (a + 0.1, x - 0.05)

    def sideboard(self):
        P, rng = self.P, self.rng
        R = self.wf("left")
        b = self.mb("Sideboard")
        a = rng.uniform(0.35, 0.5)
        c = min(a + rng.uniform(1.1, 1.4), self.door[1] - 0.35)
        d, h = 0.45, 0.82
        b.box((a + 0.03, -d + 0.05, 0), (c - 0.03, -0.02, 0.09), P["dark"], R)
        b.box((a, -d + 0.02, 0.09), (c, 0, h), P["lower"], R)
        b.box((a - 0.02, -d - 0.04, h), (c + 0.02, 0, h + 0.035), P["wood"], R)
        save = self.depth
        self.depth = d
        n = 2 if c - a < 1.15 else 3
        for i in range(n):
            xa = a + (c - a) * i / n + 0.004
            xb = a + (c - a) * (i + 1) / n - 0.004
            self.panel(b, R, xa, xb, h - 0.17, h - 0.005, P["lower"], "knob2")
            self.panel(b, R, xa, xb, 0.1, h - 0.18, P["lower"], None)
            self.knob_at(b, R, xb - 0.05 if i % 2 == 0 else xa + 0.05, -d - 0.02, h - 0.26)
        self.depth = save
        scatter(self.mb("Props"), R @ Tr(0, 0, h + 0.035), [(a, c)], d, rng, P,
                ["radio", "bowl", "plant", "books", "jar", "mug", "basket", "bottle"], skip=0.15, used=self.used)
        self.cork_span = (a + 0.05, c + 0.1)

    # ---- window, doorway, cork board, fridge, lamp
    def window(self, side, u0, u1, z0, z1, Wm, card=True, frame=None):
        P, rng = self.P, self.rng
        b = self.mb("Windows")
        fm = frame or P["trim"]
        cw, cp = 0.075, 0.025
        b.box((u0 - cw, -cp, z0), (u0, 0, z1), fm, Wm)
        b.box((u1, -cp, z0), (u1 + cw, 0, z1), fm, Wm)
        b.box((u0 - cw, -cp, z1), (u1 + cw, 0, z1 + cw), fm, Wm)
        b.box((u0 - cw - 0.03, -0.11, z0 - 0.04), (u1 + cw + 0.03, 0.0, z0), fm, Wm)
        b.box((u0 - cw, -cp, z0 - 0.12), (u1 + cw, 0, z0 - 0.04), fm, Wm)
        y0, y1 = T * 0.35, T * 0.6
        fw = 0.045
        sm = P["offwhite"] if rng.random() < 0.5 else fm
        b.box((u0, y0, z0), (u0 + fw, y1, z1), sm, Wm)
        b.box((u1 - fw, y0, z0), (u1, y1, z1), sm, Wm)
        b.box((u0 + fw, y0, z1 - fw), (u1 - fw, y1, z1), sm, Wm)
        b.box((u0 + fw, y0, z0), (u1 - fw, y1, z0 + fw), sm, Wm)
        um = (u0 + u1) / 2
        b.box((um - 0.016, y0, z0 + fw), (um + 0.016, y1, z1 - fw), sm, Wm)
        zm = z0 + (z1 - z0) * rng.uniform(0.5, 0.6)
        b.box((u0 + fw, y0, zm - 0.016), (u1 - fw, y1, zm + 0.016), sm, Wm)
        # sill clutter
        if card:
            pm = self.mb("Props")
            scatter(pm, Wm @ Tr(0, 0, z0), [(u0 - 0.05, u1 + 0.05)], 0.1, rng, P,
                    ["plant", "bottle", "jar", "plant", "glass"], skip=0.3, rot=1.0, gap=(0.03, 0.2))
        # outside: flat sky card + a row of rooftops / facades (shadowless)
        sky = self.mb("HallSky" if side == "hall" else "SkyCard")
        dist = T + 2.5
        sky.box((u0 - 4, dist, z0 - 3), (u1 + 4, dist + 0.05, z1 + 4), P["card"], Wm)
        city = self.mb("HallSky" if side == "hall" else "Skyline")
        x = u0 - 3.5
        while x < u1 + 3.5:
            bw = rng.uniform(0.9, 2.0)
            top = rng.uniform(z1 - 0.6, z1 + 1.2) if rng.random() < 0.8 else z0 - 0.5
            y = T + rng.uniform(1.4, 2.2)
            city.box((x, y, z0 - 3), (x + bw - 0.1, y + 0.3, top), P["city"], Wm)
            for k in range(rng.randint(1, 4)):
                wx = x + rng.uniform(0.1, bw - 0.4)
                wz = rng.uniform(z0 - 1.0, top - 0.4)
                lit = P["lit"] if rng.random() < 0.5 else P["dark"]
                city.box((wx, y - 0.02, wz), (wx + 0.18, y, wz + 0.28), lit, Wm)
            x += bw

    def doorway(self):
        P = self.P
        side, u0, u1 = self.door
        Wm = self.wf(side)
        b = self.mb("Trim")
        cw, cp, zh = 0.095, 0.03, 2.1
        b.box((u0 - cw, -cp, 0), (u0, 0, zh), P["trim"], Wm)
        b.box((u1, -cp, 0), (u1 + cw, 0, zh), P["trim"], Wm)
        b.box((u0 - cw - 0.02, -cp - 0.01, zh), (u1 + cw + 0.02, 0, zh + cw + 0.02), P["trim"], Wm)
        b.box((u0, 0, 0), (u0 + 0.02, T, zh), P["trim"], Wm)
        b.box((u1 - 0.02, 0, 0), (u1, T, zh), P["trim"], Wm)
        b.box((u0, 0, zh - 0.02), (u1, T, zh), P["trim"], Wm)
        b.box((u0, -0.01, 0), (u1, T, 0.012), P["wood"], Wm)

    def cork(self):
        P, rng = self.P, self.rng
        Wm = self.wf("left")
        a, c = self.cork_span
        c = min(c, a + 1.6)
        za, zb = rng.uniform(1.17, 1.25), rng.uniform(1.95, 2.1)
        b = self.mb("CorkBoard")
        f = b.box((a, -0.03, za), (c, 0, zb), P["wood"], Wm)
        b.inset(f["-y"], 0.035, -0.012, P["cork"])
        ys = -0.018
        n = rng.randint(4, 8)
        cols = max(2, int(round(math.sqrt(n * (c - a) / (zb - za)))))
        rows = int(math.ceil(n / cols))
        cells = [(i, j) for i in range(cols) for j in range(rows)]
        rng.shuffle(cells)
        cw, ch = (c - a - 0.1) / cols, (zb - za - 0.1) / rows
        for (i, j) in cells[:n]:
            pw = min(cw * rng.uniform(0.7, 0.95), 0.32)
            ph = min(ch * rng.uniform(0.75, 1.0), 0.34)
            ux = a + 0.05 + cw * (i + 0.5) + rng.uniform(-0.03, 0.03)
            zt = za + 0.05 + ch * (j + 1) - 0.01 + rng.uniform(-0.02, 0.01)
            rot = rng.uniform(-0.14, 0.14)
            tilt = -rng.uniform(0.05, 0.22) if rng.random() < 0.35 else 0.0
            M = Wm @ Tr(ux, ys, zt) @ Ry(rot) @ Rx(tilt)
            pm = _pick(rng, P, "paper", "paper", "paper_y", "paper_b", "offwhite")
            b.box((-pw / 2, -0.002, -ph), (pw / 2, 0, 0), pm, M)
            for k in range(rng.randint(0, 5)):
                lw = pw * rng.uniform(0.4, 0.8)
                lz = -0.05 - k * 0.035
                if -lz > ph - 0.03:
                    break
                b.box((-pw / 2 + 0.025, -0.0035, lz - 0.004), (-pw / 2 + 0.025 + lw, -0.002, lz), P["ink"], M)
            b.lathe([(0.011, 0), (0.011, 0.008), (0.006, 0.012), (0, 0.014)],
                    _pick(rng, P, "red", "mustard", "dustyblue", "sage"), M @ Tr(0, -0.002, -0.015) @ Rx(math.pi / 2), 8)

    def fridge(self):
        P, rng = self.P, self.rng
        R = self.wf("back")
        b = self.mb("Fridge")
        a, c = self.fx
        d, h = 0.68, rng.uniform(1.62, 1.8)
        f = b.box((a, -d + 0.03, 0.05), (c, 0, h), P["fridge"], R)
        edges = list({e for k in ("+z",) for e in f[k].edges})
        bmesh.ops.bevel(b.bm, geom=edges, offset=0.05, offset_type="OFFSET", segments=3,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
        b.box((a + 0.05, -d + 0.08, 0), (c - 0.05, -0.05, 0.05), P["dark"], R)
        zs = h - rng.uniform(0.42, 0.55)
        for za, zb in ((0.07, zs - 0.006), (zs + 0.006, h - 0.06)):
            g = b.box((a + 0.006, -d, za), (c - 0.006, -d + 0.03, zb), P["fridge"], R)
            bmesh.ops.bevel(b.bm, geom=list(g["-y"].edges), offset=0.018, offset_type="OFFSET", segments=2,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
        hm = _pick(rng, P, "steel", "black", "cream")
        hx = a + 0.06
        for za, zb in ((zs - 0.45, zs - 0.08), (zs + 0.06, zs + 0.3)):
            b.box((hx - 0.012, -d - 0.05, za), (hx + 0.012, -d - 0.03, zb), hm, R)
            for z in (za + 0.02, zb - 0.02):
                b.box((hx - 0.01, -d - 0.04, z - 0.01), (hx + 0.01, -d, z + 0.01), hm, R)
        b.box(((a + c) / 2 - 0.08, -d - 0.004, zs - 0.07), ((a + c) / 2 + 0.08, -d, zs - 0.04), P["steel"], R)
        # notes and magnets on the door
        for k in range(rng.randint(1, 4)):
            pw, ph = rng.uniform(0.1, 0.17), rng.uniform(0.12, 0.2)
            ux = rng.uniform(a + 0.18, c - 0.15)
            zt = rng.uniform(0.9, zs - 0.12)
            M = R @ Tr(ux, -d - 0.001, zt) @ Ry(rng.uniform(-0.2, 0.2))
            b.box((-pw / 2, -0.002, -ph), (pw / 2, 0, 0), _pick(rng, P, "paper", "paper_y", "paper_b"), M)
            b.cyl(0.016, 0.012, _pick(rng, P, "red", "mustard", "dustyblue", "sage"),
                  M @ Tr(0, -0.002, -0.02) @ Rx(math.pi / 2), 8)
        scatter(self.mb("Props"), R @ Tr(0, 0, h), [(a + 0.03, c - 0.03)], d - 0.05, rng, P,
                ["basket", "bottle", "jar", "books", "bowl"], skip=0.3)

    def lamp(self):
        P, rng = self.P, self.rng
        b = self.mb("Lamp")
        x = self.W * rng.uniform(0.42, 0.52)
        y = self.D * rng.uniform(0.5, 0.6)
        zl = rng.uniform(1.95, 2.1)
        b.cyl(0.006, H - zl - 0.15, P["black"], Tr(x, y, zl + 0.15), 6)
        b.cyl(0.05, 0.025, P["black"], Tr(x, y, H - 0.025), 10)
        b.lathe([(0.03, 0.17), (0.035, 0.15), (0.07, 0.1), (0.2, 0.005), (0.205, 0.0), (0.195, 0.0),
                 (0.065, 0.095), (0, 0.13)], P["shade"], Tr(x, y, zl), 18)
        b.sphere(0.045, P["bulb"], Tr(x, y, zl + 0.03), 10, 6)
        self.lamp_pos = (x, y, zl - 0.05)

    def floor_props(self):
        P, rng = self.P, self.rng
        b = self.mb("FloorProps")
        W, D = self.W, self.D
        # chair or stool in the open floor near the left wall / window
        cx = rng.uniform(1.0, 1.7)
        if self.layout == "back":
            cy = rng.uniform(self.win[0], self.win[1])
        else:
            cy = rng.uniform(1.8, self.door[1] - 0.2)
        cm = _pick(rng, P, "wood", "trim", "wood_lt", "terracotta")
        M = Tr(cx, cy, 0) @ Rz(rng.uniform(0, TAU))
        if rng.random() < 0.55:
            s, hs = 0.21, 0.45
            for sx in (-1, 1):
                for sy in (-1, 1):
                    top = 0.95 if sy > 0 else hs
                    b.box((sx * s - 0.02, sy * s - 0.02, 0), (sx * s + 0.02, sy * s + 0.02, top), cm, M)
            b.box((-s - 0.03, -s - 0.03, hs), (s + 0.03, s + 0.03, hs + 0.04), cm, M)
            for z in (0.62, 0.8):
                b.box((-s + 0.02, s - 0.015, z), (s - 0.02, s + 0.015, z + 0.07), cm, M)
            b.box((-s, -s, 0.18), (s, -s + 0.02, 0.21), cm, M)
        else:
            b.lathe([(0.17, 0.6), (0.18, 0.62), (0.18, 0.66), (0.16, 0.67), (0, 0.67)], cm, M, 16)
            for k in range(3):
                a = TAU * k / 3
                L = 0.62
                U = M @ Tr(math.cos(a) * 0.2, math.sin(a) * 0.2, 0) @ Rz(a) @ Ry(-0.15)
                b.box((-0.018, -0.018, 0), (0.018, 0.018, L), cm, U)
            b.torus(0.15, 0.01, cm, M @ Tr(0, 0, 0.25), 0, TAU, 14, 5)
        # broom leaning against a wall
        side = "right" if self.layout == "left" else rng.choice(["right", "left"])
        if side == "left":
            u = rng.uniform(self.lr_end + 0.05, self.win[0] - 0.05)
        else:
            u = rng.uniform(0.9, 1.6)  # right wall, u = D - y from the back corner
        Wm = self.wf(side)
        ang = rng.uniform(0.14, 0.22)
        U = Wm @ Tr(u, -0.05 - 1.35 * math.sin(ang), 0) @ Rz(rng.uniform(-0.3, 0.3)) @ Rx(-ang)
        b.cyl(0.013, 1.35, _pick(rng, P, "wood_lt", "red", "sage"), U @ Tr(0, 0, 0.18), 8)
        b.box((-0.11, -0.03, 0.12), (0.11, 0.03, 0.2), P["wood"], U)
        b.lathe([(0.13, 0.0), (0.1, 0.12), (0.0, 0.125)], P["mustard"],
                U @ Sc(1, 0.3, 1), 10, smooth=False)
        # bucket and rug
        if rng.random() < 0.6:
            bx = rng.uniform(1.8, W - 1.8)
            M = Tr(bx, D - self.depth - rng.uniform(0.2, 0.35), 0)
            bc = _pick(rng, P, "steel", "sage", "dustyblue")
            b.lathe([(0.11, 0), (0.14, 0.26), (0.13, 0.26), (0.1, 0.01), (0, 0.01)], bc, M, 14)
            b.torus(0.135, 0.005, P["black"], M @ Tr(0, 0, 0.26) @ Rx(math.pi / 2 + 0.6), 0, math.pi, 10, 4)
        if self.layout == "back":
            R = self.wf("left")
            sx = self.mods_sink_center()
            M = R @ Tr(sx, -self.depth - 0.5, 0)
        else:
            M = Tr((self.win[0] + self.win[1]) / 2, D - self.depth - 0.5, 0)
        rw, rd = rng.uniform(0.9, 1.3), rng.uniform(0.5, 0.65)
        f = b.box((-rw / 2, -rd / 2, 0.003), (rw / 2, rd / 2, 0.015), P["rug"], M @ Rz(rng.uniform(-0.08, 0.08)))
        f["+z"].material_index = b.mi(P["rug_b"])
        b.inset(f["+z"], 0.06, 0.0, P["rug"])
        # rubbish bin by the run end
        if rng.random() < 0.6:
            M = Tr(self.fx[0] - 0.1, D - self.depth - 0.25, 0)
            b.lathe([(0.12, 0), (0.13, 0.42), (0.135, 0.42), (0.135, 0.46), (0, 0.47)],
                    _pick(rng, P, "steel", "sage", "cream"), M, 14)

    def mods_sink_center(self):
        a, c = getattr(self, "sink_x", (0.6, 1.4))
        return (a + c) / 2

    # ---- the darker hallway beyond the doorway
    def hall(self):
        P, rng = self.P, self.rng
        F, hd, hw0, hw1 = self.F, self.hd, self.hw0, self.hw1
        Hh = 2.6
        b = self.mb("HallShell")
        wx = self.hwin
        wu0, wu1 = wx - 0.45, wx + 0.45
        z0, z1 = 0.85, 2.05
        far = F @ Tr(-hw0 - T, hd, 0)
        b.slab(hw0 + hw1 + 2 * T, Hh, [(wu0 + hw0 + T, wu1 + hw0 + T, z0, z1)], T, P["hall"], far,
               zsplit=0.95, m_lo=P["hall_lo"])
        b.slab(hd + T, Hh, [], T, P["hall"], F @ Tr(-hw0, 0, 0) @ Rz(math.pi / 2), zsplit=0.95, m_lo=P["hall_lo"])
        b.slab(hd + T, Hh, [], T, P["hall"], F @ Tr(hw1, hd + T, 0) @ Rz(-math.pi / 2), zsplit=0.95,
               m_lo=P["hall_lo"])
        b.box((-hw0 - T, -T, Hh), (hw1 + T, hd + T, Hh + 0.12), P["hall"], F)
        b.box((-hw0, hd - 0.02, 0), (hw1, hd, 0.12), P["wood_dk"], F)
        # plank floor
        fl = self.mb("HallFloor")
        pw = 0.14
        n = int(math.ceil((hw0 + hw1) / pw))
        for i in range(n):
            x0 = -hw0 + i * pw
            x1 = min(x0 + pw, hw1)
            y = -T
            while y < hd:
                L = rng.uniform(0.6, 1.4)
                y1 = min(y + L, hd)
                v = [fl.bm.verts.new(F @ Vector(c)) for c in
                     ((x0, y, 0), (x1, y, 0), (x1, y1, 0), (x0, y1, 0))]
                fl.face(v, P["hall_floor"] if rng.random() < 0.5 else P["hall_floor2"])
                y = y1
        # window with curtains
        Wm = F @ Tr(0, hd, 0)
        self.window("hall", wu0, wu1, z0, z1, Wm, card=True, frame=P["wood_dk"])
        hp = self.mb("HallProps")
        hp.cyl(0.01, 1.6, P["black"], Wm @ Tr(wx - 0.8, -0.08, z1 + 0.12) @ Ry(math.pi / 2), 8)
        ph = rng.uniform(0, TAU)
        for s0, s1 in ((wx - 0.78, wu0 + rng.uniform(0.05, 0.2)), (wu1 - rng.uniform(0.05, 0.2), wx + 0.78)):
            def fn(s, t, s0=s0, s1=s1):
                x = s0 + (s1 - s0) * s
                return Wm @ Vector((x, -0.1 - 0.03 * math.sin(x * 40 + ph), z1 + 0.11 - t * (z1 + 0.11 - 0.15)))
            hp.grid(10, 6, fn, P["curtain_h"])
        # chair, picture frame, console with a little lamp
        side = 1 if wx < 0 else -1
        cm = P["wood"]
        M = F @ Tr(wx + side * 0.85, hd - 0.45, 0) @ Rz(rng.uniform(-0.6, 0.6) + math.pi)
        s = 0.21
        for sx in (-1, 1):
            for sy in (-1, 1):
                top = 0.95 if sy > 0 else 0.45
                hp.box((sx * s - 0.02, sy * s - 0.02, 0), (sx * s + 0.02, sy * s + 0.02, top), cm, M)
        hp.box((-s - 0.03, -s - 0.03, 0.45), (s + 0.03, s + 0.03, 0.49), cm, M)
        hp.box((-s, s - 0.015, 0.7), (s, s + 0.015, 0.9), cm, M)
        if rng.random() < 0.5:
            hp.box((-s * 0.9, -s * 0.9, 0.49), (s * 0.9, s * 0.9, 0.53), P["red"], M)
        px = wx - side * rng.uniform(0.9, 1.2)
        f = hp.box((px - 0.25, hd - 0.03, 1.3), (px + 0.25, hd, 1.75), P["wood_dk"], F)
        hp.inset(f["-y"], 0.045, -0.01, P["picture"])
        ct = F @ Tr(px, hd - 0.2, 0)
        hp.box((-0.4, -0.18, 0.78), (0.4, 0.18, 0.82), P["wood_dk"], ct)
        for sx in (-0.37, 0.37):
            for sy in (-0.15, 0.15):
                hp.box((sx - 0.02, sy - 0.02, 0), (sx + 0.02, sy + 0.02, 0.78), P["wood_dk"], ct)
        hp.cyl(0.05, 0.25, P["dark"], ct @ Tr(0.2, 0, 0.82), 10)
        hp.lathe([(0.1, 0), (0.06, 0.15), (0.0, 0.15)], P["lampshade_h"], ct @ Tr(0.2, 0, 1.03), 12,
                 smooth=False, cap0=True)
        self.hall_lamp = ct @ Vector((0.2, 0, 1.02))
        # runner rug
        hp.box((-0.4, 0.1, 0.002), (0.4, min(hd - 0.3, 1.9), 0.012), P["rug"], F)

    # ---- lights
    def lights(self):
        K, rng = self.K, self.rng

        def add(name, kind, energy, color, loc, size=0.1, rot=None):
            ld = bpy.data.lights.new(name, kind)
            ld.energy = energy
            ld.color = color
            if kind == "AREA":
                ld.size = size
            else:
                ld.shadow_soft_size = size
            ob = bpy.data.objects.new(name, ld)
            ob.location = Vector(loc) + OFF
            if rot:
                ob.rotation_euler = rot
            self.col.objects.link(ob)

        x, y, z = self.lamp_pos
        if K["lamp"] > 0:
            add("PW_LampLight", "POINT", K["lamp"], (1.0, 0.78, 0.5), (x, y, z), 0.04)
            # light spilling up out of the shade so the ceiling doesn't go black
            add("PW_LampUp", "POINT", K["lamp"] * 0.3, (1.0, 0.8, 0.55), (x, y, H - 0.3), 0.5)
        cl = self.cam["location"]
        add("PW_Fill", "AREA", K["fill"], K["fcol"], (cl[0] - 0.6, cl[1] + 0.3, H - 0.05), 2.0)
        # skylight through the window: a rectangle in the opening shining into the room
        u0, u1, z0, z1 = self.win
        ld = bpy.data.lights.new("PW_WindowLight", "AREA")
        ld.shape, ld.size, ld.size_y = "RECTANGLE", u1 - u0, z1 - z0
        ld.energy, ld.color = K["win"], K["wcol"]
        ob = bpy.data.objects.new("PW_WindowLight", ld)
        self.col.objects.link(ob)
        ob.matrix_world = Matrix.Translation(OFF) @ self.wf(self.win_side) @ \
            Tr((u0 + u1) / 2, -0.02, (z0 + z1) / 2) @ Rx(-math.pi / 2)
        if K["hall"] > 0:
            add("PW_HallLight", "POINT", K["hall"], (1.0, 0.7, 0.42), tuple(self.hall_lamp), 0.05)


class Kitchen:
    """A cluttered, lived-in kitchen interior (ink-style graphic-novel panel)."""
    LABEL = "Kitchen interior"

    @staticmethod
    def build(col, seed, size, detail, height, mood="GOLDEN", **kw):
        return _Kitchen(col, seed, mood).run()

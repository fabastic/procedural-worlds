"""Coastal island: cliffs on one side, beach on the other, a lighthouse + cottage on the clifftop,
chunky rocks and sea stacks, Geometry Nodes grass tufts and an ink-authored sea with foam rings."""
import math, random
import bpy, bmesh
from mathutils import Vector, noise
from . import core
from .ink import srgb, INK

# sea colours per mood (display sRGB): near, far/horizon, shallows, foam
SEA = {
    "DAY": (srgb(0.17, 0.42, 0.44), srgb(0.50, 0.68, 0.66), srgb(0.42, 0.68, 0.60), srgb(0.96, 0.94, 0.86)),
    "GOLDEN": (srgb(0.14, 0.31, 0.34), srgb(0.72, 0.64, 0.46), srgb(0.36, 0.55, 0.45), srgb(1.0, 0.93, 0.78)),
    "DUSK": (srgb(0.12, 0.16, 0.29), srgb(0.62, 0.42, 0.42), srgb(0.24, 0.33, 0.42), srgb(0.92, 0.80, 0.74)),
    "NIGHT": (srgb(0.04, 0.07, 0.12), srgb(0.14, 0.19, 0.27), srgb(0.09, 0.17, 0.22), srgb(0.55, 0.62, 0.66)),
}


def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _mesh_obj(name, bm, col, mat=None, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    if mat is not None:
        me.materials.append(mat)
    return o


def _set_mats(o, *mats):
    for m in mats:
        o.data.materials.append(m)


# ----------------------------------------------------------------------------- materials
def terrain_material():
    """Sand (low) -> sage grass (flat, high) -> ochre-grey rock (steep), with dark strata lines on
    rock faces that read as ink after cel shading."""
    m = bpy.data.materials.get("PW_IslandTerrain") or bpy.data.materials.new("PW_IslandTerrain")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out, bsdf = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled")
    geo = N("ShaderNodeNewGeometry")
    sep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], sep.inputs[0])
    nsep = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], nsep.inputs[0])
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.35
    L(geo.outputs["Position"], nz.inputs["Vector"])

    def sk(c, i):
        return next(x for x in c if x.identifier == i)

    def mix(fac, a, b):
        mx = N("ShaderNodeMix")
        mx.data_type = "RGBA"
        for ident, v in (("A_Color", a), ("B_Color", b)):
            if isinstance(v, bpy.types.NodeSocket):
                L(v, sk(mx.inputs, ident))
            else:
                sk(mx.inputs, ident).default_value = (*v, 1)
        L(fac, sk(mx.inputs, "Factor_Float"))
        return sk(mx.outputs, "Result_Color")

    def mr(v, a, b):
        n = N("ShaderNodeMapRange")
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
        L(v, n.inputs["Value"])
        return n.outputs["Result"]

    def add(a, b):
        n = N("ShaderNodeMath")
        n.operation = "ADD"
        L(a, n.inputs[0])
        L(b, n.inputs[1])
        return n.outputs[0]

    sand, wet = srgb(0.86, 0.76, 0.55), srgb(0.62, 0.52, 0.38)
    grass, grass2 = srgb(0.46, 0.56, 0.34), srgb(0.36, 0.50, 0.36)
    rock, rock2 = srgb(0.66, 0.58, 0.46), srgb(0.52, 0.47, 0.42)
    zt = add(sep.outputs["Z"], mr(nz.outputs["Fac"], 0.3, 0.7))   # noisy height
    c = mix(mr(zt, 0.1, 0.8), wet, sand)
    gmix = mix(mr(nz.outputs["Fac"], 0.4, 0.6), grass, grass2)
    c = mix(mr(zt, 1.4, 2.0), c, gmix)
    steep = mr(nsep.outputs["Z"], 0.80, 0.62)          # 1 on cliff faces
    rk = mix(mr(nz.outputs["Fac"], 0.35, 0.65), rock, rock2)
    # strata: wobbly horizontal bands on rock faces -> dark ink lines
    wv = N("ShaderNodeTexWave")
    wv.wave_type, wv.bands_direction, wv.wave_profile = "BANDS", "Z", "SAW"
    wv.inputs["Scale"].default_value = 0.24
    wv.inputs["Distortion"].default_value = 7.0
    wv.inputs["Detail"].default_value = 1.0
    L(geo.outputs["Position"], wv.inputs["Vector"])
    lt = N("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    L(wv.outputs["Fac"], lt.inputs[0])
    lt.inputs[1].default_value = 0.07
    rk = mix(lt.outputs[0], rk, srgb(0.16, 0.13, 0.11))
    # vertical fissures: noise stretched along Z, thin dark cracks down the cliff
    fs = N("ShaderNodeVectorMath")
    fs.operation = "MULTIPLY"
    fs.inputs[1].default_value = (1.4, 1.4, 0.12)
    L(geo.outputs["Position"], fs.inputs[0])
    fn = N("ShaderNodeTexNoise")
    fn.inputs["Scale"].default_value = 1.0
    fn.inputs["Detail"].default_value = 2.0
    L(fs.outputs[0], fn.inputs["Vector"])
    crack = N("ShaderNodeMath")
    crack.operation = "COMPARE"
    crack.inputs[1].default_value = 0.5
    crack.inputs[2].default_value = 0.012
    L(fn.outputs["Fac"], crack.inputs[0])
    rk = mix(crack.outputs[0], rk, srgb(0.20, 0.16, 0.13))
    # lit ochre ledges vs darker lower face for more value structure
    rk = mix(mr(sep.outputs["Z"], 0.0, 6.0), mix(mr(nz.outputs["Fac"], 0.2, 0.8), rk, srgb(0.42, 0.36, 0.32)), rk)
    c = mix(steep, c, rk)
    L(c, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    L(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def sea_material(mood, cam_xy, seed):
    """Ink-authored sea (left alone by the toon pass): flat near/far bands, shallows, foam rings from
    the baked shore height and hand-drawn wave dashes that thin out with distance."""
    near, far, shallow, foam = SEA[mood]
    m = bpy.data.materials.get("PW_IslandSea") or bpy.data.materials.new("PW_IslandSea")
    m["pw_ink_custom"] = 1
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    from .ink import _T
    t = _T(nt)
    out = t.node("ShaderNodeOutputMaterial")
    geo = t.node("ShaderNodeNewGeometry")
    P = geo.outputs["Position"]
    pos = t.node("ShaderNodeSeparateXYZ", {"Vector": P})
    shore = t.node("ShaderNodeAttribute", attribute_name="pw_shore", attribute_type="GEOMETRY").outputs["Fac"]
    dx = t.math("SUBTRACT", pos.outputs["X"], cam_xy[0])
    dy = t.math("SUBTRACT", pos.outputs["Y"], cam_xy[1])
    dist = t.math("SQRT", t.math("ADD", t.math("MULTIPLY", dx, dx), t.math("MULTIPLY", dy, dy)))
    # flat banded water: near -> mid -> far (3 hard bands with wobbly borders)
    wob = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("SCALE", P, scale=0.02), "Scale": 2.0})
    dw = t.math("MULTIPLY", dist, t.maprange(wob.outputs["Fac"], 0.3, 0.7, 0.85, 1.15))
    b1, b2 = t.math("GREATER_THAN", dw, 140.0), t.math("GREATER_THAN", dw, 420.0)
    col = t.mix(b1, (*near, 1), t.mix(0.5, (*near, 1), (*far, 1)))
    col = t.mix(b2, col, (*far, 1))
    # shallows + foam rings (terrain height under the water, noisy)
    fn = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("SCALE", P, scale=0.25), "Scale": 1.5, "Detail": 2.0})
    f = t.math("ADD", shore, t.math("MULTIPLY", t.math("SUBTRACT", fn.outputs["Fac"], 0.5), 0.5))
    col = t.mix(t.math("GREATER_THAN", f, -1.25), col, (*shallow, 1))
    brk = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("SCALE", P, scale=0.5), "Scale": 1.2})
    br = t.math("GREATER_THAN", brk.outputs["Fac"], 0.42)
    foam_m = t.math("GREATER_THAN", f, -0.22)                       # surf band hugging the shore
    for lvl, w, gated in ((-0.55, 0.06, False), (-0.95, 0.045, True), (-1.45, 0.035, True)):
        ring = t.math("LESS_THAN", t.math("ABSOLUTE", t.math("SUBTRACT", f, lvl)), w)
        foam_m = t.math("MAXIMUM", foam_m, t.math("MULTIPLY", ring, br) if gated else ring)
    # ink edge on the outer side of the surf band
    surf_edge = t.math("LESS_THAN", t.math("ABSOLUTE", t.math("SUBTRACT", f, -0.26)), 0.035)
    col = t.mix(foam_m, col, (*foam, 1))
    col = t.mix(t.math("MULTIPLY", surf_edge, 0.85), col, (*INK, 1))
    # wave dashes: long wobbly bands broken into strokes, thinner and fewer with distance
    wv = t.node("ShaderNodeTexWave", {"Vector": t.vmath("MULTIPLY", P, (0.18, 0.9, 0.0)), "Scale": 0.8,
                                      "Distortion": 5.0, "Detail": 1.0, "Detail Scale": 0.5},
                wave_type="BANDS", bands_direction="Y", wave_profile="SAW")
    wb = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("MULTIPLY", P, (0.25, 0.6, 0.0)), "Scale": 1.0})
    width = t.maprange(dist, 25.0, 260.0, 0.075, 0.0)
    dash = t.math("MULTIPLY", t.math("LESS_THAN", wv.outputs["Fac"], width),
                  t.math("GREATER_THAN", wb.outputs["Fac"], 0.5))
    dash = t.math("MULTIPLY", dash, t.math("LESS_THAN", f, -1.6))
    col = t.mix(t.math("MULTIPLY", dash, 0.7), col, t.mix(1.0, col, (*INK, 1), blend="MULTIPLY"))
    # light crest dashes, offset from the ink ones
    wv2 = t.node("ShaderNodeTexWave", {"Vector": t.vmath("ADD", t.vmath("MULTIPLY", P, (0.18, 0.9, 0.0)), (3.0, 0.6, 0.0)),
                                       "Scale": 0.8, "Distortion": 5.0, "Detail": 1.0, "Detail Scale": 0.5},
                 wave_type="BANDS", bands_direction="Y", wave_profile="SAW")
    crest = t.math("MULTIPLY", t.math("LESS_THAN", wv2.outputs["Fac"], t.math("MULTIPLY", width, 0.6)),
                   t.math("LESS_THAN", wb.outputs["Fac"], 0.42))
    col = t.mix(t.math("MULTIPLY", crest, 0.55), col, (*foam, 1))
    em = t.node("ShaderNodeEmission", {"Color": col, "Strength": 1.0})
    t.link(em.outputs[0], out.inputs["Surface"])
    return m


# ----------------------------------------------------------------------------- props
def rock_bm(rng, radius, flat=0.7, sub=1):
    """Chunky angular rock: displaced icosphere with a flattened base."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=radius)
    o = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    sx, sy = rng.uniform(0.8, 1.35), rng.uniform(0.75, 1.25)
    for v in bm.verts:
        n = noise.noise(v.co * (1.3 / radius) + o)
        v.co *= 1.0 + 0.32 * n
        v.co.x *= sx
        v.co.y *= sy
        if v.co.z < 0:
            v.co.z *= 0.35
        v.co.z *= flat
    return bm


def lighthouse(col, base, mats, rng, mood):
    """Octagonal striped tower, gallery with railing, lantern room, dome, door; returns lamp pos."""
    white, red, dark, lamp = mats
    H, r0, r1 = 11.0, 1.9, 1.25
    segs = 5
    parts = []
    for i in range(segs):
        z0, z1 = H * i / segs, H * (i + 1) / segs
        bm = bmesh.new()
        ra = r0 + (r1 - r0) * i / segs
        rb = r0 + (r1 - r0) * (i + 1) / segs
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=ra, radius2=rb, depth=z1 - z0)
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, (z0 + z1) / 2))
        o = _mesh_obj(f"PW_LH_Seg{i}", bm, col, red if i % 2 else white)
        parts.append(o)
    # gallery deck + railing posts + lantern + dome
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r1 + 0.65, radius2=r1 + 0.65, depth=0.28)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, H + 0.14))
    parts.append(_mesh_obj("PW_LH_Deck", bm, col, dark))
    bm = bmesh.new()
    for k in range(16):
        a = k / 16 * math.tau
        p = bmesh.ops.create_cube(bm, size=1)["verts"]
        bmesh.ops.scale(bm, vec=(0.07, 0.07, 0.75), verts=p)
        bmesh.ops.translate(bm, verts=p, vec=((r1 + 0.55) * math.cos(a), (r1 + 0.55) * math.sin(a), H + 0.65))
    ring = bmesh.ops.create_cone(bm, cap_ends=False, segments=16, radius1=r1 + 0.57, radius2=r1 + 0.57, depth=0.08)
    bmesh.ops.translate(bm, verts=ring["verts"], vec=(0, 0, H + 1.03))
    parts.append(_mesh_obj("PW_LH_Rail", bm, col, dark))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r1 * 0.78, radius2=r1 * 0.78, depth=1.5)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, H + 1.05))
    parts.append(_mesh_obj("PW_LH_Lantern", bm, col, lamp))
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r1 * 0.95, radius2=0.12, depth=1.1)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, H + 2.35))
    parts.append(_mesh_obj("PW_LH_Dome", bm, col, red))
    bm = bmesh.new()
    p = bmesh.ops.create_cube(bm, size=1)["verts"]
    bmesh.ops.scale(bm, vec=(0.9, 0.25, 1.9), verts=p)
    bmesh.ops.translate(bm, verts=p, vec=(0, -r0 + 0.02, 0.95))
    for z in (4.2, 7.4):                     # two small windows up the tower
        q = bmesh.ops.create_cube(bm, size=1)["verts"]
        bmesh.ops.scale(bm, vec=(0.42, 0.22, 0.65), verts=q)
        bmesh.ops.translate(bm, verts=q, vec=(0, -(r0 + (r1 - r0) * z / H) + 0.04, z))
    parts.append(_mesh_obj("PW_LH_Door", bm, col, dark))
    for o in parts:
        o.location = base
    return Vector(base) + Vector((0, 0, H + 1.05))


def cottage(col, base, yaw, mats):
    wall, roof, dark = mats
    bm = bmesh.new()
    p = bmesh.ops.create_cube(bm, size=1)["verts"]
    bmesh.ops.scale(bm, vec=(5.0, 3.6, 2.6), verts=p)
    bmesh.ops.translate(bm, verts=p, vec=(0, 0, 1.3))
    body = _mesh_obj("PW_Cottage", bm, col, wall)
    bm = bmesh.new()   # gable roof prism with overhang
    vs = [bm.verts.new(c) for c in ((-2.8, -2.15, 2.5), (2.8, -2.15, 2.5), (2.8, 2.15, 2.5), (-2.8, 2.15, 2.5),
                                    (-2.8, 0, 4.4), (2.8, 0, 4.4))]
    for f in ((0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)):
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rf = _mesh_obj("PW_CottageRoof", bm, col, roof)
    bm = bmesh.new()
    p = bmesh.ops.create_cube(bm, size=1)["verts"]          # chimney
    bmesh.ops.scale(bm, vec=(0.6, 0.6, 1.8), verts=p)
    bmesh.ops.translate(bm, verts=p, vec=(1.6, 0.8, 4.2))
    for x in (-1.4, 1.4):                                   # windows + door
        q = bmesh.ops.create_cube(bm, size=1)["verts"]
        bmesh.ops.scale(bm, vec=(0.9, 0.2, 0.8), verts=q)
        bmesh.ops.translate(bm, verts=q, vec=(x, -1.82, 1.6))
    q = bmesh.ops.create_cube(bm, size=1)["verts"]
    bmesh.ops.scale(bm, vec=(0.8, 0.2, 1.7), verts=q)
    bmesh.ops.translate(bm, verts=q, vec=(0.0, -1.82, 0.85))
    det = _mesh_obj("PW_CottageDetail", bm, col, dark)
    for o in (body, rf, det):
        o.location = base
        o.rotation_euler.z = yaw


def tuft_proto(col, mat):
    """A tuft of 6 crossed grass blades used as the GN instance."""
    bm = bmesh.new()
    rng = random.Random(3)
    for k in range(6):
        a = k / 6 * math.pi + rng.uniform(-0.3, 0.3)
        lean = rng.uniform(-0.25, 0.25)
        h = rng.uniform(0.32, 0.55)
        w = 0.13
        ca, sa = math.cos(a), math.sin(a)
        v0 = bm.verts.new((-w * ca, -w * sa, 0))
        v1 = bm.verts.new((w * ca, w * sa, 0))
        v2 = bm.verts.new((lean * -sa + 0.02, lean * ca, h))
        bm.faces.new((v0, v1, v2))
    o = _mesh_obj("PW_TuftProto", bm, col, mat)
    o.hide_render = True
    o.hide_viewport = True
    o["pw_line"] = 0
    o["pw_wonk"] = 0
    return o


def grass_nodes(proto, density, zmin, seed):
    """GN: scatter tufts on flat ground above zmin (no weight painting: slope + height masks)."""
    name = "PW_IslandGrass"
    g = bpy.data.node_groups.get(name)
    if g is not None:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new(name, "GeometryNodeTree")
    g.is_modifier = True
    g.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    g.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    from .ink import _T
    t = _T(g)
    gi, go = t.node("NodeGroupInput"), t.node("NodeGroupOutput")
    pos = t.node("GeometryNodeInputPosition").outputs[0]
    nrm = t.node("GeometryNodeInputNormal").outputs[0]
    z = t.node("ShaderNodeSeparateXYZ", {"Vector": pos}).outputs["Z"]
    nz = t.node("ShaderNodeSeparateXYZ", {"Vector": nrm}).outputs["Z"]
    patch = t.node("ShaderNodeTexNoise", {"Vector": pos, "Scale": 0.09, "Detail": 2.0}).outputs["Fac"]
    mask = t.math("MULTIPLY", t.math("GREATER_THAN", z, zmin), t.math("GREATER_THAN", nz, 0.86))
    dens = t.math("MULTIPLY", mask, t.maprange(patch, 0.38, 0.62, 0.0, density))
    dist = t.node("GeometryNodeDistributePointsOnFaces", {"Mesh": gi.outputs[0], "Density": dens,
                                                          "Seed": seed % 10000}, distribute_method="RANDOM")
    oi = t.node("GeometryNodeObjectInfo", {"Object": proto}, transform_space="RELATIVE")
    rnd_r = t.node("FunctionNodeRandomValue", {"Min": (0, 0, 0), "Max": (0.25, 0.25, 6.28), "Seed": 3},
                   data_type="FLOAT_VECTOR")
    rnd_s = t.node("FunctionNodeRandomValue", {"Min": 0.55, "Max": 1.35, "Seed": 5}, data_type="FLOAT")
    inst = t.node("GeometryNodeInstanceOnPoints", {"Points": dist.outputs["Points"],
                                                   "Instance": oi.outputs["Geometry"],
                                                   "Rotation": rnd_r.outputs[0], "Scale": rnd_s.outputs[0]})
    real = t.node("GeometryNodeRealizeInstances", {"Geometry": inst.outputs[0]})
    join = t.node("GeometryNodeJoinGeometry")
    t.link(real.outputs[0], join.inputs[0])
    t.link(gi.outputs[0], join.inputs[0])
    t.link(join.outputs[0], go.inputs[0])
    return g


def gulls(col, center, rng, n, span):
    """A few seagull 'm' strokes drawn directly as Grease Pencil ink."""
    gp = bpy.data.grease_pencils.new("PW_Gulls")
    obj = bpy.data.objects.new("PW_Gulls", gp)
    col.objects.link(obj)
    m = bpy.data.materials.get("PW_InkStroke")
    if m is None or m.grease_pencil is None:
        m = bpy.data.materials.new("PW_InkStroke")
        bpy.data.materials.create_gpencil_data(m)
        m.grease_pencil.color = (*INK, 1)
    gp.materials.append(m)
    layer = gp.layers.new("Gulls")
    layer.use_lights = False
    dr = layer.frames.new(bpy.context.scene.frame_start).drawing
    dr.add_strokes([5] * n)
    pos = dr.attributes["position"].data
    rad = dr.attributes["radius"].data if "radius" in dr.attributes else None
    for i in range(n):
        c = Vector(center) + Vector((rng.uniform(-span, span), rng.uniform(-span * 0.4, span * 0.4),
                                     rng.uniform(-span * 0.15, span * 0.25)))
        s = rng.uniform(1.2, 1.9)
        pts = ((-1.0, 0, 0.25), (-0.5, 0, 0.45), (0.0, 0, 0.0), (0.5, 0, 0.45), (1.0, 0, 0.25))
        flap = rng.uniform(-0.2, 0.2)
        for k, p in enumerate(pts):
            pos[i * 5 + k].vector = c + Vector((p[0] * s, 0, (p[2] + (flap if k in (1, 3) else 0)) * s))
            if rad is not None:
                rad[i * 5 + k].value = 0.16 * s
    obj["pw_line"] = 0
    return obj


# ----------------------------------------------------------------------------- the scene
class CoastalIsland:
    """A cliffed island with a lighthouse, beach, rocks, sea stacks, grass and an inked sea."""
    LABEL = "Coastal island"

    @staticmethod
    def build(col, seed, size, detail, height, mood="GOLDEN", **kw):
        rng = random.Random(seed)
        R = size * 0.42                   # island radius
        H = 9.0 * height                  # clifftop height
        th_c = rng.uniform(0, math.tau)   # direction of the cliff side
        hx, hy = rng.uniform(0, 100), rng.uniform(0, 100)

        def h(x, y):
            a = math.atan2(y, x)
            rr = math.hypot(x, y) / R
            rr *= 1.0 + 0.22 * noise.noise(Vector((math.cos(a) * 1.6 + hx, math.sin(a) * 1.6 + hy, seed * 0.1)))
            s = max(0.0, min(1.0, math.cos(a - th_c) * 1.4 + 0.45))      # 1 = cliff side
            ew = 0.38 * (1 - s) + 0.035 * s
            land = smoothstep(1.0, 1.0 - ew, rr)
            hill = core.fbm(x * 0.035, y * 0.035, seed, 4) * 0.5 + 0.5
            top = H * (0.35 + 0.65 * s) * (0.55 + 0.6 * hill)
            top += 1.8 * abs(core.fbm(x * 0.09, y * 0.09, seed + 5, 3))
            z = land * top + (1 - land) * (-2.6 - rr)
            if s > 0.4 and z > 1.0:   # rocky ledges on the cliff side
                step = 2.2
                z = z + 0.45 * s * (round(z / step) * step - z)
            return z

        n = int(min(260, max(140, detail * 1.6)))
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=size * 0.62)
        for v in bm.verts:
            v.co.z = h(v.co.x, v.co.y)
        ter = _mesh_obj("PW_Terrain", bm, col, terrain_material(), smooth=True)
        ter["pw_wonk"] = 0.5

        # lighthouse spot: highest point near the cliff edge
        best = None
        for k in range(160):
            rr = rng.uniform(0.55, 0.85) * R
            a = th_c + rng.uniform(-0.45, 0.45)
            x, y = math.cos(a) * rr, math.sin(a) * rr
            z = h(x, y)
            score = z + rr * 0.08
            if best is None or score > best[0]:
                best = (score, x, y, z)
        _, lx, ly, lz = best
        mk = core.make_material
        white = mk("PW_LH_White", srgb(0.93, 0.90, 0.80))
        red = mk("PW_LH_Red", srgb(0.70, 0.30, 0.22))
        dark = mk("PW_LH_Dark", srgb(0.18, 0.20, 0.22))
        lit = mood in ("DUSK", "NIGHT")
        lamp = mk("PW_LH_Lamp", srgb(1.0, 0.86, 0.45) if lit else srgb(0.62, 0.74, 0.74),
                  emission=srgb(1.0, 0.82, 0.40) if lit else None, strength=3.0 if lit else 0.0)
        lamp_pos = lighthouse(col, (lx, ly, lz - 0.3), (white, red, dark, lamp), rng, mood)
        # cottage inland of the lighthouse, facing roughly the same way
        inward = Vector((-math.cos(th_c), -math.sin(th_c), 0))
        side = Vector((-inward.y, inward.x, 0))
        cpos = Vector((lx, ly, 0)) + inward * 8.5 + side * rng.choice((-6.0, 6.0))
        cottage(col, (cpos.x, cpos.y, h(cpos.x, cpos.y) - 0.2), th_c + math.pi / 2,
                (mk("PW_CottageWall", srgb(0.88, 0.82, 0.68)), mk("PW_CottageRoof", srgb(0.36, 0.42, 0.40)), dark))
        if lit:
            lamp_l = bpy.data.lights.new("PW_LampLight", "POINT")
            lamp_l.energy, lamp_l.color = 4000.0, srgb(1.0, 0.85, 0.55)
            lamp_l.shadow_soft_size = 0.4
            lo = bpy.data.objects.new("PW_LampLight", lamp_l)
            lo.location = lamp_pos + Vector((0, 0, 0.1)) + inward * 2.0
            col.objects.link(lo)

        # rocks: clusters on land + sea stacks off the cliff side + boulders on the beach
        rock_mats = [mk("PW_Rock_A", srgb(0.58, 0.55, 0.50)), mk("PW_Rock_B", srgb(0.50, 0.50, 0.48)),
                     mk("PW_Rock_C", srgb(0.62, 0.57, 0.48))]
        placed = 0
        for _ in range(600):
            if placed >= 46:
                break
            a, rr = rng.uniform(0, math.tau), R * math.sqrt(rng.uniform(0.02, 1.15))
            x, y = math.cos(a) * rr, math.sin(a) * rr
            z = h(x, y)
            if z < -0.4 or math.hypot(x - lx, y - ly) < 6 or (Vector((x, y, 0)) - cpos).length < 5                     or (z < 0.6 and math.cos(a - th_c) > 0.5):       # keep the cliff foot clear
                continue
            rad = rng.uniform(0.5, 1.6) * (1.6 if z < 0.6 else 1.0)
            o = _mesh_obj(f"PW_Rock_{placed}", rock_bm(rng, rad, flat=rng.uniform(0.55, 0.9)), col,
                          rng.choice(rock_mats))
            o.location = (x, y, z - rad * 0.15)
            o.rotation_euler.z = rng.uniform(0, math.tau)
            placed += 1
        for k in range(rng.randint(3, 5)):     # sea stacks
            a = th_c + rng.choice((-1, 1)) * rng.uniform(0.55, 1.2)
            rr = R * rng.uniform(1.12, 1.5)
            x, y = math.cos(a) * rr, math.sin(a) * rr
            hh = rng.uniform(5.0, 10.0) * height
            bm = rock_bm(rng, rng.uniform(1.0, 1.7), flat=1.0, sub=1)
            for v in bm.verts:
                v.co.z = (v.co.z + 2.0) * hh / 4.0 - 3.0
            o = _mesh_obj(f"PW_SeaStack_{k}", bm, col, rng.choice(rock_mats))
            o.location = (x, y, 0)
            o.rotation_euler.z = rng.uniform(0, math.tau)

        # grass tufts (GN), patchy, only on gentle ground above the sand
        gmat = mk("PW_Grass", srgb(0.34, 0.46, 0.26))
        proto = tuft_proto(col, gmat)
        md = ter.modifiers.new("PW_Grass", "NODES")
        md.node_group = grass_nodes(proto, 0.55, 1.6, seed)

        # camera: out over the sea on the cliff side, looking back at the lighthouse, sky-heavy
        cam_az = th_c + rng.choice((-1, 1)) * rng.uniform(0.55, 0.95)
        cam_d = R * rng.uniform(2.7, 3.2)
        cam = Vector((math.cos(cam_az) * cam_d, math.sin(cam_az) * cam_d, rng.uniform(9.0, 13.0) * height))
        to_lh = (Vector((lx, ly, 0)) - Vector((cam.x, cam.y, 0))).normalized()
        perp = Vector((-to_lh.y, to_lh.x, 0))
        offs = rng.choice((-1, 1))
        target = Vector((lx, ly, lz + 2.0)) + perp * offs * R * 0.42

        # sea: inner grid with baked shore height + far ring to the horizon (one mesh, no seams)
        bm = bmesh.new()
        S = size * 1.6
        bmesh.ops.create_grid(bm, x_segments=140, y_segments=140, size=S)
        edges = [e for e in bm.edges if e.is_boundary]
        ext = bmesh.ops.extrude_edge_only(bm, edges=edges)
        nv = [v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        for v in nv:
            v.co.x *= 40.0
            v.co.y *= 40.0
        sh = bm.verts.layers.float.new("pw_shore")
        for v in bm.verts:
            inside = abs(v.co.x) < size * 0.62 and abs(v.co.y) < size * 0.62
            v[sh] = h(v.co.x, v.co.y) if inside else -4.0
        sea = _mesh_obj("PW_Sea", bm, col)
        # bmesh float layers arrive as a mesh attribute of the same name
        sea.data.materials.append(sea_material(mood, (cam.x, cam.y), seed))
        sea["pw_wonk"] = 0

        gulls(col, Vector((lx, ly, lz + 16)) + perp * offs * 6, rng, rng.randint(3, 6), 9.0)

        return {"objects": len(col.objects),
                "camera": dict(location=tuple(cam), target=tuple(target), lens=rng.choice((35, 40, 45)),
                               clip_end=6000.0),
                "ink": {"sea_color": SEA[mood][1], "line_scale": 1.0, "base_height": 1.4}}

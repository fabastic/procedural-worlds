"""Ink style: turns any generated scene into a hand-inked graphic-novel panel (EEVEE).

core.generate() calls apply() for every scene, after the scene's build, lights and camera exist:
  1. materials  -> flat 2-3 tone cel shading (node group PW_InkToon: Shader to RGB -> constant bands,
                   shadows are a darker muted version of the hue, light-gated screen-space hatching,
                   AO grime in corners, stains and drips),
  2. wobble     -> hand-made wonky shapes (Geometry Nodes group PW_InkWonk, world-coherent noise),
  3. outlines   -> Grease Pencil v3 Line Art: heavy silhouettes, thin inner lines, noise, taper and
                   overshoot (lines "boil" every 2 frames when animated),
  4. sky        -> flat inked sky: banded gradient, outlined clouds, sun/moon disc, stars,
  5. compositor -> line wobble, paper grain + mottling, ink blots, smudges, warm vignette.
Shader to RGB is EEVEE-only, so ink renders use BLENDER_EEVEE with the Standard view transform.

Scene hints (all optional):
  obj["pw_line"] = 0        no outlines for this object
  obj["pw_wonk"] = 0..2     wobble multiplier (0 disables; default 1)
  mat["pw_flat"] = 1        unlit flat colour (sky cards, signs)
  mat["pw_hatch"], mat["pw_grime"]   per-material hatching / grime amount (default 1)
  mat["pw_ink_custom"] = 1  material already authored for ink; leave it alone
Build info may carry "ink": {"line_scale", "wobble", "grime", "hatch", "sea_color", "ao_distance"}.
"""
import math, zlib
import bpy
from mathutils import Vector


def srgb(r, g, b):
    """sRGB display colour -> linear (palette is authored as it should look on screen)."""
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


INK = srgb(0.07, 0.06, 0.055)
PAPER = srgb(0.95, 0.91, 0.82)

# Per mood: light tint, shadow tint, ambient (lighting only), sky top / horizon, cloud lit / shade,
# sun disc colour, key-light energy.
MOODS = {
    "DAY": dict(light=srgb(1.0, 0.98, 0.93), shadow=srgb(0.70, 0.74, 0.86), ambient=0.10,
                sky_top=srgb(0.60, 0.74, 0.76), sky_hor=srgb(0.93, 0.89, 0.76),
                cloud=srgb(0.98, 0.96, 0.89), cloud_shade=srgb(0.80, 0.83, 0.82),
                disc=srgb(1.0, 0.96, 0.80), sun=3.2, stars=False),
    "GOLDEN": dict(light=srgb(1.0, 0.90, 0.72), shadow=srgb(0.66, 0.58, 0.70), ambient=0.10,
                   sky_top=srgb(0.86, 0.66, 0.42), sky_hor=srgb(0.97, 0.85, 0.60),
                   cloud=srgb(1.0, 0.90, 0.70), cloud_shade=srgb(0.85, 0.62, 0.50),
                   disc=srgb(1.0, 0.93, 0.70), sun=3.2, stars=False),
    "DUSK": dict(light=srgb(0.90, 0.68, 0.58), shadow=srgb(0.44, 0.40, 0.60), ambient=0.12,
                 sky_top=srgb(0.36, 0.34, 0.52), sky_hor=srgb(0.90, 0.58, 0.44),
                 cloud=srgb(0.92, 0.66, 0.56), cloud_shade=srgb(0.55, 0.42, 0.55),
                 disc=srgb(1.0, 0.80, 0.60), sun=3.0, stars=False),
    "NIGHT": dict(light=srgb(0.40, 0.48, 0.66), shadow=srgb(0.21, 0.26, 0.40), ambient=0.14,
                  sky_top=srgb(0.08, 0.12, 0.20), sky_hor=srgb(0.22, 0.29, 0.38),
                  cloud=srgb(0.36, 0.42, 0.52), cloud_shade=srgb(0.20, 0.25, 0.34),
                  disc=srgb(0.93, 0.94, 0.86), sun=2.6, stars=True),
}


# ----------------------------------------------------------------------------- node helpers
def _sk(coll, ident):
    """Mix-node sockets share names: look them up by identifier."""
    return next(x for x in coll if x.identifier == ident)


class _T:
    """Tiny node-tree builder: n = t.node("ShaderNodeMath", operation="ADD"); t.link(a, b)."""

    def __init__(self, tree):
        self.tree, self.nodes, self.links = tree, tree.nodes, tree.links

    def node(self, kind, inputs=None, **props):
        n = self.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        for k, v in (inputs or {}).items():
            sock = n.inputs[k] if isinstance(k, int) else (
                n.inputs.get(k) or _sk(n.inputs, k))
            if isinstance(v, bpy.types.NodeSocket):
                self.links.new(v, sock)
            else:
                sock.default_value = v
        return n

    def link(self, a, b):
        self.links.new(a, b)

    def math(self, op, a, b=0.0, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, v in enumerate((a, b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX", clamp=True):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend, clamp_result=clamp)
        for ident, v in (("Factor_Float", fac), ("A_Color", a), ("B_Color", b)):
            s = _sk(n.inputs, ident)
            if isinstance(v, bpy.types.NodeSocket):
                self.links.new(v, s)
            else:
                s.default_value = v if ident == "Factor_Float" else (*v[:3], 1.0)
        return _sk(n.outputs, "Result_Color")

    def maprange(self, v, a, b, c=0.0, d=1.0, clamp=True):
        n = self.node("ShaderNodeMapRange", clamp=clamp)
        self.links.new(v, n.inputs["Value"])
        for k, x in (("From Min", a), ("From Max", b), ("To Min", c), ("To Max", d)):
            if isinstance(x, bpy.types.NodeSocket):
                self.links.new(x, n.inputs[k])
            else:
                n.inputs[k].default_value = x
        return n.outputs["Result"]

    def vmath(self, op, a, b=None, scale=None):
        n = self.node("ShaderNodeVectorMath", operation=op)
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                self.links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        if scale is not None:
            if isinstance(scale, bpy.types.NodeSocket):
                self.links.new(scale, n.inputs["Scale"])
            else:
                n.inputs["Scale"].default_value = scale
        return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Value"]


def _group(name, kind, inputs, outputs):
    """(Re)create a node group with the given interface; returns (group, builder, gin, gout)."""
    g = bpy.data.node_groups.get(name)
    if g is not None:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new(name, kind)
    for nm, st, dv in inputs:
        s = g.interface.new_socket(nm, in_out="INPUT", socket_type=st)
        if dv is not None:
            s.default_value = dv
    for nm, st in outputs:
        g.interface.new_socket(nm, in_out="OUTPUT", socket_type=st)
    t = _T(g)
    return g, t, t.node("NodeGroupInput"), t.node("NodeGroupOutput")


# ----------------------------------------------------------------------------- cel shading
def build_toon_group():
    """PW_InkToon shader group: Color -> flat cel-shaded, hatched, grimy emission."""
    C, F = "NodeSocketColor", "NodeSocketFloat"
    g, t, gi, go = _group("PW_InkToon", "ShaderNodeTree", [
        ("Color", C, (0.6, 0.6, 0.6, 1)), ("Light Tint", C, (1, 1, 1, 1)),
        ("Shadow Tint", C, (0.6, 0.62, 0.75, 1)), ("Hatch", F, 1.0), ("Grime", F, 1.0),
        ("Grime Color", C, (*srgb(0.42, 0.36, 0.26), 1)), ("AO Distance", F, 0.6),
        ("Stain Scale", F, 1.0), ("Aspect", F, 16 / 9), ("Hatch Density", F, 30.0),
        ("Lo", F, 0.16), ("Hi", F, 0.62), ("Ink", C, (*INK, 1)),
    ], [("Shader", "NodeSocketShader")])
    O = gi.outputs
    # light amount and light hue from a white diffuse surface
    diff = t.node("ShaderNodeBsdfDiffuse", {"Color": (1, 1, 1, 1)})
    s2r = t.node("ShaderNodeShaderToRGB", {"Shader": diff.outputs[0]})
    L = s2r.outputs["Color"]
    lum = t.node("ShaderNodeRGBToBW", {"Color": L}).outputs[0]
    inv = t.math("DIVIDE", 1.0, t.math("MAXIMUM", lum, 0.03))
    hue = t.vmath("MINIMUM", t.vmath("SCALE", L, scale=inv), (1.5, 1.5, 1.5))
    hue_mix = t.mix(0.75, (1, 1, 1), hue)
    # bands (constant): mid = lum > Lo, lit = lum > Hi; a little noise wobbles the terminator
    wob = t.node("ShaderNodeTexNoise", {"Scale": 3.0, "Detail": 1.0})
    lum_w = t.math("ADD", lum, t.math("MULTIPLY", t.math("SUBTRACT", wob.outputs["Fac"], 0.5), 0.12))
    mid = t.math("GREATER_THAN", lum_w, O["Lo"])
    lit = t.math("GREATER_THAN", lum_w, O["Hi"])
    # palette: muted, slightly dirty base; shadow = darker, cooler, desaturated same hue
    base = t.node("ShaderNodeHueSaturation", {"Color": O["Color"], "Saturation": 0.86, "Value": 0.97}).outputs[0]
    base = t.mix(0.07, base, (*PAPER, 1), blend="MULTIPLY")
    lit_col = t.mix(1.0, t.mix(1.0, base, hue_mix, blend="MULTIPLY"), O["Light Tint"], blend="MULTIPLY")
    sh = t.mix(1.0, base, O["Shadow Tint"], blend="MULTIPLY")
    sh_col = t.node("ShaderNodeHueSaturation", {"Color": sh, "Saturation": 1.05, "Value": 0.6}).outputs[0]
    sh_col = t.mix(0.25, sh_col, t.mix(1.0, sh_col, hue_mix, blend="MULTIPLY"))
    mid_col = t.mix(0.5, sh_col, lit_col)
    col = t.mix(mid, sh_col, mid_col)
    col = t.mix(lit, col, lit_col)
    # grime: AO in corners/contacts + stains and vertical drips in object space
    ao = t.node("ShaderNodeAmbientOcclusion", {"Distance": O["AO Distance"]}, samples=8)
    g_ao = t.maprange(ao.outputs["AO"], 0.30, 0.92, 1.0, 0.0)
    tc = t.node("ShaderNodeTexCoord")
    ocoord = t.vmath("SCALE", tc.outputs["Object"], scale=O["Stain Scale"])
    st = t.node("ShaderNodeTexNoise", {"Vector": ocoord, "Scale": 1.6, "Detail": 4.0, "Roughness": 0.62})
    stain = t.maprange(st.outputs["Fac"], 0.54, 0.64)
    drip_v = t.vmath("MULTIPLY", ocoord, (5.0, 5.0, 0.35))
    dr = t.node("ShaderNodeTexNoise", {"Vector": drip_v, "Scale": 2.2, "Detail": 2.0})
    drip = t.maprange(dr.outputs["Fac"], 0.60, 0.68)
    dirt = t.math("ADD", t.math("MULTIPLY", g_ao, 0.8),
                  t.math("ADD", t.math("MULTIPLY", stain, 0.16), t.math("MULTIPLY", drip, 0.12)))
    dirt = t.math("MINIMUM", t.math("MULTIPLY", dirt, O["Grime"]), 0.9)
    col = t.mix(1.0, col, t.mix(dirt, (1, 1, 1, 1), O["Grime Color"]), blend="MULTIPLY")
    # hatching: screen-space wobbly diagonal strokes, only in shadow; cross-hatch in the darkest
    win = t.node("ShaderNodeSeparateXYZ", {"Vector": tc.outputs["Window"]})
    px = t.math("MULTIPLY", win.outputs["X"], O["Aspect"])
    v1 = t.node("ShaderNodeCombineXYZ", {"X": px, "Y": win.outputs["Y"]}).outputs[0]
    v2 = t.node("ShaderNodeCombineXYZ", {"X": px, "Y": t.math("MULTIPLY", win.outputs["Y"], -1.0)}).outputs[0]
    wave = {}
    for k, v in (("a", v1), ("b", v2)):
        w = t.node("ShaderNodeTexWave", {"Vector": v, "Scale": O["Hatch Density"], "Distortion": 2.4,
                                         "Detail": 1.0, "Detail Scale": 0.8},
                   wave_type="BANDS", bands_direction="DIAGONAL", wave_profile="SAW")
        wave[k] = w.outputs["Fac"]
    shadow = t.math("SUBTRACT", 1.0, mid)
    half = t.math("MULTIPLY", mid, t.math("SUBTRACT", 1.0, lit))
    deep = t.math("LESS_THAN", lum_w, t.math("MULTIPLY", O["Lo"], 0.45))
    occ = t.maprange(g_ao, 0.05, 0.6)
    w1 = t.math("MULTIPLY", O["Hatch"], t.math("MULTIPLY", shadow, t.math("ADD", 0.025, t.math("MULTIPLY", occ, 0.26))))
    w2 = t.math("MULTIPLY", O["Hatch"], t.math("MULTIPLY", t.math("MULTIPLY", shadow, t.maprange(g_ao, 0.45, 0.9)), 0.22))
    h1 = t.math("LESS_THAN", wave["a"], w1)
    h2 = t.math("LESS_THAN", wave["b"], w2)
    brk = t.node("ShaderNodeTexNoise", {"Vector": v1, "Scale": 9.0, "Detail": 0.0})
    breaks = t.math("GREATER_THAN", brk.outputs["Fac"], 0.38)
    hatch = t.math("MULTIPLY", t.math("MAXIMUM", h1, h2), breaks)
    col = t.mix(t.math("MULTIPLY", hatch, 0.72), col, t.mix(0.65, col, O["Ink"], blend="MULTIPLY"))
    col = t.vmath("MINIMUM", col, (0.985, 0.985, 0.985))
    em = t.node("ShaderNodeEmission", {"Color": col, "Strength": 1.0})
    t.link(em.outputs[0], go.inputs["Shader"])
    return g


def _base_color_source(nt, bsdf):
    s = bsdf.inputs["Base Color"]
    if s.is_linked:
        return s.links[0].from_socket
    return tuple(s.default_value)


def strip_material(m):
    """Remove the ink nodes from a material and reconnect its original surface shader."""
    if not m.use_nodes or m.node_tree is None:
        return
    nt = m.node_tree
    for n in [n for n in nt.nodes if n.name.startswith("PW_Ink")]:
        nt.nodes.remove(n)
    orig = m.get("pw_ink_orig")
    if orig and orig in nt.nodes:
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
        if out is not None:
            nt.links.new(nt.nodes[orig].outputs[0], out.inputs["Surface"])
    if "pw_ink_orig" in m:
        del m["pw_ink_orig"]


def ink_material(m, mood, opts):
    """Insert the toon group between the material's colour and its output (original kept)."""
    if m.get("pw_ink_custom") or not m.use_nodes or m.node_tree is None:
        return
    strip_material(m)
    nt = m.node_tree
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None) \
        or next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if out is None or bsdf is None:
        return
    if out.inputs["Surface"].is_linked:
        m["pw_ink_orig"] = out.inputs["Surface"].links[0].from_node.name
    P = MOODS[mood]
    src = _base_color_source(nt, bsdf)
    estr = bsdf.inputs["Emission Strength"].default_value
    if m.get("pw_flat") or estr > 0.01:
        # neon / signs / sky cards: flat unshaded ink colour; strong emitters glow a little
        ec = bsdf.inputs["Emission Color"]
        if estr > 0.01:
            col = ec.links[0].from_socket if ec.is_linked else tuple(ec.default_value)[:3]
        else:
            col = src
        em = nt.nodes.new("ShaderNodeEmission")
        em.name = "PW_InkFlat"
        if isinstance(col, tuple):
            mx = max(col[:3]) or 1.0
            gain = 1.0 / mx if estr > 0.01 else 1.0
            em.inputs["Color"].default_value = (*[c * gain for c in col[:3]], 1)
        else:
            nt.links.new(col, em.inputs["Color"])
        em.inputs["Strength"].default_value = 1.6 if estr >= 2.0 else 1.0
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        return
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = bpy.data.node_groups["PW_InkToon"]
    grp.name = "PW_InkToon"
    grp.location = (out.location.x - 220, out.location.y - 300)
    if isinstance(src, tuple):
        grp.inputs["Color"].default_value = (*src[:3], 1)
    else:
        nt.links.new(src, grp.inputs["Color"])
    grp.inputs["Light Tint"].default_value = (*P["light"], 1)
    grp.inputs["Shadow Tint"].default_value = (*P["shadow"], 1)
    grp.inputs["Hatch"].default_value = float(m.get("pw_hatch", 1.0)) * opts["hatch"]
    grp.inputs["Grime"].default_value = float(m.get("pw_grime", 1.0)) * opts["grime"]
    grp.inputs["AO Distance"].default_value = opts["ao_distance"]
    grp.inputs["Stain Scale"].default_value = opts["stain_scale"]
    grp.inputs["Aspect"].default_value = opts["aspect"]
    if mood == "NIGHT":
        grp.inputs["Lo"].default_value, grp.inputs["Hi"].default_value = 0.14, 0.55
    nt.links.new(grp.outputs["Shader"], out.inputs["Surface"])


# ----------------------------------------------------------------------------- wobble
def build_wonk_group():
    """PW_InkWonk: subdivide low-poly meshes, then push vertices with world-space noise so
    touching objects stay sealed while every edge goes slightly hand-made and wonky."""
    G, F, I = "NodeSocketGeometry", "NodeSocketFloat", "NodeSocketInt"
    g, t, gi, go = _group("PW_InkWonk", "GeometryNodeTree", [
        ("Geometry", G, None), ("Level", I, 2), ("Strength", F, 0.02), ("Scale", F, 0.6),
        ("Seed", F, 0.0)], [("Geometry", G)])
    g.is_modifier = True
    O = gi.outputs
    sub = t.node("GeometryNodeSubdivideMesh", {"Mesh": O["Geometry"], "Level": O["Level"]})
    pos = t.node("GeometryNodeInputPosition").outputs[0]
    me = t.node("GeometryNodeSelfObject").outputs[0]
    info = t.node("GeometryNodeObjectInfo", {"Object": me}, transform_space="ORIGINAL")
    T = info.outputs["Transform"]
    wpos = t.node("FunctionNodeTransformPoint", {"Vector": pos, "Transform": T}).outputs[0]
    seedv = t.node("ShaderNodeCombineXYZ", {"X": t.math("MULTIPLY", O["Seed"], 13.17),
                                            "Y": t.math("MULTIPLY", O["Seed"], 7.31),
                                            "Z": t.math("MULTIPLY", O["Seed"], 3.77)}).outputs[0]
    nz = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("ADD", wpos, seedv), "Scale": O["Scale"],
                                       "Detail": 1.5, "Roughness": 0.4})
    off = t.vmath("SCALE", t.vmath("SUBTRACT", nz.outputs["Color"], (0.5, 0.5, 0.5)),
                  scale=t.math("MULTIPLY", O["Strength"], 2.0))
    inv = t.node("FunctionNodeInvertMatrix", {"Matrix": T}).outputs["Matrix"]
    loff = t.node("FunctionNodeTransformDirection", {"Direction": off, "Transform": inv}).outputs[0]
    sp = t.node("GeometryNodeSetPosition", {"Geometry": sub.outputs[0], "Offset": loff})
    t.link(sp.outputs[0], go.inputs["Geometry"])
    return g


def add_wobble(obj, strength, scale, seed):
    if obj.type != "MESH" or obj.get("pw_wonk", 1.0) <= 0 or not obj.data.polygons:
        return
    nf = len(obj.data.polygons)
    level = 0 if nf > 4000 else (1 if nf > 600 else (2 if nf > 60 else 3))
    md = obj.modifiers.new("PW_InkWonk", "NODES")
    md.node_group = bpy.data.node_groups["PW_InkWonk"]
    ids = {it.name: it.identifier for it in md.node_group.interface.items_tree
           if it.item_type == "SOCKET" and it.in_out == "INPUT"}
    vals = {"Level": level, "Strength": strength * float(obj.get("pw_wonk", 1.0)),
            "Scale": scale, "Seed": float(seed % 1000)}
    for k, v in vals.items():
        set_modifier_input(md, ids[k], v)


def set_modifier_input(md, ident, value):
    """Blender 5.x: GN modifier inputs are md.properties.inputs.<Socket_N>.value (ID-property
    access on the modifier raises); 4.x used md["Socket_N"]."""
    props = getattr(md, "properties", None)
    if props is not None and hasattr(props.inputs, ident):
        getattr(props.inputs, ident).value = value
    else:
        md[ident] = value
    if md.id_data is not None:
        md.id_data.update_tag()


# ----------------------------------------------------------------------------- outlines
def _stroke_material(name, color):
    m = bpy.data.materials.get(name)
    if m is None or m.grease_pencil is None:
        m = bpy.data.materials.new(name)
        bpy.data.materials.create_gpencil_data(m)
    m.grease_pencil.color = (*color, 1)
    m.grease_pencil.show_fill = False
    return m


def add_outlines(col, seed, radius, line_scale=1.0):
    """Line Art into a GP v3 object: silhouettes heavy, inner creases/intersections thin, then
    noise wobble + thickness jitter, tapered ends and slight overshoot like a brush pen."""
    gp = bpy.data.grease_pencils.new("PW_InkLines")
    gp.stroke_depth_order = "2D"   # Line Art already resolved occlusion
    obj = bpy.data.objects.new("PW_InkLines", gp)
    col.objects.link(obj)
    heavy = _stroke_material("PW_InkStroke", INK)
    thin = _stroke_material("PW_InkStrokeThin", srgb(0.12, 0.10, 0.09))
    gp.materials.append(heavy)
    gp.materials.append(thin)
    r = radius * line_scale
    for lname, mat, rr, kw in (
            ("Inner", thin, r * 0.5, dict(use_contour=True, use_crease=True, use_intersection=True,
                                          use_loose=True, crease_threshold=math.radians(128))),
            ("Silhouette", heavy, r, dict(use_contour=True, use_crease=False, use_intersection=False,
                                         use_loose=False, silhouette_filtering="INDIVIDUAL"))):
        gp.layers.new(lname)
        la = obj.modifiers.new(f"PW_LA_{lname}", "LINEART")
        la.source_type = "COLLECTION"
        la.source_collection = col
        la.target_layer = lname
        la.target_material = mat
        la.radius = rr
        la.use_material = False
        la.use_edge_mark = False
        la.use_image_boundary_trimming = True
        la.use_crease_on_smooth = False
        la.chaining_image_threshold = 0.004
        la.smooth_tolerance = 0.1
        for k, v in kw.items():
            try:
                setattr(la, k, v)
            except (AttributeError, TypeError):
                pass
    ln = obj.modifiers.new("PW_InkOvershoot", "GREASE_PENCIL_LENGTH")
    ln.mode = "RELATIVE"
    ln.use_curvature = False           # curvature extension makes long stray hooks
    ln.start_factor = ln.end_factor = 0.025
    ln.use_random, ln.random_start_factor, ln.random_end_factor, ln.seed = True, 0.015, 0.015, seed % 997
    sm = obj.modifiers.new("PW_InkSmooth", "GREASE_PENCIL_SUBDIV")
    sm.level = 1
    nz = obj.modifiers.new("PW_InkNoise", "GREASE_PENCIL_NOISE")
    nz.factor = 0.12
    nz.factor_thickness = 0.5
    nz.noise_scale = 0.12
    nz.seed = seed % 997
    nz.use_random, nz.step = True, 2         # "boils" every 2 frames when animated
    th = obj.modifiers.new("PW_InkTaper", "GREASE_PENCIL_THICKNESS")
    th.thickness_factor = 0.4
    th.use_custom_curve = True
    cm = th.custom_curve
    pts = cm.curves[0].points
    pts[0].location, pts[-1].location = (0.0, 1.0), (1.0, 1.0)
    pts.new(0.12, 0.0)
    pts.new(0.88, 0.0)
    cm.update()
    for o in col.objects:
        if o.get("pw_line", 1) == 0:
            o.lineart.usage = "EXCLUDE"
    return obj


# ----------------------------------------------------------------------------- sky
def _camera_sky_top():
    """sin(elevation) of the top edge of the frame, so bands/clouds land inside the visible sky."""
    cam = bpy.context.scene.camera
    if cam is None:
        return 0.6
    fwd = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    pitch = math.asin(max(-1.0, min(1.0, fwd.z)))
    r = bpy.context.scene.render
    aspect = r.resolution_x / max(r.resolution_y, 1)
    half_v = cam.data.angle_y / 2 if aspect >= 1 else cam.data.angle_x / 2
    if cam.data.sensor_fit == "AUTO" and aspect >= 1:
        half_v = math.atan(math.tan(cam.data.angle / 2) / aspect)
    return max(0.06, min(0.95, math.sin(pitch + half_v)))


def build_world(mood, sun_obj, seed, sea_color=None):
    P = MOODS[mood]
    ztop = _camera_sky_top()
    w = bpy.data.worlds.get("PW_InkWorld") or bpy.data.worlds.new("PW_InkWorld")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    t = _T(nt)
    out = t.node("ShaderNodeOutputWorld")
    tc = t.node("ShaderNodeTexCoord")
    d = t.vmath("NORMALIZE", tc.outputs["Generated"])
    sep = t.node("ShaderNodeSeparateXYZ", {"Vector": d})
    z = sep.outputs["Z"]
    # banded gradient (3 flat bands with wobbly edges) from horizon to zenith
    wob = t.node("ShaderNodeTexNoise", {"Vector": d, "Scale": 4.0, "Detail": 1.0})
    zz = t.math("ADD", z, t.math("MULTIPLY", t.math("SUBTRACT", wob.outputs["Fac"], 0.5), 0.05))
    band = t.math("ADD", t.math("GREATER_THAN", zz, min(0.10, ztop * 0.38)),
                  t.math("GREATER_THAN", zz, min(0.30, ztop * 0.72)))
    band = t.math("MULTIPLY", band, 0.5)
    sky = t.mix(band, (*P["sky_hor"], 1), (*P["sky_top"], 1))
    # clouds on a flat layer: noise threshold, lit tops / shaded bellies, inked outlines
    k = t.math("DIVIDE", 1.0, t.math("ADD", t.math("MAXIMUM", z, 0.0), 0.08))
    uv = t.vmath("SCALE", t.vmath("MULTIPLY", d, (1.0, 1.0, 0.0)), scale=k)
    uv = t.vmath("ADD", uv, ((seed % 97) * 3.1, (seed % 89) * 1.7, 0.0))
    cscale = 0.55 * min(1.0, max(0.25, ztop / 0.4))
    cn = t.node("ShaderNodeTexNoise", {"Vector": uv, "Scale": cscale, "Detail": 3.0, "Roughness": 0.55})
    fade = t.maprange(z, 0.004, min(0.10, ztop * 0.3), 0.6, 1.0)
    n = t.math("MULTIPLY", cn.outputs["Fac"], fade)
    T0 = 0.56
    cloud = t.math("GREATER_THAN", n, T0)
    upv = t.vmath("ADD", uv, (0.0, -0.35, 0.0))
    cn2 = t.node("ShaderNodeTexNoise", {"Vector": upv, "Scale": cscale, "Detail": 3.0, "Roughness": 0.55})
    shade = t.math("LESS_THAN", t.math("MULTIPLY", cn2.outputs["Fac"], fade), T0 + 0.02)
    ccol = t.mix(shade, (*P["cloud"], 1), (*P["cloud_shade"], 1))
    sky = t.mix(cloud, sky, ccol)
    edge = t.math("LESS_THAN", t.math("ABSOLUTE", t.math("SUBTRACT", n, T0)), 0.0045)
    # sun / moon disc with an ink ring
    sd = sun_obj.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    dp = t.vmath("DOT_PRODUCT", d, tuple(sd))
    disc = t.math("GREATER_THAN", dp, math.cos(math.radians(2.6)))
    ring = t.math("MULTIPLY", t.math("GREATER_THAN", dp, math.cos(math.radians(2.95))),
                  t.math("SUBTRACT", 1.0, disc))
    sky = t.mix(t.math("MULTIPLY", disc, t.math("SUBTRACT", 1.0, cloud)), sky, (*P["disc"], 1))
    if P["stars"]:
        wn = t.node("ShaderNodeTexWhiteNoise", {"Vector": t.vmath("SCALE", d, scale=260.0)}, noise_dimensions="3D")
        star = t.math("MULTIPLY", t.math("GREATER_THAN", wn.outputs["Value"], 0.996),
                      t.math("MULTIPLY", t.math("SUBTRACT", 1.0, cloud), t.maprange(z, 0.08, 0.3)))
        sky = t.mix(star, sky, (*srgb(0.95, 0.93, 0.80), 1))
    ink_m = t.math("MAXIMUM", edge, t.math("MULTIPLY", ring, t.math("SUBTRACT", 1.0, cloud)))
    sky = t.mix(t.math("MULTIPLY", ink_m, 0.9), sky, (*INK, 1))
    # below the horizon: sea / ground colour so no seam shows past geometry
    below = t.math("LESS_THAN", z, -0.002)
    sky = t.mix(below, sky, (*(sea_color or P["sky_hor"]), 1))
    cam_bg = t.node("ShaderNodeBackground", {"Color": sky, "Strength": 1.0})
    amb_c = tuple(c * P["ambient"] for c in P["sky_top"]) if mood != "NIGHT" else \
        tuple(c * P["ambient"] * 2.0 for c in P["sky_hor"])
    amb_c = tuple(max(c, P["ambient"] * 0.6) for c in amb_c)
    amb = t.node("ShaderNodeBackground", {"Color": (*amb_c, 1), "Strength": 1.0})
    lp = t.node("ShaderNodeLightPath")
    mixs = t.node("ShaderNodeMixShader", {0: lp.outputs["Is Camera Ray"], 1: amb.outputs[0], 2: cam_bg.outputs[0]})
    t.link(mixs.outputs[0], out.inputs["Surface"])
    bpy.context.scene.world = w
    return w


# ----------------------------------------------------------------------------- compositor
def build_compositor(scene, seed, frame_boil=True):
    name = "PW_InkComp"
    g = bpy.data.node_groups.get(name)
    if g is not None:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new(name, "CompositorNodeTree")
    g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    t = _T(g)
    rl = t.node("CompositorNodeRLayers")
    img = rl.outputs["Image"]
    uv = t.node("CompositorNodeImageCoordinates", {"Image": img}).outputs["Uniform"]
    so = ((seed % 53) * 1.37, (seed % 29) * 2.11, 0.0)
    uvs = t.vmath("ADD", uv, so)
    # 1. hand wobble on every line and tone edge (displace by low-frequency noise, ~1.5 px)
    nz = t.node("ShaderNodeTexNoise", {"Vector": uvs, "Scale": 9.0, "Detail": 1.0})
    if frame_boil:
        st = t.node("CompositorNodeSceneTime")
        fr = st.outputs.get("Frame") or st.outputs[1]
        step = t.math("FLOOR", t.math("MULTIPLY", fr, 0.5))
        nz.noise_dimensions = "4D"
        t.link(t.math("MULTIPLY", step, 0.37), nz.inputs["W"])
    disp_v = t.vmath("SCALE", t.vmath("SUBTRACT", nz.outputs["Color"], (0.5, 0.5, 0.5)),
                     scale=scene.render.resolution_x / 960 * 4.0)
    dn = t.node("CompositorNodeDisplace")
    t.link(img, dn.inputs[0])
    t.link(disp_v, dn.inputs[1])
    img = dn.outputs[0]
    # 2. neon glow (only values above 1.0 bloom: flat emitters, never the paper)
    gl = t.node("CompositorNodeGlare", {"Image": img})
    for k, v in (("glare_type", "BLOOM"), ("quality", "MEDIUM")):
        try:
            setattr(gl, k, v)
        except (AttributeError, TypeError):
            pass
    for k, v in (("Threshold", 1.0), ("Strength", 0.55), ("Size", 0.5)):
        if k in gl.inputs:
            gl.inputs[k].default_value = v
    try:
        gl.inputs["Type"].default_value = "Bloom"
    except Exception:
        pass
    img = gl.outputs[0]
    # 3. paper: tint, mottling and tooth/grain
    mott = t.node("ShaderNodeTexNoise", {"Vector": uvs, "Scale": 2.2, "Detail": 3.0})
    m = t.maprange(mott.outputs["Fac"], 0.3, 0.7, 0.93, 1.03)
    tooth = t.node("ShaderNodeTexNoise", {"Vector": uvs, "Scale": 380.0, "Detail": 2.0, "Roughness": 0.7})
    grain = t.node("ShaderNodeTexWhiteNoise", {"Vector": t.vmath("SCALE", uvs, scale=900.0)},
                   noise_dimensions="3D")
    g1 = t.maprange(tooth.outputs["Fac"], 0.3, 0.7, 0.90, 1.04)
    g2 = t.maprange(grain.outputs["Value"], 0.0, 1.0, 0.94, 1.02)
    paper_k = t.math("MULTIPLY", t.math("MULTIPLY", m, g1), g2)
    img = t.mix(1.0, img, (*PAPER, 1), blend="MULTIPLY")
    img = t.vmath("SCALE", img, scale=paper_k)
    # 4. smudges (soft grey patches) and ink blots/splatter (sparse, mostly near the frame edge)
    r = t.vmath("LENGTH", uv)
    edge = t.maprange(r, 0.35, 0.95)
    sm = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("ADD", uvs, (5.0, 1.0, 0.0)), "Scale": 1.8, "Detail": 2.0})
    smudge = t.math("MULTIPLY", t.maprange(sm.outputs["Fac"], 0.58, 0.72, 0.0, 0.16), t.math("ADD", edge, 0.35))
    vo = t.node("ShaderNodeTexVoronoi", {"Vector": t.vmath("ADD", uvs, (11.0, 3.0, 0.0)), "Scale": 7.0,
                                         "Randomness": 1.0})
    bn = t.node("ShaderNodeTexNoise", {"Vector": uvs, "Scale": 60.0, "Detail": 2.0})
    dist = t.math("ADD", vo.outputs["Distance"], t.math("MULTIPLY", bn.outputs["Fac"], 0.025))
    vcol = t.node("ShaderNodeSeparateXYZ", {"Vector": vo.outputs["Color"]})
    big = t.math("GREATER_THAN", vcol.outputs["X"], t.math("SUBTRACT", 0.97, t.math("MULTIPLY", edge, 0.12)))
    blot = t.math("MULTIPLY", t.math("LESS_THAN", dist, t.math("MULTIPLY", vcol.outputs["Y"], 0.05)), big)
    sp = t.node("ShaderNodeTexWhiteNoise", {"Vector": t.vmath("SCALE", uvs, scale=160.0)}, noise_dimensions="3D")
    splat = t.math("MULTIPLY", t.math("GREATER_THAN", sp.outputs["Value"], 0.9985), edge)
    dark = t.math("MINIMUM", t.math("ADD", t.math("MULTIPLY", t.math("MAXIMUM", blot, splat), 0.85), smudge), 0.9)
    img = t.mix(dark, img, (*INK, 1))
    # 5. warm grimy vignette
    vig = t.maprange(r, 0.55, 1.15, 0.0, 0.45)
    img = t.mix(vig, img, t.mix(1.0, img, (*srgb(0.62, 0.52, 0.40), 1), blend="MULTIPLY"))
    go = t.node("NodeGroupOutput")
    t.link(img, go.inputs[0])
    scene.compositing_node_group = g
    scene.render.use_compositing = True
    return g


# ----------------------------------------------------------------------------- entry points
def _scene_scale(scene, info):
    cam = scene.camera
    tgt = Vector(info.get("camera", {}).get("target", (0, 0, 0)))
    d = (cam.matrix_world.translation - tgt).length if cam else 10.0
    return max(d, 0.5)


def apply(context, col, seed, mood, info):
    scene = context.scene
    scene["pw_ink"] = 1
    context.view_layer.update()          # camera/sun matrix_world are stale right after creation
    opts = dict(line_scale=1.0, wobble=1.0, grime=1.0, hatch=1.0, ao_distance=None, sea_color=None)
    opts.update(info.get("ink", {}))
    d = _scene_scale(scene, info)
    cam = scene.camera.data
    sensor = cam.sensor_width
    # world-space radius giving ~4.5 px silhouettes at 960 px width at the focus distance
    radius = 0.0068 * d * (sensor / cam.lens) / 2.0
    opts["ao_distance"] = opts["ao_distance"] or 0.06 * d
    opts["stain_scale"] = 0.9 / max(d * 0.08, 0.05)
    opts["aspect"] = scene.render.resolution_x / max(scene.render.resolution_y, 1)
    build_toon_group()
    build_wonk_group()
    done = set()
    default = None
    for o in list(col.objects):
        if o.type not in ("MESH", "CURVE", "FONT"):
            continue
        if o.type == "MESH" and not o.material_slots:
            default = default or bpy.data.materials.get("PW_InkDefault") or _default_mat()
            o.data.materials.append(default)
        for slot in o.material_slots:
            m = slot.material
            if m is not None and m.name not in done:
                done.add(m.name)
                ink_material(m, mood, opts)
        h = zlib.crc32(o.name.encode()) % 1000
        add_wobble(o, strength=0.0042 * d * opts["wobble"], scale=1.6 / d, seed=seed + 0 * h)
    # mood key light: neutral white sun at a fixed energy (the mood colour lives in the palette)
    P = MOODS[mood]
    sun = next((o for o in col.objects if o.type == "LIGHT" and o.data.type == "SUN"), None)
    if sun is not None:
        sun.data.energy = P["sun"] * info.get("sun_scale", 1.0)
        sun.data.color = (1.0, 1.0, 1.0)
        sun.data.angle = math.radians(0.6)
        build_world(mood, sun, seed, opts["sea_color"])
    add_outlines(col, seed, radius, opts["line_scale"])
    build_compositor(scene, seed)
    return {"line_radius": radius, "materials": len(done)}


def _default_mat():
    m = bpy.data.materials.new("PW_InkDefault")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*srgb(0.85, 0.80, 0.68), 1)
    return m


def remove(context):
    """Switch a scene back to the realistic look: strip ink nodes, compositor off."""
    scene = context.scene
    if "pw_ink" in scene:
        del scene["pw_ink"]
    for m in bpy.data.materials:
        if m.name.startswith("PW_") and m.use_nodes:
            strip_material(m)
    if scene.compositing_node_group is not None and scene.compositing_node_group.name == "PW_InkComp":
        scene.compositing_node_group = None

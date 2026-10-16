"""Shared helpers: collection mgmt, noise, materials, lighting rigs, camera, render setup."""
import math, random
import bpy, bmesh
from mathutils import Vector, noise

COLLECTION = "PW_Generated"


def get_collection(clear=True):
    col = bpy.data.collections.get(COLLECTION)
    if col is None:
        col = bpy.data.collections.new(COLLECTION)
        bpy.context.scene.collection.children.link(col)
    if clear:
        for o in list(col.objects):
            remove_object(o)
    return col


def remove_object(o):
    """Remove an object AND its orphaned data (mesh/light/camera) so regenerating doesn't leak."""
    data = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if data is not None and data.users == 0:
        for coll in (bpy.data.meshes, bpy.data.lights, bpy.data.cameras):
            if data.name in coll and coll[data.name] is data:
                coll.remove(data)
                break


def link(obj, col):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def fbm(x, y, seed, octaves=5, lacunarity=2.0, gain=0.5):
    """Fractal noise in roughly [-1, 1]."""
    amp, freq, total, norm = 1.0, 1.0, 0.0, 0.0
    o = Vector((seed * 17.31, seed * 3.17, 0.0))
    for _ in range(octaves):
        total += amp * noise.noise(Vector((x * freq, y * freq, 0.0)) + o)
        norm += amp
        amp *= gain
        freq *= lacunarity
    return total / norm


def make_material(name, color, rough=0.6, metallic=0.0, emission=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def height_material(name, low, mid, high, lo_z, hi_z):
    """Terrain material: colour ramp driven by world-space Z (sand -> grass -> rock)."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.85
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["From Min"].default_value = lo_z
    mapr.inputs["From Max"].default_value = hi_z
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*low, 1)
    ramp.color_ramp.elements[1].color = (*high, 1)
    e = ramp.color_ramp.elements.new(0.45)
    e.color = (*mid, 1)
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 18.0
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    def sk(coll, ident):  # Mix node sockets share names; look up by identifier
        return next(x for x in coll if x.identifier == ident)
    sk(mix.inputs, "Factor_Float").default_value = 0.35
    L = nt.links.new
    L(geo.outputs["Position"], sep.inputs[0])
    L(sep.outputs["Z"], mapr.inputs["Value"])
    L(mapr.outputs["Result"], ramp.inputs["Fac"])
    L(ramp.outputs["Color"], sk(mix.inputs, "A_Color"))
    L(tex.outputs["Color"], sk(mix.inputs, "B_Color"))
    L(sk(mix.outputs, "Result_Color"), bsdf.inputs["Base Color"])
    L(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


MOODS = {
    # sun elevation(deg), azimuth(deg), sun colour, sun strength, sky colour, sky strength
    "DAY":    (55, 140, (1.0, 0.97, 0.92), 4.0, (0.45, 0.62, 0.95), 1.0),
    "GOLDEN": (14, 120, (1.0, 0.62, 0.30), 5.0, (0.95, 0.55, 0.35), 0.8),
    "DUSK":   (3, 100, (1.0, 0.35, 0.25), 2.5, (0.25, 0.20, 0.45), 0.5),
    "NIGHT":  (25, 60, (0.55, 0.65, 1.0), 0.6, (0.02, 0.03, 0.08), 0.15),
}


def setup_lighting(mood, col):
    el, az, scol, sstr, sky, skystr = MOODS[mood]
    sun = bpy.data.lights.new("PW_Sun", "SUN")
    sun.energy, sun.color, sun.angle = sstr, scol, math.radians(1.5)
    so = bpy.data.objects.new("PW_Sun", sun)
    so.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
    col.objects.link(so)
    w = bpy.context.scene.world or bpy.data.worlds.new("PW_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*sky, 1)
    bg.inputs["Strength"].default_value = skystr


def setup_camera(col, target=(0, 0, 2), distance=45, height=12, angle=35, lens=35):
    cam = bpy.data.cameras.new("PW_Camera")
    cam.lens = lens
    co = bpy.data.objects.new("PW_Camera", cam)
    a = math.radians(angle)
    co.location = (target[0] + math.sin(a) * distance, target[1] - math.cos(a) * distance, height)
    col.objects.link(co)
    d = Vector(target) - co.location
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    return co


def setup_render(engine="CYCLES", samples=64, res=(1920, 1080)):
    s = bpy.context.scene
    try:
        s.render.engine = engine
    except TypeError:
        s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = res
    if s.render.engine == "CYCLES":
        s.cycles.samples = samples
        s.cycles.use_denoising = True
    s.view_settings.view_transform = "AgX" if "AgX" in [
        i.identifier for i in s.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"


def generate(context, scene_type, seed=1, size=60.0, detail=160, height=1.0,
             mood="GOLDEN", clear=True, engine="CYCLES"):
    from . import scenes
    random.seed(seed)
    col = get_collection(clear)
    if clear:
        for o in list(context.scene.objects):
            if o.name.startswith("PW_") and o.name not in col.objects:
                remove_object(o)
    info = scenes.REGISTRY[scene_type].build(col, seed=seed, size=size, detail=detail, height=height)
    setup_lighting(mood, col)
    setup_camera(col, **info.get("camera", {}))
    setup_render(engine)
    return info

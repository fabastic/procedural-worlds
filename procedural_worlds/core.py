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


def _data_collections():
    return (bpy.data.meshes, bpy.data.lights, bpy.data.cameras, bpy.data.curves,
            bpy.data.grease_pencils, bpy.data.metaballs, bpy.data.lattices)


def remove_object(o):
    """Remove an object AND its orphaned data (mesh/light/camera/curve/grease pencil) so
    regenerating doesn't leak."""
    data = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if data is not None and data.users == 0:
        for coll in _data_collections():
            if data.name in coll and coll[data.name] is data:
                coll.remove(data)
                break


def purge_orphans(prefix="PW_"):
    """Drop zero-user PW_* materials, node groups, textures and images left by a previous build."""
    for coll in (bpy.data.materials, bpy.data.node_groups, bpy.data.textures, bpy.data.images,
                 bpy.data.worlds, bpy.data.actions, *_data_collections()):
        for d in list(coll):
            if d.name.startswith(prefix) and d.users == 0:
                coll.remove(d)


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


def setup_lighting(mood, col, sun_scale=1.0, sky_scale=1.0, sun_dir=None):
    """Mood sun + world. A scene's build info may pass sun_scale / sky_scale multipliers and
    sun_dir=(elevation_deg, azimuth_deg) to aim the sun (e.g. through an interior window)."""
    el, az, scol, sstr, sky, skystr = MOODS[mood]
    if sun_dir is not None:
        el, az = sun_dir
    sstr, skystr = sstr * sun_scale, skystr * sky_scale
    sun = bpy.data.lights.new("PW_Sun", "SUN")
    sun.energy, sun.color, sun.angle = sstr, scol, math.radians(1.5)
    so = bpy.data.objects.new("PW_Sun", sun)
    so.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
    col.objects.link(so)
    w = bpy.data.worlds.get("PW_World") or bpy.data.worlds.new("PW_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*sky, 1)
    bg.inputs["Strength"].default_value = skystr


def setup_camera(col, target=(0, 0, 2), distance=45, height=12, angle=35, lens=35,
                 location=None, clip_end=1000.0, shift_y=0.0):
    """Orbit placement (distance/height/angle around target) unless an explicit location is given."""
    cam = bpy.data.cameras.new("PW_Camera")
    cam.lens = lens
    cam.clip_start, cam.clip_end = 0.05, clip_end
    cam.shift_y = shift_y
    co = bpy.data.objects.new("PW_Camera", cam)
    if location is not None:
        co.location = location
    else:
        a = math.radians(angle)
        co.location = (target[0] + math.sin(a) * distance, target[1] - math.cos(a) * distance, height)
    col.objects.link(co)
    d = Vector(target) - co.location
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    return co


def setup_render(engine="CYCLES", samples=64, res=(1920, 1080), fast=False, ink=False):
    """fast=True: iteration settings (few TAA samples). ink=True: Standard view transform so the
    flat cel colours and black ink are displayed exactly as authored."""
    s = bpy.context.scene
    try:
        s.render.engine = engine
    except TypeError:
        s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    if s.render.engine == "CYCLES":
        s.cycles.samples = 24 if fast else samples
        s.cycles.use_denoising = True
    else:
        s.eevee.taa_render_samples = 8 if fast else 32
        s.eevee.use_shadows = True
        s.eevee.shadow_resolution_scale = 1.0
    if ink or s.get("pw_ink"):
        s.view_settings.view_transform = "Standard"
        s.view_settings.look = "None"
        s.view_settings.exposure, s.view_settings.gamma = 0.0, 1.0
        return
    for vt in ("AgX", "Filmic"):
        try:
            s.view_settings.view_transform = vt
            break
        except TypeError:
            continue


def generate(context, scene_type, seed=1, size=60.0, detail=160, height=1.0,
             mood="GOLDEN", clear=True, engine="CYCLES", ink=True, layers=None):
    """Build a scene. ink=True (default) applies the hand-inked graphic-novel style to whatever the
    generator built (see ink.py); it needs EEVEE, so the engine is forced to BLENDER_EEVEE.
    layers: optional story layers dict (genre_mood, era, weather, ...); the genre grade is read from
    presets/genre.json by the ink pass."""
    from . import scenes, ink as ink_style
    random.seed(seed)
    context.scene["pw_layers"] = dict(layers or {})        # story layers (genre grade etc.), see presets/
    col = get_collection(clear)
    if clear:
        for o in list(context.scene.objects):
            if o.name.startswith("PW_") and o.name not in col.objects:
                remove_object(o)
        purge_orphans()
    info = scenes.REGISTRY[scene_type].build(col, seed=seed, size=size, detail=detail, height=height,
                                             mood=mood)
    setup_lighting(mood, col, sun_scale=info.get("sun_scale", 1.0),
                   sky_scale=info.get("sky_scale", 1.0), sun_dir=info.get("sun_dir"))
    setup_camera(col, **info.get("camera", {}))
    context.scene["pw_cam_target"] = tuple(info.get("camera", {}).get("target", (0, 0, 0)))
    if ink:
        engine = "BLENDER_EEVEE"
        info["ink"] = ink_style.apply(context, col, seed, mood, info)
    else:
        ink_style.remove(context)
    setup_render(engine, ink=ink)
    return info


def load_preset(kind):
    """presets/<kind>.json as a dict (layers are data: adding a genre/era is adding data)."""
    import json, os
    path = os.path.join(os.path.dirname(__file__), "presets", kind + ".json")
    with open(path, encoding="utf-8") as f:
        return {k: v for k, v in json.load(f).items() if not k.startswith("_")}


def genre_grade(layers):
    g = load_preset("genre")
    return g.get((layers or {}).get("genre_mood", "slice-of-life"), g["slice-of-life"])

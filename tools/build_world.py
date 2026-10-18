"""Build the walkable world of a story for the Godot game (Phase 3).
    blender -b --factory-startup -P tools/build_world.py -- story.json [--scenes id,id] [--out story_out/<slug>/world]
Per story scene: generate it (same generator/seed/layers as the comic), apply modifiers (hand-made
wobble, grass), bake every face's ink base colour into the COLOR_0 vertex colour (alpha 0 = unlit /
emissive face: neon, lamps, sky cards, fire), drop ink-only objects (Line Art, gulls), add empties
PW_Spawn, PW_Focus_<name>, PW_Trigger_<beat> (with extras), and export <scene>.glb (+Y up, lights).
Objects that must not collide (decals, glass, sky cards, reflections) get a "__nocol" name suffix.
Writes world.json next to the GLBs (Godot coordinates: x, y=up, z=-blender_y)."""
import sys, os, json, math, importlib, time
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import bpy
from mathutils import Vector
pw = importlib.import_module("procedural_worlds")
pw.register()
for o in list(bpy.data.objects):
    if not o.name.startswith("PW_"):
        bpy.data.objects.remove(o)
from procedural_worlds import core, shots, ink

TIME_TO_MOOD = {"dawn": "GOLDEN", "day": "DAY", "golden": "GOLDEN", "dusk": "DUSK", "night": "NIGHT"}
SKIP_TYPES = {"GREASEPENCIL", "CAMERA", "EMPTY"}


def godot(v):
    return [round(v[0], 4), round(v[2], 4), round(-v[1], 4)]


def args():
    a = sys.argv[sys.argv.index("--") + 1:]
    o = {"story": a[0], "scenes": None, "out": None}
    for i, x in enumerate(a):
        if x == "--scenes":
            o["scenes"] = set(a[i + 1].split(","))
        if x == "--out":
            o["out"] = a[i + 1]
    return o


def face_colors(mat):
    """(rgb, alpha, needs_bake) for a material: alpha 0 for flat/emissive faces."""
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return (0.7, 0.7, 0.7), 1.0, False
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:                                  # ink-authored emission material (sea etc.)
        return (0.3, 0.4, 0.45), 0.0, True
    es = bsdf.inputs["Emission Strength"].default_value
    if es > 0.01 or mat.get("pw_flat"):
        ec = bsdf.inputs["Emission Color"]
        c = tuple(ec.default_value)[:3] if es > 0.01 else tuple(bsdf.inputs["Base Color"].default_value)[:3]
        return c, 0.0, bsdf.inputs["Base Color"].is_linked and es <= 0.01
    bc = bsdf.inputs["Base Color"]
    return tuple(bc.default_value)[:3], 1.0, bc.is_linked


def bake_object(o):
    """Faces with node-driven colour: Cycles DIFFUSE colour (or EMIT) bake into the colour attribute."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 1
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    emit_only = all(next((n for n in s.material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) is None
                    for s in o.material_slots if s.material and s.material.use_nodes)
    if emit_only:
        bpy.ops.object.bake(type="EMIT", target="VERTEX_COLORS")
    else:
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, target="VERTEX_COLORS")


def bake_colors(col):
    """Apply modifiers, then write COLOR_0 per face corner (constant colours direct, chains baked)."""
    meshes = [o for o in col.objects if o.type in ("MESH", "CURVE", "FONT") and not o.hide_render and o.visible_get()]
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.convert(target="MESH")         # applies wobble / grass / curves
    baked = 0
    for o in [o for o in col.objects if o.type == "MESH"]:
        me = o.data
        if not me.polygons:
            continue
        info = [face_colors(s.material) for s in o.material_slots] or [((0.7, 0.7, 0.7), 1.0, False)]
        ca = me.color_attributes.get("Col") or me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        me.color_attributes.active_color = ca
        data = ca.data
        for p in me.polygons:
            rgb, a, _ = info[min(p.material_index, len(info) - 1)]
            for li in p.loop_indices:
                data[li].color = (*rgb, a)
        if any(nb for _, _, nb in info):
            alphas = {li: info[min(p.material_index, len(info) - 1)][1] for p in me.polygons for li in p.loop_indices}
            try:
                bake_object(o)
                data = o.data.color_attributes["Col"].data   # the bake reallocates: never reuse refs
                for li, a in alphas.items():                 # keep the unlit flag after the bake
                    c = data[li].color
                    data[li].color = (c[0], c[1], c[2], a)
                baked += 1
            except Exception as e:
                print("BAKE_FAIL", o.name, e)
        if o.get("pw_line", 1) == 0 or o.name.startswith(("PW_Reflect", "PW_SkyCard", "PW_HallSky", "PW_Skyline")):
            o.name = o.name + "__nocol"
    return baked


def add_empty(col, name, loc, extras):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SPHERE"
    e.location = loc
    for k, v in extras.items():
        e[k] = v
    col.objects.link(e)
    return e


def main():
    o = args()
    story = json.load(open(o["story"], encoding="utf-8"))
    slug = story["slug"]
    out = os.path.abspath(o["out"] or os.path.join(root, "story_out", slug, "world"))
    os.makedirs(out, exist_ok=True)
    eye = float(story.get("protagonist", {}).get("eye_height_m", 1.65))
    world = {"slug": slug, "title": story["title"], "logline": story.get("logline", ""),
             "protagonist": story.get("protagonist", {}), "scenes": []}
    wpath = os.path.join(out, "world.json")
    if o["scenes"] and os.path.exists(wpath):
        world["scenes"] = [s for s in json.load(open(wpath, encoding="utf-8"))["scenes"] if s["id"] not in o["scenes"]]
    for sc in story["scenes"]:
        if o["scenes"] and sc["id"] not in o["scenes"]:
            continue
        t0 = time.time()
        mood = TIME_TO_MOOD.get(sc["layers"].get("time", "day"), "DAY")
        info = core.generate(bpy.context, sc["generator"], seed=int(sc["seed"]), size=60, detail=160, mood=mood,
                             layers=sc["layers"], ink=False)
        col = bpy.data.collections[core.COLLECTION]
        # keep the hand-made wobble in the game geometry (same GN group as the ink pass)
        ink.build_wonk_group()
        d = ink._scene_scale(bpy.context.scene, info)
        for ob in list(col.objects):
            if ob.type == "MESH" and ob.get("pw_wonk", 1.0) > 0:
                ink.add_wobble(ob, strength=0.0042 * d, scale=1.6 / d, seed=int(sc["seed"]))
        for ob in list(col.objects):
            if ob.type in ("GREASEPENCIL",) or ob.name.startswith("PW_TuftProto"):
                core.remove_object(ob)
        bpy.context.view_layer.update()
        fps = info.get("focus_points", {})
        # spawn: the scene's spawn focus, projected to the floor, facing the establishing target
        sf = fps.get(info.get("spawn", {}).get("focus", ""), None)
        cam_loc, cam_tgt, _ = shots.establishing(info)
        interior = sc["layers"].get("base") in ("interior", "vehicle", "underground")
        sp = Vector(sf["pos"]) if (sf and interior) else Vector(cam_loc)   # outdoors: the composed vantage
        dg = bpy.context.evaluated_depsgraph_get()
        gz = shots._ground_z(bpy.context.scene, dg, sp + Vector((0, 0, 1.0)))
        sp = Vector((sp.x, sp.y, gz + 0.05))
        look = Vector(cam_tgt) - sp
        yaw = math.degrees(math.atan2(-look.x, look.y)) if look.length > 1e-3 else 0.0
        baked = bake_colors(col)
        add_empty(col, "PW_Spawn", sp, {"pw_kind": "spawn", "yaw_deg": yaw, "eye_height_m": eye})
        for name, f in fps.items():
            add_empty(col, f"PW_Focus_{name}", Vector(f["pos"]), {"pw_kind": "focus", "focus": name, "size": f["size"]})
        beats = []
        for b in story["beats"]:
            if b["scene_id"] != sc["id"]:
                continue
            tr = b.get("trigger", {"type": "focus", "focus": b["shot"].get("focus"), "radius_m": 3.0})
            f = fps.get(tr.get("focus") or b["shot"].get("focus"))
            pos = Vector(f["pos"]) if f else sp
            r = float(tr.get("radius_m", 3.0)) + (f["size"] * 0.5 if f else 0.0)
            if tr.get("type") == "enter":
                pos, r = sp, 2.0
            add_empty(col, f"PW_Trigger_{b['id']}", pos, {"pw_kind": "trigger", "beat": b["id"], "radius_m": r})
            beats.append({"id": b["id"], "caption": b.get("caption", ""), "dialogue": b.get("dialogue", []),
                          "trigger": {"pos": godot(pos), "radius_m": round(r, 2), "focus": tr.get("focus")},
                          "interactables": b.get("interactables", []), "shot": b["shot"]})
        glb = os.path.join(out, f"{sc['id']}.glb")
        bpy.ops.object.select_all(action="DESELECT")
        for ob in col.objects:
            ob.select_set(ob.type not in ("CAMERA", "GREASEPENCIL"))
        bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_apply=True,
                                  export_extras=True, export_lights=True, export_cameras=False, export_yup=True,
                                  export_vertex_color="ACTIVE", export_materials="EXPORT")
        P = ink.MOODS[mood]
        sun = next((x for x in col.objects if x.type == "LIGHT" and x.data.type == "SUN"), None)
        sun_dir = sun.matrix_world.to_quaternion() @ Vector((0, 0, -1)) if sun else Vector((0, 0.4, -1)).normalized()
        world["scenes"].append({
            "id": sc["id"], "name": sc.get("name", sc["id"]), "glb": f"{sc['id']}.glb", "mood": mood,
            "layers": sc["layers"], "spawn": {"pos": godot(sp), "yaw_deg": round(yaw, 1)},
            "focus": {k: godot(v["pos"]) for k, v in fps.items()},
            "sky": {"top": P["sky_top"], "horizon": P["sky_hor"], "cloud": P["cloud"], "ambient": P["ambient"],
                    "sun_dir": godot(sun_dir), "light_tint": (info.get("ink") or {}).get("light_tint") or P["light"],
                    "shadow_tint": (info.get("ink") or {}).get("shadow_tint") or P["shadow"]},
            "interior": sc["layers"].get("base") in ("interior", "vehicle", "underground"),
            "beats": beats})
        print(f"WORLD {sc['id']} {len(col.objects)} objs, {baked} baked, {len(fps)} focus, {len(beats)} beats, "
              f"{os.path.getsize(glb) / 1e6:.1f} MB, {time.time() - t0:.1f}s")
    order = [s["id"] for s in story["scenes"]]
    world["scenes"].sort(key=lambda s: order.index(s["id"]) if s["id"] in order else 99)
    json.dump(world, open(wpath, "w", encoding="utf-8"), indent=1)
    print("WORLD_DONE", wpath)


main()

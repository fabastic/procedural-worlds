"""Scene generators. Each class has LABEL and build(col, seed, size, detail, height) -> info dict.
Add a new scene: subclass-free, just write a class and add it to REGISTRY."""
import math, random
import bpy, bmesh
from mathutils import Vector
from . import core


def _terrain_mesh(name, size, detail, fn):
    n = detail
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=size / 2)
    for v in bm.verts:
        v.co.z = fn(v.co.x, v.co.y)
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


class CoastalIsland:
    """A rocky island with beach, grass, rocks, a standing stone ring and water."""
    LABEL = "Coastal island"

    @staticmethod
    def build(col, seed, size, detail, height, mood="GOLDEN", **kw):
        amp = 9.0 * height

        def h(x, y):
            r = math.hypot(x, y) / (size * 0.42)
            falloff = max(0.0, 1.0 - r ** 2.2)
            base = (core.fbm(x * 0.03, y * 0.03, seed, 5) * 0.5 + 0.5) ** 1.3
            ridges = abs(core.fbm(x * 0.07, y * 0.07, seed + 9, 4))
            return (base * amp + ridges * amp * 0.25) * falloff - 1.2

        me = _terrain_mesh("PW_TerrainMesh", size, detail, h)
        ter = core.link(bpy.data.objects.new("PW_Terrain", me), col)
        mat = core.height_material("PW_TerrainMat", (0.76, 0.68, 0.48), (0.18, 0.32, 0.10),
                                   (0.38, 0.36, 0.34), -0.5, amp * 0.9)
        ter.data.materials.append(mat)

        # water plane
        bpy.ops.mesh.primitive_plane_add(size=size * 2.5, location=(0, 0, 0))
        w = core.link(bpy.context.active_object, col)
        w.name = "PW_Water"
        wm = core.make_material("PW_WaterMat", (0.02, 0.18, 0.30), rough=0.05)
        b = wm.node_tree.nodes["Principled BSDF"]
        b.inputs["Transmission Weight"].default_value = 0.85
        b.inputs["IOR"].default_value = 1.33
        w.data.materials.append(wm)
        wm["pw_grime"] = 0.0

        # rocks scattered on land
        rock_mat = core.make_material("PW_RockMat", (0.33, 0.31, 0.29), rough=0.9)
        rng = random.Random(seed)
        placed = 0
        for _ in range(400):
            if placed >= 70:
                break
            x, y = rng.uniform(-size * .4, size * .4), rng.uniform(-size * .4, size * .4)
            z = h(x, y)
            if z < 0.2:
                continue
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(.3, 1.4),
                                                  location=(x, y, z))
            r = core.link(bpy.context.active_object, col)
            r.name = f"PW_Rock_{placed}"
            r.scale = (rng.uniform(.8, 1.4), rng.uniform(.8, 1.4), rng.uniform(.5, .9))
            r.rotation_euler = (rng.random(), rng.random(), rng.random() * 6.28)
            r.data.materials.append(rock_mat)
            placed += 1

        # standing stones on the highest accessible spot near centre
        best = max(((h(x, y), x, y) for x in range(-12, 13, 3) for y in range(-12, 13, 3)))
        _, cx, cy = best
        stone_mat = core.make_material("PW_StoneMat", (0.5, 0.5, 0.48), rough=0.8)
        for i in range(7):
            a = i / 7 * math.tau
            x, y = cx + math.cos(a) * 4, cy + math.sin(a) * 4
            bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, h(x, y) + 1.4))
            s = core.link(bpy.context.active_object, col)
            s.name = f"PW_Stone_{i}"
            s.scale = (0.5, 0.35, 1.4 + rng.random() * .5)
            s.rotation_euler.z = a
            s.data.materials.append(stone_mat)

        return {"objects": len(col.objects), "camera": dict(target=(cx, cy, 2), distance=size * .75,
                                                             height=size * .22)}


from .scene_kitchen import Kitchen  # noqa: E402
from .scene_alley import CyberpunkAlley  # noqa: E402

REGISTRY = {"COASTAL_ISLAND": CoastalIsland, "KITCHEN": Kitchen, "CYBERPUNK_ALLEY": CyberpunkAlley}

bl_info = {
    "name": "Procedural Worlds",
    "author": "you",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Worlds",
    "description": "Generate complete 3D scenes (geometry, materials, light, camera) from a seed",
    "category": "Add Mesh",
}

import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty
from . import core, scenes


class PW_Props(bpy.types.PropertyGroup):
    scene_type: EnumProperty(
        name="Scene",
        items=[(k, v.LABEL, v.__doc__ or "") for k, v in scenes.REGISTRY.items()],
    )
    seed: IntProperty(name="Seed", default=1, min=0)
    size: FloatProperty(name="Size (m)", default=60.0, min=10.0, max=400.0)
    detail: IntProperty(name="Detail", default=160, min=32, max=512)
    height: FloatProperty(name="Height", default=1.0, min=0.0, max=4.0)
    mood: EnumProperty(
        name="Mood",
        items=[("DAY", "Day", ""), ("GOLDEN", "Golden hour", ""),
               ("DUSK", "Dusk", ""), ("NIGHT", "Night", "")],
        default="GOLDEN",
    )
    clear_first: BoolProperty(name="Clear previous", default=True)
    engine: EnumProperty(
        name="Engine",
        items=[("BLENDER_EEVEE", "EEVEE", ""), ("CYCLES", "Cycles", "")],
        default="CYCLES",
    )


class PW_OT_generate(bpy.types.Operator):
    bl_idname = "pw.generate"
    bl_label = "Generate world"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p = context.scene.pw
        core.generate(context, p.scene_type, seed=p.seed, size=p.size,
                      detail=p.detail, height=p.height, mood=p.mood,
                      clear=p.clear_first, engine=p.engine)
        return {"FINISHED"}


class PW_OT_randomize(bpy.types.Operator):
    bl_idname = "pw.randomize"
    bl_label = "Random seed"

    def execute(self, context):
        import random
        context.scene.pw.seed = random.randint(0, 99999)
        return bpy.ops.pw.generate()


class PW_PT_panel(bpy.types.Panel):
    bl_label = "Procedural Worlds"
    bl_idname = "PW_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Worlds"

    def draw(self, context):
        l, p = self.layout, context.scene.pw
        for n in ("scene_type", "seed", "size", "detail", "height", "mood", "engine", "clear_first"):
            l.prop(p, n)
        row = l.row(align=True)
        row.operator("pw.generate", icon="WORLD")
        row.operator("pw.randomize", icon="FILE_REFRESH", text="")


CLASSES = (PW_Props, PW_OT_generate, PW_OT_randomize, PW_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.pw = bpy.props.PointerProperty(type=PW_Props)


def unregister():
    del bpy.types.Scene.pw
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)

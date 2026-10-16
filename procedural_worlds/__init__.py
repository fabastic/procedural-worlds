bl_info = {
    "name": "Procedural Worlds",
    "author": "FABASTIC",
    "version": (0, 2, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Worlds",
    "description": "Generate complete scenes from a seed, rendered as hand-inked graphic-novel panels",
    "category": "Add Mesh",
}

import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty
from . import core, scenes, anim

# Panel presets: one click sets scene, seed, mood and style for a showcase panel.
PRESETS = {
    "ISLAND_GOLDEN": ("Island, golden hour", dict(scene_type="COASTAL_ISLAND", seed=7, mood="GOLDEN")),
    "ISLAND_DUSK": ("Island, dusk", dict(scene_type="COASTAL_ISLAND", seed=42, mood="DUSK")),
    "ISLAND_NIGHT": ("Island, night", dict(scene_type="COASTAL_ISLAND", seed=7, mood="NIGHT")),
    "KITCHEN_DAY": ("Kitchen, morning", dict(scene_type="KITCHEN", seed=7, mood="DAY")),
    "KITCHEN_NIGHT": ("Kitchen, night", dict(scene_type="KITCHEN", seed=42, mood="NIGHT")),
    "ALLEY_NIGHT": ("Alley, night", dict(scene_type="CYBERPUNK_ALLEY", seed=7, mood="NIGHT")),
    "ALLEY_DUSK": ("Alley, dusk", dict(scene_type="CYBERPUNK_ALLEY", seed=42, mood="DUSK")),
}


def _apply_preset(self, context):
    if self.preset == "NONE":
        return
    for k, v in PRESETS[self.preset][1].items():
        setattr(self, k, v)
    self.style = "INK"


class PW_Props(bpy.types.PropertyGroup):
    preset: EnumProperty(
        name="Preset",
        items=[("NONE", "Custom", "Keep the current settings")] +
              [(k, v[0], "") for k, v in PRESETS.items()],
        update=_apply_preset,
    )
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
    style: EnumProperty(
        name="Style",
        items=[("INK", "Ink", "Hand-inked graphic-novel look (EEVEE)"),
               ("REALISTIC", "Realistic", "Plain physically based look (Cycles or EEVEE)")],
        default="INK",
    )
    clear_first: BoolProperty(name="Clear previous", default=True)
    engine: EnumProperty(
        name="Engine",
        description="Realistic style only; the ink style always renders with EEVEE",
        items=[("BLENDER_EEVEE", "EEVEE", ""), ("CYCLES", "Cycles", "")],
        default="CYCLES",
    )
    quality: EnumProperty(
        name="Quality",
        items=[("PREVIEW", "Preview 960x540", "Fast iteration settings"),
               ("HERO", "Hero 1920x1080", "Full samples")],
        default="HERO",
    )
    fly_frames: IntProperty(name="Frames", default=72, min=12, max=1000)


class PW_OT_generate(bpy.types.Operator):
    bl_idname = "pw.generate"
    bl_label = "Generate world"
    bl_description = "Build the scene from the seed, then light, frame and style it"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p = context.scene.pw
        ink = p.style == "INK"
        core.generate(context, p.scene_type, seed=p.seed, size=p.size,
                      detail=p.detail, height=p.height, mood=p.mood,
                      clear=p.clear_first, engine=p.engine, ink=ink)
        fast = p.quality == "PREVIEW"
        core.setup_render("BLENDER_EEVEE" if ink else p.engine,
                          res=(960, 540) if fast else (1920, 1080), fast=fast, ink=ink)
        return {"FINISHED"}


class PW_OT_randomize(bpy.types.Operator):
    bl_idname = "pw.randomize"
    bl_label = "Random seed"
    bl_description = "Pick a random seed and regenerate"

    def execute(self, context):
        import random
        context.scene.pw.seed = random.randint(0, 99999)
        context.scene.pw.preset = "NONE"
        return bpy.ops.pw.generate()


class PW_OT_flythrough(bpy.types.Operator):
    bl_idname = "pw.flythrough"
    bl_label = "Set up fly-through"
    bl_description = ("Animate the camera along a spline through the generated scene and set the "
                      "output to a low-res MP4 (Render > Render Animation)")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None and context.scene.camera.name.startswith("PW_")

    def execute(self, context):
        p = context.scene.pw
        info = {"camera": {"target": tuple(context.scene.get("pw_cam_target", (0, 0, 0)))}}
        anim.setup_flythrough(context, info, seed=p.seed, frames=p.fly_frames)
        anim.set_video_output(context.scene, f"//pw_flythrough_{p.scene_type.lower()}_{p.seed}.mp4")
        self.report({"INFO"}, "Fly-through ready: Render > Render Animation (Ctrl F12)")
        return {"FINISHED"}


class PW_PT_panel(bpy.types.Panel):
    bl_label = "Procedural Worlds"
    bl_idname = "PW_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Worlds"

    def draw(self, context):
        l, p = self.layout, context.scene.pw
        l.prop(p, "preset")
        box = l.box()
        for n in ("scene_type", "seed", "mood"):
            box.prop(p, n)
        box.row().prop(p, "style", expand=True)
        if p.style == "REALISTIC":
            box.prop(p, "engine")
        col = l.column(align=True)
        for n in ("size", "detail", "height", "quality", "clear_first"):
            col.prop(p, n)
        row = l.row(align=True)
        row.scale_y = 1.4
        row.operator("pw.generate", icon="WORLD")
        row.operator("pw.randomize", icon="FILE_REFRESH", text="")
        box = l.box()
        box.label(text="Animation", icon="CAMERA_DATA")
        box.prop(p, "fly_frames")
        box.operator("pw.flythrough", icon="CURVE_PATH")


CLASSES = (PW_Props, PW_OT_generate, PW_OT_randomize, PW_OT_flythrough, PW_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.pw = bpy.props.PointerProperty(type=PW_Props)


def unregister():
    del bpy.types.Scene.pw
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)

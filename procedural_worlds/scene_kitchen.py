"""Lived-in kitchen interior (stub, being built)."""
import bpy
from . import core


class Kitchen:
    """A cluttered, lived-in kitchen interior."""
    LABEL = "Kitchen interior"

    @staticmethod
    def build(col, seed, size, detail, height, mood="GOLDEN", **kw):
        bpy.ops.mesh.primitive_plane_add(size=8)
        core.link(bpy.context.active_object, col).name = "PW_Floor"
        return {"objects": len(col.objects),
                "camera": dict(location=(0, -3.5, 1.6), target=(0, 2, 1.2), lens=20)}

"""Cyberpunk alley (stub, being built)."""
import bpy
from . import core


class CyberpunkAlley:
    """A narrow neon-lit alley between tall buildings."""
    LABEL = "Cyberpunk alley"

    @staticmethod
    def build(col, seed, size, detail, height, mood="NIGHT", **kw):
        bpy.ops.mesh.primitive_plane_add(size=8)
        core.link(bpy.context.active_object, col).name = "PW_Road"
        return {"objects": len(col.objects),
                "camera": dict(location=(0, -10, 1.7), target=(0, 10, 3), lens=24)}

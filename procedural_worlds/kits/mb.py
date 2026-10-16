"""MeshBuilder: accumulate boxes/cylinders/polys per material key into ONE object with material
slots (few objects = fast Line Art, clean regeneration). Materials come from a palette dict
{key: (r, g, b)} via core.make_material, named PW_C_<key>."""
import math
import bpy, bmesh
from mathutils import Vector, Matrix
from .. import core


class MB:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.keys = []

    def _mi(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)

    def _tag(self, faces, key):
        mi = self._mi(key)
        for f in faces:
            f.material_index = mi

    def box(self, center, size, key, rot_z=0.0, rot=None):
        """Axis box of `size` (x, y, z) centred at `center`, optionally rotated about Z."""
        g = bmesh.ops.create_cube(self.bm, size=1.0)
        vs = g["verts"]
        bmesh.ops.scale(self.bm, vec=Vector(size), verts=vs)
        m = Matrix.Rotation(rot_z, 4, "Z") if rot is None else rot
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(Vector(center)) @ m, verts=vs)
        self._tag({f for v in vs for f in v.link_faces}, key)
        return vs

    def box_minmax(self, lo, hi, key):
        lo, hi = Vector(lo), Vector(hi)
        return self.box((lo + hi) / 2, hi - lo, key)

    def cyl(self, center, r, h, key, seg=12, r2=None, axis="Z"):
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r,
                                  radius2=r if r2 is None else r2, depth=h)
        vs = g["verts"]
        rot = {"Z": Matrix(), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[axis]
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(Vector(center)) @ rot, verts=vs)
        self._tag({f for v in vs for f in v.link_faces}, key)
        return vs

    def sphere(self, center, r, key, sub=1, squash=1.0):
        g = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)
        vs = g["verts"]
        for v in vs:
            v.co.z *= squash
            v.co += Vector(center)
        self._tag({f for v in vs for f in v.link_faces}, key)
        return vs

    def poly(self, pts, key):
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        self._tag([f], key)
        return f

    def quad_grid(self, x0, y0, x1, y1, nx, ny, key_fn, z=0.0, jitter=0.0, rng=None):
        """Floor grid of nx*ny quads; key_fn(i, j) picks each tile's material (checker, planks...)."""
        verts = {}
        for i in range(nx + 1):
            for j in range(ny + 1):
                jx = (rng.uniform(-jitter, jitter) if rng and 0 < i < nx else 0.0)
                jy = (rng.uniform(-jitter, jitter) if rng and 0 < j < ny else 0.0)
                verts[i, j] = self.bm.verts.new((x0 + (x1 - x0) * i / nx + jx, y0 + (y1 - y0) * j / ny + jy, z))
        for i in range(nx):
            for j in range(ny):
                f = self.bm.faces.new((verts[i, j], verts[i + 1, j], verts[i + 1, j + 1], verts[i, j + 1]))
                self._tag([f], key_fn(i, j))

    def empty(self):
        return len(self.bm.verts) == 0

    def build(self, col, palette, **props):
        me = bpy.data.meshes.new(self.name)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        for k in self.keys:
            c = palette.get(k, (0.6, 0.6, 0.6))
            if isinstance(c, dict):
                m = core.make_material(f"PW_C_{k}", c["color"], emission=c.get("emission"),
                                       strength=c.get("strength", 0.0))
                if c.get("flat"):
                    m["pw_flat"] = 1
            else:
                m = core.make_material(f"PW_C_{k}", c)
            me.materials.append(m)
        o = bpy.data.objects.new(self.name, me)
        col.objects.link(o)
        for k, v in props.items():
            o[k] = v
        return o

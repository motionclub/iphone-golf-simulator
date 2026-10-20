"""Thin feature layers for the face lock (brows, eyes+lids, nostrils, mouth seam, helix rim), plate-placed.

Built as ONE object `Face_M` with material slots (Brow, Sclera, Iris, Pupil, Catch, LidLine, Lip, Nostril, Skin).
All surfaces are ray-cast onto the sculpted Body_M head and sit 0.5–2.5 mm proud of it.
"""
import math
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from head_lock import LM
import head_lock as hl

SKIN_HEX = '#D9A37E'
COLORS = dict(Skin=('#D9A37E', .62), Brow=('#2A1E15', .66), Sclera=('#F2EDE3', .34), Iris=('#5A3418', .40), Pupil=('#120A06', .30),
              Catch=('#FFFFFF', .12), LidLine=('#4A2E1F', .60), Lip=('#C48A75', .58), Seam=('#6A3A2A', .70), Nostril=('#5A3222', .75))


def hex_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lin(c):
    return tuple(((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in c)


def material(name, hx, rough):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes.get('Principled BSDF')
    n.inputs['Base Color'].default_value = (*lin(hex_rgb(hx)), 1)
    n.inputs['Roughness'].default_value = rough
    n.inputs['Metallic'].default_value = 0
    if 'Specular IOR Level' in n.inputs:
        n.inputs['Specular IOR Level'].default_value = .3
    m.diffuse_color = (*lin(hex_rgb(hx)), 1)
    return m


class Layers:
    def __init__(self, body):
        self.body = body
        bm = bmesh.new(); bm.from_mesh(body.data); self.tree = BVHTree.FromBMesh(bm); bm.free()
        self.verts = []; self.faces = []; self.mats = []        # faces: (ids, slot)
        self.slots = list(COLORS.keys())

    # ---- surface sampling
    def surf(self, x, z, lift=0.0, dirn=(0, 1, 0)):
        """point on the head surface at (x, z) seen from the front, lifted along the hit normal"""
        hit = self.tree.ray_cast(Vector((x, -1.0, z)), Vector(dirn), 2.0)
        if hit[0] is None:
            raise ValueError(('missed', x, z))
        p, n = hit[0], hit[1]
        return (p.x + n.x * lift, p.y + n.y * lift, p.z + n.z * lift)

    def surf_side(self, y, z, s, lift=0.0):
        hit = self.tree.ray_cast(Vector((s * 1.0, y, z)), Vector((-s, 0, 0)), 2.0)
        if hit[0] is None:
            raise ValueError(('missed side', y, z))
        p, n = hit[0], hit[1]
        return (p.x + n.x * lift, p.y + n.y * lift, p.z + n.z * lift)

    def add(self, p):
        self.verts.append(tuple(p)); return len(self.verts) - 1

    def face(self, ids, slot):
        self.faces.append((tuple(int(i) for i in ids), self.slots.index(slot)))

    # ---- primitives
    def patch(self, cx, cz, rx, top, bottom, lift, slot, n=32, k=4, almond=False, clamp=None, lift_fn=None):
        c = self.add(self.surf(cx, cz, lift if lift_fn is None else lift_fn(cx, cz)))
        rings = []
        for j in range(1, k + 1):
            rho = j / k; ring = []
            for i in range(n):
                a = math.tau * i / n; si = math.sin(a)
                x = cx + rho * rx * math.cos(a)
                z = cz + rho * (top if si >= 0 else bottom) * si * (abs(si) ** .22 if almond else 1)
                if clamp: z = clamp(x, z)
                ring.append(self.add(self.surf(x, z, lift if lift_fn is None else lift_fn(x, z))))
            rings.append(ring)
        for i in range(n): self.face((c, rings[0][i], rings[0][(i + 1) % n]), slot)
        for a, b in zip(rings, rings[1:]):
            for i in range(n): self.face((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]), slot)

    def tube(self, pts, widths, slot, n=8, depth_ratio=.55):
        rings = []
        for i, point in enumerate(pts):
            p = Vector(point)
            axis = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(0, i - 1)])).normalized()
            side = axis.cross(Vector((0, 1, 0))).normalized(); out = side.cross(axis).normalized()
            ring = []
            for j in range(n):
                a = math.tau * j / n
                ring.append(self.add(p + side * (widths[i] * math.cos(a)) + out * (widths[i] * depth_ratio * math.sin(a))))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for j in range(n): self.face((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]), slot)
        self.face(tuple(reversed(rings[0])), slot); self.face(tuple(rings[-1]), slot)

    def ribbon(self, pts, widths, slot, thick=0.0016):
        """flat strip with thickness, oriented by the local surface normal (no ring-frame flips)"""
        import numpy as np
        rings = []
        for i, p in enumerate(pts):
            p = Vector(p)
            hit = self.tree.find_nearest(p); n = hit[1] if hit[0] is not None else Vector((0, -1, 0))
            t = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(0, i - 1)])).normalized()
            side = t.cross(n).normalized(); n2 = side.cross(t).normalized()
            w = widths[i]
            ring = [self.add(p + side * w + n2 * thick * 0.5), self.add(p - side * w + n2 * thick * 0.5),
                    self.add(p - side * w - n2 * thick * 0.5), self.add(p + side * w - n2 * thick * 0.5)]
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for j in range(4): self.face((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]), slot)
        self.face(tuple(reversed(rings[0])), slot); self.face(tuple(rings[-1]), slot)

    # ---- features
    def sphere_pt(self, C, R, x, z, lift=0.0):
        """point on the eyeball sphere (centre C, radius R) at lateral x / height z, on the front hemisphere"""
        dx = x - C[0]; dz = z - C[2]
        q = max(0.0, 1.0 - (dx / hl.EYE_A) ** 2 - (dz / hl.EYE_B) ** 2)
        return (x, C[1] - (hl.EYE_C + lift) * math.sqrt(q), z)

    def eye_patch(self, C, R, cx, cz, rx, top, bottom, lift, slot, n=32, k=4, almond=False, clamp=None):
        c = self.add(self.sphere_pt(C, R, cx, cz, lift))
        rings = []
        for j in range(1, k + 1):
            rho = j / k; ring = []
            for i in range(n):
                a = math.tau * i / n; si = math.sin(a)
                x = cx + rho * rx * math.cos(a)
                z = cz + rho * (top if si >= 0 else bottom) * si * (abs(si) ** .22 if almond else 1)
                if clamp: x, z = clamp(x, z)
                ring.append(self.add(self.sphere_pt(C, R, x, z, lift)))
            rings.append(ring)
        for i in range(n): self.face((c, rings[0][i], rings[0][(i + 1) % n]), slot)
        for a_, b_ in zip(rings, rings[1:]):
            for i in range(n): self.face((a_[i], a_[(i + 1) % n], b_[(i + 1) % n], b_[i]), slot)

    def build(self, smile=0.0038, mouth_w=0.0385):
        L = LM
        ez, ex = L['eye_z'], L['eye_x']
        rx, up, dn = 0.0235, 0.0108, 0.0092
        R = hl.EYE_R
        for s in (-1, 1):
            cx = s * ex
            C = tuple(hl.EYES[s])                                    # same sphere the socket was carved for
            def inside(x, z, cx=cx):
                u = max(-0.999, min(0.999, (x - cx) / rx)); f = (1 - u * u) ** .6
                return x, max(ez - dn * f, min(ez + up * f, z))
            self.eye_patch(C, R, cx, ez, rx, up, dn, 0.0, 'Sclera', n=32, k=4, almond=True)
            icx = cx - s * 0.0010
            self.eye_patch(C, R, icx, ez - 0.0005, 0.0108, 0.0108, 0.0108, 0.0003, 'Iris', n=28, k=3, clamp=inside)
            self.eye_patch(C, R, icx, ez - 0.0005, 0.0050, 0.0050, 0.0050, 0.0006, 'Pupil', n=20, k=2, clamp=inside)
            self.eye_patch(C, R, icx - s * 0.0038, ez + 0.0040, 0.0017, 0.0017, 0.0017, 0.0009, 'Catch', n=14, k=1, clamp=inside)
            for upper in (True, False):
                pts = []; wd = []
                for i in range(33):
                    a = math.pi * i / 32; x = cx + rx * math.cos(a)
                    h = up if upper else -dn; z = ez + h * math.sin(a) ** 1.2 - (0.0 if upper else 0.0009)
                    pts.append(self.sphere_pt(C, R, x, z, 0.0008 if upper else 0.0004)); wd.append(0.0004 + (0.0014 if upper else 0.0006) * math.sin(a) ** .7)
                self.tube(pts, wd, 'LidLine' if upper else 'Skin', n=8)
            # brow: thick, dark, gently arched; inner x 0.0228 z 1.6105 -> outer 0.0815 z 1.606
            pts = []; wd = []
            for i in range(31):
                t = i / 30
                xb = s * (0.0228 + (0.0815 - 0.0228) * t)
                zb = 1.6105 + 0.0070 * math.sin(math.pi * t) - 0.0040 * t * t
                pts.append(self.surf(xb, zb, 0.0028))
                wd.append(0.0028 + 0.0030 * math.sin(math.pi * (0.08 + 0.84 * t)) ** .5)
            for _ in range(3):
                pts = [tuple((np.array(pts[max(0, i - 1)]) + 2 * np.array(pts[i]) + np.array(pts[min(30, i + 1)])) / 4) for i in range(31)]
            self.ribbon(pts, wd, 'Brow', thick=0.0030)
            # nostril dark
            self.patch(s * 0.0165, L['nose_base_z'] - 0.0012, 0.0030, 0.0013, 0.0013, 0.0007, 'Nostril', n=14, k=2)
            # ear rim: helix tube + antihelix arc on the ear's outer surface (ray-cast from the side)
            cy, cz, ry, rz = L['ear_cy'], L['ear_cz'], L['ear_ry'], L['ear_rz']
            pts = []; wd = []
            for i in range(37):
                a = -math.pi * 0.42 + i / 36 * (math.pi * 1.62)            # from the lobe, over the back and top, to the front-top
                yy = cy + 0.92 * ry * math.cos(a); zz = cz + 0.92 * rz * math.sin(a)
                pts.append(self.surf_side(yy, zz, s, 0.0028)); wd.append(0.0042 - 0.0010 * abs(math.cos(a)))
            pts = [tuple((np.array(pts[max(0, i - 1)]) + 2 * np.array(pts[i]) + np.array(pts[min(36, i + 1)])) / 4) for i in range(37)]
            self.tube(pts, wd, 'Skin', n=8, depth_ratio=.9)
            pts = []; wd = []
            for i in range(19):
                a = -math.pi * 0.10 + i / 18 * (math.pi * 0.95)
                yy = cy + 0.50 * ry * math.cos(a); zz = cz + 0.55 * rz * math.sin(a)
                pts.append(self.surf_side(yy, zz, s, 0.0014)); wd.append(0.0016)
            self.tube(pts, wd, 'Skin', n=8, depth_ratio=.7)
        # mouth: closed smile seam + lip colour bands
        pts = []; wd = []
        for i in range(49):
            t = -1 + 2 * i / 48; x = mouth_w * t
            z = L['mouth_z'] + smile * t * t
            pts.append(self.surf(x, z, 0.0013)); wd.append(0.0002 + 0.0005 * math.sin(math.pi * i / 48) ** .8)
        self.tube(pts, wd, 'Seam', n=8)
        for upper in (True, False):
            pts = []; wd = []
            for i in range(49):
                t = -1 + 2 * i / 48; x = mouth_w * 0.97 * t
                full = max(0, 1 - t * t) ** .6
                z = L['mouth_z'] + smile * t * t + (0.0030 * full if upper else -0.0034 * full)
                pts.append(self.surf(x, z, 0.0006)); wd.append(0.0003 + (0.0013 if upper else 0.0016) * full)
            for _ in range(6):
                pts = [tuple((np.array(pts[max(0, i - 1)]) + 2 * np.array(pts[i]) + np.array(pts[min(48, i + 1)])) / 4) for i in range(49)]
            self.ribbon(pts, wd, 'Lip', thick=0.0006)
        return self.make()

    def make(self, name='Face_M'):
        old = bpy.data.objects.get(name)
        if old is not None:
            me = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.verts, [], [f for f, _ in self.faces]); me.update()
        for slot in self.slots:
            me.materials.append(material('Face_' + slot, *COLORS[slot]))
        for p, (_, k) in zip(me.polygons, self.faces):
            p.material_index = k; p.use_smooth = True
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        return o

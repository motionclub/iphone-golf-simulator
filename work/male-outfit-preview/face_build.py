"""Separate facial-feature layers (eyes, brows, mouth, nostrils) for the male base.  Body_M is never modified.

Everything is generated as small meshes that sit 1-3 mm proud of the existing head surface (ray-cast onto Body_M),
grouped per expression in collections  Face_<expr>.  Positions come from the plate calibration (S = 1.7/593 m per px).
"""
import math
import bpy
from mathutils import Vector
from preview_common import *

SKIN = '#C98F69'          # warm matte soft-plastic skin (plate average ~ (201,141,105))
COL = dict(
    sclera=('#F0EBE0', .34), iris=('#5A3418', .40), pupil=('#120A06', .30), catch=('#FFFFFF', .12),
    brow=('#2A1E15', .66), lip=('#B8705A', .58), seam=('#5E2F22', .70), nostril=('#6B3C2A', .75),
    lidline=('#3A2318', .60), teeth=('#F4F0E6', .35), tongue=('#C4524F', .50), mouth=('#2A0F10', .85),
    blush=('#E08A78', .8),
)

EXPR = {
    # mouth: 'smile' closed smile / 'grin' open / 'flat' tight / 'oh' round
    'happy':    dict(mouth='smile', smile=.0052, mw=.038, opening=0.0, brow_h=.001, brow_inner=-.001, lid_up=.92, lid_low=.82, lid_line=1.0, cheek=.0010),
    'cheer':    dict(mouth='grin',  smile=.0075, mw=.041, opening=.0175, brow_h=.004, brow_inner=.002, lid_up=.78, lid_low=.62, lid_line=1.15, cheek=.0020),
    'focus':    dict(mouth='flat',  smile=-.0010, mw=.032, opening=0.0, brow_h=-.003, brow_inner=-.0075, lid_up=.72, lid_low=.88, lid_line=1.2, cheek=0),
    'surprise': dict(mouth='oh',    smile=0.0, mw=.0085, opening=.0125, brow_h=.0085, brow_inner=.003, lid_up=1.12, lid_low=1.0, lid_line=.9, cheek=0),
}


class Face:
    def __init__(self, body):
        self.body = body
        self.tree = body_bvh(body)
        self.eye_z = (654 - 102) * S
        self.eye_x = 14 * S
        self.rx = 7.0 * S
        self.up = 3.7 * S
        self.down = 2.8 * S
        self.mouth_z = (654 - 132.8) * S + .010
        self.nostril_z = (654 - 122.6) * S + .008
        self.mats = {k: material('Face_' + k, c, r) for k, (c, r) in COL.items()}
        self.mats['skin'] = material('Face_skin_lid', SKIN, .62)

    def surface(self, x, z):
        hit, normal, index, dist = self.tree.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)), 2)
        if hit is None:
            raise ValueError(('Feature missed head', x, z))
        return hit.y

    # ---- primitive builders
    def patch(self, coll, name, cx, cz, rx, top, bottom, depth, mat, n=48, k=6, almond=False, clamp=None):
        verts = [(cx, depth(cx, cz), cz)]
        rings = []
        faces = []
        for j in range(1, k + 1):
            rho = j / k
            ring = []
            for i in range(n):
                a = math.tau * i / n
                si = math.sin(a)
                x = cx + rho * rx * math.cos(a)
                z = cz + rho * (top if si >= 0 else bottom) * si * (abs(si) ** .22 if almond else 1)
                if clamp:
                    z = clamp(x, z)
                ring.append(len(verts))
                verts.append((x, depth(x, z), z))
            rings.append(ring)
        for i in range(n):
            faces.append((0, rings[0][i], rings[0][(i + 1) % n]))
        for a, b in zip(rings, rings[1:]):
            for i in range(n):
                faces.append((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
        back = len(verts)
        verts.append((cx, self.surface(cx, cz) + .003, cz))
        for i in range(n):
            faces.append((rings[-1][(i + 1) % n], rings[-1][i], back))
        return make_mesh_obj(name, verts, faces, mat, coll)

    def line(self, coll, name, pts, widths, mat, depth_ratio=.55, n=10):
        verts = []
        faces = []
        rings = []
        for i, point in enumerate(pts):
            p = Vector(point)
            axis = (Vector(pts[min(i + 1, len(pts) - 1)]) - Vector(pts[max(0, i - 1)])).normalized()
            side = axis.cross(Vector((0, 1, 0))).normalized()
            out = side.cross(axis).normalized()
            ring = []
            for j in range(n):
                a = math.tau * j / n
                ring.append(len(verts))
                verts.append(tuple(p + side * (widths[i] * math.cos(a)) + out * (widths[i] * depth_ratio * math.sin(a))))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for j in range(n):
                faces.append((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))
        faces.extend([tuple(reversed(rings[0])), tuple(rings[-1])])
        return make_mesh_obj(name, verts, faces, mat, coll)

    def band(self, coll, name, xs, z_lo, z_hi, depth_off, mat):
        """quad strip between two curves z_lo(t) / z_hi(t) sampled at xs (list of (x, zl, zh)); rows=3."""
        verts = []
        faces = []
        K = 3
        for (x, zl, zh) in xs:
            col = []
            for k in range(K + 1):
                z = zl + (zh - zl) * k / K
                col.append(len(verts))
                verts.append((x, self.surface(x, z) - depth_off, z))
            if verts:
                pass
            faces.append(col)
        quads = []
        for a, b in zip(faces, faces[1:]):
            for k in range(K):
                quads.append((a[k], b[k], b[k + 1], a[k + 1]))
        return make_mesh_obj(name, verts, quads, mat, coll)

    # ---- the face
    def build(self, expr='happy', parent=None):
        p = EXPR[expr]
        cname = 'Face_' + expr
        coll = get_collection(cname, parent)
        clear_collection(coll)
        M = self.mats
        eye_z, rx = self.eye_z, self.rx
        up, down = self.up * p['lid_up'], self.down * p['lid_low']
        for sign in (-1, 1):
            cx = sign * self.eye_x
            side = 'L' if sign < 0 else 'R'
            ez = eye_z

            def eye_depth(x, z, cx=cx, ez=ez):
                v = ((x - cx) / rx) ** 2 + ((z - ez) / (up if z >= ez else down)) ** 2
                return self.surface(x, z) - .0008 - .0026 * math.sqrt(max(0, 1 - v))

            def opening(x, z, cx=cx, ez=ez):
                u = max(-0.999, min(0.999, (x - cx) / rx))
                f = (1 - u * u) ** .61
                return max(ez - down * f, min(ez + up * f, z))

            self.patch(coll, 'Sclera_' + side, cx, ez, rx, up, down, eye_depth, M['sclera'], almond=True)
            # look slightly toward the camera/centre: iris offset toward the nose by 0.6 mm for a friendly gaze
            icx = cx - sign * .0006
            self.patch(coll, 'Iris_' + side, icx, ez, .0088, .0090, .0088, lambda x, z, d=eye_depth: d(x, z) - .00035, M['iris'], n=40, k=4, clamp=opening)
            self.patch(coll, 'Pupil_' + side, icx, ez, .0048, .0050, .0048, lambda x, z, d=eye_depth: d(x, z) - .00065, M['pupil'], n=32, k=3, clamp=opening)
            self.patch(coll, 'Catch_' + side, icx - sign * .0026, ez + .0030, .0016, .0016, .0016, lambda x, z, d=eye_depth: d(x, z) - .0009, M['catch'], n=20, k=2, clamp=opening)
            for upper in (True, False):
                pts = []
                width = []
                for i in range(41):
                    a = math.pi * i / 40
                    x = cx + rx * math.cos(a)
                    h = (up if upper else -down)
                    z = ez + h * math.sin(a) ** 1.22
                    pts.append((x, eye_depth(x, z) - .00055, z))
                    wl = p['lid_line']
                    width.append(.0003 + ((.0016 if upper else .0010) * wl) * math.sin(a) ** .7)
                self.line(coll, ('UpperLid_' if upper else 'LowerLid_') + side, pts, width, M['lidline'] if upper else M['skin'], n=8)
            # brow
            pts = []
            width = []
            for i in range(41):
                t = -1 + 2 * i / 40
                u_in = -sign * t                      # +1 at the inner end (toward the nose)
                x = cx + .026 * t
                z = ez + .023 + .0055 * (1 - t * t) + .0015 * (sign * t) + p['brow_h'] + p['brow_inner'] * (u_in * .5 + .5)
                taper = math.sin(math.pi * (0.04 + 0.92 * i / 40)) ** .55
                pts.append((x, self.surface(x, z) - .0015, z))
                width.append(.0005 + .0034 * taper)
            self.line(coll, 'Brow_' + side, pts, width, M['brow'], n=10)
            # cheek lift (smile): soft raised blush disc under the eye
            if p['cheek'] > 0:
                self.patch(coll, 'Blush_' + side, sign * .043, ez - .029, .0125, .0085, .0085, lambda x, z, d=p['cheek']: self.surface(x, z) - .0004, M['blush'], n=36, k=4)
        # nostrils
        for sign in (-1, 1):
            self.patch(coll, 'Nostril_' + ('L' if sign < 0 else 'R'), sign * .011, self.nostril_z, .0022, .00125, .0011, lambda x, z: self.surface(x, z) - .00065, M['nostril'], n=24, k=3)
        self.mouth(coll, p)
        return coll

    def mouth(self, coll, p):
        M = self.mats
        mz, mw, sm = self.mouth_z, p['mw'], p['smile']
        kind = p['mouth']
        if kind in ('smile', 'flat'):
            for upper in (True, False):
                pts = []
                width = []
                for i in range(61):
                    t = -1 + 2 * i / 60
                    x = mw * t
                    full = max(0, 1 - t * t) ** .65
                    cupid = .0005 * math.exp(-((abs(t) - .25) / .23) ** 2)
                    z = mz + sm * t * t + ((.0011 * full + cupid) if upper else -.0017 * full)
                    pts.append((x, self.surface(x, z) - .0012, z))
                    width.append(.0002 + (.0011 if upper else .00155) * full)
                self.line(coll, 'Upper_Lip' if upper else 'Lower_Lip', pts, width, M['lip'], n=8)
            pts = []
            width = []
            for i in range(61):
                t = -1 + 2 * i / 60
                x = mw * t
                z = mz + sm * t * t
                pts.append((x, self.surface(x, z) - .0023, z))
                width.append(.00015 + .00065 * math.sin(math.pi * i / 60) ** .8)
            self.line(coll, 'Closed_Smile', pts, width, M['seam'], n=8)
            if kind == 'smile':      # smile creases at the corners
                for sign in (-1, 1):
                    pts = []
                    width = []
                    for i in range(15):
                        a = i / 14
                        x = sign * (mw + .0015 + .0045 * a)
                        z = mz + sm + .0014 * a + .0030 * math.sin(a * 1.7)
                        pts.append((x, self.surface(x, z) - .0016, z))
                        width.append(.0002 + .0005 * math.sin(math.pi * a) ** .7)
                    self.line(coll, 'SmileCrease_' + str(sign), pts, width, M['seam'], n=6)
        elif kind == 'grin':
            N = 60
            op = p['opening']

            def zu(t):
                return mz + sm * t * t + .0020 * max(0, 1 - t * t) ** .6

            def zl(t):
                return mz + sm * t * t - op * max(0, 1 - t * t) ** .85

            cols = []
            for i in range(N + 1):
                t = -1 + 2 * i / N
                cols.append((mw * t, zl(t), zu(t)))
            self.band(coll, 'Mouth_Interior', cols, 0, 0, .0010, M['mouth'])
            teeth = []
            for i in range(N + 1):
                t = -1 + 2 * i / N
                if abs(t) > .86:
                    continue
                h = .0052 * max(0, 1 - (t / .86) ** 2) ** .5
                teeth.append((mw * t, zu(t) - h, zu(t) - .0001))
            self.band(coll, 'Teeth_Upper', teeth, 0, 0, .0013, M['teeth'])
            tongue = []
            for i in range(N + 1):
                t = -1 + 2 * i / N
                if abs(t) > .62:
                    continue
                h = .52 * op * max(0, 1 - (t / .62) ** 2) ** .6
                tongue.append((mw * t, zl(t) + .0002, zl(t) + h))
            self.band(coll, 'Tongue', tongue, 0, 0, .0012, M['tongue'])
            for upper in (True, False):
                pts = []
                width = []
                for i in range(N + 1):
                    t = -1 + 2 * i / N
                    x = mw * t
                    full = max(0, 1 - t * t) ** .6
                    z = zu(t) + .0006 * full if upper else zl(t) - .0006 * full
                    pts.append((x, self.surface(x, z) - .0018, z))
                    width.append(.0003 + (.0014 if upper else .0019) * full)
                self.line(coll, 'Upper_Lip' if upper else 'Lower_Lip', pts, width, M['lip'], n=8)
            for sign in (-1, 1):
                pts = []
                width = []
                for i in range(15):
                    a = i / 14
                    x = sign * (mw + .0012 + .0050 * a)
                    z = mz + sm + .0016 * a + .0034 * math.sin(a * 1.7)
                    pts.append((x, self.surface(x, z) - .0016, z))
                    width.append(.0002 + .0005 * math.sin(math.pi * a) ** .7)
                self.line(coll, 'SmileCrease_' + str(sign), pts, width, M['seam'], n=6)
        elif kind == 'oh':
            cz = mz - .002
            rxm, ry = mw, p['opening']
            self.patch(coll, 'Mouth_Interior', 0, cz, rxm, ry, ry, lambda x, z: self.surface(x, z) - .0010, M['mouth'], n=40, k=5)
            self.patch(coll, 'Tongue', 0, cz - ry * .45, rxm * .55, ry * .35, ry * .35, lambda x, z: self.surface(x, z) - .0012, M['tongue'], n=28, k=3)
            pts = []
            width = []
            for i in range(61):
                a = math.tau * i / 60
                x = (rxm + .0008) * math.cos(a)
                z = cz + (ry + .0008) * math.sin(a)
                pts.append((x, self.surface(x, z) - .0018, z))
                width.append(.0016)
            self.line(coll, 'Lips_Ring', pts, width, M['lip'], n=8)

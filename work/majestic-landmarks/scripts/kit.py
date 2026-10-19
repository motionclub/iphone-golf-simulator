"""Majestic landmark kit: shared Blender builder library (headless; Blender 5.2).

Every asset is built twice from the same recipe: q=1 -> LOD0, q=Q1 -> LOD1 (fewer segments, chamfers instead
of round bevels, LOD0-only details dropped). LOD2 is a cross-card impostor rendered from LOD0.

Mesh conventions (match chat 9's GolfArcade/MajesticDressing shader so one material covers the asset):
  vertex colour 'Col' (linear float, exported sRGB) = albedo
  UV0 = (sway weight, phase) = 0 for rigid props;  UV1 = (flap) = 0;  UV2.x = glow (emission multiplier)
FX cards (waterfalls, lava falls, plume, foam) are separate objects with real 0..1 UVs and alpha in Col.a.
Units are metres, +Z up in Blender, the asset's front faces Blender -Y. Pivots are at the base (see spec).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise

Q1 = 0.45          # LOD1 quality factor


def lin(c):
    """sRGB 0..1 (or hex) -> linear RGBA."""
    if isinstance(c, str):
        c = c.lstrip('#'); c = tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda x: x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    a = c[3] if len(c) > 3 else 1.0
    return (f(c[0]), f(c[1]), f(c[2]), a)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def M(loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    from mathutils import Euler
    return (Matrix.Translation(Vector(loc)) @ Euler([math.radians(r) for r in rot], 'XYZ').to_matrix().to_4x4()
            @ Matrix.Diagonal((*scale, 1)))


class Asset:
    """Accumulates parts into one bmesh. Each part is built in a scratch bmesh, beveled, then copied in."""

    def __init__(self, name, q=1.0, seed=1):
        self.name, self.q = name, q
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new('Col')
        self.glow = self.bm.faces.layers.float.new('glow')
        self.wn = self.bm.verts.layers.int.new('wn')     # 1 = hard-surface part: gets face-area weighted normals
        self.rng = random.Random(seed)
        self.parts = 0

    # ---- quality helpers
    def S(self, n, lo=3):
        if n <= 8 or self.q >= 1:        # low counts are shape-defining (square roofs, hex columns): keep them
            return n
        return max(8, lo, int(round(n * self.q * 1.25)))  # LOD1 keeps ~56 % of ring segs

    @property
    def lod0(self):
        return self.q >= 1

    def bseg(self):
        return 2 if self.lod0 else 1

    # ---- core: merge a scratch bmesh into the asset
    def merge(self, src, color, glow=0.0, smooth=True, xf=None, vcol=False, weighted=True):
        """vcol=True evaluates callable colours per vertex (smooth gradients on terrain); else per face (crisp bands)."""
        if xf is not None:
            bmesh.ops.transform(src, matrix=xf, verts=src.verts)
        src.normal_update()
        vc = {}
        if vcol and callable(color):
            for v in src.verts:
                c = color(v.co, v.normal)
                vc[v] = c if len(c) == 4 else (*c, 1.0)
        vmap = {v: self.bm.verts.new(v.co) for v in src.verts}
        for nv in vmap.values():
            nv[self.wn] = 1 if weighted else 0
        for f in src.faces:
            vs = [vmap[v] for v in f.verts]
            nf = self.bm.faces.new(vs)
            nf.smooth = smooth
            if vc:
                for l, ov in zip(nf.loops, f.verts):
                    l[self.col] = vc[ov]
            else:
                c = color(f.calc_center_median(), f.normal) if callable(color) else color
                c = c if len(c) == 4 else (*c, 1.0)
                for l in nf.loops:
                    l[self.col] = c
            g = glow(f.calc_center_median()) if callable(glow) else glow
            nf[self.glow] = g
        src.free()
        self.parts += 1

    def _bevel(self, bm, r, seg=None, only_sharp=0.0):
        if r <= 0:
            return
        seg = self.bseg() if seg is None else seg
        bm.normal_update()
        edges = [e for e in bm.edges if len(e.link_faces) == 2 and (only_sharp <= 0 or e.calc_face_angle(0) > only_sharp)]
        if edges:
            bmesh.ops.bevel(bm, geom=edges, offset=r, offset_type='OFFSET', profile_type='SUPERELLIPSE',
                            segments=seg, profile=0.5, affect='EDGES', clamp_overlap=True)

    # ---- primitives (all closed, manifold shells)
    def box(self, size, loc=(0, 0, 0), rot=(0, 0, 0), col=(1, 1, 1), bevel=0.0, glow=0.0, smooth=True):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((*size, 1)))
        self._bevel(bm, min(bevel, min(size) * 0.45))
        self.merge(bm, col, glow, smooth, M(loc, rot))

    def cyl(self, r1, r2, h, loc=(0, 0, 0), rot=(0, 0, 0), col=(1, 1, 1), segs=16, bevel=0.0, glow=0.0, smooth=True, base=True, phase=0.0):
        """Cone/cylinder via the lathe; bevel rounds the rims (one extra ring each, LOD0 two).
        base=True: stands on loc (z 0..h); else centred on loc."""
        z0 = 0.0 if base else -h / 2
        b = min(bevel, h * 0.3, max(r1, r2) * 0.3)
        if b > 0:
            prof = [(max(r1 - b, 1e-3), z0)]
            if self.lod0:
                prof += [(r1 - b * 0.3, z0 + b * 0.3)]
            prof += [(r1, z0 + b), (r2, z0 + h - b)]
            if self.lod0:
                prof += [(max(r2 - b * 0.3, 0), z0 + h - b * 0.3)]
            prof += [(max(r2 - b, 0), z0 + h)]
        else:
            prof = [(r1, z0), (r2, z0 + h)]
        self.revolve(prof, loc, rot, col, segs, glow, smooth, phase)

    def sphere(self, r, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), col=(1, 1, 1), segs=16, rings=None, glow=0.0, smooth=True):
        bm = bmesh.new()
        u = self.S(segs, 6); v = self.S(rings or max(4, segs // 2), 3)
        bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
        self.merge(bm, col, glow, smooth, M(loc, rot, scale), weighted=False)

    def blob(self, r, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), col=(1, 1, 1), sub=2, amp=0.18, freq=1.3,
             seed=0, flat_bottom=True, glow=0.0, smooth=True, zcut=None, vcol=True):
        """Soft lumpy rock/isle: icosphere displaced by noise; bottom flattened at z=0 (pre-transform: centre at r*scale_z)."""
        bm = bmesh.new()
        s = sub if self.lod0 else max(1, sub - 1)
        bmesh.ops.create_icosphere(bm, subdivisions=s, radius=r)
        off = Vector((seed * 7.31, seed * 3.17, seed * 5.53))
        for vt in bm.verts:
            d = vt.co.normalized()
            n = noise.noise(d * freq + off) + 0.5 * noise.noise(d * freq * 2.3 + off)
            vt.co = vt.co * (1 + amp * n)
            vt.co.x *= scale[0]; vt.co.y *= scale[1]; vt.co.z *= scale[2]
        if flat_bottom:
            zmin = min(vt.co.z for vt in bm.verts)
            cut = zcut if zcut is not None else zmin * 0.55
            for vt in bm.verts:
                vt.co.z = max(vt.co.z, cut) - cut
        self.merge(bm, col, glow, smooth, M(loc, rot), vcol=vcol, weighted=False)

    def revolve(self, prof, loc=(0, 0, 0), rot=(0, 0, 0), col=(1, 1, 1), segs=24, glow=0.0, smooth=True, phase=0.0, rfn=None, vcol=False):
        """Lathe a profile [(r, z), ...] (bottom -> top) around Z. r==0 at an end closes to a pole.
        rfn(theta, z, r) -> r lets callers wobble/facet the radius."""
        bm = bmesh.new()
        n = self.S(segs)
        rings = []
        for (r, z) in prof:
            if r <= 1e-6:
                rings.append([bm.verts.new((0, 0, z))])
            else:
                ring = []
                for i in range(n):
                    t = phase + 2 * math.pi * i / n
                    rr = rfn(t, z, r) if rfn else r
                    ring.append(bm.verts.new((rr * math.cos(t), rr * math.sin(t), z)))
                rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                for i in range(n):
                    bm.faces.new((a[0], b[i], b[(i + 1) % n]))
            elif len(b) == 1:
                for i in range(n):
                    bm.faces.new((a[i], a[(i + 1) % n], b[0]))
            else:
                for i in range(n):
                    bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
        if len(rings[0]) > 1:
            bm.faces.new(list(reversed(rings[0])))
        if len(rings[-1]) > 1:
            bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.merge(bm, col, glow, smooth, M(loc, rot), vcol=vcol)

    def prism(self, poly, z0, z1, loc=(0, 0, 0), rot=(0, 0, 0), col=(1, 1, 1), bevel=0.0, glow=0.0, smooth=True):
        """Extrude a 2D polygon [(x, y), ...] (any winding) from z0 to z1."""
        bm = bmesh.new()
        b = [bm.verts.new((x, y, z0)) for x, y in poly]
        t = [bm.verts.new((x, y, z1)) for x, y in poly]
        n = len(poly)
        bm.faces.new(b); bm.faces.new(t)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((b[i], b[j], t[j], t[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self._bevel(bm, bevel, only_sharp=math.radians(35))
        self.merge(bm, col, glow, smooth, M(loc, rot))

    def sweep(self, path, section, loc=(0, 0, 0), rot=(0, 0, 0), col=(1, 1, 1), scale=None, closed=False, glow=0.0, smooth=True, up=(0, 0, 1), vcol=False):
        """Sweep a closed 2D section [(u, v), ...] along a 3D path; u along the side axis, v along 'up'.
        scale(i, t) -> (su, sv) tapers. Ends are capped unless closed."""
        bm = bmesh.new()
        P = [Vector(p) for p in path]
        m = len(P)
        UP = Vector(up)
        rings = []
        for i, p in enumerate(P):
            if closed:
                tng = (P[(i + 1) % m] - P[i - 1])
            else:
                tng = (P[min(i + 1, m - 1)] - P[max(i - 1, 0)])
            tng.normalize()
            side = tng.cross(UP)
            if side.length < 1e-6:
                side = tng.cross(Vector((1, 0, 0)))
            side.normalize()
            upv = side.cross(tng).normalized()
            su, sv = scale(i, i / max(1, m - 1)) if scale else (1, 1)
            rings.append([bm.verts.new(p + side * (u * su) + upv * (v * sv)) for u, v in section])
        k = len(section)
        segs = m if closed else m - 1
        for i in range(segs):
            a, b2 = rings[i], rings[(i + 1) % m]
            for j in range(k):
                bm.faces.new((a[j], a[(j + 1) % k], b2[(j + 1) % k], b2[j]))
        if not closed:
            bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.merge(bm, col, glow, smooth, M(loc, rot), vcol=vcol)

    def slab(self, nx, ny, sx, sy, hfn, base_z=-0.5, loc=(0, 0, 0), rot=(0, 0, 0), col=(1, 1, 1), glow=0.0, smooth=True, xyfn=None, vcol=True):
        """Closed heightfield block: top z = hfn(x, y), flat bottom at base_z, vertical skirts.
        xyfn(x, y) -> (x, y) can bend the grid (arcs)."""
        bm = bmesh.new()
        nx = max(2, self.S(nx, 2)); ny = max(2, self.S(ny, 2))
        top, bot = {}, {}
        for i in range(nx + 1):
            for j in range(ny + 1):
                x = -sx / 2 + sx * i / nx; y = -sy / 2 + sy * j / ny
                X, Y = xyfn(x, y) if xyfn else (x, y)
                top[i, j] = bm.verts.new((X, Y, hfn(x, y)))
                if i in (0, nx) or j in (0, ny):
                    bot[i, j] = bm.verts.new((X, Y, base_z))
        for i in range(nx):
            for j in range(ny):
                bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]))
        border = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)]
        for k in range(len(border)):
            a, b2 = border[k], border[(k + 1) % len(border)]
            bm.faces.new((top[a], bot[a], bot[b2], top[b2]))
        bm.faces.new([bot[a] for a in border][::-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        self.merge(bm, col, glow, smooth, M(loc, rot), vcol=vcol)

    # ---- finish into an object
    def finish(self, obj_name, mat, sharp_deg=50.0, origin=None):
        bm = self.bm
        if origin is not None:
            bmesh.ops.translate(bm, vec=-Vector(origin), verts=bm.verts)
        # no global weld: parts are separate closed shells, and welding touching parts would make non-manifold edges
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
        bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(obj_name)
        wn_idx = [v.index for v in bm.verts if v[self.wn]]
        bm.to_mesh(me)
        glow = [f[self.glow] for f in bm.faces]
        bm.free()
        for nm in ('wn', 'glow'):
            if nm in me.attributes:
                me.attributes.remove(me.attributes[nm])
        add_uvs(me, glow)
        me.materials.append(mat)
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))
        ob = bpy.data.objects.new(obj_name, me)
        bpy.context.scene.collection.objects.link(ob)
        if origin is not None:
            ob.location = origin
        vg = ob.vertex_groups.new(name='wn'); vg.add(wn_idx, 1.0, 'REPLACE')
        mod = ob.modifiers.new('wn', 'WEIGHTED_NORMAL'); mod.keep_sharp = True; mod.weight = 50; mod.mode = 'FACE_AREA'
        mod.vertex_group = 'wn'
        apply_mods(ob)
        ob.vertex_groups.clear()
        return ob


def add_uvs(me, glow_per_face, uv0=None):
    """UV0/UV1 zero (rigid), UV2.x = glow. uv0: optional per-loop list for cards."""
    for nm in ('UV0', 'UV1', 'UV2'):
        me.uv_layers.new(name=nm)
    u2 = me.uv_layers['UV2'].data
    for p in me.polygons:
        g = glow_per_face[p.index] if glow_per_face else 0.0
        for li in p.loop_indices:
            u2[li].uv = (g, 0.0)
    if uv0:
        d = me.uv_layers['UV0'].data
        for i, uv in enumerate(uv0):
            d[i].uv = uv


def apply_mods(ob):
    vl = bpy.context.view_layer
    for o in vl.objects:
        o.select_set(False)
    vl.objects.active = ob; ob.select_set(True)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


# ---------------------------------------------------------------- FX cards (open quads with real UVs)
class Cards:
    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.float_color.new('Col')
        self.uv = self.bm.loops.layers.uv.new('UV0')

    def strip(self, pts, widths, col, alpha=(1, 1), normal_up=(0, 0, 1), vrep=1.0, side=None):
        """Ribbon along pts (list of Vector), width per point; side vector default = tangent x up. UV v runs along."""
        P = [Vector(p) for p in pts]
        n = len(P)
        L = [0.0]
        for a, b in zip(P, P[1:]):
            L.append(L[-1] + (b - a).length)
        prev = None
        rows = []
        for i, p in enumerate(P):
            t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)]).normalized()
            s = Vector(side) if side is not None else t.cross(Vector(normal_up))
            s.normalize()
            w = widths[i] if isinstance(widths, (list, tuple)) else widths
            rows.append((self.bm.verts.new(p - s * w / 2), self.bm.verts.new(p + s * w / 2)))
        for i in range(n - 1):
            a0, a1 = rows[i]; b0, b1 = rows[i + 1]
            f = self.bm.faces.new((a0, a1, b1, b0))
            vv = (L[i] / L[-1] * vrep, L[i + 1] / L[-1] * vrep)
            uvs = ((0, vv[0]), (1, vv[0]), (1, vv[1]), (0, vv[1]))
            al = (alpha[0] + (alpha[1] - alpha[0]) * i / (n - 1), alpha[0] + (alpha[1] - alpha[0]) * (i + 1) / (n - 1))
            for l, uv, a in zip(f.loops, uvs, (al[0], al[0], al[1], al[1])):
                l[self.uv].uv = uv
                l[self.col] = (*col[:3], a)

    def finish(self, obj_name, mat, origin=None):
        me = bpy.data.meshes.new(obj_name)
        if origin is not None:
            bmesh.ops.translate(self.bm, vec=-Vector(origin), verts=self.bm.verts)
        bmesh.ops.triangulate(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me); self.bm.free()
        me.uv_layers['UV0'].name = 'UV0'
        me.uv_layers.new(name='UV1'); me.uv_layers.new(name='UV2')
        me.materials.append(mat)
        ob = bpy.data.objects.new(obj_name, me)
        bpy.context.scene.collection.objects.link(ob)
        if origin is not None:
            ob.location = origin
        return ob


# ---------------------------------------------------------------- materials (Blender preview; Unity assigns its own)
def body_material(name, rough=0.55, coat=0.25):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nd = nt.nodes
    bsdf = next(n for n in nd if n.type == 'BSDF_PRINCIPLED')
    vc = nd.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    uv = nd.new('ShaderNodeUVMap'); uv.uv_map = 'UV2'
    sep = nd.new('ShaderNodeSeparateXYZ')
    nt.links.new(uv.outputs['UV'], sep.inputs[0])
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Emission Color'])
    mul = nd.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 1.6
    nt.links.new(sep.outputs['X'], mul.inputs[0])
    nt.links.new(mul.outputs[0], bsdf.inputs['Emission Strength'])
    bsdf.inputs['Roughness'].default_value = rough
    if 'Coat Weight' in bsdf.inputs:
        bsdf.inputs['Coat Weight'].default_value = coat
        bsdf.inputs['Coat Roughness'].default_value = 0.35
    return m


def fx_material(name, emit=0.6):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nd = nt.nodes
    bsdf = next(n for n in nd if n.type == 'BSDF_PRINCIPLED')
    vc = nd.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(vc.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = emit
    nt.links.new(vc.outputs['Alpha'], bsdf.inputs['Alpha'])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    m.use_backface_culling = False
    return m


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ---------------------------------------------------------------- palettes (sRGB hex, converted on use)
P = {k: lin(v) for k, v in dict(
    white='#f4f1ea', cream='#e9dcc0', limestone='#d9ccae', stone='#b9b0a0', stone_dk='#8d8476', red='#d23b30', red_dk='#a72a24',
    roof_red='#c4553a', terracotta='#c87850', wood='#9a6a3e', wood_dk='#6e4a2c', wood_lt='#c49766', thatch='#c9a25e', thatch_dk='#9c7a40',
    grass='#5fae3a', grass_dk='#3f8a2c', moss='#6f9a3a', leaf='#3f8f3a', leaf_lt='#79c24a', glass='#2d4a6a', window='#ffd27a',
    brick='#b4523a', brick_dk='#8e3c2c', iron='#3b3f46', rope='#c9ad7a', snow='#f5f8ff', snow_sh='#cfdcf2', ice='#bfe6f5',
    sand='#ecd9a8', sand_wet='#cdb582', sea='#2fb8c8', foam='#ffffff', sandstone='#d0703e', sandstone_lt='#e79a5c', sandstone_dk='#a5502e',
    basalt='#3a3340', basalt_lt='#57505e', obsidian='#221d2a', lava='#ff8a1e', lava_hot='#ffd04a', ember='#ff5a1e', ash='#7d7680',
    blacksand='#2d2a30', purple='#5a3d6e', purple_dk='#3d2a4e', teal='#3aa79a', gold='#e0b04a', tulip_r='#e8443a', tulip_y='#f5c83a',
    tulip_p='#ee77a8', flower_w='#f6f2e8', cactus='#4f8f3c', jungle_stone='#a49a7a', jungle_moss='#5f8a3a', blossom='#f4a7c4',
).items()}

"""hero_gen.py — the ideal hero, built entirely from code.

  Blender -b --factory-startup --python hero_gen.py -- sex=male out=<dir> [kit=white,navy,coral] [cap=1] [views=front,q,side,back] [res=900x1500] [game=1]

Everything is parametric (PRESET): one body generator makes both sexes, garments are their own lofted meshes (never the body pushed
out), the foot lives inside the shoe, and every colour zone is a material slot (primary / secondary / accent / skin / hair).
Metres, Z up, the hero faces -Y.
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

ARGS = dict(a.split('=', 1) for a in sys.argv[sys.argv.index('--') + 1:] if '=' in a) if '--' in sys.argv else {}
SEX = ARGS.get('sex', 'male'); OUT = ARGS.get('out', '.'); os.makedirs(OUT, exist_ok=True)
FEMALE = SEX == 'female'

def hexc(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4) for x in c) + (1,)

KIT = (ARGS.get('kit') or 'F2F0EA,22305A,E8505B').split(',')
COL = dict(primary=hexc(KIT[0]), secondary=hexc(KIT[1]), accent=hexc(KIT[2]), skin=hexc(ARGS.get('skin', 'B8733F' if not FEMALE else 'A8663A')),
           hair=hexc('1E120C'), white=hexc('F4F2EC'), sole=hexc('F0EEE8'), dark=hexc('1B1412'), iris=hexc('4A2E1C'), lip=hexc('9A4A3C'))

# ----------------------------------------------------------------------------------------------------------------- preset
P = dict(height=1.71, head=(.124, .132, .143), head_z=1.567, neck_r=.056,
         shoulder_x=.200, shoulder_z=1.330, shoulder_r=.070, arm_angle=27,
         upper=.250, fore=.235, arm_r=(.066, .062, .047, .054, .037), hand=1.22,
         torso=[(.790, .150, .110), (.860, .176, .122), (.960, .160, .114), (1.060, .152, .110), (1.180, .176, .122), (1.270, .192, .130), (1.335, .172, .112), (1.380, .098, .080)],
         hip_x=.094, hip_z=.850, knee_z=.480, ankle_z=.105, leg_r=(.100, .090, .064, .070, .039),
         eye=1.0)
if FEMALE:
    P.update(height=1.65, head=(.121, .129, .140), head_z=1.510, neck_r=.047,
             shoulder_x=.172, shoulder_z=1.280, shoulder_r=.058, arm_angle=26,
             upper=.238, fore=.224, arm_r=(.053, .050, .039, .044, .031), hand=1.10,
             torso=[(.765, .146, .108), (.835, .174, .122), (.920, .150, .108), (1.010, .126, .096), (1.120, .144, .108), (1.215, .160, .118), (1.285, .146, .100), (1.330, .086, .070)],
             hip_x=.090, hip_z=.825, knee_z=.465, ankle_z=.100, leg_r=(.090, .080, .056, .061, .035),
             eye=1.12)
HX, HY, HZ = P['head']; HC = Vector((0, 0, P['head_z']))

# ----------------------------------------------------------------------------------------------------------------- geometry helpers
def frame(t, ref=Vector((0, 1, 0))):
    t = t.normalized()
    if abs(t.dot(ref)) > .95: ref = Vector((1, 0, 0))
    u = t.cross(ref).normalized(); v = u.cross(t).normalized()
    return u, v

def tube(bm, pts, radii, segs=28, cap0=True, cap1=True, mat=0, fn=None, ref=Vector((0, 1, 0)), matfn=None):
    """Loft rings along pts. radii: float or (ru, rv) per point (ru lateral, rv front-back). fn(theta, i) scales the radius."""
    pts = [Vector(p) for p in pts]; rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        u, v = frame(t, ref); r = radii[i]; ru, rv = (r, r) if isinstance(r, (int, float)) else r
        ring = []
        for k in range(segs):
            th = 2 * math.pi * k / segs; s = fn(th, i) if fn else 1
            ring.append(bm.verts.new(p + u * (ru * math.cos(th) * s) + v * (rv * math.sin(th) * s)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(segs):
            f = bm.faces.new((rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs], rings[i + 1][k]))
            f.material_index = matfn(i, k) if matfn else mat; f.smooth = True
    for cap, ring, p in ((cap0, rings[0], pts[0]), (cap1, rings[-1], pts[-1])):
        if cap:
            c = bm.verts.new(p)
            for k in range(segs):
                f = bm.faces.new((c, ring[k], ring[(k + 1) % segs])); f.material_index = mat; f.smooth = True
    return rings

def ellipsoid(bm, c, r, mat=0, rot=None, segs=24):
    geo = bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=segs // 2, radius=1)
    m = Matrix.Translation(Vector(c)) @ (rot.to_4x4() if rot else Matrix.Identity(4)) @ Matrix.Diagonal((r[0], r[1], r[2], 1))
    for v in geo['verts']: v.co = m @ v.co
    for f in {f for v in geo['verts'] for f in v.link_faces}: f.material_index = mat; f.smooth = True
    return geo['verts']

def torus(bm, c, rx, ry, r, mat=0, n=28, m=10, tilt=0.0):
    """A ring in the XY plane (rx, ry) around c, tube radius r; tilt raises the back (+Y)."""
    rings = []
    for i in range(n):
        a = 2 * math.pi * i / n; ca, sa = math.cos(a), math.sin(a); p = Vector((c[0] + rx * ca, c[1] + ry * sa, c[2] + tilt * sa)); out = Vector((ca, sa, 0))
        rings.append([bm.verts.new(p + out * (r * math.cos(b)) + Vector((0, 0, r * math.sin(b)))) for b in (2 * math.pi * j / m for j in range(m))])
    for i in range(n):
        for j in range(m):
            f = bm.faces.new((rings[i][j], rings[(i + 1) % n][j], rings[(i + 1) % n][(j + 1) % m], rings[i][(j + 1) % m])); f.material_index = mat; f.smooth = True

def obj(name, bm, mats, parent=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for m in mats: me.materials.append(m)
    if parent: ob.parent = parent
    return ob

def bake(ob):
    """Apply the modifier stack."""
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data; ob.modifiers.clear(); ob.data = me; bpy.data.meshes.remove(old)
    for p in me.polygons: p.use_smooth = True
    return ob

def lerp(a, b, t): return a + (b - a) * t
def sstep(a, b, x):
    t = max(0, min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t)

# ----------------------------------------------------------------------------------------------------------------- materials
MATS = {}
def mat(name, color, rough=.6, sss=0, sheen=0, coat=0, bump=0, bump_scale=900, emit=0, spec=.5):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = color; b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = spec
    if sss: b.inputs['Subsurface Weight'].default_value = sss; b.inputs['Subsurface Radius'].default_value = (.9, .35, .2); b.inputs['Subsurface Scale'].default_value = .012
    if sheen: b.inputs['Sheen Weight'].default_value = sheen; b.inputs['Sheen Roughness'].default_value = .5
    if coat: b.inputs['Coat Weight'].default_value = coat; b.inputs['Coat Roughness'].default_value = .2
    if emit: b.inputs['Emission Color'].default_value = color; b.inputs['Emission Strength'].default_value = emit
    if bump:
        tc = nt.nodes.new('ShaderNodeTexCoord'); n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = bump_scale; n.inputs['Detail'].default_value = 2
        bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = bump; bp.inputs['Distance'].default_value = .002
        nt.links.new(tc.outputs['Object'], n.inputs['Vector']); nt.links.new(n.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    MATS[name] = m; return m

def skin_mat():
    m = mat('Skin', COL['skin'], rough=.52, sss=.22, spec=.35); nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_name = 'blush'
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    c = COL['skin']; mix.inputs['A'].default_value = c; mix.inputs['B'].default_value = (min(1, c[0] * 1.18), c[1] * .62, c[2] * .58, 1)
    nt.links.new(at.outputs['Fac'], mix.inputs['Factor']); nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    return m

# ----------------------------------------------------------------------------------------------------------------- body
def limb_points(side):
    a = math.radians(P['arm_angle']); d = Vector((side * math.sin(a), 0, -math.cos(a)))
    S = Vector((side * P['shoulder_x'], 0, P['shoulder_z'])); E = S + d * P['upper']; W = E + d * P['fore']
    H = Vector((side * P['hip_x'], 0, P['hip_z'])); K = Vector((side * (P['hip_x'] + .004), -.006, P['knee_z'])); A = Vector((side * (P['hip_x'] + .004), .008, P['ankle_z']))
    return S, E, W, d, H, K, A

def leg_radius(z):
    """Leg radius at height z (shared with socks and shorts)."""
    r = P['leg_r']; H, K, A = P['hip_z'], P['knee_z'], P['ankle_z']
    if z >= K:
        t = (H - z) / (H - K); return lerp(lerp(r[0], r[1], sstep(0, .55, t)), r[2], sstep(.55, 1, t))
    t = (K - z) / (K - A); return lerp(lerp(r[2], r[3], sstep(0, .3, t)), r[4], sstep(.3, 1, t))

def build_body(root):
    bm = bmesh.new()
    # torso: one loft, closed
    tz = P['torso']; pts = [(0, 0, z) for z, _, _ in tz]; rad = [(rx, ry) for _, rx, ry in tz]
    pts = [(0, 0, tz[0][0] - .035)] + pts + [(0, 0, tz[-1][0] + .02)]; rad = [(tz[0][1] * .55, tz[0][2] * .6)] + rad + [(P['neck_r'] * 1.2, P['neck_r'] * 1.15)]
    tube(bm, pts, rad, segs=36, ref=Vector((0, 1, 0)))
    # neck + head (skull, jaw/cheeks, ears, nose)
    tube(bm, [(0, .004, tz[-1][0] - .01), (0, .0, HC.z - HZ * .55)], [P['neck_r'] * 1.08, P['neck_r']], segs=24)
    ellipsoid(bm, HC, (HX, HY, HZ), segs=40)
    ellipsoid(bm, HC + Vector((0, -.008, -HZ * .40)), (HX * .88, HY * .88, HZ * .70), segs=32)          # cheeks and jaw: a soft, wide lower face
    ellipsoid(bm, HC + Vector((0, -.018, -HZ * .90)), (HX * .46, HY * .46, HZ * .22), segs=20)          # chin
    for s in (-1, 1):
        ellipsoid(bm, HC + Vector((s * (HX - .001), .014, -.022)), (.011, .022, .030), segs=16, rot=Matrix.Rotation(math.radians(-12 * s), 3, 'Z'))
    ellipsoid(bm, HC + Vector((0, -HY * .975, -.034)), (.0160, .016, .0125), segs=16)                     # nose: one soft bump
    for s in (-1, 1):
        S, E, W, d, H, K, A = limb_points(s); r = P['arm_r']
        ellipsoid(bm, S, (P['shoulder_r'],) * 3, segs=24)
        # arm: shoulder -> biceps -> elbow -> forearm belly -> wrist
        ap = [S - d * .02, S + d * (P['upper'] * .40), E - d * .03, E, E + d * (P['fore'] * .28), W - d * .03, W]
        ar = [r[0], r[1], lerp(r[1], r[2], .75), r[2], r[3], lerp(r[3], r[4], .8), r[4]]
        tube(bm, ap, [(x, x * .92) for x in ar], segs=24)
        # hand: palm, four fingers and a thumb, slightly oversized (they fuse into one soft shape at the remesh)
        hs = P['hand']; n = Matrix.Rotation(s * math.radians(-38), 3, d) @ Vector((0, -1, 0)); side_out = d.cross(n).normalized() * s   # across the palm, thumb side = forward (-Y)
        palm = W + d * (.048 * hs)
        pm = Matrix((n.cross(d).normalized(), n, d)).transposed(); ellipsoid(bm, palm, (.017 * hs, .042 * hs, .046 * hs), segs=20, rot=pm)
        for j, off in enumerate((-.0285, -.0095, .0095, .0285)):
            fd = (d + n * (-off * 5.5)).normalized(); f0 = palm + d * (.036 * hs) + n * (off * hs * -1); ln = (.052, .060, .056, .044)[j] * hs
            tube(bm, [f0, f0 + fd * ln * .5, f0 + fd * ln], [.0118 * hs, .0114 * hs, .0104 * hs], segs=12)
            ellipsoid(bm, f0 + fd * ln, (.0104 * hs,) * 3, segs=10)
        t0 = palm + n * (.030 * hs) - d * (.010 * hs); td = (d * .75 + n * .65).normalized()
        tube(bm, [t0, t0 + td * (.030 * hs), t0 + td * (.056 * hs)], [.014 * hs, .0125 * hs, .0105 * hs], segs=12)
        ellipsoid(bm, t0 + td * (.056 * hs), (.0105 * hs,) * 3, segs=10)
        # leg: hip -> thigh -> knee -> calf -> ankle (the foot itself is the shoe's job)
        lz = [P['hip_z'] + .075, P['hip_z'] - .06, lerp(P['hip_z'], P['knee_z'], .6), P['knee_z'] + .03, P['knee_z'], P['knee_z'] - .10, lerp(P['knee_z'], P['ankle_z'], .62), P['ankle_z'] + .03, P['ankle_z'] - .04]
        lp = []
        for z in lz:
            t = (P['hip_z'] - z) / (P['hip_z'] - P['ankle_z']); x = lerp(H.x, A.x, max(0, min(1, t))); y = -.012 * math.sin(max(0, min(1, t)) * math.pi) + .008 * max(0, t - .6)
            cy = .018 * sstep(.62, .8, t) * (1 - sstep(.8, 1, t))                                          # the calf sits back
            lp.append((x, y + cy, z))
        tube(bm, lp, [(leg_radius(z), leg_radius(z) * (1.0 if z > P['knee_z'] else .96)) for z in lz], segs=28, fn=None)
    ob = obj('Body', bm, [skin_mat()], root)
    rm = ob.modifiers.new('remesh', 'REMESH'); rm.mode = 'VOXEL'; rm.voxel_size = .0042; rm.use_smooth_shade = True
    bake(ob)
    vg = ob.vertex_groups.new(name='soft'); wrists = [limb_points(s)[2] for s in (-1, 1)]; dirs = [limb_points(s)[3] for s in (-1, 1)]
    for v in ob.data.vertices:
        w = 1.0
        for W, d in zip(wrists, dirs):
            t = (v.co - W).dot(d)
            if t > -.02 and (v.co - W).length < .22: w = min(w, lerp(1.0, .22, sstep(-.02, .03, t)))
        if (v.co - HC).length < HZ * 1.15 and v.co.y < 0: w = min(w, .55)                                   # keep the nose and chin
        vg.add([v.index], w, 'REPLACE')
    sm = ob.modifiers.new('smooth', 'SMOOTH'); sm.factor = .6; sm.iterations = 16; sm.vertex_group = 'soft'
    bake(ob)
    # blush: cheeks, nose tip, a touch on ears, knees and elbows
    me = ob.data; at = me.attributes.new('blush', 'FLOAT', 'POINT'); spots = []
    for s in (-1, 1):
        S, E, W, d, H, K, A = limb_points(s)
        spots += [(HC + Vector((s * HX * .58, -HY * .80, -HZ * .30)), .034, .36), (HC + Vector((s * HX, .012, -.012)), .03, .30), (E, .05, .22), (Vector((K.x, K.y - .05, K.z)), .06, .22)]
    spots.append((HC + Vector((0, -HY * 1.05, -.030)), .022, .12))
    for i, v in enumerate(me.vertices):
        w = 0
        for c, r, a in spots: w = max(w, a * math.exp(-((v.co - c).length / r) ** 2))
        at.data[i].value = w
    return ob

def head_y(x, z):
    """Front surface of the head (the more forward of skull and lower face) at (x, z)."""
    best = 0
    for c, r in ((HC, (HX, HY, HZ)), (HC + Vector((0, -.008, -HZ * .40)), (HX * .88, HY * .88, HZ * .70))):
        q = 1 - (x / r[0]) ** 2 - ((z - c.z) / r[2]) ** 2
        if q > 0: best = min(best, c.y - r[1] * math.sqrt(q))
    return best

def build_face(root):
    e = P['eye'] * 1.12; ez = HC.z - .014; ex = HX * .40
    bm = bmesh.new()
    for s in (-1, 1):
        y = head_y(s * ex, ez)
        tilt = Matrix.Rotation(math.radians(s * 16), 3, 'Z')
        ellipsoid(bm, (s * ex, y + .0075, ez), (.0205 * e, .012, .0255 * e), mat=0, rot=tilt, segs=24)           # eye white
        ellipsoid(bm, (s * ex * .97, y - .0010, ez - .002 * e), (.0128 * e, .006, .0150 * e), mat=1, rot=tilt, segs=20)  # iris
        ellipsoid(bm, (s * ex * .97, y - .0050, ez - .002 * e), (.0070 * e, .003, .0084 * e), mat=2, rot=tilt, segs=16)  # pupil
        ellipsoid(bm, (s * ex * .97 - .0050 * e, y - .0068, ez + .0050 * e), (.0034 * e, .0016, .0034 * e), mat=3, segs=10)  # catchlight
        # upper lid line (lashes for her), following the eye's top edge
        lid = []
        for k in range(9):
            a = math.radians(lerp(205, -25, k / 8)); px = s * ex + s * math.cos(a) * .0215 * e * -1; pz = ez + math.sin(a) * .0245 * e * 0 + .0245 * e * math.sin(math.radians(lerp(20, 160, k / 8)))
            lid.append((px, head_y(px, pz) - .0015 + .010 * (1 - math.sin(math.radians(lerp(0, 180, k / 8)))), pz))
        tube(bm, lid, [.0010] + [.0024 if FEMALE else .0019] * 7 + [.0010], segs=8, mat=2)
        if FEMALE:
            tip = Vector(lid[0 if s > 0 else -1]); out = Vector((s * .010, .002, .006))
            tube(bm, [tip, tip + out], [.0022, .0006], segs=8, mat=2)
        # brow: a soft arc
        bz = ez + (.047 if not FEMALE else .050) * (.9 + .1 * e); br = []
        for k in range(7):
            t = k / 6; px = s * lerp(ex - .024, ex + .030, t); pz = bz + .007 * math.sin(t * math.pi) - .004 * t
            br.append((px, head_y(px, pz) - .002, pz))
        w = (.0070, .0042) if not FEMALE else (.0044, .0030)
        tube(bm, br, [(w[0] * (.55 + .45 * math.sin(max(.12, t / 6) * math.pi)), w[1]) for t in range(7)], segs=10, mat=4, ref=Vector((0, 0, 1)))
    # mouth: a gentle closed smile
    mz = HC.z - HZ * .62; mo = []
    for k in range(11):
        t = k / 10; px = lerp(-.030, .030, t); pz = mz - .0075 * math.sin(t * math.pi) + .003
        mo.append((px, head_y(px, pz) - .0012, pz))
    tube(bm, mo, [.0012] + [.0030] * 9 + [.0012], segs=8, mat=5)
    return obj('Face', bm, [mat('EyeWhite', COL['white'], rough=.25, spec=.6), mat('Iris', COL['iris'], rough=.3), mat('Pupil', COL['dark'], rough=.3),
                            mat('Catch', (1, 1, 1, 1), emit=1.5), mat('Brow', COL['hair'], rough=.7), mat('Mouth', COL['lip'], rough=.6)], root)

def hairline(x, y):
    """Height of the hairline around the head (forehead high, dips to a sideburn, low at the nape)."""
    f = lerp(HC.z + HZ * (.60 + .08 * math.cos(min(1.5, abs(x) / HX * 1.5))), HC.z + .014, sstep(-HY * .95, -.005, y)); b = lerp(HC.z + .018, HC.z - HZ * (.50 if not FEMALE else .56), sstep(0, HY, y))
    z = f if y < 0 else b
    return z - .020 * math.exp(-((y + .012) / .028) ** 2) * (1 if abs(x) > HX * .7 else 0)

def build_hair(root, cap=False):
    bm = bmesh.new(); vs = ellipsoid(bm, HC, (1, 1, 1), segs=128)
    for v in vs:
        n = (v.co - HC); p = HC + Vector((n.x * HX, n.y * HY, n.z * HZ)); hl = hairline(p.x, p.y)
        grow = sstep(0, .035, p.z - hl); lift = .0015 + .0135 * grow + .006 * sstep(.2, 1, n.z) * (1 if not FEMALE else .6)
        if not FEMALE: lift += .010 * math.exp(-((n.y + .78) / .30) ** 2) * sstep(.25, .8, n.z)          # a little front lift
        nn = Vector((n.x / HX, n.y / HY, n.z / HZ)).normalized()
        v.co = p + nn * lerp(-.008, lift, sstep(-.006, .006, p.z - hl))
    if FEMALE:
        knot = HC + Vector((0, HY * .86, HZ * .62))
        ellipsoid(bm, knot, (.030, .026, .030), mat=1, segs=16)                                             # hair tie
        tail = [knot + Vector((0, .010, .010)), knot + Vector((0, .070, .030)), knot + Vector((0, .125, -.040)), knot + Vector((0, .135, -.140)), knot + Vector((0, .112, -.235)), knot + Vector((0, .090, -.290))]
        tube(bm, tail, [(.024, .022), (.040, .034), (.050, .040), (.046, .036), (.032, .026), (.008, .008)], segs=20)
    return obj('Hair', bm, [mat('Hair', COL['hair'], rough=.42, spec=.45), mat('Accent', COL['accent'], rough=.7)], root)

def build_cap(root):
    bm = bmesh.new(); vs = ellipsoid(bm, HC + Vector((0, 0, .004)), (HX + .020, HY + .020, HZ + .020), segs=48)
    cut = HC.z + HZ * .18
    for v in vs: v.tag = v.co.z < cut + .020 * (v.co.y / HY)
    bmesh.ops.delete(bm, geom=[v for v in vs if v.tag], context='VERTS')
    for f in bm.faces: f.material_index = 0
    brim = ellipsoid(bm, (0, -HY - .060, cut - .016), (HX * .92, .082, .0065), mat=1, rot=Matrix.Rotation(math.radians(-10), 3, 'X'), segs=32)
    ellipsoid(bm, HC + Vector((0, 0, HZ + .022)), (.011, .011, .006), mat=1, segs=12)
    ob = obj('Cap', bm, [mat('Primary', COL['primary'], rough=.8, sheen=.3, bump=.25), mat('Secondary', COL['secondary'], rough=.8, sheen=.3, bump=.25)], root)
    so = ob.modifiers.new('solid', 'SOLIDIFY'); so.thickness = .004; so.offset = 1
    return bake(ob)

# ----------------------------------------------------------------------------------------------------------------- garments
def fabric(slot): return mat(slot.capitalize(), COL[slot], rough=.85, sheen=.06, bump=.20, bump_scale=1100, spec=.22)

def finish(ob, thick=.0035, sub=1):
    so = ob.modifiers.new('solid', 'SOLIDIFY'); so.thickness = thick; so.offset = 1
    if sub: ss = ob.modifiers.new('sub', 'SUBSURF'); ss.levels = sub; ss.render_levels = sub
    return bake(ob)

def build_top(root):
    """A polo cut as its own garment: body tube with a straight hem, set-in sleeves (or bound armholes), a collar leaf and a placket."""
    tz = P['torso']; ztop = tz[-1][0]; zc = tz[5][0]; zw = tz[3][0]; zh = tz[1][0]; hem = zh - .012 if not FEMALE else tz[2][0] - .030
    ease = .020 if not FEMALE else .013
    sx, sz, shr = P['shoulder_x'], P['shoulder_z'], P['shoulder_r']
    st = [(hem, tz[1][1] + ease + .004, tz[1][2] + ease + .006), (lerp(hem, zw, .5), lerp(tz[1][1], tz[3][1], .5) + ease + .006, lerp(tz[1][2], tz[3][2], .5) + ease + .008),
          (zw, tz[3][1] + ease + .004, tz[3][2] + ease + .006), (tz[4][0], tz[4][1] + ease, tz[4][2] + ease), (zc, tz[5][1] + ease + .004, tz[5][2] + ease),
          (sz + .004, sx + shr * .18, tz[6][2] + ease + .004), (sz + shr * .62, sx - .022, tz[6][2] + ease - .010), (sz + shr * .98, sx * .62, tz[7][2] + .020),
          (ztop + .034, P['neck_r'] + .022, P['neck_r'] + .022), (ztop + .046, P['neck_r'] + .010, P['neck_r'] + .012)]
    bm = bmesh.new()
    tube(bm, [(0, 0, z) for z, _, _ in st], [(rx, ry) for _, rx, ry in st], segs=40, cap0=False, cap1=False, mat=0)
    for s in (-1, 1):
        S, E, W, d, H, K, A = limb_points(s); r = P['arm_r']
        if True:
            L = P['upper'] * (.52 if not FEMALE else .36); sp = [S - d * .070, S - d * .01, S + d * (L * .50), S + d * L]
            sr = [P['shoulder_r'] - .006, P['shoulder_r'] + .011, r[1] + .018, r[1] + .019]
            tube(bm, sp, [(x, x * .95) for x in sr], segs=28, cap0=True, cap1=False, mat=0)
            tube(bm, [S + d * (L - .022), S + d * (L + .002)], [r[1] + .0215, r[1] + .0215], segs=28, cap0=False, cap1=False, mat=2)   # cuff band, accent
    ob = finish(obj('Top', bm, [fabric('primary'), fabric('secondary'), fabric('accent')], root))
    # collar: two leaves that meet at the back and open at the front, in the secondary colour
    bm = bmesh.new(); nz = ztop + .040; segs = 44; rings = []
    prof = [(P['neck_r'] + .009, nz + .016, 0), (P['neck_r'] + .016, nz + .024, 0), (P['neck_r'] + .040, nz + .004, .010), (P['neck_r'] + .050, nz - .014, .014)]
    for r0, z0, fwd in prof:
        ring = []
        for k in range(segs + 1):
            a = lerp(math.radians(-90 + 22), math.radians(270 - 22), k / segs)                             # gap at the front (-Y)
            front = max(0, -math.sin(a)); ring.append(bm.verts.new((r0 * 1.05 * math.cos(a), r0 * math.sin(a) - fwd * front * 2.2, z0 - .020 * front * (r0 - P['neck_r']) / .06)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(segs):
            f = bm.faces.new((rings[i][k], rings[i][k + 1], rings[i + 1][k + 1], rings[i + 1][k])); f.smooth = True
    col = finish(obj('Collar', bm, [fabric('secondary')], root), thick=.004)
    # placket + two buttons + crest
    def at(z, j):
        for a, b in zip(st, st[1:]):
            if a[0] <= z <= b[0]: return lerp(a[j], b[j], (z - a[0]) / (b[0] - a[0]))
        return st[-1][j] if z > st[-1][0] else st[0][j]
    bm = bmesh.new(); py = lambda z: -at(z, 2) - .0050
    zt = sz + shr * .80; zb = zt - .115
    for k in range(6):
        z0 = lerp(zt, zb, k / 6); z1 = lerp(zt, zb, (k + 1) / 6)
        v = [bm.verts.new((-.015, py(z0), z0)), bm.verts.new((.015, py(z0), z0)), bm.verts.new((.015, py(z1), z1)), bm.verts.new((-.015, py(z1), z1))]
        bm.faces.new(v).material_index = 0
    for z in (zt - .030, zt - .072): ellipsoid(bm, (0, py(z) - .003, z), (.0060, .0022, .0060), mat=1, segs=12)
    cz = zc + .004; cx = P['shoulder_x'] * .50; cy = -at(cz, 2) * math.sqrt(max(.05, 1 - (cx / at(cz, 1)) ** 2)) - .0085
    ellipsoid(bm, (cx, cy, cz), (.024, .0030, .024), mat=2, rot=Matrix.Rotation(math.radians(-18), 3, 'Z'), segs=20)
    ellipsoid(bm, (cx, cy - .0016, cz), (.0185, .0030, .0185), mat=1, rot=Matrix.Rotation(math.radians(-18), 3, 'Z'), segs=20)
    pl = finish(obj('Placket', bm, [fabric('secondary'), mat('Button', COL['white'], rough=.35), fabric('accent')], root), thick=.002, sub=0)
    return [ob, col, pl]

def build_bottom(root):
    tz = P['torso']; out = []
    if not FEMALE:
        bm = bmesh.new(); zs = [(tz[2][0] + .020, tz[2][1] + .014, tz[2][2] + .016), (tz[1][0], tz[1][1] + .016, tz[1][2] + .020), (tz[0][0] + .020, tz[0][1] + .030, tz[0][2] + .024), (tz[0][0] - .020, tz[0][1] * .8, tz[0][2] * .9), (tz[0][0] - .040, .05, .05)]
        tube(bm, [(0, 0, z) for z, _, _ in zs], [(rx, ry) for _, rx, ry in zs], segs=36, cap0=False, cap1=True, mat=0)
        for s in (-1, 1):
            S, E, W, d, H, K, A = limb_points(s); hemz = lerp(P['hip_z'], P['knee_z'], .66)
            zz = [P['hip_z'] + .010, P['hip_z'] - .06, lerp(P['hip_z'], hemz, .6), hemz]; rr = [leg_radius(P['hip_z']) + .010, leg_radius(P['hip_z'] - .06) + .014, leg_radius(zz[2]) + .018, leg_radius(hemz) + .020]
            stripe = (lambda i, k, s=s: 2 if (k in ((0, 27) if s > 0 else (13, 14))) else 0)               # a stripe down the outer seam
            tube(bm, [(H.x + s * .004, -.004, z) for z in zz], [(r, r * .98) for r in rr], segs=28, cap0=True, cap1=False, mat=0, matfn=stripe)
        out.append(finish(obj('Shorts', bm, [fabric('secondary'), fabric('primary'), fabric('accent')], root)))
    else:
        # pleated skirt: a cone whose radius zigzags, sharper toward the hem, on a flat waistband, with fitted shorts under it
        bm = bmesh.new(); zt = tz[2][0] + .010; zb = zt - .215; N = 22; segs = N * 6; rings = []
        for i in range(9):
            t = i / 8; z = lerp(zt, zb, t); rx = lerp(tz[2][1] + .012, .215, t ** .85); ry = lerp(tz[2][2] + .014, .190, t ** .85); ring = []
            for k in range(segs):
                a = 2 * math.pi * k / segs; ph = (k % 6) / 6; saw = 1 - abs(2 * ph - 1); amp = .070 * t
                ring.append(bm.verts.new((rx * (1 + amp * (saw - .5)) * math.cos(a), ry * (1 + amp * (saw - .5)) * math.sin(a), z)))
            rings.append(ring)
        for i in range(8):
            for k in range(segs):
                f = bm.faces.new((rings[i][k], rings[i][(k + 1) % segs], rings[i + 1][(k + 1) % segs], rings[i + 1][k])); f.smooth = False; f.material_index = 2 if i == 6 else 0
        sk = obj('Skirt', bm, [fabric('secondary'), fabric('primary'), fabric('primary' if KIT[0] != KIT[1] else 'accent')], root)
        so = sk.modifiers.new('solid', 'SOLIDIFY'); so.thickness = .003; so.offset = 1; bake(sk); out.append(sk)
        for p in sk.data.polygons: p.use_smooth = False
        bm = bmesh.new(); tube(bm, [(0, 0, zt + .004), (0, 0, zt - .030)], [(tz[2][1] + .0145, tz[2][2] + .0165)] * 2, segs=40, cap0=False, cap1=False)
        out.append(finish(obj('Waistband', bm, [fabric('secondary')], root), thick=.004, sub=0))
        bm = bmesh.new()
        zs = [(tz[1][0], tz[1][1] + .006, tz[1][2] + .008), (tz[0][0] + .02, tz[0][1] + .020, tz[0][2] + .012), (tz[0][0] - .02, tz[0][1] * .8, tz[0][2] * .9), (tz[0][0] - .04, .05, .05)]
        tube(bm, [(0, 0, z) for z, _, _ in zs], [(rx, ry) for _, rx, ry in zs], segs=32, cap0=False, cap1=True)
        for s in (-1, 1):
            S, E, W, d, H, K, A = limb_points(s); hemz = zb - .028; zz = [P['hip_z'] + .01, P['hip_z'] - .06, hemz]
            tube(bm, [(H.x + s * .003, -.004, z) for z in zz], [leg_radius(z) + .006 for z in zz], segs=24, cap0=True, cap1=False)
        out.append(finish(obj('UnderShorts', bm, [fabric('secondary')], root), thick=.002))
    return out

def build_feet(root):
    """Sock + a low court sneaker on a proper last: rounded toe lower than the heel, a waist, a flat cupsole with an outsole line, a heel tab."""
    out = []
    for s in (-1, 1):
        S, E, W, d, H, K, A = limb_points(s); ax = A.x; ay = A.y
        bm = bmesh.new(); zs = [.070, .110, .140, .168 if not FEMALE else .138]
        tube(bm, [(ax, ay + .004, z) for z in zs[:len(zs)]], [leg_radius(max(z, P['ankle_z'])) + .0045 for i, z in enumerate(zs)], segs=24, cap0=False, cap1=False)
        out.append(finish(obj('Sock', bm, [mat('Sock', COL['white'], rough=.9, sheen=.4, bump=.3, bump_scale=700)], root), thick=.003, sub=0))
        # last: stations heel -> toe along -Y; half-widths (medial, lateral), top height; the tip leans toward the big toe
        Lh, Lt = .082, .196; k = 1.10 if not FEMALE else .98; Lh *= k; Lt *= k
        T = [0, .08, .22, .40, .58, .72, .84, .93, .985, 1.0]
        wm = [.024, .040, .044, .040, .041, .045, .042, .033, .019, .004]; wl = [.024, .041, .046, .045, .048, .052, .048, .035, .019, .004]
        ht = [.050, .074, .086, .088, .074, .058, .048, .040, .030, .018]; sole = .030 * k
        def section(t_i, zb, zt_scale, grow=0, n=20):
            y = ay + Lh - T[t_i] * (Lh + Lt); m = (wm[t_i] + grow) * k; l = (wl[t_i] + grow) * k; top = sole + ht[t_i] * k * zt_scale
            shift = s * -.010 * sstep(.6, 1, T[t_i]) * k                                                   # toward the other foot at the toe
            ring = []
            for j in range(n):
                a = 2 * math.pi * j / n; cx = math.cos(a); sz = math.sin(a); w = m if cx * s < 0 else l
                x = ax + shift + w * cx * (1 if sz > 0 else 1.0); z = zb + (top - zb) * max(0, sz) ** .6 if sz > 0 else zb
                ring.append((x, y, z))
            return ring
        bm = bmesh.new()
        def skin_rings(rings, mat_i):
            vr = [[bm.verts.new(p) for p in r] for r in rings]; n = len(vr[0])
            for i in range(len(vr) - 1):
                for j in range(n):
                    f = bm.faces.new((vr[i][j], vr[i][(j + 1) % n], vr[i + 1][(j + 1) % n], vr[i + 1][j])); f.material_index = mat_i; f.smooth = True
            for r in (vr[0], vr[-1]):
                c = bm.verts.new(sum((v.co for v in r), Vector()) / n)
                for j in range(n): bm.faces.new((c, r[j], r[(j + 1) % n])).material_index = mat_i
        skin_rings([section(i, sole * .9, 1.0) for i in range(len(T))], 0)                                 # upper
        # cupsole: the outline swept from the ground to the sole line, slightly proud of the upper, plus the outsole line
        def slab(z0, z1, grow, mat_i):
            lo = [[(p[0], p[1], z0) for p in section(i, 0, 0, grow)] for i in range(len(T))]; hi = [[(p[0], p[1], z1) for p in section(i, 0, 0, grow)] for i in range(len(T))]
            for i in range(len(T)):
                # each station becomes a closed loop: lower half at z0, upper half at z1
                n = len(lo[i]); loop = [(lo[i][j][0], lo[i][j][1], z1 if math.sin(2 * math.pi * j / n) > 0 else z0) for j in range(n)]; lo[i] = loop
            skin_rings(lo, mat_i)
        slab(.008 * k, sole, .0035, 1); slab(0, .009 * k, .0045, 2)
        # heel tab, tongue, laces, collar roll
        hy = ay + Lh
        ellipsoid(bm, (ax, hy - .004, sole + .062 * k), (.022 * k, .010, .026 * k), mat=2, segs=14)
        ellipsoid(bm, (ax, ay - .030 * k, sole + .086 * k), (.022 * k, .034 * k, .012), mat=0, rot=Matrix.Rotation(math.radians(24), 3, 'X'), segs=14)
        for j in range(5):
            y = ay - .012 * k - j * .019 * k; z = sole + (.090 - j * .0085) * k
            tube(bm, [(ax - .021 * k, y, z - .004), (ax, y, z + .002), (ax + .021 * k, y, z - .004)], [.0028] * 3, segs=8, mat=3)
        torus(bm, (ax, ay + .008, sole + .084 * k), .044 * k, .051 * k, .0085, mat=0, tilt=.008 * k)
        sh = obj('Shoe', bm, [mat('ShoeUpper', COL['white'], rough=.42, coat=.15, spec=.5), mat('Sole', COL['sole'], rough=.55), fabric('secondary'), mat('Lace', hexc('CFCAC0'), rough=.8)], root)
        ss = sh.modifiers.new('sub', 'SUBSURF'); ss.levels = 2; ss.render_levels = 2; bake(sh); out.append(sh)
    return out

def build_wristband(root):
    S, E, W, d, H, K, A = limb_points(-1); bm = bmesh.new()
    tube(bm, [W - d * .050, W - d * .008], [P['arm_r'][4] + .009, P['arm_r'][4] + .0075], segs=20, cap0=False, cap1=False)
    return finish(obj('Wristband', bm, [mat('Sock', COL['white'], rough=.9, sheen=.4, bump=.3, bump_scale=700)], root), thick=.004, sub=1)

# ----------------------------------------------------------------------------------------------------------------- studio + render
def studio():
    sc = bpy.context.scene
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (.36, .36, .38, 1); bg.inputs[1].default_value = .42
    # sweep
    bm = bmesh.new(); prof = [(-14, 0)] + [(5 - 2.5 * math.cos(math.radians(a)), 2.5 - 2.5 * math.sin(math.radians(a))) for a in range(90, -1, -6)] + [(5, 9)]
    rows = [[bm.verts.new((x, y, z)) for (y, z) in prof] for x in (-16, 16)]
    for i in range(len(prof) - 1): bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1])).smooth = True
    obj('Sweep', bm, [mat('Sweep', (.26, .26, .28, 1), rough=.95, spec=.05, emit=.40)])
    def area(name, loc, energy, size, color=(1, 1, 1)):
        l = bpy.data.lights.new(name, 'AREA'); l.energy = energy; l.size = size; l.color = color
        o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.location = loc
        o.rotation_euler = (Vector((0, 0, 1.0)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); return o
    area('Key', (-2.6, -4.2, 3.4), 520, 3.5, (1, .97, .93)); area('Fill', (3.6, -3.2, 1.6), 170, 5, (.93, .96, 1)); area('Rim', (2.2, 3.6, 3.2), 420, 2.5); area('Top', (0, -.5, 5), 90, 4)
    cam = bpy.data.cameras.new('Cam'); co = bpy.data.objects.new('Cam', cam); sc.collection.objects.link(co); sc.camera = co
    sc.render.engine = 'BLENDER_EEVEE'
    try: sc.eevee.taa_render_samples = 48; sc.eevee.use_raytracing = True
    except Exception as e: print('eevee', e)
    for vt in ('Standard', 'AgX', 'Filmic'):
        try: sc.view_settings.view_transform = vt; break
        except Exception: pass
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 93
    return co

def shoot(cam, root, name, yaw, target, dist, res, focal=160):
    sc = bpy.context.scene; root.rotation_euler = (0, 0, math.radians(yaw))
    cam.data.lens = focal; cam.data.sensor_fit = 'VERTICAL'; cam.data.sensor_height = 36
    cam.location = Vector(target) + Vector((0, -dist, .12)); cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x, sc.render.resolution_y = res; sc.render.filepath = os.path.join(OUT, name); bpy.ops.render.render(write_still=True)

def main():
    cam = studio(); root = bpy.data.objects.new('HERO', None); bpy.context.scene.collection.objects.link(root)
    parts = [build_body(root), build_face(root)]; cap_ob = None
    if ARGS.get('bare') != '1':
        parts += [build_hair(root)] + build_top(root) + build_bottom(root) + build_feet(root) + [build_wristband(root)]
        cap_ob = build_cap(root) if (ARGS.get('cap') == '1' or ARGS.get('kits')) else None
        if cap_ob: parts.append(cap_ob); cap_ob.hide_render = ARGS.get('cap') != '1'
    if ARGS.get('game') == '1':
        target = dict(Body=9000, Face=1400, Hair=1400, Top=3200, Collar=500, Placket=260, Shorts=2200, Skirt=2600, Waistband=160, UnderShorts=700, Sock=160, Shoe=2400, Wristband=160, Cap=700)
        for o in parts:
            o.data.calc_loop_triangles(); n = len(o.data.loop_triangles); t = target.get(o.name.split('.')[0], n)
            if n > t:
                dm = o.modifiers.new('dec', 'DECIMATE'); dm.ratio = t / n; bake(o)
        if ARGS.get('wire') == '1':
            dark = mat('Wire', (.02, .02, .03, 1), rough=.9)
            for o in list(parts):
                w = o.copy(); w.data = o.data.copy(); bpy.context.scene.collection.objects.link(w); w.data.materials.clear(); w.data.materials.append(dark)
                for p in w.data.polygons: p.material_index = 0
                wf = w.modifiers.new('wf', 'WIREFRAME'); wf.thickness = .0011; wf.use_replace = True
    tris = {}
    for o in parts:
        o.data.calc_loop_triangles(); tris[o.name.split('.')[0]] = tris.get(o.name.split('.')[0], 0) + len(o.data.loop_triangles)
    print('TRIS', sum(tris.values()), tris)
    res = tuple(int(x) for x in ARGS.get('res', '900x1500').split('x')); H = P['height']
    tag = ARGS.get('tag', SEX)
    for v in ARGS.get('views', 'front,q').split(','):
        yaw = dict(front=0, q=-35, side=-90, back=180, q2=35)[v] if v in ('front', 'q', 'side', 'back', 'q2') else None
        if yaw is not None: shoot(cam, root, f'{tag}_{v}.jpg', yaw, (0, 0, H * .50), 8.6, res)
        elif v == 'face': shoot(cam, root, f'{tag}_face.jpg', 0, (0, 0, HC.z - .02), 2.2, (1000, 1000))
        elif v == 'faceq': shoot(cam, root, f'{tag}_faceq.jpg', -35, (0, 0, HC.z - .02), 2.2, (1000, 1000))
        elif v == 'faceside': shoot(cam, root, f'{tag}_faceside.jpg', -90, (0, 0, HC.z - .02), 2.2, (1000, 1000))
        elif v == 'shoes': shoot(cam, root, f'{tag}_shoes.jpg', -55, (0, 0, .12), 2.0, (1200, 800))
        elif v == 'top': shoot(cam, root, f'{tag}_top.jpg', -20, (0, 0, P['shoulder_z'] - .16), 3.0, (1000, 1000))
    # colourways: recolour the shared Primary / Secondary / Accent materials and shoot again ("tag:prim,sec,acc[:cap]|...")
    for spec in [k for k in ARGS.get('kits', '').split('|') if k]:
        f = spec.split(':'); cols = f[1].split(',')
        for slot, hx in zip(('Primary', 'Secondary', 'Accent'), cols):
            b = next(n for n in MATS[slot].node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); b.inputs['Base Color'].default_value = hexc(hx)
        if cap_ob: cap_ob.hide_render = not (len(f) > 2 and f[2] == 'cap')
        shoot(cam, root, f'{tag}_kit_{f[0]}.jpg', -35, (0, 0, H * .50), 8.6, res)
    if ARGS.get('save') == '1': bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'{tag}.blend'))

main()

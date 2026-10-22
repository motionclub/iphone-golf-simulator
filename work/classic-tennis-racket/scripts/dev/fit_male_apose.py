"""Male right hand: derive the hand frame, place the racket in the palm (A-pose, unposed hero hand), solve the lift so the
racket clears the body by a target margin, report clearance/overlap, render quick looks.
blender -b --factory-startup --python fit_male_apose.py -- <racket.blend> [phi] [roll] [s_off] [out_prefix]"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
from fitlib import *
import render_lib as R

a = args_after_dashes()
racket_blend = a[0]
phi = float(a[1]) if len(a) > 1 else 35.0
roll = float(a[2]) if len(a) > 2 else 0.0
s_off = float(a[3]) if len(a) > 3 else 0.0
prefix = a[4] if len(a) > 4 else str(WORK / 'tmp' / 'fitm')

reset_scene()
body = load_body_copy('male')
co = mesh_co(body)
sel = (co[:, 0] < -0.50) & (co[:, 2] < 1.0)
c, u, v, S = hand_frame_from_points(co[sel])
if v[1] > 0:
    v = -v
p = np.cross(v, u)
print('hand frame u', u.round(3), 'v', v.round(3), 'p', p.round(3), 'p.x', round(float(p[0]), 3))
assert p[0] > 0, 'palm normal must point medially (+X) for the right hand'
bvh_body = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())

# palm centre on the palm surface
u_c, v_c = -0.060, -0.005
origin_probe = c + u * u_c + v * v_c
start = origin_probe + p * 0.10
hit = bvh_body.ray_cast(Vector(start), Vector(-p))
assert hit[0] is not None
Ps = np.array(hit[0])
print('palm surface point', Ps.round(4), 'depth from probe', round(float(np.dot(Ps - origin_probe, p)), 4))

# racket parts from the build
with bpy.data.libraries.load(racket_blend, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket')]
parts = {o.name: o for o in dst.objects}
for o in parts.values():
    bpy.context.scene.collection.objects.link(o)
sock = parts['Hand_Racket']
bpy.context.view_layer.update()
R_grip = 0.017


def sock_matrix(h):
    X, Y, Z = racket_axes(u, v, p, phi, roll)
    O = Ps + p * (R_grip + h) + Y * s_off
    M = np.eye(4)
    M[:3, 0], M[:3, 1], M[:3, 2], M[:3, 3] = X, Y, Z, O
    return M


def racket_world_samples(M):
    pts = []
    for name in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap'):
        o = parts[name]
        V = mesh_co(o)
        T = mesh_tris(o)
        Sx = surface_samples(V, T)
        pts.append(Sx @ M[:3, :3].T + M[:3, 3])
    return np.concatenate(pts, axis=0)


samples_local = None


def clearance_at(h):
    M = sock_matrix(h)
    pts = racket_world_samples(M)
    d = signed_clearance(bvh_body, pts)
    return float(d.min()), M, d


# bisection on the lift h (metres above tangent contact with the palm surface point)
lo, hi = -0.03, 0.03
for _ in range(14):
    mid = 0.5 * (lo + hi)
    cl, _, _ = clearance_at(mid)
    if cl < 0.0004:
        lo = mid
    else:
        hi = mid
h_sol = hi
cl, M, d = clearance_at(h_sol)
print('lift h', round(h_sol, 5), 'min clearance mm', round(cl * 1000, 3))
sock.matrix_world = Matrix([tuple(r) for r in M])
bpy.context.view_layer.update()

# exact triangle overlap racket parts vs body
dg = bpy.context.evaluated_depsgraph_get()
overlaps = {}
for name in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap'):
    overlaps[name] = tri_overlap_count(BVHTree.FromObject(parts[name], dg), bvh_body)
print('triangle overlaps racket-vs-body', overlaps)
# per part clearance
res = dict(phi=phi, roll=roll, s_off=s_off, lift=h_sol, min_clearance_mm=cl * 1000, overlaps=overlaps, matrix=M.tolist(), hand_frame=dict(c=c.tolist(), u=u.tolist(), v=v.tolist(), p=p.tolist()), palm_surface_point=Ps.tolist())
Path(prefix + '.json').write_text(json.dumps(res, indent=1))

# quick render
mat = bpy.data.materials.new('G'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.30, 0.30, 0.32, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
body.data.materials.clear(); body.data.materials.append(mat)
parts['Collider_Racket'].hide_render = True
R.studio(bg=(0.36, 0.37, 0.39), samples=40)
tgt = tuple(Ps + (np.array([-0.0, -0.18, -0.06])))
R.shot(prefix + '_front.png', (-0.55, -0.25, 0.80), az=0, el=5, dist=1.7, lens=60, res=(900, 900))
R.shot(prefix + '_side.png', (-0.55, -0.25, 0.80), az=-90, el=5, dist=1.7, lens=60, res=(900, 900))
R.shot(prefix + '_q3.png', (-0.55, -0.25, 0.80), az=-40, el=18, dist=1.7, lens=60, res=(900, 900))
R.shot(prefix + '_close.png', tuple(Ps), az=-60, el=10, dist=0.45, lens=70, res=(900, 900))
R.shot(prefix + '_top.png', tuple(Ps), az=0, el=85, dist=0.8, lens=70, res=(900, 900))
print('FIT_DONE')

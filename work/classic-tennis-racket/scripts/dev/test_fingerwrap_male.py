"""Male A-pose: place the racket (analytic lift), wrap the four fingers with the path method on a COPY, render views.
blender -b --factory-startup --python test_fingerwrap_male.py -- <racket.blend> <phi> <U_g> <V_g> <tag>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
from fitlib import *
import render_lib as R
import male_hand as MH
import wrap as WR
import fingerwrap as FW

a_ = args_after_dashes()
racket_blend, phi, U_g, V_g, tag = a_[0], float(a_[1]), float(a_[2]), float(a_[3]), a_[4]

reset_scene()
body = load_body_copy('male')
co = mesh_co(body)
T = mesh_tris(body)
sel, c, u, v, p = MH.frame_from_body(co)
Q = MH.to_hand(co[sel], c, u, v, p)
idxmap = -np.ones(len(co), int); idxmap[sel] = np.arange(len(sel))
Ts = idxmap[T]; Ts = Ts[np.all(Ts >= 0, axis=1)]
qa, qb, qc = Q[Ts[:, 0]], Q[Ts[:, 1]], Q[Ts[:, 2]]
Qs = np.concatenate([Q, (qa + qb) / 2, (qb + qc) / 2, (qc + qa) / 2, (qa + qb + qc) / 3])
chains = MH.build_chains(Q)
a = WR.axis_dir(phi)
W_g = WR.lift_for_clearance(Qs, (U_g, V_g), a, margin=0.0005)
O = np.array([U_g, V_g, W_g])
print('cylinder O', O.round(4), 'a', a.round(3))

Qn = Q.copy()
infos = {}
for name, ch in chains.items():
    M = ch.J[0]
    out, info = FW.wrap_finger(Q, ch.member, M, ch.axis_dir, None, O, a, length=MH.FINGERS[name]['tip'] - MH.U_MCP)
    infos[name] = info
    Qn += (out - Q)
print({k: v.get('ok') for k, v in infos.items()})
d = WR.cyl_dist(Qn, O, a)
print('hand-vs-cylinder min distance mm (all hand verts):', round(float(d.min() * 1000), 2))
for name, ch in chains.items():
    m = ch.member > 0.5
    print(f'   {name}: min dist {d[m].min()*1000:+.2f} mm  tip displacement {np.linalg.norm((Qn-Q)[m], axis=1).max()*1000:.0f} mm')
co2 = co.copy()
co2[sel] = MH.from_hand(Qn, c, u, v, p)
body.data.vertices.foreach_get  # noqa
body.data.vertices.foreach_set('co', co2.ravel())
body.data.update()

# racket in world: Y_r = a (world), Z_r = p, origin from hand-frame O
a_w = a[0] * u + a[1] * v
Y = a_w / np.linalg.norm(a_w)
Z = p - np.dot(p, Y) * Y; Z /= np.linalg.norm(Z)
X = np.cross(Y, Z)
Ow = c + O[0] * u + O[1] * v + O[2] * p
M4 = np.eye(4); M4[:3, 0], M4[:3, 1], M4[:3, 2], M4[:3, 3] = X, Y, Z, Ow
with bpy.data.libraries.load(racket_blend, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket')]
parts = {o.name: o for o in dst.objects}
for o in parts.values():
    bpy.context.scene.collection.objects.link(o)
parts['Hand_Racket'].matrix_world = Matrix([tuple(r) for r in M4])
parts['Collider_Racket'].hide_render = True
mat = bpy.data.materials.new('G'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.30, 0.30, 0.32, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
body.data.materials.clear(); body.data.materials.append(mat)
bpy.context.view_layer.update()
R.studio(bg=(0.36, 0.37, 0.39), samples=40)
tg = tuple(Ow)
pre = str(WORK / 'tmp' / f'fw_{tag}')
R.shot(pre + '_close_a.png', tg, az=-40, el=15, dist=0.5, lens=70, res=(800, 800))
R.shot(pre + '_close_b.png', tg, az=-110, el=10, dist=0.5, lens=70, res=(800, 800))
R.shot(pre + '_close_c.png', tg, az=0, el=5, dist=0.5, lens=70, res=(800, 800))
R.shot(pre + '_front.png', (-0.55, -0.25, 0.80), az=0, el=5, dist=1.7, lens=60, res=(800, 800))
print('FW_DONE')

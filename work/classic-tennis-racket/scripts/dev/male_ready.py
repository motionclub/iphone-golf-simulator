"""Male: grip placement (hand frame), finger wrap, arm pose (ready stance), racket follows the hand. Renders proof views.
blender -b --factory-startup --python male_ready.py -- <racket.blend> <phi> <U_g> <V_g> <adduct> <flex> <tag>"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from common import *
from fitlib import *
import render_lib as R
import male_hand as MH
import wrap as WR
import fingerwrap as FW
from armpose import ArmRig

a_ = args_after_dashes()
racket_blend, phi, U_g, V_g, adduct, flex, tag = a_[0], float(a_[1]), float(a_[2]), float(a_[3]), float(a_[4]), float(a_[5]), a_[6]
roll = float(a_[7]) if len(a_) > 7 else 0.0

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
Qn = Q.copy()
for name, ch in chains.items():
    out, info = FW.wrap_finger(Q, ch.member, ch.J[0], ch.axis_dir, None, O, a, length=MH.FINGERS[name]['tip'] - MH.U_MCP)
    Qn += (out - Q)
co2 = co.copy()
co2[sel] = MH.from_hand(Qn, c, u, v, p)

# racket in the REST world frame (A-pose hand)
a_w = a[0] * u + a[1] * v
Y = a_w / np.linalg.norm(a_w)
Z = p - np.dot(p, Y) * Y; Z /= np.linalg.norm(Z)
Z = rot_about(Y, np.radians(roll)) @ Z
X = np.cross(Y, Z)
Ow = c + O[0] * u + O[1] * v + O[2] * p
M_rest = np.eye(4); M_rest[:3, 0], M_rest[:3, 1], M_rest[:3, 2], M_rest[:3, 3] = X, Y, Z, Ow

# arm pose
S = np.array([-0.2102, -0.0291, 1.3896]); E = np.array([-0.3345, -0.0380, 1.1535]); Wr = np.array([-0.529, -0.081, 0.967])
rig = ArmRig(S, E, Wr)
force = np.zeros(len(co)); force[sel] = 1.0
rig.force = force
co3 = rig.skin(co2, adduct, flex, P_rest=co)
Mh = rig.rigid_hand(adduct, flex)
M_posed = Mh @ M_rest
body.data.vertices.foreach_set('co', co3.ravel())
body.data.update()

with bpy.data.libraries.load(racket_blend, link=False) as (src, dst):
    dst.objects = [n for n in src.objects if n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket')]
parts = {o.name: o for o in dst.objects}
for o in parts.values():
    bpy.context.scene.collection.objects.link(o)
parts['Hand_Racket'].matrix_world = Matrix([tuple(r) for r in M_posed])
parts['Collider_Racket'].hide_render = True
mat = bpy.data.materials.new('G'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.30, 0.30, 0.32, 1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.6
body.data.materials.clear(); body.data.materials.append(mat)
bpy.context.view_layer.update()
# racket vs posed body overlap
dg = bpy.context.evaluated_depsgraph_get()
bvh_body = BVHTree.FromObject(body, dg)
ov = {n: tri_overlap_count(BVHTree.FromObject(parts[n], dg), bvh_body) for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')}
print('overlaps racket vs posed body', ov)
R.studio(bg=(0.36, 0.37, 0.39), samples=40)
pre = str(WORK / 'tmp' / f'mr_{tag}')
ctr = (np.array(M_posed[:3, 3]) + np.array([0.0, 0.0, 0.1])).tolist()
tg = (-0.25, -0.30, 1.05)
R.shot(pre + '_front.png', tg, az=0, el=5, dist=2.4, lens=60, res=(900, 900))
R.shot(pre + '_side.png', tg, az=-90, el=5, dist=2.4, lens=60, res=(900, 900))
R.shot(pre + '_q3.png', tg, az=-40, el=15, dist=2.4, lens=60, res=(900, 900))
R.shot(pre + '_close.png', tuple(M_posed[:3, 3]), az=-60, el=10, dist=0.55, lens=70, res=(900, 900))
print('MR_DONE')
# extra debug views of the horn
R.shot(pre + '_dbgA.png', (-0.30, -0.35, 1.05), az=0, el=5, dist=0.9, lens=70, res=(900, 900))
R.shot(pre + '_dbgB.png', (-0.30, -0.35, 1.05), az=-90, el=5, dist=0.9, lens=70, res=(900, 900))

"""Driver: blender -b --factory-startup --python run_onhand.py -- <male|female> <racket.blend> <out_dir> [phi U_g V_g roll]"""
import sys, json
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket/scripts')
from onhand import *

a_ = args_after_dashes()
tag, racket_blend, out_dir = a_[0], Path(a_[1]), Path(a_[2])
phi = float(a_[3]) if len(a_) > 3 else 52.0
U_g = float(a_[4]) if len(a_) > 4 else -0.02
V_g = float(a_[5]) if len(a_) > 5 else 0.0
roll = float(a_[6]) if len(a_) > 6 else 45.0
out_dir.mkdir(parents=True, exist_ok=True)
PROOF = out_dir
NAME = {'male': 'Male', 'female': 'Female'}[tag]
BODYNAME = {'male': 'Body_M', 'female': 'Body_F'}[tag]
res = dict(tag=tag, phi=phi, U_g=U_g, V_g=V_g, roll=roll)

# ============================================================== A-pose (unposed hero hand, copy of the body)
reset_scene()
body = load_body_copy(tag)
prof = Profile(tag, body)
hero_hash = sha_arr(prof.co)
sk = prof.socket(phi, U_g, V_g, roll)
M_rest = prof.racket_matrix_rest(sk)
grey_body_material(body)
parts = load_racket(racket_blend)
sock = parts['Hand_Racket']
parts['Collider_Racket'].hide_render = True
sock.parent = body
sock.matrix_parent_inverse = body.matrix_world.inverted()
sock.matrix_world = Matrix([tuple(r) for r in M_rest])
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
body_tree = BVHTree.FromObject(body, dg)
tri_ok = np.all(np.isin(prof.tris, prof.sel), axis=1)
hand_tree = bvh_from_arrays(prof.co, prof.tris[tri_ok])
# solve the lift against the exact racket meshes: raise W_g until the racket clears the HAND by >= 0.4 mm
for it in range(8):
    cl_hand = min_clearance(parts, hand_tree)
    if cl_hand >= 0.0004:
        break
    sk['W_g'] += (0.0004 - cl_hand) + 0.0001
    sk['O'][2] = sk['W_g']
    M_rest = prof.racket_matrix_rest(sk)
    sock.matrix_world = Matrix([tuple(r) for r in M_rest])
    bpy.context.view_layer.update()
cl_hand = min_clearance(parts, hand_tree)
dg = bpy.context.evaluated_depsgraph_get()
cl_body = min_clearance(parts, body_tree)
ov_hand = {n: tri_overlap_count(bvh_world(parts[n]), hand_tree) for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')}
ov_body = racket_vs_body(parts, body_tree, dg)
res['apose'] = dict(W_g=sk['W_g'], min_clearance_hand_mm=cl_hand * 1000, min_clearance_body_mm=cl_body * 1000,
                    tri_overlaps_hand=ov_hand, tri_overlaps_body=ov_body, matrix_world=M_rest.tolist())
print('A-pose', tag, json.dumps(res['apose'], default=float)[:400])
# parent / unparent tests: body vertex data unchanged
h_with = sha_arr(mesh_co(body))
sock_world = np.array(sock.matrix_world)
# (1) clear parent keeping transform on the socket
bpy.ops.object.select_all(action='DESELECT')
sock.select_set(True)
bpy.context.view_layer.objects.active = sock
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
same_world = float(np.abs(np.array(sock.matrix_world) - sock_world).max())
h_unparent = sha_arr(mesh_co(body))
# (2) delete racket hierarchy -> body untouched
for n in ('Collider_Racket', 'ButtCap', 'Grip', 'StringBed', 'Racket_Classic', 'Hand_Racket'):
    bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
h_deleted = sha_arr(mesh_co(body))
res['parent_tests'] = dict(hero_vertex_hash=hero_hash, hash_with_racket=h_with, hash_after_unparent=h_unparent, hash_after_delete=h_deleted,
                           unparent_keeps_world_transform_err=same_world,
                           body_unchanged=bool(hero_hash == h_with == h_unparent == h_deleted))
print('parent tests', res['parent_tests']['body_unchanged'], same_world)

# rebuild the A-pose scene (parented) for saving + renders
reset_scene()
body = load_body_copy(tag)
grey_body_material(body)
parts = load_racket(racket_blend)
sock = parts['Hand_Racket']
parts['Collider_Racket'].hide_render = True
sock.parent = body
sock.matrix_parent_inverse = body.matrix_world.inverted()
sock.matrix_world = Matrix([tuple(r) for r in M_rest])
bpy.context.view_layer.update()
R.studio(bg=(0.36, 0.37, 0.39), samples=48)
ctr = tuple(M_rest[:3, 3])
views = {'front': dict(az=0, el=5), 'side': dict(az=-90, el=5), 'q3': dict(az=-42, el=16)}
for nm, kw in views.items():
    R.shot(str(PROOF / f'{tag}_apose_{nm}.png'), prof.hand_tgt_apose if tag == 'male' else (-0.22, -0.02, 0.85), dist=1.9 if tag == 'male' else 2.6, lens=60, res=(1000, 1000), **kw)
R.shot(str(PROOF / f'{tag}_apose_grip_close.png'), ctr, az=-55, el=10, dist=0.5, lens=70, res=(1000, 1000))
R.shot(str(PROOF / f'{tag}_apose_grip_close2.png'), ctr, az=-120, el=25, dist=0.5, lens=70, res=(1000, 1000))
sock['socket_note'] = ('Hand_Racket: origin = racket grip centre (palm hold point); racket +Y = shaft towards head, +Z = hitting-face normal (palm normal rolled %.0f deg about the shaft), +X = Y x Z. '
                       'Parented to the COPY of the hero body in the locked A-pose; hero blend untouched.' % roll)
sock['hero_blend_sha256'] = BODIES[tag]['sha']
if tag == 'female':
    sock['warning'] = 'Static A-pose bind: the female arm hangs flush to the thigh with a pronated (palm-back) placeholder hand, so the racket crosses the thigh here. Use the ReadyStance proof pose for fit.'
bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f'RacketOnHero_{NAME}_APose.blend'))

# ============================================================== ready stance (proof-only posed duplicate)
reset_scene()
body = load_body_copy(tag)
prof = Profile(tag, body)
co3, co2, Mh, Qn, infos = prof.posed_body(sk)
body.name = f'{BODYNAME}_PROOFPOSE'
body.data.vertices.foreach_set('co', co3.ravel())
body.data.update()
grey_body_material(body)
parts = load_racket(racket_blend)
sock = parts['Hand_Racket']
parts['Collider_Racket'].hide_render = True
M_posed = Mh @ M_rest
sock.parent = body
sock.matrix_parent_inverse = body.matrix_world.inverted()
sock.matrix_world = Matrix([tuple(r) for r in M_posed])
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
body_tree = BVHTree.FromObject(body, dg)
cl_body = min_clearance(parts, body_tree)
ov_body = racket_vs_body(parts, body_tree, dg)
# per-finger distance to the cylinder after the wrap (hand frame, rigid afterwards)
dcyl = {}
for f in prof.fingers:
    m = f['member'] > 0.5
    dcyl[f['name']] = float(WR.cyl_dist(Qn[m], sk['O'], sk['a'], R=0.0173).min() * 1000)
d_all = float(WR.cyl_dist(Qn, sk['O'], sk['a'], R=0.0173).min() * 1000)
tri_ok = np.all(np.isin(prof.tris, prof.sel), axis=1)
hand_tree_posed = bvh_from_arrays(co3, prof.tris[tri_ok])
ov_hand_posed = {n: tri_overlap_count(bvh_world(parts[n]), hand_tree_posed) for n in ('Racket_Classic', 'StringBed', 'Grip', 'ButtCap')}
cl_hand_posed = min_clearance(parts, hand_tree_posed)
res['ready'] = dict(pose=prof.pose, min_clearance_body_mm=cl_body * 1000, min_clearance_hand_mm=cl_hand_posed * 1000, tri_overlaps_body=ov_body,
                    tri_overlaps_hand=ov_hand_posed, hand_vs_grip_cylinder_min_mm=d_all, finger_vs_cylinder_min_mm=dcyl, matrix_world=M_posed.tolist(),
                    finger_paths_ok={k: v.get('ok') for k, v in infos.items()})
print('Ready', tag, json.dumps(res['ready'], default=float)[:500])
R.studio(bg=(0.36, 0.37, 0.39), samples=48)
ctr = tuple(M_posed[:3, 3])
tg = prof.view_tgt_ready
for nm, kw in views.items():
    R.shot(str(PROOF / f'{tag}_ready_{nm}.png'), tg, dist=2.3, lens=60, res=(1000, 1000), **kw)
R.shot(str(PROOF / f'{tag}_ready_grip_close.png'), ctr, az=-55, el=10, dist=0.5, lens=70, res=(1000, 1000))
R.shot(str(PROOF / f'{tag}_ready_grip_close2.png'), ctr, az=-120, el=25, dist=0.5, lens=70, res=(1000, 1000))
sock['socket_note'] = 'PROOF-ONLY pose on a duplicate of the hero body (fingers wrapped, arm skinned). Racket follows the hand rigidly via the same Hand_Racket socket.'
bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / f'RacketOnHero_{NAME}_ReadyStance_PROOFPOSE.blend'))

# ---- socket data (hand frame + A-pose world + Unity conversion)
c, u, v, p = prof.c, prof.u, prof.v, prof.p
Mr = np.array(M_rest)
# Blender -> Unity world mapping used by the hero FBX pipeline (verified empirically in Unity 6000.3.24f1, see export_report):
#   (x, y, z)_Blender -> (-x, z, -y)_Unity   (reflection C, det = -1);  a rotation R maps to C R C^T
C = np.array([[-1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])
RU = C @ Mr[:3, :3] @ C.T
pU = C @ Mr[:3, 3]
qU = Matrix([tuple(r) for r in RU]).to_quaternion()      # proper rotation (det +1) -> quaternion of the matrix as numbers
res['socket'] = dict(
    note='Hand_Racket origin = racket grip centre; racket local +Y = shaft towards the head, +Z = hitting-face normal, +X = Y x Z (Blender frame)',
    hand_frame_blender=dict(origin=c.tolist(), u_fingers=u.tolist(), v_thumb=v.tolist(), p_palm_normal=p.tolist()),
    hand_frame_unity=dict(origin=(C @ c).tolist(), u_fingers=(C @ u).tolist(), v_thumb=(C @ v).tolist(), p_palm_normal=(C @ p).tolist()),
    grip_in_hand_frame=dict(phi_deg=phi, U_g=U_g, V_g=V_g, W_g=sk['W_g'], roll_deg=roll,
                            axis_UVW=[float(x) for x in sk['a']], origin_UVW=[float(x) for x in sk['O']],
                            meaning='U along the fingers, V towards the thumb, W = palm normal; handle axis = (sin phi, cos phi, 0) in (U,V,W); grip centre = (U_g, V_g, W_g)'),
    apose_world_blender=dict(position=Mr[:3, 3].tolist(), X=Mr[:3, 0].tolist(), Y=Mr[:3, 1].tolist(), Z=Mr[:3, 2].tolist(),
                             euler_xyz_deg=[float(np.degrees(a)) for a in Matrix([tuple(r) for r in Mr]).to_euler('XYZ')]),
    apose_world_unity=dict(position=pU.tolist(), right=RU[:, 0].tolist(), up=RU[:, 1].tolist(), forward=RU[:, 2].tolist(),
                           quaternion_xyzw_of_matrix=[float(qU.x), float(qU.y), float(qU.z), float(qU.w)],
                           use='transform.position = position; transform.rotation = Quaternion.LookRotation(forward, up)'),
)
(out_dir / f'onhand_{tag}.json').write_text(json.dumps(res, indent=1, default=float))
print('ONHAND_DONE', tag)

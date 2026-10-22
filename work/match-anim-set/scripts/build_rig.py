"""Stage 1: fit a skeleton to the hero, skin the body to it, bind face/hair to the head, put the racket on the right-hand socket.

  blender -b --factory-startup --python build_rig.py -- <male|female>

* byte-copies the source blend into export/_stage/ (the source is never opened for writing) and asserts SHA(copy) == SHA(source);
* builds `Rig_<Hero>` from data/rig_spec_<hero>.json (landmarks measured on the hero's own mesh: scripts/lm.py);
* skins `Body_*` with Blender's automatic weights, replaces the hand region by the dressed-look digit weights (blended into the
  forearm weights over +-1.5 cm around the wrist), limits to 4 influences;
* Face_* / Hair_F get bone-parented to `Head` (no data added to those meshes);
* appends the classic racket, `Hand_Racket` on the right-hand bone with the dressed-look grip placement;
* writes data/rig_<hero>.json (rest matrices, lengths, weights summary, right-hand grip angles) and the stage blend.
The body mesh geometry is never edited; the only data added to the body datablock are vertex groups named after the deform bones."""
import os
import shutil
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'dressed-look', 'scripts'))
from common import *
from rigbuild import *
import lm
from geom import Mesh
from handlib import adjacency
from handmodel import finger_weights, smoothstep
import bpy
from mathutils import Matrix, Vector

tag = args_after_dashes()[0]
H = HERO[tag]
NAME = H['label']
STAGE = f'{EXPORT}/_stage'
os.makedirs(STAGE, exist_ok=True)
OUT = f'{STAGE}/{NAME}_rig.blend'
assert OUT.startswith(WORK + '/')
src_path = SRC[tag]
assert sha256_file(src_path) == SHA[tag], 'source SHA differs from the brief - stop'
shutil.copyfile(src_path, OUT)
assert sha256_file(OUT) == SHA[tag]
report = dict(tag=tag, copy_sha256_before_edit=sha256_file(OUT))
bpy.ops.wm.open_mainfile(filepath=OUT)
sc = bpy.context.scene
body = bpy.data.objects[H['body']]
face = bpy.data.objects[H['face']]
hair = bpy.data.objects.get(H['hair']) if H['hair'] else None
src_meshes = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
report['source_mesh_geometry_hash'] = {n: mesh_geometry_hash(o.data) for n, o in src_meshes.items()}
orig_vg_names = [g.name for g in body.vertex_groups]
report['source_vgroups'] = orig_vg_names
report['source_vgroups_hash'] = original_vgroups_hash(body, orig_vg_names)
report['source_nverts'] = {n: len(o.data.vertices) for n, o in src_meshes.items()}
report['unit'] = [sc.unit_settings.system, sc.unit_settings.scale_length]

spec = json.load(open(f'{DATA}/rig_spec_{tag}.json'))
rig = build_armature(spec, 'Rig_' + NAME)
bpy.context.view_layer.update()

# ------------------------------------------------------------------ automatic weights
for o in bpy.context.view_layer.objects:
    o.select_set(False)
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
assert body.parent == rig
mods = [m for m in body.modifiers if m.type == 'ARMATURE']
assert len(mods) == 1
mods[0].name = 'Armature_' + NAME
mods[0].use_deform_preserve_volume = False
print('auto weights: vertex groups on body', len(body.vertex_groups))

# ------------------------------------------------------------------ custom digit weights for both hands
co = mesh_co(body)
M = Mesh(co, np.zeros((0, 3), np.int64), np.zeros((0, 2), np.int64)) if False else None
d = np.load(f'{DATA}/{tag}_body_mesh.npz')
assert np.abs(d['co'] - co).max() < 1e-6
adj = adjacency(len(co), d['ed'])
mesh = Mesh(d['co'], d['tri'], d['ed'])
hands = lm.hand_pipeline(mesh, adj, tag, print)
spec_b = {b['name']: b for b in spec['bones']}
FN = {'thumb': 'Thumb', 'index': 'Index', 'middle': 'Middle', 'ring': 'Ring', 'pinky': 'Little'}
DEF_NAMES = {f'{n}_{k}': None for n in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb') for k in (1, 2, 3)}
SEG = {1: 'Proximal', 2: 'Intermediate', 3: 'Distal'}


def my_name(sd, key):
    Sd = 'Left' if sd == 'L' else 'Right'
    if key == 'Hand_R':
        return f'{Sd}Hand'
    dg, k = key.split('_')
    fn = {'Index': 'Index', 'Middle': 'Middle', 'Ring': 'Ring', 'Pinky': 'Little', 'Thumb': 'Thumb'}[dg]
    return f'{Sd}{fn}{SEG[int(k)]}'


def vweights(i):
    return {body.vertex_groups[g.group].name: g.weight for g in body.data.vertices[i].groups}


deform_names = [b.name for b in rig.data.bones if b.use_deform]
hand_report = {}
for sd, s in (('L', 1), ('R', -1)):
    Hm = hands[sd]
    hand = Hm['hand']
    W = finger_weights(Hm['c_mirror'], hand, Hm['raw'], Hm['p_raw'])
    wrist = np.array(spec['joints'][f'wrist_{sd}'])
    uvec = lm.unit(Hm['mid_mcp'] - wrist)
    t = (co[hand] - wrist) @ uvec
    a = smoothstep((t + 0.015) / 0.03)
    n_changed = 0
    for k, vi in enumerate(hand):
        auto = vweights(int(vi))
        # keep only deform-bone auto weights
        auto = {n: w for n, w in auto.items() if n in deform_names}
        fin = {}
        for key, arr in W.items():
            w = float(arr[k])
            if w > 1e-5:
                fin[my_name(sd, key)] = w
        tot_auto = sum(auto.values())
        out = {}
        for n, w in fin.items():
            out[n] = out.get(n, 0.0) + a[k] * w
        if tot_auto > 1e-9:
            for n, w in auto.items():
                out[n] = out.get(n, 0.0) + (1.0 - a[k]) * w / tot_auto
        tot = sum(out.values())
        for n in deform_names:
            vg = body.vertex_groups.get(n)
            w = out.get(n, 0.0) / tot if tot > 0 else 0.0
            if w > 1e-5:
                vg.add([int(vi)], float(w), 'REPLACE')
            elif n in auto:
                vg.remove([int(vi)])
        n_changed += 1
    hand_report[sd] = dict(n_hand_vertices=int(len(hand)), n_wrist_blend=int(((a > 0.0) & (a < 1.0)).sum()), wrist=wrist.tolist())
report['hands'] = hand_report

# ------------------------------------------------------------------ clean: 4 influences, normalise (deform groups only; the original LOOP_* groups are not touched)
bpy.context.view_layer.objects.active = body
for o in bpy.context.view_layer.objects:
    o.select_set(False)
body.select_set(True)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.vertex_group_clean(group_select_mode='BONE_DEFORM', limit=0.002, keep_single=True)
bpy.ops.object.vertex_group_limit_total(group_select_mode='BONE_DEFORM', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='BONE_DEFORM', lock_active=False)
assert original_vgroups_hash(body, orig_vg_names) == report['source_vgroups_hash'], 'original vertex groups changed'
# weights sanity
wsum = np.zeros(len(body.data.vertices))
ninf = np.zeros(len(body.data.vertices), int)
dn = set(deform_names)
for v in body.data.vertices:
    for g in v.groups:
        if body.vertex_groups[g.group].name in dn:
            wsum[v.index] += g.weight
            ninf[v.index] += 1
report['weights'] = dict(min_sum=float(wsum.min()), max_sum=float(wsum.max()), unweighted=int((wsum < 0.99).sum()), max_influences=int(ninf.max()))
print('weights', report['weights'])
assert report['weights']['unweighted'] == 0

# ------------------------------------------------------------------ face / hair -> Head bone
bpy.context.view_layer.update()
head_pb = rig.pose.bones['Head']
P = rig.matrix_world @ head_pb.matrix @ Matrix.Translation((0.0, head_pb.bone.length, 0.0))
for o in [face] + ([hair] if hair else []):
    o.parent = rig
    o.parent_type = 'BONE'
    o.parent_bone = 'Head'
    o.matrix_parent_inverse = P.inverted()
bpy.context.view_layer.update()
for o in [face] + ([hair] if hair else []):
    assert np.abs(mesh_co(o, world=True) - mesh_co(o)).max() < 1e-5, 'face/hair moved when parented to the head'

# ------------------------------------------------------------------ racket socket (dressed-look grip placement, right hand)
with bpy.data.libraries.load(SRC['racket'], link=False) as (s_, d_):
    d_.objects = ['Racket_Classic', 'StringBed', 'Grip', 'ButtCap', 'Collider_Racket', 'Hand_Racket']
rk = {o.name: o for o in d_.objects}
col_rk = bpy.data.collections.new('Racket')
sc.collection.children.link(col_rk)
for n, o in rk.items():
    col_rk.objects.link(o)
dl = json.load(open(f'{REPO}/work/dressed-look/data/build_{tag}.json'))['rig']
Mw = Matrix([tuple(r) for r in dl['racket_world_matrix']])
hr = rk['Hand_Racket']
hr.parent = None
hr.matrix_world = Mw
hr.matrix_basis = Matrix.Identity(4)
hr.parent = rig
hr.parent_type = 'BONE'
hr.parent_bone = 'RightHand'
hr.matrix_parent_inverse = Matrix.Identity(4)
bpy.context.view_layer.update()
Pb = hr.matrix_world.copy()
hr.matrix_parent_inverse = Pb.inverted() @ Mw
bpy.context.view_layer.update()
report['hand_racket_world_err'] = float(np.abs(np.array(hr.matrix_world) - np.array(Mw)).max())
rk['Collider_Racket'].hide_render = True
rk['Collider_Racket'].hide_set(True)
report['racket_geometry_hash'] = {n: mesh_geometry_hash(o.data) for n, o in rk.items() if o.type == 'MESH'}

# right-hand grip angles of the dressed-look solution, mapped to this rig's bone names
ang = {}
for key, v in dl['angles'].items():
    ang[my_name('R', key)] = float(v)
report['right_grip_angles_deg'] = ang
report['right_grip_source'] = f'work/dressed-look/data/build_{tag}.json rig.angles (same digit model, same bone rest geometry)'

# ------------------------------------------------------------------ rest data for the numpy kinematics
bones = []
for b in rig.data.bones:
    bones.append(dict(name=b.name, parent=b.parent.name if b.parent else None, head=list(b.head_local), tail=list(b.tail_local),
                      length=b.length, matrix_local=[list(r) for r in b.matrix_local], deform=b.use_deform))
rest = dict(tag=tag, bones=bones, height=spec['height'], joints=spec['joints'])
# anthropometrics measured on this rig
J = {k: np.array(v) for k, v in spec['joints'].items()}
rest['measures'] = dict(
    shoulder_joint_width=float(np.linalg.norm(J['shoulder_L'] - J['shoulder_R'])),
    upper_arm=float(np.linalg.norm(J['elbow_L'] - J['shoulder_L'])),
    forearm=float(np.linalg.norm(J['wrist_L'] - J['elbow_L'])),
    arm_length_shoulder_to_wrist=float(np.linalg.norm(J['wrist_L'] - J['shoulder_L'])),
    thigh=float(np.linalg.norm(J['knee_L'] - J['hip_L'])),
    shank=float(np.linalg.norm(J['ankle_L'] - J['knee_L'])),
    leg_length_hip_to_ankle=float(np.linalg.norm(J['ankle_L'] - J['hip_L'])),
    hip_joint_width=float(np.linalg.norm(J['hip_L'] - J['hip_R'])),
    foot_ankle_to_ball=float(np.linalg.norm(J['ball_L'] - J['ankle_L'])),
    pelvis_height=float(J['hips'][2]),
)
json.dump(rest, open(f'{DATA}/rig_{tag}.json', 'w'), indent=1)

# ------------------------------------------------------------------ save
rig['source_blend'] = src_path
rig['source_sha256'] = SHA[tag]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=OUT)
report['saved'] = OUT
report['mesh_geometry_hash_after'] = {n: mesh_geometry_hash(o.data) for n, o in src_meshes.items()}
report['mesh_hash_equal'] = {n: report['mesh_geometry_hash_after'][n] == report['source_mesh_geometry_hash'][n] for n in src_meshes}
assert all(report['mesh_hash_equal'].values()), report['mesh_hash_equal']
report['measures'] = rest['measures']
json.dump(report, open(f'{DATA}/build_rig_{tag}.json', 'w'), indent=1)
print('BUILD_RIG_DONE', tag, json.dumps(rest['measures']))

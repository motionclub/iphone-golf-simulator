"""Mesh-level gate measurements on the baked blend (Blender headless):

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python verify_blend.py -- <male|female>

BODY_UNCHANGED, ON_HERO, RACKET_HELD (mesh part), IN_PLACE (floor + Root), READS_FROM_BEHIND (occlusion).  Writes data/verify_blend_<hero>.json.
Definitions: GATE_DEFS_preregistered.md."""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from common import *

tag = args_after_dashes()[0]
H = HERO[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
body = bpy.data.objects[H['body']]
face = bpy.data.objects[H['face']]
hair = bpy.data.objects[H['hair']] if H['hair'] else None
grip_o = bpy.data.objects['Grip']
butt_o = bpy.data.objects['ButtCap']
bed_o = bpy.data.objects['StringBed']
socket = bpy.data.objects['Hand_Racket']
meta = json.load(open(f'{DATA}/bake_{tag}.json'))['clips']
A = np.load(f'{DATA}/anim_{tag}.npz')
rigj = json.load(open(f'{DATA}/rig_{tag}.json'))
R = {}                                    # results
fails = {}


def note(gate, msg):
    fails.setdefault(gate, []).append(msg)


def activate(clip):
    act = bpy.data.actions[clip]
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    return act


def eval_world(obj):
    """evaluated (deformed) mesh of obj in world space: (co (n,3), tris (m,3))"""
    dg = bpy.context.evaluated_depsgraph_get()
    eo = obj.evaluated_get(dg)
    me = eo.to_mesh()
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    M = np.array(eo.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    tris = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get('vertices', tris)
    tris = tris.reshape(-1, 3)
    eo.to_mesh_clear()
    return co, tris


def bvh_of(co, tris):
    return BVHTree.FromPolygons([tuple(v) for v in co], [tuple(t) for t in tris], all_triangles=True)


# =============================================================================================== BODY_UNCHANGED
try:
    src_sha_now = {k: sha256_file(SRC[k]) for k in ('male', 'female', 'racket')}
    R['source_sha_now'] = src_sha_now
    R['source_sha_expected'] = SHA
    R['source_sha_equal'] = {k: src_sha_now[k] == SHA[k] for k in src_sha_now}
    for k, v in R['source_sha_equal'].items():
        if not v:
            note('BODY_UNCHANGED', f'source {k} SHA changed')
    names_src = [H['body'], H['face']] + ([H['hair']] if H['hair'] else [])
    with bpy.data.libraries.load(SRC[tag], link=False) as (df, dt):
        dt.objects = [n for n in names_src if n in df.objects]
    src_objs = {o.name.split('.')[0]: o for o in dt.objects if o is not None}
    hashes = {}
    pose_mode0 = rig.data.pose_position
    rig.data.pose_position = 'REST'                    # the copies hang on the rig: their world matrices equal the source ones in the bind pose
    bpy.context.view_layer.update()
    for n in names_src:
        so = bpy.data.objects[n]                       # the copy in this file (name wins: the library objects get a .001 suffix)
        lo = [o for o in dt.objects if o is not None and o.name.startswith(n) and o is not so]
        lo = lo[0]
        h_src, h_cp = mesh_geometry_hash(lo.data), mesh_geometry_hash(so.data)
        d = dict(geometry_hash_source=h_src, geometry_hash_copy=h_cp, equal=h_src == h_cp, vertices=len(so.data.vertices))
        if n == H['body']:
            names0 = sorted(g.name for g in lo.vertex_groups)
            d['original_vertex_groups'] = len(names0)
            d['vgroups_hash_source'] = original_vgroups_hash(lo, set(names0))
            d['vgroups_hash_copy'] = original_vgroups_hash(so, set(names0))
            d['vgroups_equal'] = d['vgroups_hash_source'] == d['vgroups_hash_copy']
            added = sorted(g.name for g in so.vertex_groups if g.name not in names0)
            bones = {b.name for b in rig.data.bones}
            d['added_vertex_groups'] = len(added)
            d['added_all_bone_names'] = all(a in bones for a in added)
            d['shape_keys'] = so.data.shape_keys is not None
            if not d['vgroups_equal']:
                note('BODY_UNCHANGED', f'{n}: original vertex groups changed')
            if not d['added_all_bone_names']:
                note('BODY_UNCHANGED', f'{n}: a vertex group that is not a bone was added')
            if d['shape_keys']:
                note('BODY_UNCHANGED', f'{n}: shape keys present')
        Ms, Mc = np.array(lo.matrix_world), np.array(so.matrix_world)
        # the copy is parented to the rig (identity), so compare the world matrices
        d['world_matrix_max_diff'] = float(np.abs(Ms - Mc).max())
        if not d['equal']:
            note('BODY_UNCHANGED', f'{n}: mesh geometry hash differs')
        if d['world_matrix_max_diff'] > 1e-6:
            note('BODY_UNCHANGED', f'{n}: object transform differs ({d["world_matrix_max_diff"]:.2e})')
        hashes[n] = d
    rig.data.pose_position = pose_mode0
    bpy.context.view_layer.update()
    R['body_unchanged'] = hashes
    # remove the library objects again (this file is not saved)
    for o in dt.objects:
        if o is not None and o.name not in names_src:
            bpy.data.objects.remove(o)
except Exception as e:                                         # noqa
    note('BODY_UNCHANGED', 'check failed: ' + repr(e))
    R['body_unchanged_error'] = repr(e)

# =============================================================================================== ON_HERO
try:
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    R['armatures'] = [o.name for o in arms]
    if len(arms) != 1 or arms[0].name != H['rig']:
        note('ON_HERO', f'armatures: {R["armatures"]}')
    mod = [m for m in body.modifiers if m.type == 'ARMATURE']
    R['body_armature_modifier_target'] = mod[0].object.name if mod and mod[0].object else None
    if not mod or mod[0].object != rig:
        note('ON_HERO', 'Body is not skinned to the rig')
    # bones inside the mesh (ray parity) at the bind pose
    me = body.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    me.calc_loop_triangles()
    tri = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get('vertices', tri)
    tri = tri.reshape(-1, 3)
    bv = bvh_of(co, tri)

    def inside(p):
        votes = 0
        for dvec in (Vector((0, 0, 1)), Vector((1, 0.13, 0.07)).normalized(), Vector((-0.11, 1, 0.17)).normalized()):
            n, pos = 0, Vector(p)
            for _ in range(40):
                hit = bv.ray_cast(pos, dvec)
                if hit[0] is None:
                    break
                n += 1
                pos = hit[0] + dvec * 1e-5
            votes += (n % 2)
        return votes >= 2
    outside = []
    for b in rig.data.bones:
        if b.name == 'Root':
            continue
        if not inside(rig.matrix_world @ b.head_local):
            outside.append(b.name)
    R['bones_outside_mesh'] = outside
    R['bone_count'] = len(rig.data.bones)
    if outside:
        note('ON_HERO', f'{len(outside)} bone heads outside the body mesh: {outside[:8]}')
    # limb joints vs the local cross-section centroid of the limb: the section perpendicular to the segment axis (+-20 mm slab) 5 cm from the joint on the proximal
    # side (and the distal side for elbow / knee), vertices whose dominant skin bone is that segment's bone; the joint's offset from its centroid must be <= 20 mm.
    # (the hand / foot are not part of a forearm / shank section and bias a section closer than ~4 cm to the joint)
    jn = rigj['joints']
    cen = {}

    vgn2 = {g.index: g.name for g in body.vertex_groups}
    dom2 = np.array([vgn2.get(max(v.groups, key=lambda g: g.weight).group, '') if len(v.groups) else '' for v in body.data.vertices], dtype=object)

    def sect(J, ax, off, ok, radius=0.15):
        rel = co - (J + ax * off)
        along = rel @ ax
        perp = rel - np.outer(along, ax)
        sel = ok & (np.abs(along) < 0.020) & (np.linalg.norm(perp, axis=1) < radius)
        if sel.sum() < 6:
            return None
        cc = co[sel].mean(axis=0) - (J + ax * off)
        return cc - np.dot(cc, ax) * ax

    for sd in 'LR':
        for jname, prox, dist_ in (('elbow', 'shoulder', 'wrist'), ('knee', 'hip', 'ankle'), ('wrist', 'elbow', None), ('ankle', 'knee', None)):
            J = np.array(jn[f'{jname}_{sd}'])
            ax_p = (J - np.array(jn[f'{prox}_{sd}']))
            ax_p /= np.linalg.norm(ax_p)
            side = 'Left' if sd == 'L' else 'Right'
            prox_names = {'elbow': ('UpperArm',), 'knee': ('UpperLeg',), 'wrist': ('LowerArm',), 'ankle': ('LowerLeg',)}[jname]
            dist_names = {'elbow': ('LowerArm',), 'knee': ('LowerLeg',)}.get(jname, ())
            sides = [(ax_p, -1.0, prox_names)]
            if dist_ is not None:
                ax_d = np.array(jn[f'{dist_}_{sd}']) - J
                sides.append((ax_d / np.linalg.norm(ax_d), +1.0, dist_names))
            vals = []
            for ax, sg, nm in sides:
                ok_ = np.array([n in {side + g for g in nm} for n in dom2])
                v5 = sect(J, ax, sg * 0.05, ok_)
                if v5 is not None:
                    vals.append(float(np.linalg.norm(v5)))
            cen[f'{jname}_{sd}'] = float(max(vals)) if vals else None
    R['limb_joint_to_section_centroid_m'] = cen
    for k, v in cen.items():
        if v is None:
            note('ON_HERO', f'{k}: no cross-section vertices found')
        elif v > 0.020:
            note('ON_HERO', f'{k}: {v * 1000:.1f} mm from the cross-section centroid (> 20)')
    R['rig_measures'] = rigj['measures']
    # all 16 actions drive the armature
    bone_names = {b.name for b in rig.data.bones}
    drv = {}
    for clip in CLIPS:
        act = bpy.data.actions[clip]
        paths = set()
        try:
            for ly in act.layers:
                for st in ly.strips:
                    for cb in st.channelbags:
                        for fc in cb.fcurves:
                            paths.add(fc.data_path)
        except Exception:
            paths = {fc.data_path for fc in act.fcurves}
        bad = [p for p in paths if not (p.startswith('pose.bones["') and p.split('"')[1] in bone_names)]
        drv[clip] = dict(fcurve_paths=len(paths), bad=len(bad))
        if bad or not paths:
            note('ON_HERO', f'{clip}: action does not drive the rig ({len(bad)} foreign paths, {len(paths)} total)')
    R['action_drives_rig'] = drv
except Exception as e:                                         # noqa
    note('ON_HERO', 'check failed: ' + repr(e))
    R['on_hero_error'] = repr(e)

# =============================================================================================== sampled-frame mesh checks
vgnames = {g.index: g.name for g in body.vertex_groups}
nv = len(body.data.vertices)
wmax_name = []
for v in body.data.vertices:
    best, bw = None, -1.0
    for g in v.groups:
        if g.weight > bw:
            best, bw = vgnames[g.group], g.weight
    wmax_name.append(best)
wmax_name = np.array(wmax_name, dtype=object)


def bones_below(root):
    out = set()
    for b in rig.data.bones:
        p = b
        while p is not None:
            if p.name == root:
                out.add(b.name)
                break
            p = p.parent
    return out


HAND = {sd: bones_below(f'{sd}Hand') for sd in ('Left', 'Right')}
ARMB = {sd: bones_below(f'{sd}UpperArm') for sd in ('Left', 'Right')}
TORSO_B = {'Hips', 'Spine', 'Chest', 'UpperChest', 'Neck'}
hand_mask = {sd: np.array([n in HAND[sd] for n in wmax_name]) for sd in HAND}
arm_mask = np.array([n in (ARMB['Left'] | ARMB['Right']) for n in wmax_name])
torso_mask = np.array([n in TORSO_B for n in wmax_name])
R['hand_vertices'] = {sd: int(hand_mask[sd].sum()) for sd in hand_mask}

tris_body = None


def tri_subset(tris, mask):
    return tris[mask[tris].all(axis=1)]


rack_o = bpy.data.objects['Racket_Classic']


def racket_bvh():
    parts = [eval_world(o) for o in (rack_o, grip_o, butt_o)]
    offs = np.cumsum([0] + [len(p[0]) for p in parts])
    return bvh_of(np.vstack([p[0] for p in parts]), np.vstack([p[1] + offs[i] for i, p in enumerate(parts)]))


def hand_to_grip(sd, co_b, tris_b):
    """min distance (m) from the hand's skinned vertices to the racket (frame + handle + butt cap), the number of overlapping hand / racket triangle pairs and the
    deepest penetration of a hand vertex into the racket (m)"""
    gb = racket_bvh()
    hv = np.where(hand_mask[sd])[0]
    dmin, pen = 1e9, 0.0
    for i in hv:
        loc = gb.find_nearest(Vector(co_b[i]))
        if loc[0] is not None:
            s = (Vector(co_b[i]) - loc[0]).dot(loc[1])
            dmin = min(dmin, loc[3])
            if s < 0:
                pen = max(pen, loc[3])
    ht = tri_subset(tris_b, hand_mask[sd])
    hb = bvh_of(co_b, ht)
    ov = len(hb.overlap(gb))
    return dmin, ov, pen


try:
    # --- baselines: the right-hand grip and the left THROAT grip at ReadyIdle frame 0; the left HANDLE grip at the first Backhand frame with l_grip = 1 and attached
    act = activate('ReadyIdle')
    sc.frame_set(0)
    bpy.context.view_layer.update()
    cob, trb = eval_world(body)
    base = {}
    for sd in ('Right', 'Left'):
        d_, ov_, pn_ = hand_to_grip(sd, cob, trb)
        base[sd] = dict(min_dist_mm=d_ * 1000.0, overlap_pairs=ov_, penetration_mm=pn_ * 1000.0)
    act = activate('Backhand')
    lg = A['Backhand/l_grip']
    at = A['Backhand/l_attach']
    fh = [i for i in range(len(lg)) if lg[i] >= 0.999 and at[i] >= 0.99]
    sc.frame_set(fh[0] if fh else 0)
    bpy.context.view_layer.update()
    cob, trb = eval_world(body)
    d_, ov_, pn_ = hand_to_grip('Left', cob, trb)
    base['LeftHandle'] = dict(frame=fh[0] if fh else None, min_dist_mm=d_ * 1000.0, overlap_pairs=ov_, penetration_mm=pn_ * 1000.0)
    R['grip_baseline'] = base
    # --- socket matrix constant over all frames of all clips; right-hand fingers closed
    mats = []
    right_fingers = [b for b in HAND['Right'] if b != 'RightHand']
    finger_dev = 0.0
    ref_q = {}
    held = {}
    left_ov_limit = max(base['Left']['overlap_pairs'], base['LeftHandle']['overlap_pairs'])
    left_pen_limit = max(base['Left']['penetration_mm'], base['LeftHandle']['penetration_mm'])
    foot_planted_floor = []
    for clip in CLIPS:
        act = activate(clip)
        n = int(round(act.frame_end)) + 1
        contact_f = None if meta[clip]['contact_s'] is None else int(round(meta[clip]['contact_s'] * FPS))
        frames = sorted(set(list(range(0, n, 3)) + [n - 1] + ([contact_f] if contact_f is not None else [])))
        mind_R, ov_R, pen_R, mind_L_att, ov_L, pen_L = [], [], [], [], [], []
        floor_min = 1e9
        for f in frames:
            sc.frame_set(f)
            bpy.context.view_layer.update()
            Mloc = np.array(socket.matrix_local)
            mats.append(Mloc)
            for bn in right_fingers:
                q = np.array(rig.pose.bones[bn].rotation_quaternion)
                if bn not in ref_q:
                    ref_q[bn] = q.copy()
                finger_dev = max(finger_dev, float(np.abs(q - ref_q[bn]).max()))
            cob, trb = eval_world(body)
            floor_min = min(floor_min, float(cob[:, 2].min()))
            for o in (face, hair, bed_o, grip_o):
                if o is not None:
                    c2, _ = eval_world(o)
                    floor_min = min(floor_min, float(c2[:, 2].min()))
            dR, oR, pR = hand_to_grip('Right', cob, trb)
            mind_R.append(dR * 1000.0)
            ov_R.append(oR)
            pen_R.append(pR * 1000.0)
            att = float(A[clip + '/l_attach'][f]) if f < len(A[clip + '/l_attach']) else 0.0
            if att >= 0.99:
                dL, oL, pL = hand_to_grip('Left', cob, trb)
                mind_L_att.append((f, dL * 1000.0))
                ov_L.append(oL)
                pen_L.append(pL * 1000.0)
            # a planted foot (no lift, no heel raise) stands on the floor: its lowest vertex within 5 mm of the floor
            for sd, kl, kh in (('L', 'lift_L', 'heel_L'), ('R', 'lift_R', 'heel_R')):
                if A[clip + '/' + kl][f] <= 1e-6 and A[clip + '/' + kh][f] <= 1e-6:
                    zs = cob[[i for i in range(len(wmax_name)) if wmax_name[i] in ({'L': ('LeftFoot', 'LeftToes'), 'R': ('RightFoot', 'RightToes')}[sd])], 2].min()
                    foot_planted_floor.append((clip, f, sd, float(zs)))
        held[clip] = dict(frames_checked=len(frames), right_min_dist_mm_max=max(mind_R), right_overlap_max=max(ov_R), right_penetration_mm_max=max(pen_R),
                          left_attached_frames=len(mind_L_att), left_min_dist_mm_max=max([d for _, d in mind_L_att]) if mind_L_att else None,
                          left_overlap_max=max(ov_L) if ov_L else None, left_penetration_mm_max=max(pen_L) if pen_L else None, floor_min_m=floor_min)
        if max(mind_R) > 3.0:
            note('RACKET_HELD', f'{clip}: right hand {max(mind_R):.2f} mm from the racket')
        if max(ov_R) > base['Right']['overlap_pairs']:
            note('RACKET_HELD', f'{clip}: right hand / racket overlapping pairs {max(ov_R)} > baseline {base["Right"]["overlap_pairs"]}')
        if held[clip]['left_min_dist_mm_max'] is not None and held[clip]['left_min_dist_mm_max'] > 3.0:
            note('RACKET_HELD', f'{clip}: attached left hand {held[clip]["left_min_dist_mm_max"]:.2f} mm from the racket')
        # (penetration depths are reported for information only: the signed test depends on the racket's face normals; the gate uses distance and overlapping pairs)
        if floor_min < -0.003:
            note('IN_PLACE', f'{clip}: a vertex is {floor_min * 1000:.1f} mm below the floor')
    R['racket_held'] = held
    R['planted_foot_lowest_vertex_mm'] = dict(min=min([z for *_, z in foot_planted_floor] or [0]) * 1000.0, max=max([z for *_, z in foot_planted_floor] or [0]) * 1000.0,
                                              frames=len(foot_planted_floor))
    for clip, f, sd, z in foot_planted_floor:
        if z > 0.005 or z < -0.003:
            note('IN_PLACE', f'{clip} f{f}: planted {sd} foot lowest vertex at {z * 1000:.1f} mm')
            break
    M0 = mats[0]
    R['socket_matrix_max_dev'] = float(max(np.abs(M - M0).max() for M in mats))
    R['right_finger_pose_max_dev'] = finger_dev
    if R['socket_matrix_max_dev'] > 1e-6:
        note('RACKET_HELD', 'Hand_Racket matrix changes over the frames')
    if finger_dev > 1e-6:
        note('RACKET_HELD', 'right-hand finger pose changes over the frames')
    R['socket_parent'] = f'{socket.parent.name}:{socket.parent_bone}' if socket.parent else None
    if not (socket.parent == rig and socket.parent_bone == 'RightHand'):
        note('RACKET_HELD', 'Hand_Racket is not a child of the right-hand bone')
except Exception as e:                                         # noqa
    note('RACKET_HELD', 'check failed: ' + repr(e))
    R['racket_held_error'] = repr(e)

# =============================================================================================== Root bone / object carry no motion; two-hand release; slice
try:
    root_paths = []
    for clip in CLIPS:
        act = bpy.data.actions[clip]
        try:
            for ly in act.layers:
                for st in ly.strips:
                    for cb in st.channelbags:
                        for fc in cb.fcurves:
                            if 'pose.bones["Root"]' in fc.data_path:
                                root_paths.append((clip, fc.data_path))
        except Exception:
            pass
    R['root_bone_fcurves'] = len(root_paths)
    if root_paths:
        note('IN_PLACE', f'Root bone is animated in {len(root_paths)} f-curves')
    ad = rig.animation_data
    R['armature_object_translation'] = [float(x) for x in rig.location]
    if any(abs(x) > 1e-6 for x in rig.location):
        note('IN_PLACE', 'armature object has a translation')
    # release events from the traces
    ev = {}
    for clip in ('Backhand', 'BackhandWide', 'Return', 'VolleyBackhand', 'SliceApproach'):
        att = A[clip + '/l_attach']
        c = meta[clip]['contact_s']
        ci = None if c is None else int(round(c * FPS))
        d = dict(left_release_s=meta[clip]['events'].get('left_release_s'), att_at_contact=float(att[ci]) if ci is not None else None,
                 first_attached_frame=int(np.where(att >= 0.99)[0][0]) if (att >= 0.99).any() else None,
                 attached_at_end=float(att[-1]))
        if clip != 'SliceApproach':
            sh_ = A[clip + '/R_shoulder'] - A[clip + '/L_shoulder']
            yaw_ = np.degrees(np.arctan2(sh_[:, 1], sh_[:, 0]))
            yaw_ = np.abs((yaw_ - yaw_[0] + 180.0) % 360.0 - 180.0)
            pk = int(np.argmax(yaw_[:ci + 1]))
            d['take_back_peak_frame'] = pk
            d['attached_from_peak_through_contact'] = bool(np.all(att[pk:ci + 1] >= 0.99))
            if not d['attached_from_peak_through_contact']:
                note('RACKET_HELD', f'{clip}: left hand not attached on every frame from the take-back peak (f{pk}) to the contact (f{ci})')
            if d['left_release_s'] is None or d['left_release_s'] <= c:
                note('RACKET_HELD', f'{clip}: no left-hand release after the contact')
        else:
            rel = d['left_release_s']
            d['forward_swing_start_s'] = None
            d['off_hand_on_racket_from_release_to_finish_hold_end'] = bool(np.all(att[int(round(rel * FPS)):int(round((c + 0.4) * FPS))] < 0.5)) if rel is not None else None
        ev[clip] = d
    R['two_hand_events'] = ev
except Exception as e:                                         # noqa
    note('RACKET_HELD', 'event check failed: ' + repr(e))

# =============================================================================================== one-handed clips: the off hand is not on the racket from the take-back through the finish
# (the clips end on a pose blendable to ReadyIdle, whose off hand is on the throat, so the re-grasp starts after the finish is held: the interval tested ends at the
# third frame of the held finish)
try:
    ONE = ['Forehand', 'ForehandOpen', 'ForehandWide', 'ForehandShort', 'SliceApproach', 'Serve', 'Overhead', 'VolleyForehand']
    off = {}
    for clip in ONE:
        act = activate(clip)
        n = int(round(act.frame_end)) + 1
        sh_ = A[clip + '/R_shoulder'] - A[clip + '/L_shoulder']
        yaw_ = np.degrees(np.arctan2(sh_[:, 1], sh_[:, 0]))
        yaw_ = np.abs((yaw_ - yaw_[0] + 180.0) % 360.0 - 180.0)
        ci = int(round(meta[clip]['contact_s'] * FPS))
        pk = int(np.argmax(yaw_[:ci + 1]))
        if clip == 'SliceApproach':
            rel = meta[clip]['events'].get('left_release_s')
            pk = int(round(rel * FPS)) if rel is not None else pk
        sw_ = A[clip + '/sweet']
        v_ = np.linalg.norm(np.diff(sw_, axis=0), axis=1) * FPS
        ipk_ = int(v_.argmax())
        end_hold = n - 1
        run = 0
        for k in range(ipk_ + 1, len(v_)):
            run = run + 1 if v_[k] <= 0.12 * float(v_.max()) else 0
            if run >= 3:                                # the third consecutive slow frame of the held finish
                end_hold = k + 1
                break
        dmin = 1e9
        for f in range(pk, end_hold + 1):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            cob, trb = eval_world(body)
            dL, _, _ = hand_to_grip('Left', cob, trb)
            dmin = min(dmin, dL * 1000.0)
        att_arr = A[clip + '/l_attach']
        regrasp = [i for i in range(end_hold, n) if att_arr[i] > 0.02]
        off[clip] = dict(from_frame=pk, to_frame=end_hold, left_min_dist_mm=dmin, regrasp_starts_frame=regrasp[0] if regrasp else None, last_frame=n - 1)
        if dmin <= 3.0:
            note('RACKET_HELD', f'{clip}: the off hand is on the racket ({dmin:.2f} mm) between frame {pk} and the end of the held finish (frame {end_hold})')
    R['one_handed_off_hand'] = off
    acts = sorted(a.name for a in bpy.data.actions)
    R['actions_in_blend'] = acts
    if acts != sorted(CLIPS):
        note('ALL_CLIPS', f'actions in the blend: {acts}')
except Exception as e:                                         # noqa
    note('RACKET_HELD', 'one-handed check failed: ' + repr(e))

# =============================================================================================== READS_FROM_BEHIND occlusion + ON_HERO penetration
CAM = Vector((0.0, 4.6, 2.0))                                # the behind-the-court proof camera (proofs.py VIEWS['behind'])
try:
    occ = {}
    pen = {}
    for clip in CLIPS:
        act = activate(clip)
        n = int(round(act.frame_end)) + 1
        c = meta[clip]['contact_s']
        names = {'finish': None}
        sw = A[clip + '/sweet']
        v = np.linalg.norm(np.diff(sw, axis=0), axis=1) * FPS
        ipk = int(v.argmax())
        vpk = float(v.max())
        fin = None
        for k in range(ipk + 1, len(v)):
            if v[k] <= 0.12 * vpk:
                fin = k
                break
        yaw_series = np.arctan2((A[clip + '/R_shoulder'] - A[clip + '/L_shoulder'])[:, 1], (A[clip + '/R_shoulder'] - A[clip + '/L_shoulder'])[:, 0])
        peak_back = int(np.argmax(np.abs(np.degrees(yaw_series - yaw_series[0]))))
        frames = {'peak_turn': peak_back, 'finish': fin if fin is not None else n - 1}
        if c is not None:
            frames['contact'] = int(round(c * FPS))
        occ[clip] = {}
        pen[clip] = {}
        for lab, f in frames.items():
            sc.frame_set(f)
            bpy.context.view_layer.update()
            cob, trb = eval_world(body)
            occ_meshes = [(cob, trb)]
            cf, tf = eval_world(face)
            occ_meshes.append((cf, tf))
            if hair is not None:
                ch, th = eval_world(hair)
                occ_meshes.append((ch, th))
            allc = np.vstack([m[0] for m in occ_meshes])
            offs = np.cumsum([0] + [len(m[0]) for m in occ_meshes])
            allt = np.vstack([m[1] + offs[i] for i, m in enumerate(occ_meshes)])
            bvh = bvh_of(allc, allt)
            # racket head samples: the string bed vertices
            cs, _ = eval_world(bed_o)
            idx = np.linspace(0, len(cs) - 1, 240).astype(int)
            pts = cs[idx]
            seen = 0
            for p in pts:
                dvec = Vector(p) - CAM
                dist = dvec.length
                hit = bvh.ray_cast(CAM, dvec.normalized(), dist - 0.002)
                if hit[0] is None:
                    seen += 1
            occ[clip][lab] = dict(frame=f, unoccluded_fraction=seen / len(pts))
            if lab == 'contact' and seen / len(pts) < 0.5:
                note('READS_FROM_BEHIND', f'{clip}: only {seen / len(pts) * 100:.0f} % of the racket head is visible from behind at contact')
            # penetration: arm triangles (all three vertices skinned mainly to the arm bones, 13 cm or more from the shoulder joints) and racket triangles against the
            # torso triangle set (all three vertices skinned mainly to hips / spine / chest / neck): every overlapping triangle pair is measured by how far the arm /
            # racket triangle's vertices lie behind the torso triangle's plane (outward normal)
            tor_t = tri_subset(trb, torso_mask)
            if len(tor_t) > 0:
                tb = bvh_of(cob, tor_t)
                p0, p1, p2 = cob[tor_t[:, 0]], cob[tor_t[:, 1]], cob[tor_t[:, 2]]
                nrm = np.cross(p1 - p0, p2 - p0)
                nrm /= np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-12)

                def pair_depth(co_a, tri_a, pairs):
                    worst = 0.0
                    for ti, ai in pairs:
                        d_ = -((co_a[tri_a[ai]] - p0[ti]) @ nrm[ti])
                        worst = max(worst, float(min(d_.max(), 0.2)))
                    return worst
                shoulder_pts = [np.array(rig.matrix_world @ rig.pose.bones[f'{sd}UpperArm'].head) for sd in ('Left', 'Right')]
                far = np.array([min(np.linalg.norm(cob[i] - s_) for s_ in shoulder_pts) > 0.13 for i in range(len(cob))])
                arm_t = trb[(arm_mask[trb] & far[trb]).all(axis=1)]
                worst_arm = 0.0
                if len(arm_t):
                    worst_arm = pair_depth(cob, arm_t, tb.overlap(bvh_of(cob, arm_t)))
                cr, tr_ = eval_world(bpy.data.objects['Racket_Classic'])
                worst_rk = pair_depth(cr, tr_, tb.overlap(bvh_of(cr, tr_)))
                pen[clip][lab] = dict(frame=f, arm_depth_mm=worst_arm * 1000.0, racket_depth_mm=worst_rk * 1000.0)
    R['occlusion'] = occ
    R['torso_penetration'] = pen
    fitted = []
    for clip, d in pen.items():
        for lab, x in d.items():
            if x['arm_depth_mm'] > 15.0 or x['racket_depth_mm'] > 15.0:
                fitted.append(f'{clip}@{lab}: arm {x["arm_depth_mm"]:.0f} mm, racket {x["racket_depth_mm"]:.0f} mm')
    R['fitted_to_the_hero'] = fitted
except Exception as e:                                         # noqa
    note('READS_FROM_BEHIND', 'occlusion / penetration check failed: ' + repr(e))
    R['occlusion_error'] = repr(e)

R['failed'] = fails
json.dump(R, open(f'{DATA}/verify_blend_{tag}.json', 'w'), indent=1)
print('VERIFY_BLEND_DONE', tag, {k: len(v) for k, v in fails.items()})
for k, v in fails.items():
    for m in v[:12]:
        print('  FAIL', k, m)

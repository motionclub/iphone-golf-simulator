"""Right-hand finger rig + grip pose for the dressed heroes (runs inside Blender, headless).

The body mesh geometry is never edited.  What is added to the dressed copy:
  * armature `Rig_Hand_R` (identity transform): palm bone `Hand_R` + 3 bones for each of index / middle / ring / pinky / thumb,
    heads/tails taken from the mesh itself (handmodel.py),
  * vertex groups with the same names on the body (skin weights, right hand only),
  * an Armature modifier on the body, the body / face (/ hair) parented to the rig,
  * actions `Pose_GripClosed` (active) and `Pose_Rest`: rotation of the finger bones about their local X (the flexion hinge),
  * `Hand_Racket` parented to bone `Hand_R`.

Grip pose: the racket keeps the classic-racket chat's hold (shaft 52 deg off the fingers, face rolled 45 deg) expressed in the landmark hand
frame; its position in the palm plane (and a small yaw) is searched so that as many fingers as possible wrap it; the lift off the palm is the
smallest that clears the OPEN hand (female: fingers straightened virtually, her relaxed hand is cupped; male: bind pose); then every finger is
closed on the grip until its segments touch (stop 0.3 mm short).  The search runs on a numpy twin of the armature (handpose_np.py) that is
verified against Blender's real armature modifier, and the chosen pose is re-checked against the real racket mesh with exact triangle tests."""
import json
import math

import numpy as np
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from dl_common import *
from handlib import *
from handmodel import *
import handpose_np as HP

MARGIN = 0.0003
LIMITS = dict(MCP=(-35.0, 95.0), PIP=(-8.0, 110.0), DIP=(-8.0, 80.0))     # hard anatomical range, degrees relative to the bind pose
RELAXED = [70.0, 90.0, 55.0]      # no-contact fingers stop at a relaxed-grip curl instead of the anatomical maximum
MAX_NEIGHBOUR_DIFF = 25.0         # deg per joint between adjacent fingers (keeps the interdigital skin from shearing apart)
FINGER_ORDER = ['index', 'middle', 'ring', 'pinky']


def _unit(x):
    return x / np.linalg.norm(x)


def create_rig(digits, landmark, collection):
    wrist, mid_mcp, u, v, p = landmark
    arm = bpy.data.armatures.new('Rig_Hand_R')
    rig = bpy.data.objects.new('Rig_Hand_R', arm)
    collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones

    def add(name, head, tail, parent=None, connect=False, zvec=p):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        b.use_deform = True
        d = _unit(np.asarray(tail) - np.asarray(head))
        zv = zvec - np.dot(zvec, d) * d
        b.align_roll(Vector(_unit(zv)))
        if parent is not None:
            b.parent = eb[parent]
            b.use_connect = connect
        return b

    add('Hand_R', wrist, mid_mcp, None)
    for nm in ('index', 'middle', 'ring', 'pinky', 'thumb'):
        cap = nm.capitalize()
        J = digits[nm]['J']
        add(f'{cap}_1', J[0], J[1], 'Hand_R', False)
        add(f'{cap}_2', J[1], J[2], f'{cap}_1', True)
        add(f'{cap}_3', J[2], J[3], f'{cap}_2', True)
    bpy.ops.object.mode_set(mode='OBJECT')
    arm.display_type = 'STICK'
    rig.show_in_front = True
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'
    return rig


def add_weights(body, hand, W):
    for name, w in W.items():
        vg = body.vertex_groups.get(name) or body.vertex_groups.new(name=name)
        for k in np.where(w > 1e-4)[0]:
            vg.add([int(hand[k])], float(w[k]), 'REPLACE')


class PoseEval:
    """evaluate the body through the real armature modifier; set joint angles in degrees."""

    def __init__(self, body, rig, hand):
        self.body, self.rig, self.hand = body, rig, hand

    def set_angles(self, ang):
        for name, a in ang.items():
            self.rig.pose.bones[name].rotation_euler = (math.radians(a), 0.0, 0.0)
        bpy.context.view_layer.update()

    def co(self):
        dg = bpy.context.evaluated_depsgraph_get()
        ev = self.body.evaluated_get(dg)
        m = ev.to_mesh()
        a = np.empty(len(m.vertices) * 3, np.float32)
        m.vertices.foreach_get('co', a)
        ev.to_mesh_clear()
        return a.reshape(-1, 3).astype(np.float64)[self.hand]


def signed_bend(d_prev, d_next, p):
    pt = _unit(p - np.dot(p, d_prev) * d_prev)
    return math.degrees(math.atan2(np.dot(d_next, pt), np.dot(d_next, d_prev)))


def zero_angles():
    return {f'{nm}_{k}': 0.0 for nm in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb') for k in (1, 2, 3)}


def open_angles(digits, landmark):
    """angles (deg) that straighten every finger into the palm plane (female: her relaxed hand is cupped).  Thumb stays at its bind pose."""
    wrist, mid_mcp, u, v, p = landmark
    out = zero_angles()
    for nm in FINGER_ORDER:
        J = digits[nm]['J']
        cap = nm.capitalize()
        d1, d2, d3 = _unit(J[1] - J[0]), _unit(J[2] - J[1]), _unit(J[3] - J[2])
        meta = _unit(J[0] - wrist)
        out[f'{cap}_1'] = float(np.clip(-signed_bend(meta, d1, p), LIMITS['MCP'][0], 0.0))
        out[f'{cap}_2'] = float(np.clip(-signed_bend(d1, d2, p), LIMITS['PIP'][0], 0.0))
        out[f'{cap}_3'] = float(np.clip(-signed_bend(d2, d3, p), LIMITS['DIP'][0], 0.0))
    return out


def tri_bvh(V, T):
    return BVHTree.FromPolygons([tuple(map(float, x)) for x in V], [tuple(int(i) for i in t) for t in T], epsilon=0.0)


def racket_mesh_world(rk, M):
    V, T, off = [], [], 0
    for n in ('Grip', 'ButtCap', 'Racket_Classic', 'StringBed'):
        o = rk[n]
        v_ = mesh_co(o).astype(float)
        V.append(v_ @ M[:3, :3].T + M[:3, 3])
        T.append(mesh_tris(o) + off)
        off += len(v_)
    return np.concatenate(V), np.concatenate(T)


def male_calibration(Mm):
    """male grip pose expressed in the male landmark hand frame: R_rel (3x3), t_rel (3,)."""
    with bpy.data.libraries.load(SRC['male_body'], link=False) as (s, d):
        d.objects = ['Body_M']
    mb = d.objects[0]
    co_m = mesh_co(mb).astype(float)
    adj_m = adjacency(len(co_m), edges_of(mb.data))
    hand_m = hand_region(co_m, adj_m, 'male')
    fr0_m = pca_frame(co_m[hand_m])
    uc_m, dig_m = build_model(co_m, adj_m, 'male', hand_m, fr0_m)
    wr_m, mm_m, u_m, v_m, p_m = landmark_frame(co_m, hand_m, dig_m, fr0_m)
    F_m = np.stack([u_m, v_m, p_m], 1)
    mbm = mb.data
    bpy.data.objects.remove(mb, do_unlink=True)
    bpy.data.meshes.remove(mbm)
    return F_m.T @ Mm[:3, :3], F_m.T @ (Mm[:3, 3] - mm_m)


def rot_about(axis, ang):
    axis = _unit(np.asarray(axis, float))
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


def build_and_pose(tag, body, rk, sockets, collections, socket_json_male, kit_objs=(), log=print):
    report = {}
    co = mesh_co(body).astype(float)
    me = body.data
    adj = adjacency(len(co), edges_of(me))
    hand = hand_region(co, adj, tag)
    frame0 = pca_frame(co[hand])
    ucut, digits = build_model(co, adj, tag, hand, frame0)
    landmark = landmark_frame(co, hand, digits, frame0)
    wrist, mid_mcp, u, v, p = landmark
    F = np.stack([u, v, p], 1)
    Wt = finger_weights(co, hand, digits, p)
    rig = create_rig(digits, landmark, collections['rig'])
    add_weights(body, hand, Wt)
    mod = body.modifiers.new('Rig_Hand_R', 'ARMATURE')
    mod.object = rig
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False
    mod.use_deform_preserve_volume = False
    for o in [body] + [o for o in bpy.data.objects if o.type == 'MESH' and o is not body and o.name in ('Face_M', 'Face_F', 'Hair_F')]:
        o.parent = rig
        o.parent_type = 'OBJECT'
        o.matrix_parent_inverse = rig.matrix_world.inverted()
    bpy.context.view_layer.update()
    pe = PoseEval(body, rig, hand)
    rest_hand = co[hand]
    pe.set_angles(zero_angles())
    report['rest_pose_max_dev_m'] = float(np.abs(pe.co() - rest_hand).max())
    log('rest pose deviation', report['rest_pose_max_dev_m'])

    # ---- numpy twin of the armature, verified against Blender with random poses
    lbs = HP.NumpyLBS(rig, rest_hand, Wt)
    rng = np.random.RandomState(7)
    worst = 0.0
    for _ in range(4):
        test = {n: float(rng.uniform(-10, 70)) for n in zero_angles()}
        pe.set_angles(test)
        worst = max(worst, float(np.abs(pe.co() - lbs.skin(test)).max()))
    report['numpy_vs_blender_max_err_m'] = worst
    log('numpy twin vs Blender armature: max error %.2e m' % worst)
    assert worst < 5e-5, 'numpy skinning twin does not match the armature'
    d_tip = np.linalg.norm(rest_hand - digits['index']['J'][3], axis=1)
    tipk = int(np.argmin(d_tip))
    pe.set_angles(dict(zero_angles(), Index_1=30.0))
    disp = pe.co()[tipk] - rest_hand[tipk]
    report['flex_dir_test_disp_dot_p'] = float(np.dot(disp, p))
    assert np.dot(disp, p) > 0
    pe.set_angles(zero_angles())

    # ---- baseline hold (racket chat) in the landmark frame
    Mm = np.eye(4)
    sjm = socket_json_male['socket_bind_pose_blender']
    for i, k in enumerate(('X', 'Y', 'Z')):
        Mm[:3, i] = sjm[k]
    Mm[:3, 3] = sjm['position']
    R_rel, t_rel = male_calibration(Mm)
    report['male_calibration'] = dict(R_rel=R_rel.tolist(), t_rel=t_rel.tolist())
    open_ang = zero_angles() if tag == 'male' else open_angles(digits, landmark)
    report['open_angles'] = open_ang
    X_open = lbs.skin(open_ang)
    seg_masks = {nm: [Wt[f'{nm.capitalize()}_{k}'] > 0.55 for k in (1, 2, 3)] for nm in FINGER_ORDER}
    tops = list(RELAXED)

    R0 = F @ R_rel

    def orient(dyaw_deg, tilt_deg, roll_deg):
        R1 = rot_about(p, math.radians(dyaw_deg)) @ R0                 # yaw about the palm normal (axis swings in the palm plane)
        R2 = rot_about(u, math.radians(tilt_deg)) @ R1                 # tilt about the finger direction (wrist deviation)
        return rot_about(R2[:, 1], math.radians(roll_deg)) @ R2        # roll about the shaft (does not touch the grip contact)

    def place(du, dv, dyaw_deg, W, tilt_deg=0.0, roll_deg=0.0):
        M = np.eye(4)
        M[:3, :3] = orient(dyaw_deg, tilt_deg, roll_deg)
        M[:3, 3] = mid_mcp + u * (t_rel[0] + du) + v * (t_rel[1] + dv) + p * W
        return M

    def solve_lift(du, dv, dyaw_deg, tilt_deg=0.0):
        lo, hi = -0.03, 0.12
        for _ in range(36):
            mid = 0.5 * (lo + hi)
            rkm = HP.RacketModel(place(du, dv, dyaw_deg, mid, tilt_deg))
            if rkm.dist(X_open).min() >= 0.0004:
                hi = mid
            else:
                lo = mid
        return hi

    def close_all(M):
        rkm = HP.RacketModel(M)
        ang = dict(open_ang)
        res = {}
        for nm in FINGER_ORDER:
            cap = nm.capitalize()
            names = [f'{cap}_1', f'{cap}_2', f'{cap}_3']
            cur, frozen, trace = HP.close_digit_np(lbs, rkm, ang, names, seg_masks[nm], tops, margin=MARGIN)
            for k in range(3):
                ang[names[k]] = cur[k]
            res[nm] = (cur, trace)
        for _ in range(4):                     # neighbouring fingers: open the more curled one (never closes -> no new penetration)
            for a_, b_ in zip(FINGER_ORDER[:-1], FINGER_ORDER[1:]):
                for k in (1, 2, 3):
                    na, nb = f'{a_.capitalize()}_{k}', f'{b_.capitalize()}_{k}'
                    if ang[nb] - ang[na] > MAX_NEIGHBOUR_DIFF:
                        ang[nb] = ang[na] + MAX_NEIGHBOUR_DIFF
                    elif ang[na] - ang[nb] > MAX_NEIGHBOUR_DIFF:
                        ang[na] = ang[nb] + MAX_NEIGHBOUR_DIFF
        X = lbs.skin(ang)
        d_f = {nm: float(min(rkm.dist(X[seg_masks[nm][k]]).min() for k in range(3) if seg_masks[nm][k].any())) for nm in FINGER_ORDER}
        pen = float(rkm.dist(X).min())
        score = 0.0
        for nm in FINGER_ORDER:
            cap = nm.capitalize()
            tot = sum(ang[f'{cap}_{k}'] - open_ang[f'{cap}_{k}'] for k in (1, 2, 3))
            if d_f[nm] <= 0.0008:
                score += 1.0 + 0.5 * min(1.0, tot / 150.0)
        if pen < -0.0004:
            score -= 5.0
        return score, ang, d_f, pen, res

    # obstacles for the collision term: the body outside the hand (arm, hip, thigh ...) and the kit pieces actually worn (exact triangle overlaps)
    idx_in_hand = -np.ones(len(co), np.int64)
    idx_in_hand[hand] = np.arange(len(hand))
    tris_body = mesh_tris(body)
    nh_mask = ~np.any(idx_in_hand[tris_body] >= 0, axis=1)
    obst = {'body': tri_bvh(co, tris_body[nh_mask])}
    for o in kit_objs:
        obst[o.name] = tri_bvh(mesh_co(o, world=True), mesh_tris(o))

    nh_vert = np.ones(len(co), bool)
    nh_vert[hand] = False
    cloud = [co[nh_vert]]
    for o in kit_objs:
        cloud.append(mesh_co(o, world=True))
    cloud = np.concatenate(cloud)
    cloud = cloud[np.linalg.norm(cloud - mid_mcp, axis=1) < 0.32]
    report['obstacle_cloud_points'] = int(len(cloud))

    def proxy_pen(M):
        """number of obstacle vertices (body outside the hand + worn kit) inside the grip / stem / butt-cap model: cheap collision proxy."""
        return int((HP.RacketModel(M).dist(cloud) < 0.0).sum())

    def collisions(M, X_hand=None):
        V_r, T_r = racket_mesh_world(rk, M)
        rt = tri_bvh(V_r, T_r)
        n = {k: len(rt.overlap(t)) for k, t in obst.items()}
        if X_hand is not None:
            ht = tri_bvh(X_hand, T_hand_local)
            n['hand_vs_racket_mesh'] = len(ht.overlap(rt))
            n['hand_vs_body'] = len(ht.overlap(obst['body']))
            for o in kit_objs:
                n['hand_vs_' + o.name] = len(ht.overlap(obst[o.name]))
        return n

    T_hand_local = idx_in_hand[tris_body]
    T_hand_local = T_hand_local[np.all(T_hand_local >= 0, axis=1)]

    # ---- stage 1: where on the palm does the hold wrap the most fingers
    stage1 = []
    for dy in (-40.0, -32.0, -24.0, -16.0, -8.0, 0.0, 8.0, 16.0):
        for du in (-0.035, -0.025, -0.015, -0.005, 0.005, 0.015, 0.025):
            for dv in (-0.055, -0.045, -0.035, -0.025, -0.015, -0.005, 0.005, 0.015):
                W = solve_lift(du, dv, dy)
                M_ = place(du, dv, dy, W)
                sc_, ang_, d_f, pen, res = close_all(M_)
                sc_ -= 0.15 * (abs(du) / 0.035 + abs(dv) / 0.035 + abs(dy) / 14.0)      # mild preference for the classic hold
                sc_ -= 0.004 * proxy_pen(M_)                                             # cheap collision proxy (grip/stem vs body + kit vertices)
                stage1.append((sc_, du, dv, dy))
    stage1.sort(reverse=True)
    log('stage 1 (%d placements): best score %.2f' % (len(stage1), stage1[0][0]))
    # ---- stage 2: add a small wrist tilt, re-close the fingers
    stage2 = []
    for sc1, du, dv, dy in stage1[:40]:
        for tilt in (-12.0, 0.0, 12.0):
            W = solve_lift(du, dv, dy, tilt)
            M_ = place(du, dv, dy, W, tilt)
            sc_, ang_, d_f, pen, res = close_all(M_)
            sc_ -= 0.15 * (abs(du) / 0.035 + abs(dv) / 0.035 + abs(dy) / 14.0) + 0.05 * abs(tilt) / 12.0
            sc_ -= 0.004 * proxy_pen(M_)
            stage2.append((sc_, du, dv, dy, tilt, W))
    stage2.sort(reverse=True)
    keep = [c for c in stage2 if c[0] >= stage2[0][0] - 1.5][:60]
    log('stage 2: %d candidates within 1.5 of the best score %.2f' % (len(keep), stage2[0][0]))
    # ---- stage 3: racket roll about the shaft + collisions (racket and posed fingers against the body and the kit)
    best = None
    table = []
    for sc_, du, dv, dy, tilt, W in keep:
        M0 = place(du, dv, dy, W, tilt, 0.0)
        s_, ang_, d_f, pen, res = close_all(M0)
        X_pose = lbs.skin(ang_)
        for roll in (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0):
            M = place(du, dv, dy, W, tilt, roll)
            col = collisions(M, X_pose)
            n_pairs = sum(col.values())
            penalty = (0.5 if n_pairs > 0 else 0.0) + n_pairs / 700.0 + 0.25 * col.get('hand_vs_racket_mesh', 0)       # hand through the racket is never accepted lightly
            total = sc_ - penalty - 0.01 * abs(((roll + 180.0) % 360.0) - 180.0) / 90.0   # `roll` is EXTRA to the classic hold (which already has the 45 deg face roll): tie-break towards 0
            table.append((round(total, 3), round(sc_, 3), n_pairs, du, dv, dy, tilt, roll, round(W, 4)))
            if best is None or total > best[0]:
                best = (total, du, dv, dy, tilt, roll, W, M, ang_, d_f, pen, res, col)
    table.sort(reverse=True)
    total, du, dv, dy, tilt, roll, Wv, M_world, ang, d_f, pen, res, col = best
    log('grip search best: total %.2f  du %.3f dv %.3f yaw %.0f tilt %.0f extra-roll %.0f (face roll %.0f from the palm normal) lift %.4f' % (total, du, dv, dy, tilt, roll, 45.0 + roll, Wv))
    log('collision pairs at best:', {k: v_ for k, v_ in col.items() if v_})
    log('finger-to-grip min distance (mm):', {k: round(x * 1000, 2) for k, x in d_f.items()}, ' hand min to racket model', round(pen * 1000, 2))
    report['search'] = dict(best=dict(total=total, du=du, dv=dv, yaw_deg=dy, tilt_deg=tilt, roll_deg=roll, face_roll_from_palm_normal_deg=45.0 + roll, lift=Wv), top8=table[:8],
                            n_stage1=len(stage1), n_stage2=len(keep), n_stage3=len(table), collisions_at_best=col)
    report['finger_min_dist_mm'] = {k: x * 1000 for k, x in d_f.items()}
    report['hand_min_dist_to_racket_model_mm'] = pen * 1000
    report['closing_trace'] = {k: [str(t) for t in v_[1]] for k, v_ in res.items()}
    report['racket_world_matrix'] = M_world.tolist()
    for k in list(ang):
        if k.startswith('Thumb'):
            ang[k] = 0.0                       # thumb stays in its bind pose (as in the racket chat's proof pose)
    report['angles'] = dict(ang)

    # ---- verify through Blender's real armature + the real racket mesh
    pe.set_angles(ang)
    Xb = pe.co()
    V_r, T_r = racket_mesh_world(rk, M_world)
    rtree = tri_bvh(V_r, T_r)
    htree = tri_bvh(Xb, T_hand_local)
    n_ov = len(rtree.overlap(htree))
    gv = V_r[:len(mesh_co(rk['Grip']))]
    d_grip = min(htree.find_nearest(Vector(q))[3] for q in gv[::2])
    report['verify'] = dict(racket_hand_tri_overlaps=n_ov, grip_to_hand_min_dist_mm=d_grip * 1000,
                            numpy_vs_blender_final_max_err_m=float(np.abs(Xb - lbs.skin(ang)).max()))
    log('real-mesh check: racket/hand overlapping triangles', n_ov, ' grip-hand min dist %.2f mm' % (d_grip * 1000))

    # ---- racket socket + actions
    hr = rk['Hand_Racket']
    hr.parent = None
    hr.matrix_world = Matrix([tuple(r) for r in M_world])
    pe.set_angles(zero_angles())
    act_rest = bpy.data.actions.new('Pose_Rest')
    act_rest.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = act_rest
    for name in zero_angles():
        pb = rig.pose.bones[name]
        pb.rotation_euler = (0.0, 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1, group=name)
    act_grip = bpy.data.actions.new('Pose_GripClosed')
    act_grip.use_fake_user = True
    rig.animation_data.action = act_grip
    for name, a in ang.items():
        pb = rig.pose.bones[name]
        pb.rotation_euler = (math.radians(a), 0.0, 0.0)
        pb.keyframe_insert('rotation_euler', frame=1, group=name)
    bpy.context.view_layer.update()
    hr.matrix_basis = Matrix.Identity(4)
    hr.parent = rig
    hr.parent_type = 'BONE'
    hr.parent_bone = 'Hand_R'
    hr.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    P = hr.matrix_world.copy()            # basis is identity: this is the bone's parent matrix (Blender puts bone-children at the bone TAIL)
    hr.matrix_parent_inverse = P.inverted() @ Matrix([tuple(r) for r in M_world])
    bpy.context.view_layer.update()
    report['hand_racket_world_err'] = float(np.abs(np.array(hr.matrix_world) - M_world).max())
    report['bones'] = [b.name for b in rig.data.bones]
    report['vertex_groups_added'] = sorted(Wt.keys())
    report['hand_vertex_count'] = int(len(hand))
    return report

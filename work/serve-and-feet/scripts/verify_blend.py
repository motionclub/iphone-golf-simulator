"""Mesh-level measurements of the five new clips on the baked blend (Blender headless, evaluated deformed meshes).

  blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/verify_blend.py -- <male|female>

Definitions: GATE_DEFS_preregistered.md.  Writes data/verify_blend_<hero>.json (all numbers) and prints one line per failed definition."""
import json
import math
import os
import sys

import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

REPO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
sys.path.insert(0, REPO + '/work/serve-and-feet/scripts')
sys.path.insert(0, REPO + '/work/match-anim-set/scripts')
import loco
from common import mesh_geometry_hash, sha256_file  # noqa: E402  (read-only import of the previous job's helpers)

tag = sys.argv[sys.argv.index('--') + 1]
H = dict(male=dict(body='Body_M', face='Face_M', hair=None, rig='Rig_Male', src_hero='/work/male-pelvis-form3/export/merged_fd04bc28.blend'),
         female=dict(body='Body_F', face='Face_F', hair='Hair_F', rig='Rig_Female', src_hero='/work/female-full-merge/export/HeroBase_Female_FULL_STAGED.blend'))[tag]
sc = bpy.context.scene
rig = bpy.data.objects[H['rig']]
body = bpy.data.objects[H['body']]
face = bpy.data.objects[H['face']]
hair = bpy.data.objects[H['hair']] if H['hair'] else None
socket = bpy.data.objects['Hand_Racket']
bed = bpy.data.objects['StringBed']
hero = loco.Hero(tag)
sk = np.load(f'{loco.DATA}/skin_{tag}.npz')
dom = sk['dom']
rj = hero.rig
ix = rj.idx
FOOT = {'L': np.isin(dom, [ix['LeftFoot'], ix['LeftToes']]), 'R': np.isin(dom, [ix['RightFoot'], ix['RightToes']])}
floor = hero.floor
R = dict(tag=tag, floor_mm=floor * 1000.0)
FAIL = {}


def note(gate, msg):
    FAIL.setdefault(gate, []).append(msg)


def activate(clip):
    act = bpy.data.actions[clip]
    rig.animation_data_create()
    rig.animation_data.action = act
    try:
        rig.animation_data.action_slot = act.slots[0]
    except Exception:
        pass
    return act


def eval_co(obj):
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
    eo.to_mesh_clear()
    return co, tris.reshape(-1, 3)


def bone_pos(name):
    return np.array(rig.pose.bones[name].head) + np.array(rig.matrix_world.translation)


def hips_yaw():
    M = np.array(rig.pose.bones['Hips'].matrix)[:3, :3]
    Rr = rj.Rrest[ix['Hips']]
    fwd = M @ Rr.T @ np.array([0, -1.0, 0])
    a = np.array([-fwd[0], -fwd[1], fwd[2]])
    return math.degrees(math.atan2(a[0], a[1]))


def chest_yaw():
    M = np.array(rig.pose.bones['Chest'].matrix)[:3, :3]
    Rr = rj.Rrest[ix['Chest']]
    fwd = M @ Rr.T @ np.array([0, -1.0, 0])
    a = np.array([-fwd[0], -fwd[1], fwd[2]])
    return math.degrees(math.atan2(a[0], a[1]))


# --------------------------------------------------------------------------------------------------------- BODY_UNCHANGED (mesh geometry equals the source blend)
src = bpy.data.libraries  # (no linked libraries expected)
sidecar = json.load(open(f'{loco.MA}/data/build_rig_{tag}.json'))
want = sidecar['mesh_geometry_hash_after']
got = {}
for o in (body, face, hair):
    if o is not None:
        got[o.name] = mesh_geometry_hash(o.data)
R['mesh_hash'] = dict(now=got, expected=want)
for k, v in got.items():
    if want.get(k) != v:
        note('OTHER_CLIPS_UNCHANGED', f'mesh geometry hash of {k} differs from the match-anim-set stage')
R['source_sha256'] = dict(match_anims_blend=sha256_file(f'{loco.MA}/export/HeroBase_{"Male" if tag == "male" else "Female"}_MatchAnims.blend'),
                          hero_blend=sha256_file(REPO + H['src_hero']))

# --------------------------------------------------------------------------------------------------------- per clip
clips_meta = {}
CLIPS = ['Walk', 'RunForward', 'RunRight', 'RunLeft', 'Serve']
others = [a.name for a in bpy.data.actions if a.name not in CLIPS and not a.name.endswith('_old')]
R['other_actions'] = others
bone_names = rj.names
for clip in CLIPS:
    act = activate(clip)
    gen = json.loads(act['gen'])
    nF = int(act.frame_end) + 1
    rec = dict(frames=nF, length_s=(nF - 1) / 30.0, meta=gen)
    hL, hR, tL, tR, allmin = [], [], [], [], []
    yaw_h, yaw_c = [], []
    lpalm = []
    socket_rel = []
    sweet = []
    rk_clear = []
    toeL, toeR = [], []
    for f in range(nF):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        co, tris = eval_co(body)
        z = co[:, 2]
        hL.append(float(z[FOOT['L']].min() - floor))
        hR.append(float(z[FOOT['R']].min() - floor))
        allmin.append(float(z.min() - floor))
        yaw_h.append(hips_yaw())
        yaw_c.append(chest_yaw())
        toeL.append(bone_pos('LeftToes'))
        toeR.append(bone_pos('RightToes'))
        lpalm.append(float(bone_pos('LeftHand')[2]))
        bone_M = np.array(rig.pose.bones['RightHand'].matrix)
        socket_rel.append(np.linalg.inv(bone_M) @ np.array(socket.matrix_world))
        dg = bpy.context.evaluated_depsgraph_get()
        eb = bed.evaluated_get(dg)
        me = eb.to_mesh()
        bc = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get('co', bc)
        bc = bc.reshape(-1, 3) @ np.array(eb.matrix_world)[:3, :3].T + np.array(eb.matrix_world)[:3, 3]
        eb.to_mesh_clear()
        sweet.append(bc.mean(0))
    hL, hR = np.array(hL), np.array(hR)
    toeL, toeR = np.array(toeL), np.array(toeR)
    rec['foot_height_mm'] = dict(L=(hL * 1000).round(2).tolist(), R=(hR * 1000).round(2).tolist())
    rec['lowest_vertex_mm'] = float(min(allmin) * 1000)
    rec['hips_yaw_deg'] = np.round(yaw_h, 2).tolist()
    rec['chest_yaw_deg'] = np.round(yaw_c, 2).tolist()
    rec['left_palm_z_m'] = np.round(lpalm, 4).tolist()
    sr = np.array(socket_rel)
    rec['socket_max_dev'] = float(np.abs(sr - sr[0]).max())
    sweet = np.array(sweet)
    rec['sweet_z'] = np.round(sweet[:, 2], 4).tolist()
    # loop closure
    q0 = np.array([list(rig.pose.bones[n].rotation_quaternion) for n in bone_names])
    if gen.get('loop'):
        loops = {}
        sc.frame_set(0)
        bpy.context.view_layer.update()
        qa = np.array([list(rig.pose.bones[n].rotation_quaternion) for n in bone_names])
        la = np.array(rig.pose.bones['Hips'].location)
        sc.frame_set(nF - 1)
        bpy.context.view_layer.update()
        qb = np.array([list(rig.pose.bones[n].rotation_quaternion) for n in bone_names])
        lb = np.array(rig.pose.bones['Hips'].location)
        rec['loop_closure'] = dict(max_quat_diff=float(np.abs(qa - qb).max()), max_hips_diff=float(np.abs(la - lb).max()))
    # planted / clear statistics over the cycle (frames 0..N-1; the last frame repeats the first)
    n = nF - 1 if gen.get('loop') else nF
    st = {}
    for sd, h in (('L', hL[:n]), ('R', hR[:n])):
        st[sd] = dict(planted_frac=float((h <= 0.010).mean()), clear40_frac=float((h >= 0.040).mean()), clear60_frac=float((h >= 0.060).mean()), peak_mm=float(h.max() * 1000),
                      min_mm=float(h.min() * 1000))
    rec['stats'] = st
    # planted-foot speed along the travel direction (frames fully inside the pinned stance of the design)
    if gen.get('kind') in ('walk', 'run'):
        T = gen['cycle_s']
        Sfr = gen['S']
        trav = gen.get('travel', 0.0)
        d = np.array([-math.sin(math.radians(trav)), -math.cos(math.radians(trav)), 0.0])    # authoring (r,f) -> world (-r,-f)
        sp = {}
        for sd, toe, phase in (('R', toeR, 0.0), ('L', toeL, 0.5)):
            vs = []
            for k in range(n):
                u0, u1 = (k / n + phase) % 1.0, ((k + 1) / n + phase) % 1.0
                if u0 <= Sfr - 1e-9 and u1 <= Sfr + 1e-9 and u1 > u0:
                    vs.append(float(-np.dot(toe[k + 1] - toe[k], d) * 30.0))             # backwards speed of the ball joint along the travel axis
            sp[sd] = dict(n=len(vs), mean=float(np.mean(vs)) if vs else None, min=float(np.min(vs)) if vs else None, max=float(np.max(vs)) if vs else None)
        rec['planted_speed'] = sp
        rec['design_speed'] = gen['V']
    clips_meta[clip] = rec
R['clips'] = clips_meta

# --------------------------------------------------------------------------------------------------------- gate-style checks
for clip in ('Walk', 'RunForward', 'RunRight', 'RunLeft'):
    r = clips_meta[clip]
    g = 'WALK_STEPS' if clip == 'Walk' else 'RUN_BOTH_LEGS'
    lc = r['loop_closure']
    if lc['max_quat_diff'] > 1e-6 or lc['max_hips_diff'] > 1e-6:
        note(g, f'{clip}: loop does not close ({lc})')
    L = r['length_s']
    if clip == 'Walk' and not (1.0 - 1e-6 <= L <= 1.3 + 1e-6):
        note(g, f'Walk cycle {L:.3f} s outside 1.0-1.3')
    if clip != 'Walk' and not (0.5 - 1e-6 <= L <= 0.8 + 1e-6):
        note(g, f'{clip} cycle {L:.3f} s outside 0.50-0.80')
    h = {sd: np.array(r['foot_height_mm'][sd][:-1]) for sd in 'LR'}
    for sd in 'LR':
        s = r['stats'][sd]
        if clip == 'Walk':
            if s['planted_frac'] < 0.35:
                note(g, f'Walk {sd} foot planted only {s["planted_frac"]:.2f} of the cycle')
            if s['clear40_frac'] < 0.20:
                note(g, f'Walk {sd} foot clear (>=40 mm) only {s["clear40_frac"]:.2f} of the cycle')
            if s['peak_mm'] < 60:
                note(g, f'Walk {sd} foot peak {s["peak_mm"]:.0f} mm < 60')
        else:
            if s['planted_frac'] <= 0.0:
                note(g, f'{clip} {sd} foot is never planted')
            if s['peak_mm'] < 90 or s['clear60_frac'] <= 0:
                note(g, f'{clip} {sd} foot never clears 60 mm / peak {s["peak_mm"]:.0f} mm < 90')
            if s['planted_frac'] > 0.55:
                note(g, f'{clip} {sd} foot planted {s["planted_frac"]:.2f} of the cycle > 0.55')
    if clip != 'Walk':
        pk = sorted([r['stats']['L']['peak_mm'], r['stats']['R']['peak_mm']])
        if pk[0] < 0.7 * pk[1]:
            note(g, f'{clip}: weaker leg peak {pk[0]:.0f} mm < 70 % of {pk[1]:.0f}')
    if clip == 'Walk':
        both = ((h['L'] > 10) & (h['R'] > 10)).any()
        if both:
            note(g, 'Walk has a frame with both feet off the floor')
    ps = r['planted_speed']
    for sd in 'LR':
        if ps[sd]['n'] == 0 or abs(ps[sd]['min'] / r['design_speed'] - 1) > 0.08 or abs(ps[sd]['max'] / r['design_speed'] - 1) > 0.08:
            note(g, f'{clip} {sd} planted foot speed {ps[sd]} vs design {r["design_speed"]:.2f}')
    if r['lowest_vertex_mm'] < -3.0:
        note(g, f'{clip}: a vertex is {r["lowest_vertex_mm"]:.1f} mm below the floor')
    # direction of the runs: pelvis yaw relative to the Root
    yh = np.array(r['hips_yaw_deg'][:-1])
    if clip == 'RunRight' and yh.mean() < 50:
        note(g, f'RunRight pelvis yaw mean {yh.mean():.1f} < 50')
    if clip == 'RunLeft' and yh.mean() > -50:
        note(g, f'RunLeft pelvis yaw mean {yh.mean():.1f} > -50')
    if r['socket_max_dev'] > 1e-5:
        note(g, f'{clip}: racket socket moved ({r["socket_max_dev"]:.2e})')

# serve
r = clips_meta['Serve']
meta = r['meta']
fps = 30
yh = np.array(r['hips_yaw_deg'])
ts, tr, tt, td, tc = (int(round(meta[k] * fps)) for k in ('stance', 'release', 'trophy', 'deepest', 'contact'))
kn = np.array(meta.get('knee_deepest_frame', [td]))
r['hip_yaw'] = dict(frame0=float(yh[0]), stance=float(yh[ts]), release=float(yh[tr]), trophy=float(yh[tt]), deepest=float(yh[td]), contact=float(yh[tc]),
                    load_from_stance=float(yh[td] - yh[ts]), load_from_frame0=float(yh[td] - yh[0]), unwind_to_contact=float(yh[td] - yh[tc]),
                    chest_deepest=float(r['chest_yaw_deg'][td]), chest_stance=float(r['chest_yaw_deg'][ts]))
if r['hip_yaw']['load_from_stance'] < 25 or r['hip_yaw']['load_from_frame0'] < 25 or r['hip_yaw']['unwind_to_contact'] < 40:
    note('SERVE_HIPS', f'hip yaw {r["hip_yaw"]}')
pz = np.array(r['left_palm_z_m'])
r['bounce_check'] = dict(palm_min_to_release=float(pz[:tr + 1].min()), palm_frame0=float(pz[0]), palm_stance=float(pz[ts]), drop_after_stance_mm=float((pz[ts] - pz[ts:tr + 1].min()) * 1000),
                         drop_from_frame0_mm=float((pz[0] - pz[:tr + 1].min()) * 1000), palm_min_to_contact=float(pz[:tc].min()))   # GATE_DEFS_preregistered 2: from frame 0, not from the stance
if pz[0] - pz[:tr + 1].min() > 0.015 or pz[:tc].min() < 0.55:
    note('SERVE_BOUNCE', f'tossing palm dips: {r["bounce_check"]}, min before contact {pz[:tc].min():.3f}')
sz = np.array(r['sweet_z'])
lo, hi = max(0, tc - 6), min(len(sz), tc + 7)
r['contact_check'] = dict(contact_frame=tc, sweet_z_at_contact=float(sz[tc]), sweet_z_max_window=float(sz[lo:hi].max()), argmax_window=int(lo + sz[lo:hi].argmax()))
if sz[tc] < sz[lo:hi].max() - 0.04:
    note('SERVE_CONTACT', f'the sweet spot is not near its highest at the contact frame: {r["contact_check"]}')
if r['socket_max_dev'] > 1e-5:
    note('SERVE_CONTACT', f'Serve racket socket moved ({r["socket_max_dev"]:.2e})')
if r['lowest_vertex_mm'] < -3.0:
    note('SERVE_CONTACT', f'Serve: a vertex is {r["lowest_vertex_mm"]:.1f} mm below the floor')
R['fails'] = FAIL
json.dump(R, open(f'{loco.DATA}/verify_blend_{tag}.json', 'w'), indent=1, default=float)
for g, msgs in FAIL.items():
    for m in msgs:
        print('VERIFY_FAIL', g, m)
print('VERIFY_DONE', tag, 'failed definitions:', {g: len(m) for g, m in FAIL.items()})

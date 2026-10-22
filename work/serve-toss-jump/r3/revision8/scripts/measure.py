"""measure.py -- arm / racket numbers of the baked Serve (world metres, Blender Z up; hero root frame is the armature object).
blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/measure.py -- <male|female> [out.json] [action name]"""
import json, sys
import numpy as np
import bpy
a = sys.argv[sys.argv.index('--') + 1:]
tag = a[0]; outp = a[1] if len(a) > 1 else None; actname = a[2] if len(a) > 2 else 'Serve'
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
act = bpy.data.actions[actname]
rig.animation_data.action = act
try: rig.animation_data.action_slot = act.slots[0]
except Exception: pass
sc = bpy.context.scene
W = rig.matrix_world
def P(name, tail=False):
    b = rig.pose.bones[name]
    return np.array(W @ (b.tail if tail else b.head))
def angle(u, v):
    u = u / np.linalg.norm(u); v = v / np.linalg.norm(v)
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v), -1, 1))))
racket = bpy.data.objects.get('Racket_Classic'); bed = bpy.data.objects.get('StringBed'); grip = bpy.data.objects.get('Grip')
out = []
for f in range(int(act.frame_start), int(act.frame_end) + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    r = dict(f=f, t=f / 30.0)
    for s, S in (('L', 'Left'), ('R', 'Right')):
        sh = P(S + 'UpperArm'); el = P(S + 'LowerArm'); wr = P(S + 'Hand')
        r[s + 'wrist_rel_sh'] = (wr - sh).round(3).tolist()
        r[s + 'elbow_flex'] = 180.0 - angle(sh - el, wr - el)       # 0 = straight
        r[s + 'upper_dir_el'] = float(np.degrees(np.arcsin((el - sh)[2] / np.linalg.norm(el - sh))))
        r[s + 'wrist_z'] = float(wr[2]); r[s + 'sh_z'] = float(sh[2])
        r[s + 'elbow_rel_sh'] = (el - sh).round(3).tolist()
    head = P('Head'); r['head_z'] = float(head[2]); r['head'] = head.round(3).tolist()
    r['headtop_z'] = float(P('Head', True)[2])
    if bed is not None:
        bb = np.array([W @ v for v in [bed.matrix_world @ __import__('mathutils').Vector(c) for c in bed.bound_box]]) if False else None
        dg = bpy.context.evaluated_depsgraph_get()
        bc = np.array(bed.evaluated_get(dg).matrix_world.translation); r['bed'] = bc.round(3).tolist()
    if grip is not None:
        gc = np.array(grip.evaluated_get(dg).matrix_world.translation) if bed is not None else np.zeros(3); r['grip'] = gc.round(3).tolist()
        if bed is not None:
            ax = bc - P('RightHand'); r['racket_head_above_handle'] = float(ax[2]); r['racket_elev'] = float(np.degrees(np.arcsin(ax[2] / np.linalg.norm(ax))))
            r['racket_bed_rel_head'] = (bc - head).round(3).tolist()
    if racket is not None:
        dg = bpy.context.evaluated_depsgraph_get(); ev = racket.evaluated_get(dg); me = ev.to_mesh()
        V = np.array([ev.matrix_world @ v.co for v in me.vertices]); ev.to_mesh_clear()
        c = V.mean(0); u, sv, vt = np.linalg.svd(V - c, full_matrices=False); ax = vt[0]
        hand = P('RightHand')
        if np.dot(ax, c - hand) < 0: ax = -ax
        proj = (V - hand) @ ax; tip = V[proj.argmax()]
        r['rk_axis'] = ax.round(3).tolist(); r['rk_elev'] = float(np.degrees(np.arcsin(ax[2]))); r['rk_tip'] = tip.round(3).tolist(); r['rk_tip_z_minus_headtop'] = float(tip[2] - r['headtop_z'])
        r['rk_hoopc_rel_head'] = (c - head).round(3).tolist(); r['rk_hoopc_z_minus_hand_z'] = float(c[2] - hand[2])
    out.append(r)
if outp: json.dump(out, open(outp, 'w'))
for r in out[:56:2]:
    print('f%2d t%.2f  L wrist-sh %s flexL %5.1f upperEl %5.1f | wristZ-headtop %+.2f | R flex %5.1f | racket elev %s tipZ-headtop %s hoopc-head %s' % (
        r['f'], r['t'], r['Lwrist_rel_sh'], r['Lelbow_flex'], r['Lupper_dir_el'], r['Lwrist_z'] - r['headtop_z'], r['Relbow_flex'], ('%.0f' % r['rk_elev']) if 'rk_elev' in r else '-', ('%+.2f' % r['rk_tip_z_minus_headtop']) if 'rk_elev' in r else '-', r.get('rk_hoopc_rel_head')))

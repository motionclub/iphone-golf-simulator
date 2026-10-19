"""Toe-bone ground slide of a baked clip as the driver's MeasureSkate sees it: the Toes bone's horizontal speed relative to the ground when the clip is played at its design speed
(the hero moves along the travel axis at V), counted when the toe bone is within 15 mm of its READY height.   blender -b export/HeroBase_<H>_MatchAnims.blend --python scripts/dev/toe_slide.py -- <Rig> Walk RunForward ..."""
import sys, json
import numpy as np
import bpy
a = sys.argv[sys.argv.index('--') + 1:]
rig = bpy.data.objects[a[0]]
sc = bpy.context.scene
def toe_pos(side):
    pb = rig.pose.bones[f'{side}Toes']
    return np.array((rig.matrix_world @ pb.head))
def foot_pos(side):
    pb = rig.pose.bones[f'{side}Foot']
    return np.array((rig.matrix_world @ pb.head))
def setact(name):
    act = bpy.data.actions[name]
    rig.animation_data_create(); rig.animation_data.action = act
    try: rig.animation_data.action_slot = act.slots[0]
    except Exception: pass
    return act
setact('ReadyIdle'); sc.frame_set(0); bpy.context.view_layer.update()
rest = {s: toe_pos(s)[2] for s in ('Left', 'Right')}
restf = {s: foot_pos(s)[2] for s in ('Left', 'Right')}
print('toe rest z', rest, 'heel(foot bone) rest z', restf)
out = {}
for name in a[1:]:
    act = setact(name)
    meta = json.loads(bpy.data.actions[name].get('clip_meta', '{}')) if 'clip_meta' in bpy.data.actions[name] else {}
    nF = int(act.frame_end) + 1
    # design speed and travel direction (authoring frame r,f -> Blender -x,-y): from the clip's own table
    tab = json.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/data/clip_table_new.json'))
    V = tab['walkSpeed'] if name == 'Walk' else tab['runSpeed']
    heading = {'RunRight': 90.0, 'RunLeft': -90.0}.get(name, 0.0)       # travel direction (deg, + = right)
    th = np.radians(heading)
    tv = np.array([-np.sin(th), -np.cos(th), 0.0]) * V                # Blender world velocity of the hero (right = -x, forward = -y)
    P = {s: [] for s in ('Left', 'Right')}; H = {s: [] for s in ('Left', 'Right')}; HF = {s: [] for s in ('Left', 'Right')}
    for f in range(nF):
        sc.frame_set(f); bpy.context.view_layer.update()
        for s in P:
            p = toe_pos(s); P[s].append(p); H[s].append(p[2] - rest[s]); HF[s].append(foot_pos(s)[2] - restf[s])
    dt = 1.0 / 30
    res = {}
    for s in P:
        p = np.array(P[s]); v = np.diff(p, axis=0) / dt
        v[:, :2] += tv[:2]   # the hero travels: the toe's world velocity is its velocity in the hero's frame plus the hero's velocity... the hero moves +tv, so ground-relative = clip velocity + tv
        sp = np.hypot(v[:, 0], v[:, 1])
        h = np.array(H[s][1:])
        low = h < 0.015
        res[s] = dict(frames_low=int(low.sum()), frames_low_over_015=int((low & (sp > 0.15)).sum()), speeds_low=[round(float(x), 2) for x in sp[low]], h_mm=[round(float(x) * 1000, 1) for x in H[s]])
    out[name] = res
    n = nF - 1
    tot = sum(res[s]['frames_low_over_015'] for s in res)
    print('TOE', name, 'V', round(V, 3), 'cycle frames', n, {s: dict(low_frames=res[s]['frames_low'], low_frames_with_slide_over_0_15=res[s]['frames_low_over_015']) for s in res})
    for s in res:
        print('  ', s, 'h(mm):', res[s]['h_mm'][:nF], '\n     slide speeds while low:', res[s]['speeds_low'])
json.dump(out, open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/frame-rate-60/feet/data/toe_slide_%s.json' % a[0], 'w'))

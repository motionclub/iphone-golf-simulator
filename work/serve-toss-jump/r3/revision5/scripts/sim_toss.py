"""sim_toss.py -- offline model of the game's toss arm on the baked clip (the same maths as HeroTennisDriver.BuildServeRitualPoints + TossArm, no Unity):
the ball goes from the stance palm to the release palm by smoothstep over the wind-up (clip time 0.2 + 0.5 u), the left palm is pulled onto the ball by the two-bone reach.
blender -b export/HeroBase_<Hero>_MatchAnims.blend --python scripts/sim_toss.py -- <tag> [action]
prints: T_H (ball reaches the head bone height), the left elbow flex there and 0.15 s later, wrist height vs head.  Blender axes -> hero-local: x = -X, y = Z, z = -Y."""
import sys
import numpy as np
import bpy
a = sys.argv[sys.argv.index('--') + 1:]
tag = a[0]; actname = a[1] if len(a) > 1 else 'Serve'
rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
act = bpy.data.actions[actname]; rig.animation_data.action = act
try: rig.animation_data.action_slot = act.slots[0]
except Exception: pass
sc = bpy.context.scene; W = rig.matrix_world
loc = lambda v: np.array([-v[0], v[2], -v[1]])
def P(name):
    return loc(W @ rig.pose.bones[name].head)
data = {}
for f in range(int(act.frame_start), int(act.frame_end) + 1):
    sc.frame_set(f); bpy.context.view_layer.update()
    wr, mid, sh, el, hd = P('LeftHand'), P('LeftMiddleProximal'), P('LeftUpperArm'), P('LeftLowerArm'), P('Head')
    data[f] = dict(wr=wr, palm=wr + 0.7 * (mid - wr), sh=sh, el=el, head=hd, rsh=P('RightUpperArm'), rwr=P('RightHand'))
fi = lambda t: int(round(t * 30))
lerpf = lambda t, key: data[int(np.floor(t * 30))][key] * (1 - (t * 30 - np.floor(t * 30))) + data[min(int(np.floor(t * 30)) + 1, max(data))][key] * ((t * 30 - np.floor(t * 30)))
up = np.array([0, 1.0, 0])
H = data[fi(0.2)]['palm'] - 0.045 * up; R = data[fi(0.7)]['palm'] + 0.045 * up
d0 = data[6]; a_len = np.linalg.norm(d0['el'] - d0['sh']); b_len = np.linalg.norm(d0['wr'] - d0['el'])
def flex(c):
    c = min(c, a_len + b_len - 1e-3); cosi = (a_len ** 2 + b_len ** 2 - c ** 2) / (2 * a_len * b_len)
    return 180.0 - np.degrees(np.arccos(np.clip(cosi, -1, 1)))
sm = lambda u: u * u * (3 - 2 * u)
rows = []
for k in range(0, 41):
    u = k / 40.0; t = 0.2 + 0.5 * u; s = sm(u)
    ball = H * (1 - s) + R * s
    pc, wc, shc, hdc = lerpf(t, 'palm'), lerpf(t, 'wr'), lerpf(t, 'sh'), lerpf(t, 'head')
    wt = wc + (ball - 0.045 * up - pc)
    c = np.linalg.norm(wt - shc)
    rows.append(dict(u=u, t=t, ball_y=ball[1], head_y=hdc[1], chord=c, flex=flex(c), wrist_y=wt[1], ball=ball, sh=shc))
i_h = next(i for i, r in enumerate(rows) if r['ball_y'] >= r['head_y'])
r = rows[i_h]; j = min(len(rows) - 1, i_h + int(round(0.15 / (0.5 / 0.75 / 40))))   # 0.15 s real = 0.1125 gs at pace .75 = 9 steps of 1/80 gs.. the windup is 0.5 gs = 0.667 s real
print('SIM', actname, tag, 'T_H at u=%.2f (%.2f s real into the wind-up), clip t=%.2f: flexL %.0f deg (chord %.2f m), wrist-head y %+.2f | flex at +0.15 s %.0f | at release flex %.0f wrist-head %+.2f' % (
    r['u'], r['u'] * 0.667, r['t'], r['flex'], r['chord'], r['wrist_y'] - r['head_y'], rows[j]['flex'], rows[-1]['flex'], rows[-1]['wrist_y'] - rows[-1]['head_y']))
print('SIM   ball path radius from the shoulder:', ' '.join('%.2f' % np.linalg.norm(rr['ball'] - rr['sh']) for rr in rows[::5]), '| flex:', ' '.join('%.0f' % rr['flex'] for rr in rows[::5]))

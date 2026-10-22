import sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'emotes', 'scripts')); sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/match-anim-set/scripts')
import bpy
import emo_hero as EH
import emo_clips2 as EC
import preview as PV
a_ = sys.argv[sys.argv.index('--') + 1:]
tag, clip = a_[0], a_[1]
ts = [float(x) for x in a_[2].split(',')]
H = EH.EmoHero(tag); C = EC.build(clip, H)
rig_o = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
PV.setup_scene(rig_o, samples=1)
BODY = 'Body_M' if tag == 'male' else 'Body_F'
ob = bpy.data.objects[BODY]
names = list(H.rig.names)
prev = None
for t in ts:
    d = C.solve(t)
    prev = PV.apply_pose(rig_o, H.rig, d['basis'], d['hips'], prev)
    bpy.context.view_layer.update()
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    M = np.array(ev.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    ev.to_mesh_clear()
    mine = H.mesh(d['basis'], d['hips'])
    dev = np.linalg.norm(co - mine, axis=1)
    dom = H.dom
    print('t=%.3f  max dev %.4f m (p99 %.4f)' % (t, dev.max(), np.percentile(dev, 99)))
    worst = {}
    for i in np.argsort(-dev)[:300]:
        worst.setdefault(names[dom[i]], []).append(dev[i])
    print('   worst bones:', {k: (len(v), round(max(v), 4)) for k, v in list(worst.items())[:8]})

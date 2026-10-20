"""Compare the current ArtDir blend's Body_M / Face_M with the START positions.  blender -b --python diffbase.py -- <blend> <D.npy>"""
import sys, numpy as np, bpy
W = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1k-head'
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0]); D = np.load(argv[1]); V0 = np.load(W + '/data/V_start.npy').astype(np.float32)
me = bpy.data.objects['Body_M'].data; n = len(me.vertices)
Vb = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', Vb); Vb = Vb.reshape(-1, 3)
diff = np.any(Vb != V0, axis=1); zone = V0[:, 2] >= 1.40; hasD = np.linalg.norm(D, axis=1) > 0
print('verts', n, 'differ from START', int(diff.sum()), 'in zone', int((diff & zone).sum()), 'under D', int((diff & hasD).sum()))
if diff.any():
    d = np.linalg.norm(Vb - V0, axis=1)
    print('z range of differing', float(V0[diff, 2].min()), float(V0[diff, 2].max()), 'max move mm', float(d.max() * 1000))
    print('x range', float(V0[diff, 0].min()), float(V0[diff, 0].max()))
    hands = diff & (np.abs(V0[:, 0]) > 0.44) & (V0[:, 2] < 1.06); print('hands differing', int(hands.sum()))
for o in bpy.data.objects: print(o.name, o.type, len(o.data.vertices) if o.type == 'MESH' else '')

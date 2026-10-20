import sys
sys.path.insert(0, '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1j-head/pylib')
import numpy as np, bpy
def grab(p):
    bpy.ops.wm.open_mainfile(filepath=p); me = bpy.data.objects['Body_M'].data
    V = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', V)
    cn = np.empty(len(me.loops) * 3, np.float32); me.corner_normals.foreach_get('vector', cn)
    return V.reshape(-1, 3), cn.reshape(-1, 3)
argv = sys.argv[sys.argv.index('--') + 1:]
a, ca = grab(argv[0]); b, cb = grab(argv[1])
ang = np.degrees(np.arccos(np.clip((ca * cb).sum(1), -1, 1)))
print('CMP positions bitwise equal:', bool(np.array_equal(a, b)), '| max |dV| mm %.6f' % (np.abs(a - b).max() * 1000), '| normals max angle %.4f deg, corners >0.05deg %d' % (ang.max(), (ang > 0.05).sum()))

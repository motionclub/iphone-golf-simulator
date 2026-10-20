"""Compare two blends: Body_M positions, corner normals, Face_M.  blender -b --python cmp_blends_l.py -- a.blend b.blend"""
import sys, bpy, numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
def grab(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    me = bpy.data.objects['Body_M'].data; n = len(me.vertices)
    V = np.empty(n * 3, np.float32); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    cn = np.empty(len(me.loops) * 3, np.float32); me.corner_normals.foreach_get('vector', cn); cn = cn.reshape(-1, 3)
    f = bpy.data.objects['Face_M'].data; FV = np.empty(len(f.vertices) * 3, np.float32); f.vertices.foreach_get('co', FV)
    fm = [m.name for m in f.materials]; pm = np.array([p.material_index for p in f.polygons])
    return V, cn, FV, fm, pm
A = grab(argv[0]); B_ = grab(argv[1])
print('CMP positions identical:', np.array_equal(A[0], B_[0]), ' max diff mm %.6f' % (np.abs(A[0] - B_[0]).max() * 1000))
ang = np.degrees(np.arccos(np.clip((A[1] * B_[1]).sum(1), -1, 1))); print('CMP corner normals: max diff deg %.4f, corners >0.01deg: %d of %d' % (ang.max(), (ang > 0.01).sum(), len(ang)))
print('CMP Face_M verts identical:', A[2].shape == B_[2].shape and np.array_equal(A[2], B_[2]), ' slots identical:', A[3] == B_[3], ' poly slot ids identical:', np.array_equal(A[4], B_[4]))

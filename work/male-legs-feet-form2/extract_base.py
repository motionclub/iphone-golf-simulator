import sys, pickle, numpy as np, bpy
src, outv, outf = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=src)
me = bpy.data.objects['Body_M'].data; n = len(me.vertices)
V = np.empty(n * 3); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
np.save(outv, V)
pickle.dump([list(p.vertices) for p in me.polygons], open(outf, 'wb'))
print('saved', n, len(me.polygons))

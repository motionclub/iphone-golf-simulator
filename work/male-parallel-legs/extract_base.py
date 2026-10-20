import sys, numpy as np, bpy
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
me=bpy.data.objects['Body_M'].data; n=len(me.vertices)
V=np.empty(n*3); me.vertices.foreach_get('co',V); np.save(sys.argv[sys.argv.index('--')+2],V.reshape(-1,3)); print('saved',n)

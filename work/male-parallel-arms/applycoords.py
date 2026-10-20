import os, numpy as np, bpy
def apply():
    p=os.environ.get('COORDS')
    if not p: return
    V=np.load(p).astype(np.float32)
    me=bpy.data.objects['Body_M'].data
    assert len(me.vertices)==len(V),(len(me.vertices),len(V))
    me.vertices.foreach_set('co',V.ravel()); me.update()

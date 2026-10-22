import bpy, numpy as np
me=bpy.data.objects['Body_F'].data
a=me.attributes['custom_normal']; print(a.data_type,a.domain,len(a.data))
buf=np.empty(len(a.data)*2,np.int16)
try:
    a.data.foreach_get('value',buf); print('foreach_get ok',buf[:6],buf.dtype)
except Exception as e: print('foreach_get failed',e)
# round trip: set the same values back and check normals identical
n0=np.array([tuple(x.vector) for x in me.corner_normals],np.float32)
a.data.foreach_set('value',buf); me.update()
n1=np.array([tuple(x.vector) for x in me.corner_normals],np.float32); print('set-back identical',np.array_equal(n0,n1))

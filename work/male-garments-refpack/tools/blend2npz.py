import bpy, numpy as np, sys
out=sys.argv[sys.argv.index('--')+1]
ob=[o for o in bpy.data.objects if o.type=='MESH'][0]; me=ob.data
me.calc_loop_triangles()
P=np.zeros(len(me.vertices)*3); me.vertices.foreach_get('co',P)
T=np.zeros(len(me.loop_triangles)*3,np.int32); me.loop_triangles.foreach_get('vertices',T)
TP=np.zeros(len(me.loop_triangles),np.int32); me.loop_triangles.foreach_get('polygon_index',TP)
d=dict(P=P.reshape(-1,3),T=T.reshape(-1,3))
for a in me.attributes:
    if a.domain=='FACE' and a.data_type=='INT':
        v=np.zeros(len(me.polygons),np.int32); a.data.foreach_get('value',v); d['f_'+a.name]=v[TP]
    if a.domain=='POINT' and a.data_type=='FLOAT':
        v=np.zeros(len(me.vertices),np.float32); a.data.foreach_get('value',v); d['v_'+a.name]=v
mi=np.zeros(len(me.polygons),np.int32); me.polygons.foreach_get('material_index',mi); d['f_mat']=mi[TP]
np.savez_compressed(out,**d); print('NPZ',out,len(P)//3,len(T)//3)

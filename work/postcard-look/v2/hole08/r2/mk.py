import bpy, numpy as np
YD=0.9144
bpy.ops.wm.open_mainfile(filepath="dev1/dev_hole_08.blend")
pv=[]
for o in bpy.data.objects:
    if o.name.startswith("DRESS_PATH_01") and o.type=='MESH':
        M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3)@M[:3,:3].T+M[:3,3]; pv=V
for n in ("TEE_MARKER_1","TEE_MARKER_2","BALL_START","MARKER_TEE"):
    o=bpy.data.objects.get(n)
    if o:
        p=np.array(o.matrix_world.translation); d=np.hypot(pv[:,0]-p[0],pv[:,1]-p[1]).min()
        print("MK",n,(p[:2]/YD).round(2),"dist to tee path %.2f m"%d, "dims", tuple(round(x,2) for x in o.dimensions))

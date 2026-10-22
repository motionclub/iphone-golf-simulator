import bpy, sys, numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
n=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=R+f'blender/hole_{n}.blend')
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    if o.type!='MESH' or not o.name.startswith(('FAIRWAY','GREEN','TEE_BOX','GREEN_APRON')): continue
    me=o.data; uv=me.uv_layers.active.data; M=np.array(o.matrix_world)[:3,:3]; me.calc_loop_triangles()
    A=[]
    for t in me.loop_triangles:
        p=[M@np.array(me.vertices[i].co) for i in t.vertices]; u=[np.array(uv[l].uv) for l in t.loops]
        e1,e2=p[1]-p[0],p[2]-p[0]; d1,d2=u[1]-u[0],u[2]-u[0]
        Muv=np.array([[d1[0],d2[0]],[d1[1],d2[1]]]); det=np.linalg.det(Muv)
        if abs(det)<1e-12: continue
        Pm=np.stack([e1,e2],1)@np.linalg.inv(Muv)   # columns dP/du, dP/dv (blender world xyz)
        A.append((Pm[:,0],Pm[:,1]))
    du=np.mean([a[0] for a in A],0); dv=np.mean([a[1] for a in A],0)
    ang_u=np.degrees(np.arctan2(du[1],du[0])); ang_v=np.degrees(np.arctan2(dv[1],dv[0]))
    print(f'{o.name:18s} dP/du dir {ang_u:7.1f} deg (|.|={np.linalg.norm(du):6.2f})  dP/dv dir {ang_v:7.1f} deg (|.|={np.linalg.norm(dv):6.2f})  [blender xy; +y = Unity z forward]')

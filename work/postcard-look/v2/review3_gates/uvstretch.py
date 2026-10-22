import bpy,sys,numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
n=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=R+f'blender/hole_{n}.blend')
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('ROCK_SKIN','ROCK_WALL','DRESS_','TERRAIN')) : continue
    me=o.data
    if not me.uv_layers: rows.append((o.name,'NOUV')); continue
    uv=me.uv_layers.active.data; M=np.array(o.matrix_world)[:3,:3]
    me.calc_loop_triangles(); A=[];W=[]
    for t in me.loop_triangles:
        p=[M@np.array(me.vertices[i].co) for i in t.vertices]; u=[np.array(uv[l].uv) for l in t.loops]
        e1,e2=p[1]-p[0],p[2]-p[0]; d1,d2=u[1]-u[0],u[2]-u[0]
        area3=np.linalg.norm(np.cross(e1,e2))/2
        if area3<1e-9: continue
        # Jacobian from uv to 3D: columns = dP/du, dP/dv
        Muv=np.array([[d1[0],d2[0]],[d1[1],d2[1]]])
        det=np.linalg.det(Muv)
        if abs(det)<1e-12: A.append(999); W.append(area3); continue
        inv=np.linalg.inv(Muv)
        Pm=np.stack([e1,e2],1)@inv   # 3x2
        s=np.linalg.svd(Pm,compute_uv=False)
        A.append(s[0]/max(s[1],1e-9)); W.append(area3)
    A=np.array(A);W=np.array(W)
    if len(A): rows.append((o.name,len(A),round(float(np.average(A>2.0,weights=W))*100,1),round(float(np.percentile(A,95)),2),round(float(A.max()),1)))
print('hole',n); [print(r) for r in rows[:30]]

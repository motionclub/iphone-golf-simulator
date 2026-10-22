import bpy, sys, numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
n=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=R+f'blender/hole_{n}.blend')
for o in bpy.data.objects:
    if o.type!='MESH' or not o.name.startswith(('TERRAIN','FAIRWAY','GREEN','TEE_BOX')): continue
    me=o.data
    if not me.uv_layers: print(o.name,'NOUV'); continue
    uv=me.uv_layers.active.data; M=np.array(o.matrix_world)[:3,:3]
    me.calc_loop_triangles()
    rec={}
    for t in me.loop_triangles:
        mat=me.materials[t.material_index].name if me.materials and t.material_index<len(me.materials) and me.materials[t.material_index] else '?'
        p=[M@np.array(me.vertices[i].co) for i in t.vertices]; u=[np.array(uv[l].uv) for l in t.loops]
        e1,e2=p[1]-p[0],p[2]-p[0]; d1,d2=u[1]-u[0],u[2]-u[0]
        area3=np.linalg.norm(np.cross(e1,e2))/2
        if area3<1e-9: continue
        nrm=np.cross(e1,e2); nrm/=np.linalg.norm(nrm)
        Muv=np.array([[d1[0],d2[0]],[d1[1],d2[1]]]); det=np.linalg.det(Muv)
        if abs(det)<1e-12: continue
        Pm=np.stack([e1,e2],1)@np.linalg.inv(Muv)
        s=np.linalg.svd(Pm,compute_uv=False)
        rec.setdefault(mat,[]).append((s[0]/max(s[1],1e-9), area3, abs(nrm[2]), s[0], s[1]))
    for mat,r in rec.items():
        r=np.array(r); w=r[:,1]
        print(f'{o.name:22s} {mat:12s} tris {len(r):6d} area {w.sum():9.0f} m2 | stretch>2 {np.average(r[:,0]>2,weights=w)*100:5.1f}% >4 {np.average(r[:,0]>4,weights=w)*100:5.1f}% p95 {np.percentile(r[:,0],95):6.2f} | slope(nz<.8) {np.average(r[:,2]<.8,weights=w)*100:5.1f}% | texel m/uv-unit: major wmean {np.average(r[:,3],weights=w):6.2f} minor {np.average(r[:,4],weights=w):6.2f}')

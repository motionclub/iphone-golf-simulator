"""blender -b --factory-startup --python audit_legs.py -- <base.blend> <new.blend> <out.json>
Zone audit for the legs/feet chat: every vertex outside the zone must be bit-identical to the base; topology identical; plus quality + silhouette numbers."""
import sys, json, hashlib
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-parallel-legs')
from pathlib import Path
from collections import defaultdict
import numpy as np, bpy
from leglib import ZONE, ZT, XMAX
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'); M=R/'work/male-silhouette'
base,new,outj=sys.argv[sys.argv.index('--')+1:]
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    b=bpy.data.objects['Body_M']; me=b.data; n=len(me.vertices)
    V=np.empty(n*3); me.vertices.foreach_get('co',V); V=V.reshape(-1,3)
    F=[list(p.vertices) for p in me.polygons]
    f=bpy.data.objects.get('Face_M'); Vf=None
    if f:
        m2=f.data; Vf=np.empty(len(m2.vertices)*3); m2.vertices.foreach_get('co',Vf)
    return V.astype(np.float32),F,len(me.edges),Vf,sorted(vg.name for vg in b.vertex_groups),[m.name if m else None for m in me.materials]
Vb,Fb,Eb,Vfb,vgb,matb=load(base)
res=dict(base=base,base_sha256=sha(base),new=new,new_sha256=sha(new))
Vn,Fn,En,Vfn,vgn,matn=load(new)
n=len(Vb)
same=np.all(Vb==Vn,axis=1)
res['verts']=int(n); res['faces_identical']=bool(Fb==Fn); res['edges_equal']=bool(Eb==En)
res['zone_def']=dict(z_lt=ZT,absx_lt=XMAX,zone_verts=int(ZONE.sum()))
res['moved_total']=int((~same).sum()); res['moved_in_zone']=int((~same&ZONE).sum()); res['moved_outside_zone']=int((~same&~ZONE).sum())
res['outside_zone_bit_identical']=bool(res['moved_outside_zone']==0)
z=Vb[:,2]; x=Vb[:,0]
for nm,sel in (('head_z_ge_1.40',z>=1.40),('torso_z_0.765_1.40',(z>=ZT)&(z<1.40)&(np.abs(x)<XMAX)),('arms_hands_absx_ge_0.27',np.abs(x)>=XMAX)):
    res['moved_'+nm]=int((~same&sel).sum())
res['face_m_unchanged']=bool(Vfb is not None and np.array_equal(Vfb,Vfn))
res['vertex_groups_equal']=vgb==vgn; res['materials_equal']=matb==matn
d=np.linalg.norm(Vn.astype(np.float64)-Vb.astype(np.float64),axis=1)
res['zone_move_mm']=dict(rms=float(np.sqrt((d[ZONE]**2).mean())*1000),max=float(d.max()*1000),verts_moved_gt_1mm=int((d>0.001).sum()),verts_moved_gt_10mm=int((d>0.01).sum()))
# top-of-zone fade: displacement of the topmost 3 cm of the zone
band=ZONE&(z>ZT-0.03); res['zone_top_band_3cm_move_mm']=dict(max=float(d[band].max()*1000),rms=float(np.sqrt((d[band]**2).mean())*1000))
res['min_z_base']=float(Vb[:,2].min()); res['min_z_new']=float(Vn[:,2].min()); res['max_z_equal']=bool(Vb[:,2].max()==Vn[:,2].max())
res['height_m_base']=float(Vb[:,2].max()-Vb[:,2].min()); res['height_m_new']=float(Vn[:,2].max()-Vn[:,2].min())
res['nan_or_inf']=bool(~np.isfinite(Vn).all())
tris=lambda FF: int(sum(len(p)-2 for p in FF)); res['tris_base']=tris(Fb); res['tris_new']=tris(Fn)
def bnd(FF):
    ec=defaultdict(int)
    for p in FF:
        for k in range(len(p)):
            a,b=p[k],p[(k+1)%len(p)]; ec[(min(a,b),max(a,b))]+=1
    return sum(1 for c in ec.values() if c==1),sum(1 for c in ec.values() if c>2)
res['boundary_nonmanifold_base']=bnd(Fb); res['boundary_nonmanifold_new']=bnd(Fn)
# quality in the zone
def fn(V,FF):
    V=V.astype(np.float64); out=[]
    for p in FF:
        nn=np.cross(V[p[2]]-V[p[0]],V[p[3]]-V[p[1]]) if len(p)==4 else np.cross(V[p[1]]-V[p[0]],V[p[2]]-V[p[0]])
        out.append(nn/max(np.linalg.norm(nn),1e-15))
    return np.array(out)
zf=np.array([any(ZONE[i] for i in p) for p in Fb])
dots=(fn(Vb,Fb)*fn(Vn,Fn)).sum(1)
res['zone_faces']=int(zf.sum()); res['flipped_faces']=int((dots[zf]<0).sum()); res['min_face_normal_dot_vs_base']=float(dots[zf].min())
E=set()
for p in Fn:
    for k in range(len(p)): E.add((min(p[k],p[(k+1)%len(p)]),max(p[k],p[(k+1)%len(p)])))
E=np.array(sorted(E)); ez=ZONE[E[:,0]]&ZONE[E[:,1]]
elb=np.linalg.norm(Vb[E[ez,0]].astype(float)-Vb[E[ez,1]].astype(float),axis=1)*1000; eln=np.linalg.norm(Vn[E[ez,0]].astype(float)-Vn[E[ez,1]].astype(float),axis=1)*1000
res['zone_edge_mm_base']=dict(mean=float(elb.mean()),p99=float(np.percentile(elb,99)),max=float(elb.max())); res['zone_edge_mm_new']=dict(mean=float(eln.mean()),p99=float(np.percentile(eln,99)),max=float(eln.max()))
def qa(V,FF):
    V=V.astype(float); mn=[];mx=[]
    for p in FF:
        a=[]
        for k in range(4):
            u=V[p[(k-1)%4]]-V[p[k]]; v=V[p[(k+1)%4]]-V[p[k]]; a.append(np.degrees(np.arccos(np.clip(u@v/np.linalg.norm(u)/np.linalg.norm(v),-1,1))))
        mn.append(min(a)); mx.append(max(a))
    return min(mn),max(mx)
zq=[i for i in range(len(Fb)) if zf[i] and len(Fb[i])==4]
res['zone_quad_angle_base']=qa(Vb,[Fb[i] for i in zq]); res['zone_quad_angle_new']=qa(Vn,[Fn[i] for i in zq])
L=Vn[(ZONE)&(Vb[:,0]>0)].astype(float); Rr=Vn[(ZONE)&(Vb[:,0]<0)].astype(float)
mind=1e9
for a in range(0,len(L),500): mind=min(mind,np.linalg.norm(L[a:a+500,None,:]-Rr[None,:,:],axis=2).min())
res['min_gap_between_legs_vertices_mm']=float(mind*1000)
# silhouettes (the locked workbench: Body_M only, film transparent, 1280x720, alpha>0.5) for base and new
sil={}
for tag,path in (('base',base),('new',new)):
    bpy.ops.wm.open_mainfile(filepath=path)
    sc=bpy.context.scene; sc.render.film_transparent=True; sc.render.image_settings.color_mode='RGBA'; sc.render.image_settings.file_format='PNG'
    sc.render.resolution_x=1280; sc.render.resolution_y=720; sc.render.resolution_percentage=100
    for o in bpy.data.objects:
        if o.type=='EMPTY': o.hide_render=True
    fo=bpy.data.objects.get('Face_M')
    for fshow in (False,True):
        if fo: fo.hide_render=not fshow
        for view in ('bald_front','bald_back'):
            sc.camera=bpy.data.objects['Locked_'+view]; p=R/f'work/male-parallel-legs/proof/_sil_{tag}_{int(fshow)}_{view}.png'; sc.render.filepath=str(p); bpy.ops.render.render(write_still=True)
            img=bpy.data.images.load(str(p),check_existing=False); a=np.array(img.pixels[:],np.float32).reshape(img.size[1],img.size[0],4)[:,:,3]>0.5; bpy.data.images.remove(img)
            timg=bpy.data.images.load(str(M/f'{view}_target.png'),check_existing=False); t=np.array(timg.pixels[:],np.float32).reshape(timg.size[1],timg.size[0],4); bpy.data.images.remove(timg)
            tm=(t[:,:,3]>0.5) if t[:,:,3].min()<0.99 else (t[:,:,0]>0.5)
            diff=int((a!=tm).sum()); uni=int((a|tm).sum())
            H=a.shape[0]; rows=slice(0,H-int(round(654-ZT/0.0028668))+0)   # rows below the crotch line (bottom-up arrays)
            dl=int((a[rows]!=tm[rows]).sum()); ul=int((a[rows]|tm[rows]).sum())
            sil[f'{tag}_{"withface" if fshow else "body"}_{view}']=dict(pct=100.0*diff/uni,legs_pct=100.0*dl/ul)
res['silhouette']=sil
Path(outj).write_text(json.dumps(res,indent=1))
print('AUDIT',json.dumps({k:res[k] for k in ('moved_outside_zone','moved_in_zone','faces_identical','tris_new','flipped_faces','min_gap_between_legs_vertices_mm')}))
print('SIL',json.dumps({k:round(v['pct'],3) for k,v in sil.items()}))

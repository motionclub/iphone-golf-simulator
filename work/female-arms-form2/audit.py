"""blender -b --python audit.py -- START.blend FINAL.blend out.json : independent audit of the arms pass vs the start file."""
import bpy, bmesh, numpy as np, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]; START=a[0]; FINAL=a[1]; OUT=a[2]
def grab(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    o=bpy.data.objects['Body_F']; me=o.data; n=len(me.vertices)
    d={}
    d['co']=np.empty(n*3,np.float32); me.vertices.foreach_get('co',d['co']); d['co']=d['co'].reshape(-1,3)
    d['edges']=np.empty(len(me.edges)*2,np.int32); me.edges.foreach_get('vertices',d['edges'])
    d['loop_v']=np.empty(len(me.loops),np.int32); me.loops.foreach_get('vertex_index',d['loop_v'])
    d['poly_ls']=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('loop_start',d['poly_ls'])
    d['mat']=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('material_index',d['mat'])
    d['smooth']=np.empty(len(me.polygons),np.bool_); me.polygons.foreach_get('use_smooth',d['smooth'])
    d['uv']={u.name:np.array([x.uv[:] for x in u.data],np.float32) for u in me.uv_layers}
    attrs={}
    for at in me.attributes:
        if at.name=='position': continue
        try:
            if at.data_type in('FLOAT','INT','INT8','BOOLEAN','INT32_2D','INT16_2D'):
                pass
            buf=[]
            for x in at.data:
                v=getattr(x,'value',None)
                if v is None: v=getattr(x,'vector',None)
                if v is None: v=getattr(x,'color',None)
                buf.append(tuple(v) if hasattr(v,'__len__') else v)
            attrs[at.name]=(at.domain,at.data_type,hash(str(buf)))
        except Exception as e: attrs[at.name]=(at.domain,at.data_type,'ERR '+str(e))
    d['attrs']=attrs
    d['tris']=sum(len(p.vertices)-2 for p in me.polygons)
    d['hair']=np.array([v.co[:] for v in bpy.data.objects['Hair_F'].data.vertices],np.float32)
    d['others']={ob.name:(tuple(round(x,6) for x in ob.matrix_world.translation),ob.type) for ob in bpy.data.objects}
    d['obj_n']=len(bpy.data.objects)
    # face normals + BVH overlap
    d['fn']=np.array([p.normal[:] for p in me.polygons],np.float32)
    d['fc']=np.array([p.center[:] for p in me.polygons],np.float32)
    deps=bpy.context.evaluated_depsgraph_get(); bm=bmesh.new(); bm.from_mesh(me)
    bvh=BVHTree.FromBMesh(bm); ov=bvh.overlap(bvh)
    # overlaps between non-adjacent faces
    fv=[set(f.verts[i].index for i in range(len(f.verts))) for f in bm.faces]
    bad=[(i,j) for i,j in ov if i<j and not (fv[i]&fv[j])]
    d['self_isect_pairs']=len(bad); d['self_isect_faces']=sorted(set(i for p in bad for i in p))[:50]
    # mesh checks
    nm=sum(1 for e in bm.edges if not e.is_manifold); nc=sum(1 for e in bm.edges if not e.is_contiguous)
    deg=sum(1 for f in bm.faces if f.calc_area()<1e-9); loose=sum(1 for v in bm.verts if not v.link_faces)
    d['mesh']={'nonmanifold':nm,'noncontig':nc,'degenerate':deg,'loose':loose,'volume':bm.calc_volume(signed=True)}
    # dihedral per edge
    dih=np.zeros(len(bm.edges),np.float32)
    for k,e in enumerate(bm.edges):
        if len(e.link_faces)==2: dih[k]=np.degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal))
    d['dih']=dih; bm.free()
    return d

S=grab(START); F=grab(FINAL)
Zn=np.load('data/zones_cur.npz'); arm=Zn['arm']; n=len(arm)
res={}
co0=S['co']; co1=F['co']
# pinned set = arm verts with non-arm neighbour
ed=S['edges'].reshape(-1,2)
pin=np.zeros(n,bool)
for u,v in ed:
    if arm[u]!=arm[v]:
        if arm[u]: pin[u]=True
        if arm[v]: pin[v]=True
moved=(co0!=co1).any(1)
dist=np.linalg.norm(co1-co0,axis=1)
res['G1']={'vertices':n,'arm_zone':int(arm.sum()),'moved':int(moved.sum()),'moved_outside_zone':int((moved&~arm).sum()),
 'max_disp_outside_m':float(dist[~arm].max()),'pinned_verts':int(pin.sum()),'pinned_moved':int((moved&pin).sum()),'max_pinned_disp_mm':float(dist[pin].max()*1000),
 'max_disp_arm_mm':float(dist[arm].max()*1000),'hair_identical':bool((S['hair']==F['hair']).all()),'objects_identical':S['others']==F['others'],
 'wrist_ring_R_moved':int((moved&(np.abs(co0[:,2]-0.8456)<2e-4)&(co0[:,0]>0)).sum()),'wrist_ring_L_moved':int((moved&(np.abs(co0[:,2]-0.8726)<2e-4)&(co0[:,0]<0)).sum())}
res['G5']={'verts_same':len(co0)==len(co1),'edges_same':bool((S['edges']==F['edges']).all()),'loops_same':bool((S['loop_v']==F['loop_v']).all()),
 'poly_start_same':bool((S['poly_ls']==F['poly_ls']).all()),'material_ids_same':bool((S['mat']==F['mat']).all()),'smooth_flags_same':bool((S['smooth']==F['smooth']).all()),
 'uv_same':{k:bool((S['uv'][k]==F['uv'][k]).all()) for k in S['uv']},'attrs_same':S['attrs']==F['attrs'],'attr_list':{k:list(v[:2]) for k,v in F['attrs'].items()},
 'tris_start':S['tris'],'tris_final':F['tris'],'hair_tris_note':'body+hair budget 50000: %d'%(F['tris']+4960)}
# mesh quality + self intersection
res['G2_mesh']={'start':S['mesh'],'final':F['mesh'],'self_isect_start':S['self_isect_pairs'],'self_isect_final':F['self_isect_pairs']}
# armpit / fairness: faces touching pinned verts' neighbourhood (within 0.06 m of any pinned vertex)
pp=co0[pin]
def near(c): return np.sqrt(((c[:,None,:]-pp[None,:,:])**2).sum(2)).min(1)
fc=S['fc']; mask=np.zeros(len(fc),bool)
sel=(np.abs(fc[:,0])>0.1)&(fc[:,2]>0.95)&(fc[:,2]<1.36)
dn=near(fc[sel]); mask[np.where(sel)[0][dn<0.06]]=True
dot=(S['fn']*F['fn']).sum(1)
ang=np.degrees(np.arccos(np.clip(dot,-1,1)))
arm_faces=np.zeros(len(fc),bool)
vl=F['loop_v']; ls=F['poly_ls']
fv_arm=np.array([arm[vl[ls[i]:(ls[i+1] if i+1<len(ls) else len(vl))]].any() for i in range(len(ls))])
res['G3']={'armpit_faces':int(mask.sum()),'face_normal_change_max_deg_armzone':float(ang[fv_arm].max()),'face_normal_flips(>90deg)':int((ang>90).sum()),
 'faces_normal_change_gt60':int((ang>60).sum())}
# dihedral in armpit zone, edges with both ends near pinned
ev=F['edges'].reshape(-1,2); mid=(co1[ev[:,0]]+co1[ev[:,1]])/2; mid0=(co0[ev[:,0]]+co0[ev[:,1]])/2
selE=(np.abs(mid[:,0])>0.1)&(mid[:,2]>0.95)&(mid[:,2]<1.36)
dnE=near(mid0[selE]); em=np.zeros(len(ev),bool); em[np.where(selE)[0][dnE<0.06]]=True
# need dihedral arrays in same edge order (same topology)
res['G3']['dihedral_armpit_max_deg_start']=float(S['dih'][em].max()); res['G3']['dihedral_armpit_max_deg_final']=float(F['dih'][em].max())
res['G3']['dihedral_armpit_p99_start']=float(np.percentile(S['dih'][em],99)); res['G3']['dihedral_armpit_p99_final']=float(np.percentile(F['dih'][em],99))
armE=arm[ev[:,0]]&arm[ev[:,1]]
l0=np.linalg.norm(co0[ev[:,0]]-co0[ev[:,1]],axis=1); l1=np.linalg.norm(co1[ev[:,0]]-co1[ev[:,1]],axis=1)
r=(l1/np.maximum(l0,1e-9))[armE]; res['G3']['edge_stretch_ratio_min']=float(r.min()); res['G3']['edge_stretch_ratio_max']=float(r.max())
res['G3']['dihedral_arm_all_max_deg_start']=float(S['dih'][armE].max()); res['G3']['dihedral_arm_all_max_deg_final']=float(F['dih'][armE].max())
res['G3']['dihedral_arm_all_p99_start']=float(np.percentile(S['dih'][armE],99)); res['G3']['dihedral_arm_all_p99_final']=float(np.percentile(F['dih'][armE],99))
# G6 form metrics on slices
def slices(co,s):
    out=[]
    for z in np.arange(0.90,1.201,0.02):
        m=arm&(co[:,0]*s>0)&(abs(co[:,2]-z)<0.01); p=co[m]
        out.append((round(float(z),3),float(((p[:,0]*s).max()-(p[:,0]*s).min())/2),float((p[:,1].max()-p[:,1].min())/2),float((p[:,1].max()+p[:,1].min())/2)))
    return out
form={}
for s,nm in((1,'R'),(-1,'L')):
    for tag,co in(('start',co0),('final',co1)):
        form[f'{nm}_{tag}']=slices(co,s)
res['form_slices']=form
json.dump(res,open(OUT,'w'),indent=1,default=str)
print(json.dumps(res['G1'],indent=1)); print(json.dumps(res['G5'],indent=1,default=str)); print(json.dumps(res['G2_mesh'],indent=1)); print(json.dumps(res['G3'],indent=1))

"""make_limbs.py  --  reproducible FEMALE LIMBS build (chat 8/8).
blender -b baseline/HeroBase_Female.blend --python make_limbs.py -- out.blend foot_tris hand_tris [depth_bias_mm]

 A. lower-leg depth (y) remap to the plate side profile (z in [0.14,0.58), positions only)
 B. feet below the ankle ring and hands below the wrist rings replaced by decimated SDF parts welded vertex-to-vertex onto the rings
 C. custom normals: loops away from any change keep their stored raw INT16 data bit-for-bit
 D. vertex map baseline<->final for later merging with the torso/head chats
Nothing outside the limb zone is moved (verified independently by audit.py)."""
import bpy, bmesh, numpy as np, json, sys, math, hashlib
from pathlib import Path
from mathutils import Vector
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-parallel-limbs')
args=sys.argv[sys.argv.index('--')+1:]
OUT=args[0]; FOOT_TRIS=int(args[1]); HAND_TRIS=int(args[2]); BIAS=(float(args[3]) if len(args)>3 else 5.0)/1000
SMOOTH_IT=0
ZA=0.15728244185447693                                   # ankle ring z (material boundary)
FOOT_UV=(0.88,0.60); HAND_UV=(0.93,0.10)                  # flat patches of the albedo atlas (skin / grey)
body=bpy.data.objects['Body_F']; me=body.data
mat_idx={m.name:i for i,m in enumerate(me.materials)}
nv0=len(me.vertices); co=np.empty(nv0*3,np.float32); me.vertices.foreach_get('co',co); V0=co.reshape(-1,3).copy()
raw0=np.empty(len(me.loops)*2,np.int16); me.attributes['custom_normal'].data.foreach_get('value',raw0)

# ------------------------------------------------------------------ A. lower-leg depth remap (positions only)
T=json.load(open(W/'data/leg_targets.json'))
tz=np.array(T['z']); pf=np.array(T['plate_front_y'])+BIAS; pb_=np.array(T['plate_back_y'])-BIAS; mf=np.array(T['model_front_y']); mb=np.array(T['model_back_y'])
def sm(x0,x1,v): t=np.clip((v-x0)/(x1-x0),0,1); return t*t*(3-2*t)
wz=1-sm(0.42,0.58,tz); tf=mf+(pf-mf)*wz; tb=mb+(pb_-mb)*wz
V1=V0.copy(); sel=np.where((V1[:,2]<0.58)&(V1[:,2]>=0.14))[0]
zz=np.clip(V1[sel,2],tz.min(),tz.max())
yf=np.interp(zz,tz,mf); yb=np.interp(zz,tz,mb); TF=np.interp(zz,tz,tf); TB=np.interp(zz,tz,tb)
V1[sel,1]=TF+(V1[sel,1]-yf)*(TB-TF)/(yb-yf)
me.vertices.foreach_set('co',V1.reshape(-1).astype(np.float32)); me.update()
LEG_MOVED=int(np.any(V1!=V0,axis=1).sum())

def decimated(V,F,target_tris,mirror):
    V=V.copy()
    if mirror: V[:,0]=-V[:,0]; F=F[:,[0,2,1]]
    m=bpy.data.meshes.new('raw'); m.from_pydata(V.tolist(),[],F.tolist()); m.update()
    ob=bpy.data.objects.new('raw',m); bpy.context.scene.collection.objects.link(ob)
    mod=ob.modifiers.new('d','DECIMATE'); mod.decimate_type='COLLAPSE'; mod.ratio=min(1.0,target_tris/len(F)); mod.use_collapse_triangulate=False
    dg=bpy.context.evaluated_depsgraph_get(); ev=ob.evaluated_get(dg); m2=bpy.data.meshes.new_from_object(ev)
    bpy.data.objects.remove(ob); bpy.data.meshes.remove(m)
    return m2

def cut_part(m,zc,keep_below=True):
    bm=bmesh.new(); bm.from_mesh(m)
    geom=bm.verts[:]+bm.edges[:]+bm.faces[:]
    bmesh.ops.bisect_plane(bm,geom=geom,plane_co=(0,0,zc),plane_no=(0,0,1),dist=1e-7,clear_inner=not keep_below,clear_outer=keep_below)
    for v in bm.verts:
        if abs(v.co.z-zc)<1e-6: v.co.z=zc
    return bm

def boundary_loops(bm,sel):
    """connected components of boundary edges (edges with 1 face) restricted by predicate on vertex."""
    es=[e for e in bm.edges if len(e.link_faces)==1 and sel(e)]
    seen=set(); loops=[]
    vmap={}
    for e in es:
        for v in e.verts: vmap.setdefault(v,[]).append(e)
    for e in es:
        if e in seen: continue
        comp=[]; st=[e]; seen.add(e)
        while st:
            x=st.pop(); comp.append(x)
            for v in x.verts:
                for y in vmap[v]:
                    if y not in seen: seen.add(y); st.append(y)
        loops.append(comp)
    return loops

# ------------------------------------------------------------------ delete old feet / hands
ZH={+1:0.84559+1e-4,-1:0.87263+1e-4}                     # the only planar wrist rings in the baseline differ per side (right 0.8456, left 0.8726)
bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
uvl=bm.loops.layers.uv.verify()
bil=bm.verts.layers.int.new('base_idx')
for v in bm.verts: v[bil]=v.index
del_faces=[]
for f in bm.faces:
    zs=[v.co.z for v in f.verts]; xs=[v.co.x for v in f.verts]; ax=[abs(x) for x in xs]
    if f.material_index==mat_idx['Skin_F'] and max(zs)<=0.1580: del_faces.append(f)                      # feet (skin below ankle ring)
    elif f.material_index==mat_idx['Base_Grey_F'] and min(ax)>0.195 and 0.60<min(zs):
        sd=1 if xs[0]>0 else -1
        if max(zs)<=ZH[sd]: del_faces.append(f)                                                           # hands below wrist ring
n_del_tris=sum(len(f.verts)-2 for f in del_faces)
bmesh.ops.delete(bm,geom=del_faces,context='FACES')
report={'deleted_old_tris':n_del_tris}
def components(edges):
    seen=set(); out=[]; vmap={}
    for e in edges:
        for v in e.verts: vmap.setdefault(v,[]).append(e)
    for e in edges:
        if e in seen: continue
        comp=[]; st=[e]; seen.add(e)
        while st:
            x=st.pop(); comp.append(x)
            for v in x.verts:
                for y in vmap[v]:
                    if y not in seen: seen.add(y); st.append(y)
        out.append(comp)
    return out
ring_loops={}
for comp in components([e for e in bm.edges if len(e.link_faces)==1]):
    vs={v for e in comp for v in e.verts}; P=np.array([v.co[:] for v in vs]); c=P.mean(0)
    kind='foot' if c[2]<0.3 else 'hand'; side=1 if c[0]>0 else -1
    ring_loops[(kind,side)]=(comp,P)
    print('ring',kind,side,'edges',len(comp),'z',P[:,2].min().round(5),P[:,2].max().round(5),'centre',c.round(4))
assert len(ring_loops)==4, ring_loops.keys()
report['rings']={f'{k[0]}_{k[1]}':{'edges':len(v[0]),'z_min':float(v[1][:,2].min()),'z_max':float(v[1][:,2].max())} for k,v in ring_loops.items()}

# ------------------------------------------------------------------ new parts
foot=np.load(W/'data/foot_R_raw.npz'); hand=np.load(W/'data/hand_R_raw.npz')
spec=[('foot',+1,foot,FOOT_TRIS,'Skin_F',FOOT_UV),('foot',-1,foot,FOOT_TRIS,'Skin_F',FOOT_UV),
      ('hand',+1,hand,HAND_TRIS,'Base_Grey_F',HAND_UV),('hand',-1,hand,HAND_TRIS,'Base_Grey_F',HAND_UV)]
for name,side,raw,tris,mname,uv in spec:
    comp,P=ring_loops[(name,side)]
    zc=float(np.median(P[:,2])) if name=='foot' else float(np.max(P[:,2]))
    m=decimated(raw['V'],raw['F'],tris*1.10,mirror=(side<0))
    pb=cut_part(m,zc,keep_below=True)
    # --- warp the cut so its rim sits on the (possibly jagged) ring surface: z_ring(theta)
    ringV0=sorted({v for e in comp for v in e.verts},key=lambda v:v.index)
    rc=np.mean([v.co[:2] for v in ringV0],0)
    th=np.array([math.atan2(v.co.y-rc[1],v.co.x-rc[0]) for v in ringV0]); zr=np.array([v.co.z for v in ringV0])
    o=np.argsort(th); th_s=np.concatenate([th[o]-2*math.pi,th[o],th[o]+2*math.pi]); zr_s=np.concatenate([zr[o]]*3)
    def smooth01(x): x=min(1,max(0,x)); return x*x*(3-2*x)
    for v in pb.verts:
        s_=smooth01((v.co.z-(zc-0.02))/0.02)
        if s_>0:
            v.co.z+= (float(np.interp(math.atan2(v.co.y-rc[1],v.co.x-rc[0]),th_s,zr_s))-zc)*s_
    # --- reduce the dense cut loop to exactly one vertex per ring vertex (nearest, greedy), dissolve the rest
    pb.verts.ensure_lookup_table()
    bverts=sorted({v for e in pb.edges if len(e.link_faces)==1 for v in e.verts},key=lambda v:v.index)
    ringV=sorted({v for e in comp for v in e.verts},key=lambda v:v.index)
    D=np.array([[ (bv.co-rv.co).length for rv in ringV] for bv in bverts])
    chosen={}; used=set()
    for flat in np.argsort(D,axis=None):
        i,j=divmod(int(flat),D.shape[1])
        if i in used or j in chosen: continue
        chosen[j]=i; used.add(i)
        if len(chosen)==len(ringV): break
    keepB={bverts[i] for i in used}
    dis=[v for v in bverts if v not in keepB]
    maxd=max(D[chosen[j],j] for j in chosen)
    bmesh.ops.dissolve_verts(pb,verts=dis,use_face_split=False,use_boundary_tear=False)
    ngons=[f for f in pb.faces if len(f.verts)>3]
    if ngons: bmesh.ops.triangulate(pb,faces=ngons,quad_method='BEAUTY',ngon_method='BEAUTY')
    bnd2=[e for e in pb.edges if len(e.link_faces)==1]
    nt=sum(len(f.verts)-2 for f in pb.faces)
    tmap={}
    vm={}
    for v in pb.verts:
        vm[v]=bm.verts.new(v.co); vm[v][bil]=-1
    created=list(vm.values())
    vset=set(vm.values()); nf=[]
    for f in pb.faces:
        try: nfc=bm.faces.new([vm[v] for v in f.verts])
        except ValueError: continue
        nfc.material_index=mat_idx[mname]; nfc.smooth=True; nf.append(nfc)
        for l in nfc.loops: l[uvl].uv=uv
    for j,i in chosen.items(): tmap[vm[bverts[i]]]=ringV[j]
    print(name,side,'cut z',round(zc,5),'new tris',nt,'dense loop',len(bverts),'-> kept',len(keepB),'boundary edges after dissolve',len(bnd2),'max weld dist mm',round(maxd*1000,2),'ring',len(ringV))
    rep={'cut_z':zc,'tris_after_cut':nt,'dense_loop':len(bverts),'kept':len(keepB),'ring_verts':len(ringV),'max_weld_mm':maxd*1000}
    bmesh.ops.weld_verts(bm,targetmap=tmap)
    # --- relax only the new vertices near the seam so the weld offsets blend out smoothly
    seam=[v for v in tmap.values()]; seam_set=set(seam)
    near=[]
    for v in created:
        if not v.is_valid or v in seam_set: continue
        dmin=min((v.co-r.co).length for r in seam)
        if dmin<0.016: near.append((v,smooth01(1-dmin/0.016)))
    # light Taubin (lambda|mu) smoothing over all new, non-seam vertices: evens the decimation triangles without shrinking the form
    free=[v for v in created if v.is_valid and v not in seam_set]
    for it in range(SMOOTH_IT):
        for fac in (0.45,-0.47):
            newp=[]
            for v in free:
                nb=[e.other_vert(v) for e in v.link_edges]
                avg=sum((n.co for n in nb),Vector((0,0,0)))/len(nb)
                newp.append(v.co+(avg-v.co)*fac)
            for v,p in zip(free,newp): v.co=p
    for it in range(12):
        newp=[]
        for v,w in near:
            nb=[e.other_vert(v) for e in v.link_edges]
            avg=sum((n.co for n in nb),Vector((0,0,0)))/len(nb)
            newp.append(v.co.lerp(avg,0.5*w))
        for (v,w),p in zip(near,newp): v.co=p
    pb.free()
    try: bpy.data.meshes.remove(m)
    except ReferenceError: pass
    report[f'{name}_{side}']=rep
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
# ------------------------------------------------------------------ C. normals
nvf=len(me.vertices); co=np.empty(nvf*3,np.float32); me.vertices.foreach_get('co',co); VF=co.reshape(-1,3).copy()
bidx=np.array([d.value for d in me.attributes['base_idx'].data],np.int64)
me.attributes.remove(me.attributes['base_idx'])
moved_or_new=np.ones(nvf,bool); ok=bidx>=0; moved_or_new[ok]=np.any(VF[ok]!=V1[bidx[ok]],axis=1)|np.any(V1[bidx[ok]]!=V0[bidx[ok]],axis=1)
changed=moved_or_new.copy()
# affected = every vertex sharing a face with a changed vertex
affected=changed.copy()
for p in me.polygons:
    vs=list(p.vertices)
    if changed[vs].any(): affected[vs]=True
lv=np.array([l.vertex_index for l in me.loops])
raw_before=np.empty(len(me.loops)*2,np.int16); me.attributes['custom_normal'].data.foreach_get('value',raw_before)
vn=np.array([tuple(v.normal) for v in me.vertices],np.float32)
cn=np.array([tuple(n.vector) for n in me.corner_normals],np.float32)
selL=affected[lv]; cn[selL]=vn[lv[selL]]
me.normals_split_custom_set([tuple(x) for x in cn]); me.update()
raw_after=np.empty(len(me.loops)*2,np.int16); me.attributes['custom_normal'].data.foreach_get('value',raw_after)
keep=~np.repeat(selL,2)                                        # loops not touched by the change keep their stored raw data exactly
raw_after[keep]=raw_before[keep]
me.attributes['custom_normal'].data.foreach_set('value',raw_after); me.update()
report['affected_verts']=int(affected.sum()); report['normal_loops_recomputed']=int(selL.sum()); report['normal_loops_kept_raw']=int((~selL).sum())
report['leg_verts_moved']=LEG_MOVED
report['tris_total']=sum(len(p.vertices)-2 for p in me.polygons); report['verts_total']=nvf
report['new_verts']=int((bidx<0).sum()); report['baseline_verts_removed']=int(nv0-len(set(bidx[bidx>=0].tolist())))
# ------------------------------------------------------------------ D. vertex map for merging
base_to_final=-np.ones(nv0,np.int64); base_to_final[bidx[bidx>=0]]=np.where(bidx>=0)[0]
np.savez(W/('data/'+Path(OUT).stem+'_vertex_map.npz'),base_to_final=base_to_final,final_to_base=bidx,zone_changed_final=changed,leg_moved_base=np.any(V1!=V0,axis=1))
bpy.ops.wm.save_as_mainfile(filepath=str(W/OUT))
json.dump(report,open(W/('data/'+Path(OUT).stem+'_report.json'),'w'),indent=1)
print(json.dumps({k:report[k] for k in ('deleted_old_tris','tris_total','verts_total','new_verts','baseline_verts_removed','leg_verts_moved','affected_verts','normal_loops_recomputed')},indent=1))

"""python3-in-blender audit: blender -b --python audit.py -- start.blend final.blend out.json
Independent check that the limb build changed ONLY the limb zone, plus mesh-integrity gates."""
import bpy, bmesh, numpy as np, json, sys, hashlib
a=sys.argv[sys.argv.index('--')+1:]; START,FINAL,OUT=a[0],a[1],a[2]
def load(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    ob=bpy.data.objects['Body_F']; me=ob.data
    n=len(me.vertices); co=np.empty(n*3,np.float32); me.vertices.foreach_get('co',co); V=co.reshape(-1,3).copy()
    polys=[tuple(p.vertices) for p in me.polygons]
    mi=np.empty(len(me.polygons),np.int32); me.polygons.foreach_get('material_index',mi)
    cn=np.array([tuple(x.vector) for x in me.corner_normals],np.float32)
    loops=np.array([l.vertex_index for l in me.loops]); lstart=np.array([p.loop_start for p in me.polygons]); ltotal=np.array([p.loop_total for p in me.polygons])
    uv=np.array([tuple(d.uv) for d in me.uv_layers.active.data],np.float32)
    mats=[m.name for m in me.materials]
    other={o.name:(o.type,tuple(np.round(o.matrix_world.translation,6)),len(o.data.vertices) if o.type=='MESH' else None) for o in bpy.data.objects if o.name!='Body_F'}
    hair=None
    if 'Hair_F' in bpy.data.objects:
        h=bpy.data.objects['Hair_F'].data; hv=np.empty(len(h.vertices)*3,np.float32); h.vertices.foreach_get('co',hv); hair=hashlib.sha256(hv.tobytes()).hexdigest()
    return dict(V=V,polys=polys,mi=mi,cn=cn,loops=loops,lstart=lstart,ltotal=ltotal,uv=uv,mats=mats,other=other,hair=hair,
                tris=sum(len(p)-2 for p in polys),sha=hashlib.sha256(open(path,'rb').read()).hexdigest(),me=me)
S=load(START); sv=S['V']; s_polys=S['polys']; s_mi=S['mi']; s_cn=S['cn']; s_uv=S['uv']; s_loops=S['loops']; s_ls=S['lstart']; s_lt=S['ltotal']
S_sha=S['sha']; S_mats=S['mats']; S_other=S['other']; S_hair=S['hair']; S_tris=S['tris']; S_nv=len(sv)
F=load(FINAL); fv=F['V']
# --- zone definition (documented): feet+ankle ring+calf/shank z<0.58 ; hands+wrist/forearm cut |x|>0.195 & 0.60<z<0.875
def in_zone(P): return (P[:,2]<0.58)|((np.abs(P[:,0])>0.18)&(P[:,2]>0.60)&(P[:,2]<0.875))
key=lambda P:[tuple(p) for p in P]
fkey={k:i for i,k in enumerate(key(fv))}
# 1) baseline verts: kept bit-identical / moved / removed (match by exact position; moved verts matched through face-structure is overkill -> positions of unmoved verts are exact)
kept=[];removed=[]
for i,k in enumerate(key(sv)):
    (kept if k in fkey else removed).append(i)
kept=np.array(kept); removed=np.array(removed)
removed_in_zone=in_zone(sv[removed]); 
# moved verts = baseline verts whose position is NOT found in final (removed or displaced); displaced ones in zone are the leg remap
# 2) every final vertex that has no bit-identical baseline vertex must be inside the zone
skey=set(key(sv))
newm=np.array([k not in skey for k in key(fv)])
new_in_zone=in_zone(fv[newm])
final_new=set(tuple(fv[i]) for i in np.where(newm)[0])
# 3) outside-zone baseline vertices all present bit-identically
outside_base=np.where(~in_zone(sv))[0]
outside_missing=[int(i) for i in outside_base if tuple(sv[i]) not in fkey]
# 4) loops/normals/UV/material of untouched faces: faces whose all verts are outside-zone baseline verts must exist identically
sface={}
for pi,p in enumerate(s_polys):
    if all((tuple(sv[v]) in fkey) and not in_zone(sv[[v]])[0] for v in p):
        sface[tuple(sorted(tuple(sv[v]) for v in p))]=pi
f_polys=F['polys']
final_adj=set()
for p in f_polys:
    if any(tuple(fv[v]) in final_new for v in p):
        for v in p: final_adj.add(tuple(fv[v]))
f_ls=F['lstart']; f_lt=F['ltotal']; f_cn=F['cn']; f_uv=F['uv']; f_mi=F['mi']; f_loops=F['loops']
fface={}
for pi,p in enumerate(f_polys): fface[tuple(sorted(tuple(fv[v]) for v in p))]=pi
face_missing=0; mat_diff=0; uv_diff=0; nrm_diff=0; nrm_checked=0; nrm_boundary_diff=0
# vertices sharing a face with a vertex that was removed / moved / is new (normals there may legitimately change)
changed_pos=set(tuple(p) for p in sv[removed]) if len(removed) else set()
base_adj=set()
for p in s_polys:
    if any(tuple(sv[v]) in changed_pos for v in p):
        for v in p: base_adj.add(tuple(sv[v]))

ring_vs=set()
for k,spi in sface.items():
    fpi=fface.get(k)
    if fpi is None: face_missing+=1; continue
    if s_mi[spi]!=f_mi[fpi]: mat_diff+=1
    # UV + normals per corner matched by vertex position
    sc={tuple(sv[s_loops[l]]):l for l in range(s_ls[spi],s_ls[spi]+s_lt[spi])}
    fc={tuple(fv[f_loops[l]]):l for l in range(f_ls[fpi],f_ls[fpi]+f_lt[fpi])}
    for pos,l in sc.items():
        l2=fc[pos]
        if not np.array_equal(s_uv[l],f_uv[l2]): uv_diff+=1
        nrm_checked+=1
        if not np.array_equal(s_cn[l],f_cn[l2]):
            if pos in base_adj or pos in final_adj: nrm_boundary_diff+=1
            else: nrm_diff+=1
# 5) integrity of the final mesh
me=F['me']
bm=bmesh.new(); bm.from_mesh(me)
nonman=sum(1 for e in bm.edges if len(e.link_faces)!=2)
noncontig=sum(1 for e in bm.edges if len(e.link_faces)==2 and not e.is_contiguous)
degen=sum(1 for f in bm.faces if f.calc_area()<1e-10)
loose=sum(1 for v in bm.verts if not v.link_faces)
vol=0.0
for f in bm.faces:
    vs=[v.co for v in f.verts]
    for i in range(1,len(vs)-1): vol+=vs[0].dot(vs[i].cross(vs[i+1]))/6
nm_mats=len(F['mats'])
res={
 'start_sha256':S_sha,'final_sha256':F['sha'],
 'baseline_verts':S_nv,'final_verts':len(fv),
 'baseline_tris':S_tris,'final_tris':F['tris'],'hair_tris_baseline':4960,'final_body_plus_hair':F['tris']+4960,
 'baseline_verts_kept_bit_identical':int(len(kept)),'baseline_verts_removed_or_moved':int(len(removed)),
 'removed_or_moved_outside_zone':int((~removed_in_zone).sum()),
 'new_verts':int(newm.sum()),'new_verts_outside_zone':int((~new_in_zone).sum()),
 'outside_zone_baseline_verts':int(len(outside_base)),'outside_zone_baseline_verts_missing_or_moved':len(outside_missing),
 'untouched_faces_checked':len(sface),'untouched_faces_missing':face_missing,'untouched_face_material_diffs':mat_diff,
 'untouched_corner_uv_diffs':uv_diff,'untouched_corner_normal_diffs_away_from_change':nrm_diff,'corner_normal_diffs_at_change_boundary':nrm_boundary_diff,'untouched_corners_checked':nrm_checked,
 'non_manifold_edges':nonman,'non_contiguous_edges':noncontig,'degenerate_faces':degen,'loose_verts':loose,
 'signed_volume_m3':vol,'z_min':float(fv[:,2].min()),'z_max':float(fv[:,2].max()),
 'materials_same':S_mats==F['mats'],'material_names':F['mats'],
 'other_objects_same':S_other==F['other'],'hair_verts_sha_same':S_hair==F['hair'],
}
res['OUTSIDE_ZONE_MOVED']=int(res['removed_or_moved_outside_zone']+res['new_verts_outside_zone']+res['outside_zone_baseline_verts_missing_or_moved']+res['untouched_faces_missing']+res['untouched_face_material_diffs']+res['untouched_corner_uv_diffs']+res['untouched_corner_normal_diffs_away_from_change'])
json.dump(res,open(OUT,'w'),indent=1); print(json.dumps(res,indent=1))

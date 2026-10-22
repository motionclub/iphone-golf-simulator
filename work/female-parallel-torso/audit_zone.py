"""Outside-zone audit: start blend vs candidate blend (exact float32 compare)."""
import numpy as np, json, hashlib, sys
A=np.load('audit/start.npz'); B=np.load('audit/cand.npz')
ma=json.load(open('audit/start.json')); mb=json.load(open('audit/cand.json'))
Z=np.load('data/zone.npz'); T=Z['torso']; W=Z['w']; arm=Z['arm']
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
res={'start_blend':'work/female-parallel-torso/HeroBase_Female_torso.blend','start_sha256':sha('HeroBase_Female_torso.blend'),
     'artdir_blend_sha256_now':sha('../../ArtDir/hero/base_lock/blender/HeroBase_Female.blend'),
     'expected_start_sha256':'200dc3b93e65491a8a7c3a8220c76cde5ca02ec7d1279e339f154005b22685cd',
     'candidate_blend':'work/female-parallel-torso/export/HeroBase_Female_torso_candidate.blend','candidate_sha256':sha('export/HeroBase_Female_torso_candidate.blend')}
res['start_sha_matches_expected']=res['start_sha256']==res['expected_start_sha256']
co0=A['Body_F/co']; co1=B['Body_F/co']; n=len(co0)
moved=(co0!=co1).any(1)
mi=np.where(moved)[0]
disp=np.linalg.norm(co1.astype(np.float64)-co0.astype(np.float64),axis=1)
res['vertex_count']=int(n); res['zone_vertex_count(flag)']=int(T.sum()); res['zone_vertices_with_weight>0']=int((W>0).sum())
res['moved_vertex_count']=int(moved.sum())
outside=moved&~T
res['moved_outside_zone']=int(outside.sum())
res['max_displacement_outside_zone_m']=float(disp[~T].max()) if (~T).any() else 0.0
res['max_displacement_inside_zone_mm']=float(disp[T].max()*1000)
z=co0[:,2]
reg={}
def cnt(name,mask): reg[name]={'verts':int(mask.sum()),'moved':int((moved&mask).sum()),'max_disp_mm':float(disp[mask].max()*1000) if mask.any() else 0.0}
cnt('head_neck_z>=1.37',z>=1.37)
cnt('arms_beyond_shoulder_ball(flag)',arm&~T)
cnt('hands_and_arms_z<0.795',(z<0.795)&(np.abs(co0[:,0])>0.19))
cnt('legs_feet_z<0.795',(z<0.795)&~(np.abs(co0[:,0])>0.19))
cnt('torso_zone',T)
cnt('everything_else_not_zone',~T)
res['regions']=reg
# topology / attributes
topo={}
for k in ('poly_start','poly_total','loop_vert','edges','mat_index','smooth'):
    topo[k]=bool(np.array_equal(A[f'Body_F/{k}'],B[f'Body_F/{k}']))
topo['uv_UVMap_identical']=bool(np.array_equal(A['Body_F/uv/UVMap'],B['Body_F/uv/UVMap']))
topo['custom_normal_raw_codes_identical(all loops)']=bool(np.array_equal(A['Body_F/custom_normal_raw'],B['Body_F/custom_normal_raw']))
topo['attribute_list_identical']=ma['objects'][0]['attributes']==mb['objects'][0]['attributes']
topo['has_custom_normals_same']=ma['objects'][0]['has_custom_normals']==mb['objects'][0]['has_custom_normals']
topo['triangle_count']=[ma['objects'][0]['tris'],mb['objects'][0]['tris']] if ma['objects'][0]['name']=='Body_F' else None
res['topology_identical']=topo
# other objects
oth={}
for oa,ob in zip(ma['objects'],mb['objects']):
    if oa['name']=='Body_F':
        oth['Body_F_transform_identical']=oa['matrix_world']==ob['matrix_world']; continue
    same=(oa['matrix_world']==ob['matrix_world'])
    if oa['type']=='MESH':
        same=same and bool(np.array_equal(A[f"{oa['name']}/co"],B[f"{ob['name']}/co"]))
    oth[oa['name']]=bool(same)
res['other_objects_identical']=oth
res['normals_note']='Only positions are written. The authored custom_normal attribute is bit-identical for every loop; its decoded value follows the new geometry (codes are relative to the computed loop normal). Blender decode itself has ~0.05deg session-to-session noise (start vs start measured 0.048deg).'
ok=(res['moved_outside_zone']==0 and all(v for k,v in topo.items() if isinstance(v,bool)) and all(oth.values()) and res['start_sha_matches_expected'])
res['PASS_outside_zone_equals_0']=bool(ok)
json.dump(res,open('outside_zone_audit.json','w'),indent=1)
print(json.dumps(res,indent=1))

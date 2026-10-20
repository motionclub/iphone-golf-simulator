"""Build the FORM2 coordinates from export/form2_params.json, write the staged blend + delta + audit.   python3 tools/make_final.py [params.json]"""
import sys,json,subprocess,hashlib; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from torso2 import *
import seam, rough
B='/Applications/Blender.app/Contents/MacOS/Blender'
pj=sys.argv[1] if len(sys.argv)>1 else str(WD/'export/form2_params.json')
P={**DEFAULT2,**json.load(open(pj))}
co=build2(P); np.save(WD/'data/co_FORM2_final.npy',co); np.save(WD/'data/torso_final.npy',co)
out_blend=str(WD/'export/HeroBase_Female_torso_form2_candidate.blend')
r=subprocess.run([B,'-b',str(WD/'START_torso_candidate.blend'),'--python',str(WD/'tools/apply_coords.py'),'--',str(WD/'data/co_FORM2_final.npy'),out_blend],capture_output=True,text=True); assert 'saved' in r.stdout,r.stdout[-500:]
r=subprocess.run([B,'-b',out_blend,'--python',str(WD/'tools/dump_blend.py'),'--',str(WD/'audit/form2.npz')],capture_output=True,text=True); assert 'dumped' in r.stdout
A=np.load(WD/'audit/cand_start.npz'); Bz=np.load(WD/'audit/form2.npz'); ma=json.load(open(WD/'audit/cand_start.json')); mb=json.load(open(WD/'audit/form2.json'))
co0=A['Body_F/co']; co1=Bz['Body_F/co']; orig32=np.load(WD/'data/orig.npz')['co'].astype(np.float32)
moved=(co0!=co1).any(1); moved_o=(orig32!=co1).any(1)
res={'moved_vs_chat7_candidate':int(moved.sum()),'moved_outside_zone_vs_chat7_candidate':int((moved&~T).sum()),'moved_vs_original_start':int(moved_o.sum()),'moved_outside_zone_vs_original_start':int((moved_o&~T).sum()),
     'border_vertices':int(BORDER.sum()),'border_vertices_moved_vs_original':int((moved_o&BORDER).sum()),'zone_vertices':int(T.sum())}
topo={k:bool(np.array_equal(A[f'Body_F/{k}'],Bz[f'Body_F/{k}'])) for k in ('poly_start','poly_total','loop_vert','edges','mat_index','smooth','custom_normal_raw')}
topo['uv']=bool(np.array_equal(A['Body_F/uv/UVMap'],Bz['Body_F/uv/UVMap'])); topo['hair_identical']=bool(np.array_equal(A['Hair_F/co'],Bz['Hair_F/co'])); topo['tris_candidate_vs_new']=[ma['objects'][0]['tris'],mb['objects'][0]['tris']]
other={}
for oa,ob in zip(ma['objects'],mb['objects']):
    if oa['name']=='Body_F': other['Body_F_matrix_identical']=oa['matrix_world']==ob['matrix_world']; continue
    other[oa['name']]=bool(oa['matrix_world']==ob['matrix_world'])
topo['other_objects_identical']=all(other.values()); res['topology']=topo
mi=np.where(moved_o)[0]
np.savez_compressed(WD/'export/torso_form2_delta.npz',moved_idx=mi.astype(np.int32),start_co=orig32[mi],new_co=co1[mi],zone_mask=T,vertex_count=np.int32(len(co1)))
res['delta_moved_vertices']=int(len(mi))
tri=TRI
def fn(c): v0,v1,v2=c[tri[:,0]],c[tri[:,1]],c[tri[:,2]]; n=np.cross(v1-v0,v2-v0); return n/np.maximum(np.linalg.norm(n,axis=1),1e-18)[:,None]
zt=T[tri].any(1); dot=(fn(CO0)*fn(co)).sum(1); res['flipped_zone_tris_vs_original']=int(((dot<0)&zt).sum()); res['zone_tris_turned_gt60deg']=int(((dot<0.5)&zt).sum())
res['max_vertex_move_mm_vs_original']=float(np.linalg.norm(co-CO0,axis=1).max()*1000)
res['dihedral']={'original':seam.stats(CO0),'chat7_candidate':seam.stats(np.load(WD/'data/cand_co.npy')),'form2':seam.stats(co)}
res['border_steps_mm']=seam.border_steps(co)[0]
cand=np.load(WD/'data/cand_co.npy')
inner=T&(D_ARM>0.012)&(D_LEG>0.012)&(D_TOP>0.012)
rn={k:rough.second_diff_noise(v) for k,v in (('original',CO0),('chat7_candidate',cand),('form2',co))}
res['bi_laplacian_roughness_mm_zone_interior']={k:{'mean':float(v[inner].mean()*1000),'p95':float(np.percentile(v[inner],95)*1000),'max':float(v[inner].max()*1000)} for k,v in rn.items()}
json.dump(res,open(WD/'export/form2_checks.json','w'),indent=1)
sha=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest()
print(json.dumps({k:res[k] for k in ('moved_outside_zone_vs_chat7_candidate','moved_outside_zone_vs_original_start','border_vertices_moved_vs_original','delta_moved_vertices','flipped_zone_tris_vs_original','zone_tris_turned_gt60deg','max_vertex_move_mm_vs_original','border_steps_mm')},indent=1)); print('topology',topo)
print('SHA blend',sha(out_blend)[:16],'delta',sha(str(WD/'export/torso_form2_delta.npz'))[:16])

"""Finite H9 shared whole-tuft compound prototype; scratch outputs only.
No validators, sources, installed files, or frozen stage files are changed.
"""
import bpy,sys,math,json,hashlib,collections
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[5]
sys.path.insert(0,str(ROOT/'blender/scripts'))
import postcard_lib as P,postcard_look_lib as L,postcard_props_lib as PL
import postcard_look_verify as Q
D=P.start('hole09_design',out_dir=str(OUT/'stage'));D.mod.SCENERY['tee_box_m']=(10.4,13.2)
stage=ROOT/'work/postcard-look/v3/hole09/stage/hole_09.blend';stage_sha=hashlib.sha256(stage.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(stage));D.terrain=bpy.data.objects[D.terrain_name]
loops=L.terrain_top_loops(D,D.terrain);D.loops=[[(float(x),float(y)) for x,y in ps] for ps,_ in loops];D.loop_kinds=['outer' if P.signed_area(np.array(ps))>0 else 'hole' for ps in D.loops];D._distfield=None
# Load only original QA definitions before its mutating main program.
qa={ '__name__':'qa_defs','__file__':str(ROOT/'blender/scripts/hole09_qa.py') }
text=(ROOT/'blender/scripts/hole09_qa.py').read_text();sys.argv=['prototype','--','--blend',str(stage)]
exec(compile(text[:text.index('# ----------------------------------------------------------------------------------------------- main')],qa['__file__'],'exec'),qa)
design,dp=Q.load_design(9);C=Q.Ctx(9,design,dp,{})
def snap():bpy.context.view_layer.update();return Q.Snap('blend',C)
S=snap();original=sorted((o for n,o in S.meshes.items() if n.startswith('PLANT_TUFT')),key=lambda o:o.name)
plants_before=len(S.named('PLANT_'));tri_before=sum(S.loc(o)['ntri'] for o in S.meshes.values())
ground=qa['ground_bvh'](list(S.meshes.values()));route=qa['HL'].route_m(D);shore=np.array([P.m(x,y) for x,y in D.SHORE]+[P.m(*D.SHORE[0])])
frozen={n:dict(V=S.wld(o)['W'].copy(),T=S.wld(o)['T'].copy()) for n,o in S.meshes.items() if n.startswith(Q.COLL_PREFIXES)}
source={o.name:dict(kind=o.data.name,V=S.wld(o)['W'].copy(),pivot=np.array(o.matrix_world.translation),uv=np.array([u.uv[:] for u in o.data.uv_layers.active.data]),rgba=Q.sway_colors(o.data)[0],faces=len(o.data.polygons),tri=S.loc(o)['ntri'],zone=str(o.get('h9_zone',o.get('h9_class','old'))),fringe=int(o.get('lk_fringe',0))) for o in original}
# Respect original singles and original author cluster identities; no invisible
# nodes remain. Field tufts without fringe IDs may form genuine nearby groups.
keys=collections.defaultdict(list)
for o in original:
 r=source[o.name];k=o.data.name
 if not k.startswith(('PLANT_TUFT_D','PLANT_TUFT_E','PLANT_TUFT_F','PLANT_TUFT_S','PLANT_TUFT_T')):continue
 keys[(r['zone'],r['fringe'])].append(o)
candidate_groups=[];singles=0
for key,items in sorted(keys.items()):
 if key[1]>0 and len(items)==1:singles+=1;continue
 pending=list(items)
 while pending:
  o=pending.pop(0);r=source[o.name];near=sorted((x for x in pending if np.linalg.norm(source[x.name]['pivot'][:2]-r['pivot'][:2])<=1.8),key=lambda x:np.linalg.norm(source[x.name]['pivot'][:2]-r['pivot'][:2]))
  fillers=[x for x in near if source[x.name]['faces']<=40]
  members=[o]
  if r['faces']<=40 and len(fillers)>=2:members+=fillers[:2]
  elif r['faces']>40 and fillers:members+=fillers[:1]
  elif r['faces']<=40:
   tall=[x for x in near if 40<source[x.name]['faces']<=84]
   if tall:members=[tall[0],o]
  if len(members)==1:continue
  for x in members:
   if x in pending:pending.remove(x)
  if sum(source[x.name]['faces'] for x in members)>120:raise RuntimeError('compound violates120poly cap')
  candidate_groups.append((key,members))
# Use >=3 real shape templates per kind sequence, repeated instances. A sequence
# with fewer six legal proposals stays unchanged rather than creating uniques.
by=collections.defaultdict(list)
for key,obs in candidate_groups:
 obs=sorted(obs,key=lambda o:o.data.name);by[tuple(o.data.name for o in obs)].append((key,obs))
variants={};proposals=[];reject=collections.Counter();groups=[]
for kinds,items in sorted(by.items()):
 if len(items)<6:reject['insufficient_real_variant_instances']+=len(items);continue
 for j in range(3):
  key,obs=items[j];pivot=np.array(obs[0].matrix_world.translation);V=[];F=[];UV=[];colors=[];parts=[];vi=fi=li=0
  for ob in obs:
   r=source[ob.name];W=r['V']-pivot
   # All actual tuple roots are on frozen flat ground. Preserve every source
   # vertex, polygon, UV and Col float in the authored template.
   V.extend(map(tuple,W));F.extend(tuple(vi+i for i in p.vertices) for p in ob.data.polygons)
   UV.extend(map(tuple,r['uv']));colors.extend(map(tuple,r['rgba']))
   parts.append(dict(source=ob.name,kind=ob.data.name,verts=[vi,vi+len(W)],faces=[fi,fi+len(ob.data.polygons)],root_local=(r['pivot']-pivot).tolist(),source_vertex_sha=hashlib.sha256(np.asarray(W,np.float64).tobytes()).hexdigest(),rgba_sha=hashlib.sha256(r['rgba'].tobytes()).hexdigest()))
   vi+=len(W);fi+=len(ob.data.polygons)
  me=bpy.data.meshes.new('PLANT_TUFT_COMPOUND_'+str(len(variants)));me.from_pydata(V,[],F);me.materials.append(bpy.data.materials['LK_PLANTS'])
  uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',np.asarray(UV,float).ravel())
  col=me.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT');col.data.foreach_set('color',np.asarray(colors,np.float32).ravel());me.color_attributes.active_color_name='Col';me.color_attributes.render_color_index=0
  me.update();me['lk_v3_real_tuft_parts']=json.dumps(parts);variants[(kinds,j)]=(me,parts)
 for i,(key,obs) in enumerate(items):
  me,parts=variants[(kinds,i%3)];oldp=np.array(obs[0].matrix_world.translation);local=np.array([v.co[:] for v in me.vertices]);old_height=max(source[o.name]['V'][:,2].max() for o in obs)-oldp[2]
  scale=min(2.,old_height/max(local[:,2].max(),1e-9));scale=max(.5,scale)
  # Genuine original pivot with a shared rotated whole-clump template. Scenery
  # positions and shader pivot phase may change; scoring positions may not.
  angle=float(obs[0].rotation_euler.z);rot=np.array(Matrix.Rotation(angle,3,'Z'))
  W=(local*scale)@rot.T+oldp;roots=np.array([p['root_local'] for p in parts])*scale@rot.T+oldp
  lies=P.lie_codes_m(D,roots[:,0],roots[:,1]);vertex_route=float(qa['dist_poly'](route,W[:,:2]).min());rootshore=float(qa['dist_poly'](shore,roots[:,:2]).min())
  if np.isin(lies,[P.LIE_WATER,P.LIE_FAIRWAY,P.LIE_GREEN,P.LIE_TEE,P.LIE_BUNKER]).any():reject['root_lie']+=1;continue
  if rootshore<1.1:reject['shore']+=1;continue
  if vertex_route<2.:reject['route']+=1;continue
  if np.linalg.norm(np.ptp(W[:,:2],axis=0))>20.:reject['span']+=1;continue
  if float(np.ptp(W[:,2]))>2.0:reject['height']+=1;continue
  # Keep the original group's largest cap: this does not prune real tufts.
  if W[:,2].max()>max(source[o.name]['V'][:,2].max() for o in obs)+1e-6:reject['original_top_cap']+=1;continue
  supported=True
  for root in roots:
   hit=ground.ray_cast(Vector((float(root[0]),float(root[1]),40.)),Vector((0,0,-1)))
   if hit[0] is None or abs(float(root[2])-hit[0].z)>.06:supported=False;break
  if not supported:reject['all_root_support']+=1;continue
  prototypes=[o for o in bpy.data.objects if o.name.startswith('PLANT_TUFT_COMPOUND') and o.data==me]
  proposals.append(dict(key=key,obs=obs,me=me,parts=parts,loc=oldp,scale=scale,angle=angle,roots=roots,span=float(np.linalg.norm(np.ptp(W[:,:2],axis=0)))))
# Insufficient real mesh users are not installed; no keepalive hidden objects.
users=collections.Counter(x['me'].name for x in proposals)
for row in proposals:
 if users[row['me'].name]<2:reject['one_accepted_variant_user']+=1;continue
 obs=row['obs'];ob=bpy.data.objects.new(row['me'].name+'.'+str(len(groups)).zfill(3),row['me']);obs[0].users_collection[0].objects.link(ob);ob.parent=obs[0].parent;ob.location=row['loc'];ob.scale=(row['scale'],)*3;ob.rotation_euler.z=row['angle']
 ob['h9_zone']=row['key'][0];ob['lk_v3_real_tuft_parts']=json.dumps(row['parts']);ob['lk_v3_reauthored_clump']=True
 groups.append(dict(name=ob.name,replaced=[x.name for x in obs],real_tufts=len(obs),mesh=ob.data.name,span_m=row['span'],actual_roots=row['roots'].tolist(),parts=row['parts']))
 for old in obs:bpy.data.objects.remove(old,do_unlink=True)
S=snap();checks={};tests=[Q.g_prop_budget,Q.g_plants_material,Q.g_plants_instanced,Q.g_plant_sway_colors,Q.g_plant_sway_caps,Q.g_no_plant_on_water,Q.g_uv]
for fn in tests:
 try:checks[fn.__name__]=fn(S,C)
 except Exception as ex:checks[fn.__name__]=[False,repr(ex)]
objs=list(S.meshes.values());checks['H_NO_PLANT_ON_WATER']=qa['g_no_plant_on_water']('scratch_compound',D,objs,shore);checks['H_RIDGE_PLANTS_ROCKS']=qa['g_ridge_features'](D,objs);checks['H_RIDGE_THICKETS']=qa['g_thickets'](D,objs);checks['H_SCRUB_BOUNDARY_COVERED']=qa['g_scrub_boundary'](D,objs);checks.update({'H_LEGACY_'+k:v for k,v in qa['g_legacy_rules'](D,objs,shore).items()})
# Check each real authored tuft's lowest4% root vertices independently, not only
# the merged mesh's global minimum. These are actual face/vertex ranges.
root_records=[];root_rgba_ok=True;rgba_copy_ok=True
for (kinds,j),(me,parts) in variants.items():
 colors=Q.sway_colors(me)[0];co=np.array([v.co[:] for v in me.vertices])
 for part in parts:
  a,b=part['verts'];q=co[a:b];rgba=colors[a:b];z=q[:,2];r=z<=z.min()+.04*max(float(np.ptp(z)),1e-9);mx=float(rgba[r,0].max());root_rgba_ok &= mx<=.05
  rgba_copy_ok &= hashlib.sha256(rgba.tobytes()).hexdigest()==part['rgba_sha'];root_records.append(dict(mesh=me.name,source=part['source'],root_max=mx,root_vertices=int(r.sum()),rgba_exact=hashlib.sha256(rgba.tobytes()).hexdigest()==part['rgba_sha']))
checks['INDEPENDENT_EVERY_REAL_TUFT_ROOT_RGBA']=[bool(root_rgba_ok and rgba_copy_ok),f'{len(root_records)} real whole-tuft ranges; every root R<=.05; exact original template RGBA {rgba_copy_ok}']
max_delta=0.;topology_ok=True
for n,old in frozen.items():
 ob=S.meshes[n];w=S.wld(ob);max_delta=max(max_delta,float(np.abs(w['W']-old['V']).max()));topology_ok &= np.array_equal(w['T'],old['T'])
checks['FROZEN_SCORING_EXACT']=[max_delta==0 and topology_ok,f'exact maximum world delta {max_delta}m; triangle topology exact {topology_ok}']
tri_after=sum(S.loc(o)['ntri'] for o in S.meshes.values());checks['EXACT_SOURCE_TRIANGLE_TOTAL']=[tri_after==tri_before and tri_after<=250000,f'{tri_before}->{tri_after}; legacy250000cap']
physical_before=len(original);physical_after=sum(row['real_tufts'] for row in groups)+len([o for n,o in S.meshes.items() if n.startswith('PLANT_TUFT') and not o.get('lk_v3_reauthored_clump')]);checks['ACTUAL_WHOLE_TUFT_CENSUS']=[physical_before==physical_after,f'{physical_before}->{physical_after} real source-copy tufts; no empty/invisible keepalive nodes']
result=dict(stage_source_sha_before=stage_sha,stage_source_sha_after=hashlib.sha256(stage.read_bytes()).hexdigest(),production_applied=False,plants_before=plants_before,plants_after=len(S.named('PLANT_')),mesh_objects_before=1417,mesh_objects_after=len(S.meshes),tuft_objects_before=len(original),tuft_objects_after=len(S.named('PLANT_TUFT')),real_tufts_before=physical_before,real_tufts_after=physical_after,compound_renderers=len(groups),real_shared_compound_variants=len({g['mesh'] for g in groups}),original_singles_retained=singles,rejects=dict(reject),checks=checks,groups=groups,per_real_tuft_root_checks=root_records,native_draw_calls_unmeasured=True)
(OUT/'result.json').write_text(json.dumps(result,indent=2,default=lambda x:float(x) if isinstance(x,np.generic) else str(x))+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('groups','per_real_tuft_root_checks')},indent=2,default=str),flush=True)
# Save only a labelled prototype, not any production/final stage path.
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'compound_unverified.blend'),relative_remap=False)

"""Resume the unverified native-builder checkpoint with actual H9 UV repair."""
import ast,json,os,sys,types
sys.dont_write_bytecode=True
import bpy,numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.abspath(os.path.join(HERE,'../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import postcard_lib as P
import postcard_look_lib as L
import hole09_look as HL
import postcard_look_verify as V
os.chdir(ROOT)
meta=json.load(open(HERE+'/checkpoints/unverified_pre_batch.json'))
D=P.start('hole09_design',out_dir=HERE+'/stage')
D.mod.SCENERY['tee_box_m']=(10.4,13.2)
bpy.ops.wm.open_mainfile(filepath=HERE+'/checkpoints/unverified_pre_batch.blend',load_ui=False)
D.terrain=bpy.data.objects[D.terrain_name]
loops=L.terrain_top_loops(D,D.terrain)
D.loops=[xy.tolist() for xy,ids in loops]
D.loop_kinds=['outer' if P.signed_area(x)>0 else 'hole' for x in D.loops]
D._distfield=None
D.objects={o.name:o for o in P._export_objects(D)}
D.look_objects=[o.name for o in P._export_objects(D) if o.name.startswith(('ROCK_','PLANT_','DRESS_','WATER_'))]
D.strata_kwargs=meta['strata_kwargs']
D.strata_stats=meta['strata_stats']
D.postcard_outline=meta['cliff_outline']
snapshot=L.snapshot_ground(D)
scenery={k:[bpy.data.objects[n] for n in names] for k,names in meta['scenery'].items()}
scenery['knoll_specs']=meta['ridge_specs']
scenery['grass']=meta['grass']
batch_stats=HL.merge_static_scenery(D,scenery)
knoll_faces=HL.repair_knoll_rock_uvs(D)
# Execute the native builder's exact parallax function/constant assignment.
tree=ast.parse(open(ROOT+'/blender/scripts/hole09_build.py').read())
nodes=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name=='tee_parallax_uvs') or
       (isinstance(n,ast.Assign) and any(isinstance(t,ast.Tuple) and any(isinstance(x,ast.Name) and x.id=='TEE_CAM_BACK_YD' for x in t.elts) for t in n.targets))]
scope=dict(np=np,bpy=bpy,P=P,L=L)
exec(compile(ast.Module(body=nodes,type_ignores=[]),ROOT+'/blender/scripts/hole09_build.py','exec'),scope)
scope['tee_parallax_uvs'](D)
bpy.data.objects['FAIRWAY_FIRSTCUT'].data.materials[0]=L.look_material('LK_ROUGH',D)
firstcut_faces=HL.repair_firstcut_uvs(D)
bpy.context.view_layer.update()
C=types.SimpleNamespace(tag='09',hole=9)
S=V.Snap('blend',C)
uv_gates=[]
for name,fn in [('UV_DENSITY',V.g_uv),('GROUND_UV_LOCAL_SMEAR',V.g_uv_local_smear)]:
    ok,detail=fn(S,C);uv_gates.append(dict(name=name,ok=ok,detail=detail))
    print('GATE: '+name+' '+('PASS' if ok else 'FAIL')+' - '+detail,flush=True)
json.dump(dict(knoll_rock_faces=knoll_faces,firstcut_top_faces=firstcut_faces,gates=uv_gates),open(HERE+'/uv_repair.json','w'),indent=2)
if not all(r['ok'] for r in uv_gates):raise RuntimeError('Actual UV repair fails unchanged gates')
gates=[]
ok,detail=L.compare_ground(D,snapshot)
gates.append(dict(name='H_PLAY_UNCHANGED_INBUILD',ok=ok,detail=detail))
for name,ok,detail in L.audit_look(D)+L.v2_gates(D,pockets=L.sea_pockets(D,None)):
    gates.append(dict(name=name,ok=ok,detail=detail))
tort=L.skin_tortuosity(D)
gates.append(dict(name='SKIN_JAGGED',ok=tort is not None and tort>=1.15,detail=f'actual tortuosity{tort}; unchanged>=1.15'))
for row in gates:print('GATE: '+row['name']+' '+('PASS' if row['ok'] else 'FAIL')+' - '+row['detail'],flush=True)
stats=P.stats(D)
info=dict(stats=stats,gates=gates,masonry_batches=batch_stats,cliff_outline=D.postcard_outline,
          strata_stats=D.strata_stats,ridge_specs=scenery['knoll_specs'],grass=scenery['grass'],
          plant_counts={k:len(scenery[k]) for k in ('shrubs','shrubs_out','agave','flowers','tufts')},
          resumed_unverified_checkpoint=True,uv_repair=dict(knoll_faces=knoll_faces,firstcut_faces=firstcut_faces))
json.dump(info,open(HERE+'/stage/phase3_build.json','w'),indent=2)
if not all(r['ok'] for r in gates):raise RuntimeError('Original audits fail; final stage/export blocked')
bpy.ops.wm.save_as_mainfile(filepath=HERE+'/stage/hole_09.blend',relative_remap=False)
L.export_look_fbx(D)
print('RESUMED_STAGE '+json.dumps({k:stats[k] for k in ('meshes','objects','tris','ground_tris')}),flush=True)

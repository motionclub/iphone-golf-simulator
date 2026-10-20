import bpy,sys,json,numpy as np
from pathlib import Path
R=Path(sys.argv[sys.argv.index('--')+1]);W=R/'work/cloth-overhaul';res={}
for sex in ['Male','Female']:
 all={}
 for label,path in [('old',W/f'rollback/Unity/Assets/Characters/MatchHeroKit/{sex}_Kit.fbx'),('new',W/f'export/{sex}_Kit.fbx')]:
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
  info={'rigMatrix':[list(v) for v in rig.matrix_world],'bones':{b.name:{'head':list(rig.matrix_world@b.head_local),'matrix':[list(v) for v in b.matrix_local],'parent':b.parent.name if b.parent else None} for b in rig.data.bones},'meshes':{}}
  for o in bpy.data.objects:
   if o.type!='MESH':continue
   dg=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(dg);m=e.to_mesh();P=np.array([o.matrix_world@v.co for v in m.vertices]);e.to_mesh_clear()
   info['meshes'][o.name]={'matrix':[list(v) for v in o.matrix_world],'parentInverse':[list(v) for v in o.matrix_parent_inverse],'evalMin':P.min(0).tolist(),'evalMax':P.max(0).tolist(),'sumError':max(abs(1-sum(g.weight for g in v.groups)) for v in o.data.vertices)}
  all[label]=info
 res[sex]=all
(W/'fbx_diagnostic.json').write_text(json.dumps(res,indent=2))
for s in res:
 a,b=res[s]['old'],res[s]['new'];print(s,'rig',a['rigMatrix'],b['rigMatrix']);print('head max',max(np.linalg.norm(np.array(a['bones'][n]['head'])-b['bones'][n]['head']) for n in a['bones']))
 for n in a['meshes']:print(n,a['meshes'][n]['evalMin'],b['meshes'][n]['evalMin'],a['meshes'][n]['evalMax'],b['meshes'][n]['evalMax'])

import bpy,json
from pathlib import Path
R=Path.cwd();out=R/'work/reference-rebuild/coastal-scenery-audit'
for label,path in [('original','Unity/Assets/Resources/Course/hole_12.fbx'),('reference','Unity/Assets/Resources/Course/Resort/ReferenceHole12.fbx')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(R/path),use_anim=False)
 records=[];markers=[]
 for o in bpy.context.scene.objects:
  if o.name.startswith('PLANT_') or o.name.startswith('MARKER_'):
   markers.append({'name':o.name,'position':list(o.matrix_world.translation),'scale':list(o.matrix_world.to_scale())})
  if o.type!='MESH' or not o.name.upper().startswith(('TREE','SHRUB','BUSH','ROCK','LIGHTHOUSE','TOWER','CLUBHOUSE')):continue
  m=o.data;records.append({'name':o.name,'localVertices':[list(v.co) for v in m.vertices],'worldVertices':[list(o.matrix_world@v.co) for v in m.vertices],'faces':[list(p.vertices) for p in m.polygons]})
 (out/(label+'.json')).write_text(json.dumps({'source':path,'meshes':records,'markers':markers},separators=(',',':')))
 print('SCENERY_SOURCE',label,'meshes',len(records),'plants',sum(x['name'].startswith('PLANT_') for x in markers),flush=True)

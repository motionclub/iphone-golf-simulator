import bpy,bmesh,pathlib,json
from mathutils import Vector
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';manifest={}
for sex in ('male','female'):
 bpy.ops.wm.open_mainfile(filepath=str(O/f'{sex}_reference_form1.blend'));head=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('GEO-') and all(x not in o.name for x in ('.iris.','.sclera.','.eye.')))
 if sex=='female':
  for o in bpy.data.objects:
   if o.type=='MESH' and o.name.startswith('Eye_Iris_Candidate'):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
 sc=bpy.context.scene;target=Vector((0,0,.006))
 for angle,loc in [('front',(0,-1.1,.010)),('threequarter',(.58,-1.1,.025))]:
  sc.camera.location=loc;sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/f'{sex}_reference_form1_{angle}.png');bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_reference_form1.blend'))
 meshes=[];stats=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in list(bpy.data.objects):
  if o.type!='MESH':continue
  if o!=head and not any(t in o.name for t in ('.iris.','.sclera.','.eye.','Eye_Iris_Candidate','Brow_Candidate')):continue
  for m in o.modifiers:
   if m.type=='SUBSURF':m.levels=0 if (o!=head or sex=='male') else 1;m.render_levels=m.levels
  bpy.context.view_layer.update();ev=o.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev);me.transform(o.matrix_world);me.update()
  if o==head:
   bm=bmesh.new();bm.from_mesh(me);remove=[v for v in bm.verts if v.co.z<-.215];bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(me);bm.free();me.update();name='HeadSkin'
  elif 'Brow' in o.name:name='Brow_'+('L' if sum(v.co.x for v in me.vertices)>0 else 'R')
  elif 'iris' in o.name.lower():name='Eye_Iris_'+('L' if sum(v.co.x for v in me.vertices)>0 else 'R')
  else:name='Eye_Sclera_'+('L' if sum(v.co.x for v in me.vertices)>0 else 'R')
  ob=bpy.data.objects.new('Pilot_'+name,me);meshes.append(ob);me.calc_loop_triangles();stats.append({'name':name,'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'materials':[m.name for m in me.materials]})
 for o in list(bpy.data.objects):
  if o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
 root=bpy.data.objects.new('HeadAssembly',None);bpy.context.scene.collection.objects.link(root)
 for o in meshes:bpy.context.scene.collection.objects.link(o);o.parent=root;o.name=o.name.removeprefix('Pilot_');o.select_set(True)
 root.select_set(True);bpy.context.view_layer.objects.active=meshes[0]
 path=O/f'{sex}_reference_pilot.fbx';bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH','EMPTY'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,axis_forward='-Z',axis_up='Y',path_mode='AUTO');bpy.ops.wm.save_as_mainfile(filepath=str(O/f'{sex}_reference_pilot.blend'))
 manifest[sex]={'file':str(path),'meshes':stats,'totalTriangles':sum(x['triangles'] for x in stats),'sourceFrame':'metres, eye midpoint=(0,0,0), source front -Y, up Z','noProductionIntegration':True,'facialMorphs':'pending actual art approval'}
(O/'pilot-manifest.json').write_text(json.dumps(manifest,indent=2));print('PILOT_EXPORT',json.dumps(manifest))

import bpy,pathlib,json,math
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/characters';bpy.ops.wm.open_mainfile(filepath=str(O/'female_reference_pilot.blend'));manifest=json.loads((O/'pilot-manifest.json').read_text());stats=[]
for ob in list(bpy.data.objects):
 if ob.type!='MESH':continue
 if ob.name.startswith('Eye_Iris_'):
  old=ob.data;verts=[old.vertices[r*64+j*2].co[:] for r in range(16) for j in range(32)];faces=[];roles=[]
  for r in range(15):
   for j in range(32):faces.append((r*32+j,(r+1)*32+j,(r+1)*32+(j+1)%32,r*32+(j+1)%32));roles.append(old.polygons[r*64+j*2].material_index)
  me=bpy.data.meshes.new('BoundedIris32');me.from_pydata(verts,[],faces)
  for m in old.materials:me.materials.append(m)
  for p,role in zip(me.polygons,roles):p.material_index=role;p.use_smooth=True
  ob.data=me
 if ob.name.startswith('Eye_Sclera'):
  ob.data.materials.pop(index=2);ob.data.materials.pop(index=1)
 ob.data.calc_loop_triangles();stats.append({'name':ob.name,'vertices':len(ob.data.vertices),'triangles':len(ob.data.loop_triangles),'materials':[m.name for m in ob.data.materials]});ob.select_set(True)
for ob in bpy.data.objects:
 if ob.type=='EMPTY':ob.select_set(True)
manifest['female']['meshes']=stats;manifest['female']['totalTriangles']=sum(x['triangles'] for x in stats);manifest['female']['irisExportLOD']='32 angular samples vs64 studio; maximum circle chord deviation0.118mm at24.5mmradius'
bpy.ops.export_scene.fbx(filepath=str(O/'female_reference_pilot.fbx'),use_selection=True,object_types={'MESH','EMPTY'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,axis_forward='-Z',axis_up='Y',path_mode='AUTO');bpy.ops.wm.save_as_mainfile(filepath=str(O/'female_reference_pilot.blend'));(O/'pilot-manifest.json').write_text(json.dumps(manifest,indent=2));print('BOUNDED_FEMALE',manifest['female']['totalTriangles'])

import bpy,sys,numpy as np,json,math
from pathlib import Path
W=Path(sys.argv[sys.argv.index('--')+1])/'work/cloth-overhaul';sys.path.insert(0,str(W/'scripts'))
from pocket_construction import construct_pockets
p=W/'export/Cloth_Male.blend';bpy.ops.wm.open_mainfile(filepath=str(p));o=bpy.data.objects['Kit_Bottom'];before=sum(len(f.vertices)-2 for f in o.data.polygons);cut=construct_pockets(o);m=o.data
for f in m.polygons:f.use_smooth=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.4,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
m.calc_loop_triangles();P=np.array([v.co[:] for v in m.vertices]);CN=np.array([n.vector[:] for n in m.corner_normals]);UV=np.array([u.uv[:] for u in m.uv_layers[0].data]);tri=np.array([t.vertices[:] for t in m.loop_triangles]);tl=np.array([t.loops[:] for t in m.loop_triangles]);mi=np.array([t.material_index for t in m.loop_triangles]);np.savez(W/'export/Male_Kit_Bottom.npz',P=P,normal=CN,uv=UV,tri=tri,triloops=tl,material=mi,materials=np.array([s.name for s in m.materials]));bpy.ops.wm.save_as_mainfile(filepath=str(p))
kit=[bpy.data.objects[n] for n in ['Kit_Top','Kit_Bottom','Kit_Sock_L','Kit_Sock_R','Kit_Shoe_L','Kit_Shoe_R']];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in kit:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.export_scene.fbx(filepath=str(W/'export/Male_Kit.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
(W/'pocket_geometry.json').write_text(json.dumps({'cut_faces':cut,'before_tris':before,'after_tris':len(tri)},indent=2));print('POCKETS',cut,before,len(tri),flush=True)

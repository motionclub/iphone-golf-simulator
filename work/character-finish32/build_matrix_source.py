import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
w=Path('work/character-finish32');bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Refined.blend'));o=bpy.data.objects['Kit_Top'];rig=next(x for x in bpy.data.objects if x.type=='ARMATURE');b=json.loads((w/'refined/poses/male_intro.json').read_text())['parts'][0];bp=[Vector((-b['vertices'][i],*b['vertices'][i+1:i+3])) for i in range(0,len(b['vertices']),3)];bn=[Vector((-b['normals'][i],*b['normals'][i+1:i+3])) for i in range(0,len(b['normals']),3)];bt=[b['triangles'][i:i+3][::-1] for i in range(0,len(b['triangles']),3)];tree=BVHTree.FromPolygons(bp,bt,all_triangles=True)
def smooth(a,z,x):
 t=min(1,max(0,(x-a)/(z-a)));return t*t*(3-2*t)
changed=0
for v in o.data.vertices:
 x,y,z=v.co;f=smooth(.105,.145,abs(x))*(1-smooth(.19,.225,abs(x)))*smooth(1.07,1.14,z)*(1-smooth(1.24,1.31,z))
 if f<=0:continue
 hit,n,fi,dist=tree.find_nearest(v.co);n=sum((bn[j] for j in bt[fi]),Vector()).normalized();v.co+=n*(.009*f);changed+=1
bpy.context.view_layer.objects.active=o;o.select_set(True)
if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_MatrixSource.blend'));bpy.ops.export_scene.fbx(filepath=str(w/'review-project/Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
q=json.loads((w/'twist-source-queue.json').read_text());q[0]['name']='character-finish32-matrix-source';q[0]['env']['VISUAL_CHARACTER_OUT']=str(w.resolve()/'matrix-source');q[0]['env']['VISUAL_CHARACTER_CLOTH_MATRIX_ONLY']='1';(w/'matrix-source-queue.json').write_text(json.dumps(q,indent=2));print('SOURCE SIDE EASE',changed,'max9mm',flush=True)

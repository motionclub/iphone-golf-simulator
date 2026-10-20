import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator');w=r/'work/character-finish32'
bpy.ops.wm.open_mainfile(filepath=str(w/'Male_Polo_Clean.blend'));o=bpy.data.objects['Kit_Top'];m=o.data;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
data=json.loads((w/'baseline/poses/male_intro.json').read_text());body=data['parts'][0];bp=[Vector((-body['vertices'][i],*body['vertices'][i+1:i+3])) for i in range(0,len(body['vertices']),3)];bn=[Vector((-body['normals'][i],*body['normals'][i+1:i+3])) for i in range(0,len(body['normals']),3)];tri=[body['triangles'][i:i+3][::-1] for i in range(0,len(body['triangles']),3)];tree=BVHTree.FromPolygons(bp,tri,all_triangles=True)
changed=0
for v in m.vertices:
 x,y,z=v.co;s=(abs(x)-.165)*.72+(1.384-z)*.69;t=min(1,max(0,(s-.10)/.08));t=t*t*(3-2*t)*min(1,max(0,(abs(x)-.18)/.040))*min(1,max(0,(z-1.165)/.025))
 if t<=0:continue
 v.co+=Vector((math.copysign(.72,x),-.03,-.69))*.027*t
 hit,n,fi,dist=tree.find_nearest(v.co);ids=tri[fi];bc=barycentric_transform(hit,*[bp[j] for j in ids],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)));n=sum((bn[j]*alpha for j,alpha in zip(ids,bc)),Vector()).normalized();signed=(v.co-hit).dot(n)
 if signed<.009:v.co=hit+n*.009
 weights={}
 for j,a in zip(ids,bc):
  for slot in range(4):
   name=body['bones'][body['indices'][j*4+slot]];value=body['weights'][j*4+slot]*max(0,a);weights[name]=weights.get(name,0)+value
 weights=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(v for _,v in weights)
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for name,value in weights:o.vertex_groups[name].add([v.index],value/total,'REPLACE')
 changed+=1
m.update()
if m.has_custom_normals:bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.wm.save_as_mainfile(filepath=str(w/'Male_Polo_Sleeve.blend'))
bpy.ops.export_scene.fbx(filepath=str(r/'Unity/Assets/Resources/Tennis/KitsTailored/Male.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='AUTO',embed_textures=False)
print('SLEEVE',changed)

import bpy,math,json
from pathlib import Path
from mathutils import Matrix,Vector
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(r/f'ArtDir/golf/source/gallery3-inputs/{sex}GolfMaster.blend'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='POSE'
 for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
 bpy.context.view_layer.update()
 for side in ['Left','Right']:
  b=rig.pose.bones[side+'UpperArm'];a=math.radians(30 if sex=='Male' else 5)*(1 if side=='Left' else -1);h=b.head.copy();b.matrix=Matrix.Translation(h)@Matrix.Rotation(a,4,'Y')@Matrix.Translation(-h)@b.matrix
 body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));names=[g.name for g in body.vertex_groups];floor=-.0305 if sex=='Male' else -.0255
 for enabled in [True,False]:
  for mod in body.modifiers:
   if mod.type=='NODES':mod.show_viewport=enabled;mod.show_render=enabled
  bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();samples=[]
  for v in mesh.vertices:
   p=body.matrix_world@v.co-Vector((0,0,floor))
   if p.z<1.30 or p.z>1.445 or abs(p.x)>.105:continue
   head=sum(g.weight for g in v.groups if g.group<len(names) and names[g.group] in ['Head','Neck'])
   samples.append((p.x,p.y,p.z,head))
  report={'sex':sex,'nodes':enabled,'verts':len(mesh.vertices),'polys':len(mesh.polygons),'neck_sample_count':len(samples),'neck_y_range':(min(p[1] for p in samples),max(p[1] for p in samples)) if samples else None,'front_chest_samples':[(round(y,4),round(z,4),round(h,2)) for x,y,z,h in samples if abs(x)<.01 and y<-.09][:50]}
  print('NECK_PROBE',json.dumps(report));ev.to_mesh_clear()

import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[4]
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(R/'ArtDir/golf/source/gallery3-inputs'/f'{sex}GolfMaster.blend'))
 rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='POSE'
 for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for obj in bpy.data.objects:
  if obj.type!='MESH' or not obj.name.startswith(('Kit_Shoe','Kit_Sock')):continue
  ev=obj.evaluated_get(deps);m=ev.to_mesh();pts=[obj.matrix_world@v.co for v in m.vertices];m.calc_loop_triangles()
  print('SOURCE_DATA',json.dumps({'sex':sex,'object':obj.name,'bounds':[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],'tris':len(m.loop_triangles),'materials':[mat.name if mat else '?' for mat in m.materials],'modifiers':[(mod.name,mod.type) for mod in obj.modifiers],'z_percentiles':[sorted(p.z for p in pts)[int(q*(len(pts)-1))] for q in [0,.1,.25,.5,.75,.9,1]],'anchors':{n:list(rig.matrix_world@rig.pose.bones[n].head) for n in ['LeftFoot','RightFoot','LeftToes','RightToes']}}))
  ev.to_mesh_clear()

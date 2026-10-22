import bpy,json,os
from pathlib import Path
from mathutils import Vector
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
a=bpy.data.actions.get('ReadyIdle');rig.animation_data_create();rig.animation_data.action=a;bpy.context.scene.frame_set(15);bpy.context.view_layer.update()
racket=bpy.data.objects.get('Racket_Classic')
rows=[]
for side in ['Right','Left']:
 hand=rig.pose.bones[side+'Hand']; index=rig.pose.bones[side+'IndexProximal'];little=rig.pose.bones[side+'LittleProximal'];middle=rig.pose.bones[side+'MiddleProximal']
 W=rig.matrix_world
 u=(middle.head-hand.head).normalized();v=(index.head-little.head).normalized();p=v.cross(u).normalized()
 for finger in ['Index','Middle','Ring','Little','Thumb']:
  for joint in ['Proximal','Intermediate','Distal']:
   name=side+finger+joint;b=rig.pose.bones.get(name)
   if not b:continue
   direction=(b.tail-b.head).normalized();towards=p-direction*direction.dot(p);towards.normalize();hinge=direction.cross(towards).normalized()
   local=b.matrix.to_3x3().inverted()@hinge
   rows.append({'name':name,'head':list(W@b.head),'tail':list(W@b.tail),'localBendAxis':list(local),'palmNormal':list(p),'rotation':list(b.rotation_quaternion)})
print('GRIP_AUDIT '+rig.name+' racket='+str(racket))
out=Path(os.environ['GRIP_AUDIT_OUT']);out.write_text(json.dumps({'rig':rig.name,'racketMatrix':[list(r) for r in racket.matrix_world] if racket else None,'bones':rows},indent=2))

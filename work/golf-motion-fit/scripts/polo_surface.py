"""Tailor the golf shell in an A-pose, then return to the immutable rig rest pose.
The A-pose separates the arm and torso surfaces before garment-only remeshing.
"""
import bpy,bmesh,numpy as np
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree

def build_surface(body,rig):
 rig.data.pose_position='POSE';rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 for side,sign in [('Left',-1),('Right',1)]:
  pb=rig.pose.bones[side+'UpperArm'];head=pb.bone.head_local
  pb.matrix=Matrix.Translation(head)@Matrix.Rotation(np.radians(sign*45),4,'Y')@Matrix.Translation(-head)@pb.bone.matrix_local
 coverage=body.modifiers.get('Golf outfit coverage')
 if coverage:coverage.show_viewport=False
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);posed=ev.to_mesh()
 if len(posed.vertices)!=len(body.data.vertices):raise RuntimeError('Authoring body vertex correspondence changed')
 kd=KDTree(len(posed.vertices))
 for v in posed.vertices:kd.insert(v.co,v.index)
 kd.balance()
 mesh=posed.copy();ev.to_mesh_clear();shell=bpy.data.objects.new('GolfTailoringSurface',mesh);bpy.context.scene.collection.objects.link(shell)
 bpy.ops.object.select_all(action='DESELECT');shell.select_set(True);bpy.context.view_layer.objects.active=shell
 shell.data.remesh_voxel_size=.004;shell.data.use_remesh_preserve_volume=True;bpy.ops.object.voxel_remesh()
 boneNames=[b.name for b in rig.data.bones];skin={n:np.array(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()) for n in boneNames}
 allowed={'Hips','Spine','Chest','UpperChest','Neck','LeftShoulder','RightShoulder','LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm','LeftUpperLeg','RightUpperLeg'}
 rest=[];rows=[];accept=[]
 for v in shell.data.vertices:
  row={}
  for _,i,d in kd.find_n(v.co,16):
   for g in body.data.vertices[i].groups:
    n=body.vertex_groups[g.group].name;row[n]=row.get(n,0)+g.weight/((d+.012)**2)
  total=sum(row.values());row={n:w/total for n,w in row.items()}
  banned=sum(w for n,w in row.items() if n=='Head' or 'Hand' in n or any(t in n for t in ['Thumb','Index','Middle','Ring','Little']))
  row=dict(sorted([(n,w) for n,w in row.items() if n in allowed],key=lambda p:p[1],reverse=True)[:4]);total=sum(row.values())
  if not total:row={'Hips':1.0}
  else:row={n:w/total for n,w in row.items()}
  M=sum((skin[n]*w for n,w in row.items()),np.zeros((4,4)));ease=.004 if v.co.z<1.04 else .009
  p=np.linalg.solve(M,np.r_[np.array(v.co)+np.array(v.normal)*ease,1])[:3];keep=.935<p[2]<1.432 and banned<.15
  for side in ['Left','Right']:
   a=rig.data.bones[side+'UpperArm'].head_local;b=rig.data.bones[side+'LowerArm'].head_local
   if row.get(side+'UpperArm',0)+row.get(side+'LowerArm',0)>.4 and (Vector(p)-(a+(b-a)*.68)).dot((b-a).normalized())>.008:keep=False
  rest.append(p);rows.append(row);accept.append(keep)
 faces=[tuple(p.vertices) for p in shell.data.polygons if all(accept[i] for i in p.vertices)];used=sorted({i for face in faces for i in face});mapping={i:j for j,i in enumerate(used)}
 result=([rest[i] for i in used],[tuple(mapping[i] for i in f) for f in faces],[rows[i] for i in used])
 bpy.data.objects.remove(shell,do_unlink=True)
 if coverage:coverage.show_viewport=True
 rig.data.pose_position='REST'
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();print('A_POSE_GOLF_SURFACE',len(result[0]),len(result[1]),flush=True)
 return result

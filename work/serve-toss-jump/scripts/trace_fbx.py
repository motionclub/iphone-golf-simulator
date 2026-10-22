"""Independent measurements after FBX re-import. No source assets are modified."""
import bpy,json,sys,math,numpy as np
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];src,tag,out=args[:3]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src,automatic_bone_orientation=False)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;sc.render.fps=30
act=rig.animation_data.action
sc.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['Body_M' if tag=='male' else 'Body_F'];groups={g.index:g.name for g in body.vertex_groups}
# Foot samples are chosen on the imported bind mesh, separately from its deformation.
sels={}
for sd,S in [('L','Left'),('R','Right')]:
 ids=[v.index for v in body.data.vertices if v.groups and groups[max(v.groups,key=lambda g:g.weight).group] in (S+'Foot',S+'Toes')]
 co=np.array([body.matrix_world@body.data.vertices[i].co for i in ids]);ank=np.array(rig.matrix_world@rig.data.bones[S+'Foot'].head_local);toe=np.array(rig.matrix_world@rig.data.bones[S+'Toes'].head_local)
 forward=toe-ank;forward[2]=0;forward/=np.linalg.norm(forward);proj=(co-ank)@forward
 sels[sd]={'all':ids,'toe':[ids[i] for i in np.where(proj>=np.percentile(proj,70))[0]],'heel':[ids[i] for i in np.where(proj<=np.percentile(proj,25))[0]]}
def P(n):return np.array(rig.matrix_world@rig.pose.bones[n].head)
def angle(u,v):return math.degrees(math.acos(float(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))))
rows=[]
for f in range(76):
 sc.frame_set(f+1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh();vv=np.empty((len(me.vertices),3));me.vertices.foreach_get('co',vv.ravel());M=np.array(ev.matrix_world);vv=vv@M[:3,:3].T+M[:3,3];ev.to_mesh_clear()
 r={'f':f,'t':f/30,'hips':P('Hips').tolist(),'root':P('Root').tolist(),'bones':{b.name:P(b.name).tolist() for b in rig.pose.bones},'lengths':{b.name:float((rig.matrix_world.to_3x3()@(b.tail-b.head)).length) for b in rig.pose.bones}}
 for sd,S in [('L','Left'),('R','Right')]:
  hip,knee,ank,wr,el,sh=[P(S+n) for n in ['UpperLeg','LowerLeg','Foot','Hand','LowerArm','UpperArm']]
  r[sd+'knee']=180-angle(hip-knee,ank-knee);r[sd+'elbow']=angle(sh-el,wr-el)
  for reg,ids in sels[sd].items():
   v=vv[ids];j=np.argmin(v[:,2]);r[sd+reg+'_z']=float(v[j,2]);r[sd+reg+'_low']=v[j].tolist();r[sd+reg+'_mean']=v.mean(0).tolist()
  q=rig.pose.bones[S+'Hand'].matrix_basis.to_quaternion();r[sd+'twist']=math.degrees(2*math.atan2(q.y,q.w));r[sd+'hand']=wr.tolist()
 bed=bpy.data.objects['StringBed'].evaluated_get(dg); bm=bed.to_mesh(); bc=np.empty((len(bm.vertices),3));bm.vertices.foreach_get('co',bc.ravel()); centre=(bc.min(0)+bc.max(0))/2; r['strings']=list(bed.matrix_world@Vector(centre)); bed.to_mesh_clear()
 rows.append(r)
json.dump({'source':src,'fps':30,'frames':len(rows),'length':2.5,'bones':list(rows[0]['bones']),'rows':rows},open(out,'w'),indent=1)
print('TRACE',out,len(rows),'bone count',len(rows[0]['bones']))

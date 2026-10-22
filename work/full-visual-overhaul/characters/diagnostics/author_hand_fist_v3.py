import bpy,sys,pathlib,json,math,itertools
from mathutils import Matrix,Vector,Quaternion
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ContinuousHandsV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'))
rig.animation_data_clear();rig.data.pose_position='POSE'
for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=Vector();p.scale=Vector((1,1,1))
rest={b.name:b.matrix_local.copy() for b in rig.data.bones};records={}
for side in ('Left','Right'):
 hand=rest[side+'Hand'];H=hand.inverted();get=lambda d,j:rig.data.bones[side+d+j]
 palm=((H@get('Index','Proximal').head_local)-(H@get('Little','Proximal').head_local)).cross(H@get('Middle','Proximal').head_local).normalized();palm=Vector((0,0,1 if palm.z>0 else -1))
 b2h=H@rig.matrix_world.inverted()@body.matrix_world
 hg=body.vertex_groups[side+'Hand'].index
 handIds={g.index for g in body.vertex_groups if g.name==side+'Hand' or any(g.name.startswith(side+d) for d in ('Thumb','Index','Middle','Ring','Little'))}
 palmpoints=[b2h@v.co for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in handIds)>.8 and .04<(b2h@v.co).y<.09]
 for digit in ('Index','Middle','Ring','Little'):
  names=[side+digit+j for j in ('Proximal','Intermediate','Distal')];frames=[H@rest[n] for n in names]
  local=[frames[0],frames[0].inverted()@frames[1],frames[1].inverted()@frames[2]]
  points=[H@rig.data.bones[n].head_local for n in names]+[H@rig.data.bones[names[-1]].tail_local]
  axes=[frames[j].to_3x3().inverted()@((points[j+1]-points[j]).cross(palm).normalized()) for j in range(3)]
  axes=[a.normalized() for a in axes];tip=frames[2].inverted()@points[-1]
  # Target the lower palm, below the metacarpal fold, along the real flexion plane.
  aim=points[0]+Vector((0,-points[0].y*.28,0));hinge=(points[1]-points[0]).cross(palm).normalized()
  aim-=hinge*(aim-points[0]).dot(hinge)
  minplane=min(((p-aim)-(p-aim).dot(palm)*palm).length_squared for p in palmpoints)
  close=[p for p in palmpoints if ((p-aim)-(p-aim).dot(palm)*palm).length_squared<minplane+.000006]
  surface=max(close,key=lambda p:p.dot(palm));target=surface-hinge*(surface-points[0]).dot(hinge)+palm*(.006 if sex=='Male' else .005)
  def fk(angles):
   m=Matrix.Identity(4)
   for j,a in enumerate(angles):m=m@local[j]@Quaternion(axes[j],math.radians(a)).to_matrix().to_4x4()
   return m@tip
  def cost(a):
   p=fk(a);return (p-target).length_squared+1e-8*sum((x-y)**2 for x,y in zip(a,(80,100,50)))
  best=min(itertools.product(range(0,101,10),range(0,116,10),range(0,81,10)),key=cost);best=list(best)
  for repeat in range(3):
   for j in (2,1,0):
    lo=max(0,best[j]-10);hi=min((100,115,80)[j],best[j]+10)
    values=[]
    for v in range(lo,hi+1):a=best.copy();a[j]=v;values.append((cost(a),a))
    best=min(values,key=lambda item:item[0])[1]
  for j,n in enumerate(names):rig.pose.bones[n].rotation_quaternion=Quaternion(axes[j],math.radians(best[j]))
  records[side+digit]={'angles':best,'axes':[list(a) for a in axes],'targetHandLocal':list(target),'tipHandLocal':list(fk(best)),'tipResidual':(fk(best)-target).length}
 bpy.context.view_layer.update()
 # Authored opposition: basal thumb pivots across the curled index on the FRONT
 # palm side. Distal remains rounded; the source basal segment is now anatomical.
 names=[side+'Thumb'+j for j in ('Proximal','Intermediate','Distal')];frames=[H@rest[n] for n in names]
 pts=[H@rig.data.bones[n].head_local for n in names]+[H@rig.data.bones[names[-1]].tail_local]
 axes=[(frames[j].to_3x3().inverted()@(pts[j+1]-pts[j]).cross(palm).normalized()).normalized() for j in range(3)]
 bpy.context.view_layer.update();index=rig.pose.bones[side+'IndexIntermediate'];indexmid=rig.pose.bones[side+'IndexDistal']
 across=(hand.to_3x3()@(H@rig.data.bones[side+'MiddleProximal'].head_local-H@rig.data.bones[side+'IndexProximal'].head_local)).normalized()
 target=index.head.lerp(indexmid.head,.5)+across*(.025 if sex=='Male' else .018)+hand.to_3x3()@palm*.009
 base=rig.pose.bones[names[0]];distance=(target-base.head).length
 def thumbRadius(a,b):
  local=[frames[0],frames[0].inverted()@frames[1],frames[1].inverted()@frames[2]];tip=frames[2].inverted()@pts[3]
  transform=local[0]@local[1]@Quaternion(axes[1],math.radians(a)).to_matrix().to_4x4()@local[2]@Quaternion(axes[2],math.radians(b)).to_matrix().to_4x4()
  return (transform@tip-pts[0]).length
 ta,tb=min(itertools.product(range(20,101,5),range(15,86,5)),key=lambda a:(thumbRadius(*a)-distance)**2+1e-10*((a[0]-60)**2+(a[1]-35)**2))
 for j,a in enumerate((0,ta,tb)):rig.pose.bones[names[j]].rotation_quaternion=Quaternion(axes[j],math.radians(a))
 bpy.context.view_layer.update()
 distal=rig.pose.bones[names[-1]];base=rig.pose.bones[names[0]];fromdir=distal.tail-base.head;todir=target-base.head
 turn=Matrix.Translation(base.head)@fromdir.rotation_difference(todir).to_matrix().to_4x4()@Matrix.Translation(-base.head)
 base.matrix=turn@base.matrix;bpy.context.view_layer.update()
 records[side+'Thumb']={'targetHandLocal':list(H@target),'tipHandLocal':list(H@rig.pose.bones[names[-1]].tail),'tipResidual':(rig.pose.bones[names[-1]].tail-target).length}
rig.animation_data_create();rig.animation_data.action=bpy.data.actions.new('HandFist')
for p in rig.pose.bones:
 if any(p.name.startswith(side+digit) for side in ('Left','Right') for digit in ('Thumb','Index','Middle','Ring','Little')):
  for frame in (1,31):
   p.keyframe_insert(data_path='rotation_quaternion',frame=frame);p.keyframe_insert(data_path='location',frame=frame);p.keyframe_insert(data_path='scale',frame=frame)
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=31;bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
out=R/f'work/full-visual-overhaul/characters/exports/HandsV3/{sex}_Fist.fbx';out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'ARMATURE'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=False,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='STRIP')
# Save actual edit-friendly source pose, not merely guessed runtime angles.
source=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(source))
(R/f'proof/full-visual-overhaul/characters/fist-v3-source-{sex}.json').write_text(json.dumps({'sex':sex,'source':str(source),'records':records,'visualGate':'UNVERIFIED'},indent=2))
print('AUTHORED_FIST_V3',sex,records,flush=True)

"""Proof-only V4 swing extremes on the unchanged match skeleton. No Unity writes.

Run with export/Golf_<Sex>_Draft.blend open, -- Male|Female. Produces a separate
work-folder blend. Retargeting is for garment stress proofs, never gameplay.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion

W=Path(__file__).resolve().parents[1];R=W.parents[1];sex=sys.argv[-1]
rig=bpy.data.objects['Rig_'+sex]
body=bpy.data.objects['Body_F' if sex=='Female' else 'Body_M']
sc=bpy.context.scene
def geometry(o):
    return hashlib.sha256(repr(([(tuple(v.co),[(g.group,round(g.weight,8)) for g in v.groups]) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
before_body=geometry(body)
before_bones=[(b.name,tuple(map(tuple,b.matrix_local)),tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones]
ready=bpy.data.actions['ReadyIdle'];rig.animation_data_create();rig.animation_data.action=ready
if ready.slots:rig.animation_data.action_slot=ready.slots[0]
sc.frame_set(0);bpy.context.view_layer.update()
ready_basis={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
ready_world={pb.name:(rig.matrix_world@pb.matrix).to_quaternion().copy() for pb in rig.pose.bones}
existing=set(bpy.data.objects)
source=R/f'Unity/Assets/Resources/StandardCharacters/standard_{sex.lower()}_golf.fbx'
bpy.ops.import_scene.fbx(filepath=str(source),use_anim=True)
v4=next(o for o in bpy.data.objects if o not in existing and o.type=='ARMATURE')
action=v4.animation_data.action
fps=sc.render.fps/sc.render.fps_base
start=float(action.frame_range[0])
states=[('Top',1.77),('Impact',2.4),('Finish',3.0)]
mapping={n:n for n in ['Root','Hips','Spine','Chest','Neck','Head']}
for side,suffix in [('Left','.L'),('Right','.R')]:
    for part in ['Shoulder','UpperArm','LowerArm','Hand','UpperLeg','LowerLeg','Foot','Toes']:
        mapping[side+part]=part+suffix
mapping={d:s for d,s in mapping.items() if d in rig.pose.bones and s in v4.pose.bones}
samples={}
for name,t in states:
    frame=min(float(action.frame_range[1]),start+t*fps)
    sc.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
    samples[name]={d:{'rest':(v4.matrix_world@v4.data.bones[s].matrix_local).to_quaternion().copy(),
                     'pose':(v4.matrix_world@v4.pose.bones[s].matrix).to_quaternion().copy()} for d,s in mapping.items()}
    print('V4 sample',sex,name,t,frame,flush=True)

for o in list(bpy.data.objects):
    if o not in existing:bpy.data.objects.remove(o,do_unlink=True)
rig.animation_data.action=None
rig.data.pose_position='POSE'
rest={b.name:(rig.matrix_world@b.matrix_local).to_quaternion() for b in rig.data.bones}
reflect=Matrix.Diagonal((-1,1,1))
def mirror(q):return (reflect@q.to_matrix()@reflect).to_quaternion()
def counterpart(n):return 'Right'+n[4:] if n.startswith('Left') else 'Left'+n[5:] if n.startswith('Right') else n
def clear():
    rig.animation_data.action=None
    for pb in rig.pose.bones:
        pb.rotation_mode='QUATERNION';pb.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()

rows=[]
ordered=sorted(rig.pose.bones,key=lambda pb:len(pb.parent_recursive))
for hand in ['RH','LH']:
    for name,t in states:
        clear();desired={}
        for dst,info in samples[name].items():
            src=counterpart(dst) if hand=='LH' else dst
            source_info=samples[name].get(src,info)
            qs0,qs1=source_info['rest'],source_info['pose']
            delta=qs1@qs0.inverted()
            if any(x in dst for x in ['Arm','Hand','Leg','Foot','Toes','Shoulder']):
                # Absolute segment aim removes the female's A-pose/rest-arm bias.
                y0=qs0@Vector((0,1,0));y1=qs1@Vector((0,1,0))
                twist=delta@y0.rotation_difference(y1).inverted()
                if hand=='LH':
                    y1=reflect@y1;twist=mirror(twist)
                aim=(rest[dst]@Vector((0,1,0))).rotation_difference(y1)
                desired[dst]=(twist@aim@rest[dst]).normalized()
            else:
                if hand=='LH':delta=mirror(delta)
                desired[dst]=(delta@rest[dst]).normalized()
        for pb in ordered:
            if pb.name in desired:
                parent_q=(rig.matrix_world@pb.parent.matrix).to_quaternion() if pb.parent else rig.matrix_world.to_quaternion()
                rest_rel=(pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local).to_quaternion() if pb.parent else pb.bone.matrix_local.to_quaternion()
                pb.rotation_quaternion=(rest_rel.inverted()@parent_q.inverted()@desired[pb.name]).normalized()
            elif any(x in pb.name for x in ['Thumb','Index','Middle','Ring','Little']):
                src=counterpart(pb.name) if hand=='LH' else pb.name
                q=ready_basis.get(src,ready_basis[pb.name]).to_quaternion()
                if hand=='LH': q=rest[pb.name].inverted()@mirror(rest[src]@q@rest[src].inverted())@rest[pb.name]
                pb.rotation_quaternion=q.normalized()
            bpy.context.view_layer.update()
        label=f'GolfProof_{hand}_{name}'
        a=bpy.data.actions.new(label);a.use_fake_user=True
        rig.animation_data.action=a
        for pb in rig.pose.bones:
            for channel in ['location','rotation_quaternion','scale']:pb.keyframe_insert(channel,frame=0,group=pb.name)
        sc.frame_set(0);bpy.context.view_layer.update()
        # Keep proof feet planted without changing any rest matrix.
        feet=[v for v in body.data.vertices if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in ['LeftFoot','RightFoot','LeftToes','RightToes'])>.5]
        dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh()
        minz=min((ev.matrix_world@me.vertices[v.index].co).z for v in feet)
        ev.to_mesh_clear()
        root=rig.pose.bones.get('Root')
        if root:
            correction=(rig.matrix_world@root.bone.matrix_local).to_3x3().inverted()@Vector((0,0,-minz))
            root.location+=correction
            root.keyframe_insert('location',frame=0,group=root.name)
        rows.append(dict(action=label,state=name,handedness=hand,v4_seconds=t,v4_frame=min(start+t*fps,start+3*fps),foot_ground_correction_m=-minz,mapped_bones=len(mapping),finger_pose='ReadyIdle-derived; V4 has no finger bones',status='proof retarget; not gameplay motion or deformation PASS'))
        print('RETARGET',label,flush=True)

# The left-handed ReadyIdle is also explicit, rather than just moving a glove.
clear()
for pb in ordered:
    src=counterpart(pb.name)
    src_delta=ready_world[src]@rest[src].inverted()
    desired_q=mirror(src_delta)@rest[pb.name]
    parent_q=(rig.matrix_world@pb.parent.matrix).to_quaternion() if pb.parent else rig.matrix_world.to_quaternion()
    rest_rel=(pb.parent.bone.matrix_local.inverted()@pb.bone.matrix_local).to_quaternion() if pb.parent else pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion=(rest_rel.inverted()@parent_q.inverted()@desired_q).normalized()
    bpy.context.view_layer.update()
a=bpy.data.actions.new('GolfProof_LH_ReadyIdle');a.use_fake_user=True
rig.animation_data.action=a
for pb in rig.pose.bones:
    for channel in ['location','rotation_quaternion','scale']:pb.keyframe_insert(channel,frame=0,group=pb.name)
rows.append(dict(action=a.name,state='ReadyIdle',handedness='LH',v4_seconds=None,v4_frame=None,mapped_bones=len(rig.pose.bones),finger_pose='mirrored ReadyIdle',status='proof mirror; not gameplay motion or deformation PASS'))

assert before_body==geometry(body),'Body geometry/weights changed'
assert before_bones==[(b.name,tuple(map(tuple,b.matrix_local)),tuple(b.head_local),tuple(b.tail_local)) for b in rig.data.bones],'Skeleton changed'
rig.animation_data.action=ready
if ready.slots:rig.animation_data.action_slot=ready.slots[0]
sc.frame_set(0)
out=W/f'export/Golf_{sex}_SwingProof.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out))
(W/f'data/retarget_{sex}.json').write_text(json.dumps(dict(sex=sex,source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),fps=fps,source_action=action.name,mapping=mapping,body_unchanged=True,rest_matrices_unchanged=True,new_bones=0,poses=rows,output=str(out)),indent=2)+'\n')
print('Proof-only retarget saved',out,flush=True)

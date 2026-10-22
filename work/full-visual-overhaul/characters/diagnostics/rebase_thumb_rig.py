"""Editable, versioned thumb rest migration; old approved skinning remains exact.

Blender -b -t 2 --python this.py -- Male|Female [tennis|golf]
Only the six thumb bones receive new pose curves. Every original action remains
named and every other bone, mesh vertex, weight and material is retained.
"""
import bpy, pathlib, sys, json, math
from mathutils import Vector, Matrix
R=pathlib.Path(__file__).resolve().parents[4]
args=sys.argv[sys.argv.index('--')+1:]; sex=args[0]; sport=args[1] if len(args)>1 else 'tennis'
source=R/(f'Unity/Assets/Resources/Hero/golfer_{"f" if sex=="Female" else "m"}.fbx' if sport=='golf-runtime' else f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend' if sport=='tennis' else f'work/golf-motion-fit/export/Golf_{sex}_Master.blend')
if sport=='golf-runtime':bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(source))
else:bpy.ops.wm.open_mainfile(filepath=str(source))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
body=next(o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith('Body_') or o.name=='Body'))
names=[s+'Thumb'+j for s in ('Left','Right') for j in ('Proximal','Intermediate','Distal')]
old={n:rig.data.bones[n].matrix_local.copy() for n in names}
actions=list(bpy.data.actions)
cache={}; gold={}; metrics=[]; old_deltas={}
def curves(action):
    # Blender 5 stores fcurves in a layered action's assigned slot channelbag.
    if hasattr(action,'fcurves'):return action.fcurves
    return action.layers[0].strips[0].channelbag(action.slots[0]).fcurves
def evaluated_points():
    bpy.context.view_layer.update(); obj=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=obj.to_mesh(); data=[v.co.copy() for v in mesh.vertices]; obj.to_mesh_clear(); return data
def sample(action,frame):
    rig.animation_data.action=action; bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
for action in actions:
    # A dense source-frame rebake with exact fractional final time. Existing other
    # fcurves remain their authored interpolation, timing and contact landmarks.
    lo,hi=action.frame_range;frames=sorted(set([lo,hi]+[float(f) for f in range(math.ceil(lo),math.floor(hi)+1)]))
    sampled={}; probes={}; max_hand=0
    check=set(frames[round(i*(len(frames)-1)/10)] for i in range(11))
    for frame in frames:
        sample(action,frame); sampled[frame]={n:rig.pose.bones[n].matrix.copy() for n in names}
        if frame in check:probes[frame]=evaluated_points()
        for side in ('Left','Right'):
            p=side+'ThumbProximal';h=side+'Hand'
            thumb=rig.pose.bones[p].matrix@old[p].inverted();hand=rig.pose.bones[h].matrix@rig.data.bones[h].matrix_local.inverted()
            max_hand=max(max_hand,max(abs(thumb[r][c]-hand[r][c]) for r in range(4) for c in range(4)))
    cache[action.name]=sampled;gold[action.name]=probes;old_deltas[action.name]=max_hand
rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
changes=[]
for side in ('Left','Right'):
    if sex=='Female' and side=='Right':continue
    hand=rig.data.edit_bones[side+'Hand'];p=rig.data.edit_bones[side+'ThumbProximal'];mid=rig.data.edit_bones[side+'ThumbIntermediate']
    old_head=p.head.copy();h=hand.matrix.inverted()@p.head
    local=Vector((math.copysign(.010 if sex=='Female' else .030,h.x),.041 if sex=='Female' else .055,h.z*.5))
    old_z=p.z_axis.copy();p.use_connect=False;p.head=hand.matrix@local;p.tail=mid.head.copy();p.align_roll(old_z)
    changes.append({'bone':p.name,'oldHead':list(old_head),'newHead':list(p.head),'tail':list(p.tail),'headTravelMetres':(p.head-old_head).length})
bpy.ops.object.mode_set(mode='OBJECT')
new={n:rig.data.bones[n].matrix_local.copy() for n in names}
for action in actions:
    # Remove the thumb channels only; replay original world-space deformation into
    # the corrected rest. Absolute child rest is retained, local child translation
    # changes automatically. Missing translation curves would invalidate parity.
    for f in list(curves(action)):
        if any(f.data_path.startswith('pose.bones["'+n+'"]') for n in names):curves(action).remove(f)
    for frame,poses in cache[action.name].items():
        sample(action,frame)
        for n in names:
            p=rig.pose.bones[n];p.rotation_mode='QUATERNION';p.matrix=poses[n]@old[n].inverted()@new[n]
            # PoseBone.matrix assignment accounts for unchanged live parent pose.
            p.keyframe_insert('location',frame=frame,group=n);p.keyframe_insert('rotation_quaternion',frame=frame,group=n);p.keyframe_insert('scale',frame=frame,group=n)
            bpy.context.view_layer.update()
    for f in curves(action):
        if any(f.data_path.startswith('pose.bones["'+n+'"]') for n in names):
            for k in f.keyframe_points:k.interpolation='LINEAR'
    maximum=mean=0;count=0
    for frame,points in gold[action.name].items():
        sample(action,frame);current=evaluated_points();assert len(points)==len(current)
        for a,b in zip(points,current):distance=(a-b).length;maximum=max(maximum,distance);mean+=distance;count+=1
    metrics.append({'action':action.name,'maxSkinPositionErrorMetres':maximum,'meanSkinPositionErrorMetres':mean/count,'samples':len(gold[action.name]),'verticesPerSample':len(points),'oldThumbVsHandMatrixMax':old_deltas[action.name]})
    print('THUMB_RIG_PARITY',sex,sport,action.name,maximum,flush=True)
rig['rig_contract']='match-hero-thumb-anatomy-v2';rig['source_rest_migration']='Only thumb basal pivot/rest; all six old thumb tracks rebased; hierarchy exact'
out=R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_{sport.title()}_ThumbRigV2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={'version':'match-hero-thumb-anatomy-v2','sex':sex,'sport':sport,'source':str(source),'sourceOutput':str(out),'boneCount':len(rig.data.bones),'changes':changes,'actions':metrics,'maxSkinPositionErrorMetres':max(m['maxSkinPositionErrorMetres'] for m in metrics),'gate':'PASS exact old approved source deformation' if all(m['maxSkinPositionErrorMetres']<.00005 for m in metrics) else 'FAIL source deformation parity; do not install'}
(R/f'proof/full-visual-overhaul/characters/thumb-rig-v2-{sport}-{sex}.json').write_text(json.dumps(report,indent=2))
assert report['maxSkinPositionErrorMetres']<.00005,report
print('THUMB_RIG_SOURCE_COMPLETE',out,flush=True)

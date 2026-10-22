import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).parent));import fbx_curves as F
W=Path(__file__).resolve().parents[1];p=W/'rollback/fbx/Male_Emote_Scuba.fbx'
r,v,models,channels=F.read(p)
bpy.ops.import_scene.fbx(filepath=str(p),axis_forward='-Z',axis_up='Y');arm=next(x for x in bpy.data.objects if x.type=='ARMATURE');bpy.context.scene.frame_set(1)
for nm in ['Hips','Spine','Chest','RightHand','Root']:
 pb=arm.pose.bones[nm];local=pb.parent.matrix.inverted()@pb.matrix if pb.parent else pb.matrix
 angles=[x*180/math.pi for x in local.to_3x3().to_euler('XYZ')];original=[float(F.data(channels[nm,'Lcl Rotation',a],b'KeyValueFloat')[0]) for a in 'XYZ']
 print(nm,angles,original,'rest',tuple(pb.scale))

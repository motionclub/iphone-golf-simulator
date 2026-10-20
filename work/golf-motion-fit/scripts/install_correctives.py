"""Bake garment-only shape coefficients beside the bone/equipment actions.
Both runtime renderers consume these same optional tracks from the manifest.
"""
import bpy,sys,json,math
from pathlib import Path
import numpy as np
W=Path(__file__).resolve().parents[1];R=W.parents[1];sex=sys.argv[-1];tag=sex.lower()
sys.path.insert(0,str(R/'work/match-anim-set/scripts'));import kin
k=kin.Rig(str(R/f'work/match-anim-set/data/rig_{tag}.json'))
baseNames=['GolfHipTwistLeft','GolfHipTwistRight','GolfThighLiftLeft','GolfThighLiftRight']
anchorsPath=W/f'data/shoulder_anchors_{sex}.json'
anchors=json.loads(anchorsPath.read_text()) if anchorsPath.exists() else []
names=baseNames+[a['name'] for a in anchors if a['name']]
data=dict(np.load(W/f'data/animations_{sex}.npz'));manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text())
pieces=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Golf_') and o.data.shape_keys and all(n in o.data.shape_keys.key_blocks for n in baseNames)]
for o in pieces:
 if o.data.shape_keys.animation_data:
  for tr in list(o.data.shape_keys.animation_data.nla_tracks):o.data.shape_keys.animation_data.nla_tracks.remove(tr)
folder=W/'export/correctives';folder.mkdir(exist_ok=True)
def matrices(q):
 q=q/np.linalg.norm(q,axis=-1,keepdims=True);w,x,y,z=np.moveaxis(q,-1,0)
 return np.stack([1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w),2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w),2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)],axis=-1).reshape(q.shape[:-1]+(3,3))
for clip in manifest['clips']:
 ident=clip['id'];B=matrices(data[ident+'_quats']);Q=np.empty_like(B);P=np.empty(B.shape[:2]+(3,));loc=data[ident+'_hips']
 for i in range(k.n):
  p=k.parent[i];Q[:,i]=k.rel_rot[i]@B[:,i] if p<0 else Q[:,p]@k.rel_rot[i]@B[:,i]
  off=np.broadcast_to(k.rel_off[i],(len(B),3)).copy()
  if k.names[i]=='Hips':off+=np.einsum('ij,nj->ni',k.rel_rot[i],loc)
  P[:,i]=off if p<0 else P[:,p]+np.einsum('nij,nj->ni',Q[:,p],off)
 hip=Q[:,k.idx['Hips']]@k.Rrest[k.idx['Hips']].T
 yaw=-np.arctan2(hip[:,1,0],hip[:,0,0]);tracks=np.zeros((len(B),len(names)),np.float32)
 tracks[:,0]=np.clip(yaw/math.radians(72),0,1);tracks[:,1]=np.clip(-yaw/math.radians(72),0,1)
 for side,column in [('Left',2),('Right',3)]:
  direction=np.einsum('nji,nj->ni',hip,Q[:,k.idx[side+'UpperLeg'],:,1]);angle=np.arctan2(-direction[:,1],-direction[:,2]);tracks[:,column]=np.clip(angle/math.radians(75),0,1)
 if anchors:
  features=[]
  for side in ['Left','Right']:
   for a,b in [('UpperArm','LowerArm'),('LowerArm','Hand')]:
    vec=P[:,k.idx[side+b]]-P[:,k.idx[side+a]];vec/=np.linalg.norm(vec,axis=1)[:,None];features.append(np.einsum('nji,nj->ni',Q[:,k.idx['UpperChest']],vec))
  features=np.concatenate(features,axis=1);distance=((features[:,None]-np.array([a['features'] for a in anchors])[None])**2).sum(2)
  weights=1/np.maximum(distance,1e-12)**2;weights/=weights.sum(1)[:,None];tracks[:,4:]=weights[:,1:]
 data[ident+'_correctives']=tracks
 clip['correctiveTracks']=names;clip['correctiveFile']='correctives/'+ident+'.json'
 (folder/(ident+'.json')).write_text(json.dumps(dict(version=1,fps=120,frames=len(B),names=names,values=tracks.tolist()),separators=(',',':'))+'\n')
 for o in pieces:
  keys=o.data.shape_keys;keys.animation_data_create();action=bpy.data.actions.new(ident+'_'+o.name+'_Correctives');action.use_fake_user=True;keys.animation_data.action=action
  for c,name in enumerate(names):
   if name not in keys.key_blocks:continue
   curve=action.fcurve_ensure_for_datablock(keys,f'key_blocks["{name}"].value',index=0);curve.keyframe_points.add(len(B));co=np.empty(len(B)*2);co[0::2]=np.arange(len(B));co[1::2]=tracks[:,c];curve.keyframe_points.foreach_set('co',co)
   for point in curve.keyframe_points:point.interpolation='LINEAR'
   curve.update()
  tr=keys.animation_data.nla_tracks.new();tr.name=ident;tr.mute=True;tr.strips.new(ident,0,action)
  action.asset_mark();action.asset_data.description='Golf garment coefficients, '+clip['motion']+', '+clip['handedness']
 action=bpy.data.actions[ident];action.asset_mark();action.asset_data.description=f'{sex} {clip["handedness"]} {clip["motion"]}; explicit hands; impact {clip["impact"]}; in place.'
 print('CORRECTIVES',ident,flush=True)
ident=f'Drive_{sex}_RH'
for o in pieces:o.data.shape_keys.animation_data.action=bpy.data.actions[ident+'_'+o.name+'_Correctives']
np.savez_compressed(W/f'data/animations_{sex}.npz',**data)
(W/f'export/golf_manifest_{sex}.json').write_text(json.dumps(manifest,indent=2)+'\n')
bpy.context.scene.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(W/f'export/Golf_{sex}_Dressed.blend'),compress=True)
print('CORRECTIVES_COMPLETE',sex,flush=True)

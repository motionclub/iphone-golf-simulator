"""Reuse the entry clearance evaluator for remaining transition-frame intersections."""
from pathlib import Path
source=Path(__file__).with_name('clear_entry_r3.py').read_text()
exec(compile(source[:source.index("i=hero.rig.idx['LeftHand']")],str(Path(__file__).with_name('clear_entry_r3.py')),'exec'))
frames=[7,8] if tag=='male' else [7]
result=[];i=hero.rig.idx['LeftHand']
for f in frames:
 for j,n in enumerate(hero.rig.names):rig.pose.bones[n].rotation_quaternion=q[f,j]
 rig.pose.bones['Hips'].location=data['hips'][f]
 original=Quaternion(q[f,i]);best=(10**9,None,None);trials=[]
 for angle in [0,-5,5,-10,10,-15,15,-20,20,-30,30,-45,45,-60,60]:
  for axis in [(1,0,0),(0,0,1),(1,0,1),(-1,0,1)]:
   turn=Quaternion(Vector(axis).normalized(),math.radians(angle));rig.pose.bones['LeftHand'].rotation_quaternion=original@turn
   n,who=cost();trials.append(dict(angle=angle,axis=axis,inside=n,who=who))
   if (n,abs(angle)) < (best[0],abs(best[1] or 1e9)):best=(n,angle,axis)
   if n==0:break
  if best[0]==0:break
 n,angle,axis=best;turn=np.array(Quaternion(Vector(axis).normalized(),math.radians(angle)))
 q[f,i]=kin.qmul(q[f,i],turn)
 result.append(dict(frame=f,best=dict(inside=n,angle=angle,axis=axis),trials=trials));print('FRAME_CLEARANCE',tag,f,best)
data['quats']=q;np.savez_compressed(W+'/data/gen_serve_'+tag+'.npz',**data)
open(W+'/r3/transition_clearance_'+tag+'.json','w').write(json.dumps(result,indent=2))

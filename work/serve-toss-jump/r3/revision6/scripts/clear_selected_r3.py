"""Clear remaining measured racket intersections using wrist rotations only."""
from pathlib import Path
source=Path(__file__).with_name('clear_entry_r3.py').read_text()
exec(compile(source[:source.index("i=hero.rig.idx['LeftHand']")],str(Path(__file__).with_name('clear_entry_r3.py')),'exec'))
tasks=[(7,'LeftHand'),(8,'LeftHand'),(43,'RightHand'),(44,'RightHand'),(75,'RightHand')] if tag=='male' else [(7,'LeftHand'),(17,'RightHand'),(42,'RightHand'),(43,'RightHand'),(58,'RightHand'),(75,'RightHand')]
result=[]
for f,name in tasks:
 i=hero.rig.idx[name]
 for j,n in enumerate(hero.rig.names):rig.pose.bones[n].rotation_quaternion=q[f,j]
 rig.pose.bones['Hips'].location=data['hips'][f]
 original=Quaternion(q[f,i]);best=(10**9,None,None);trials=[]
 for angle in [0,-3,3,-5,5,-10,10,-15,15,-20,20,-30,30,-45,45,-60,60]:
  for axis in [(1,0,0),(0,0,1),(1,0,1),(-1,0,1),(0,1,0)]:
   trial=original@Quaternion(Vector(axis).normalized(),math.radians(angle));rig.pose.bones[name].rotation_quaternion=trial
   inside,who=cost();trials.append(dict(angle=angle,axis=axis,inside=inside,who=who))
   if inside<best[0]:best=(inside,trial.copy(),dict(angle=angle,axis=axis))
   if inside==0:break
  if best[0]==0:break
 q[f,i]=np.array(best[1]);result.append(dict(frame=f,bone=name,best=dict(inside=best[0],**best[2]),trials=trials))
 print('CLEAR',tag,f,name,result[-1]['best'])
data['quats']=q;np.savez_compressed(W+'/data/gen_serve_'+tag+'.npz',**data)
Path(W+'/r3/selected_clearance_'+tag+'.json').write_text(json.dumps(result,indent=2))

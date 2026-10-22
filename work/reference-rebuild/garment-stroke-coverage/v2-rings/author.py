import bpy,pathlib,json,numpy as np,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();BASE=R/'work/reference-rebuild/garment-stroke-coverage';W=BASE/'v2-rings';D=R/'proof/reference-rebuild/character-cloth14-control/poses';REPORT={}
# Reuse v2's permitted cuff region and exact profile/shape contracts; replace
# the local operation by a coherent fit of rings about the live upper arm.
text=(BASE/'v2/author_cuff_expansion.py').read_text();prefix=text[:text.rindex("for sex in ('Male','Female'):")];prefix=prefix.replace("W=BASE/'v2'","W=BASE/'v2-rings'");exec(prefix)
old="for i in np.where(seeds)[0]:\n  h,n,gap,_,_=hit(gBefore[i]);delta[i]=n*max(0,.006-gap)"
new="""topIds=arr(top,'indices',4).astype(int);topWeights=arr(top,'weights',4);bodyIds=arr(body,'indices',4).astype(int);bodyWeights=arr(body,'weights',4)
 bm=np.array(body['rendererToRoot']).reshape(4,4);bodyRest=xf(bm,arr(body,'vertices',3));liveBones=tm[None,:,:]@np.array(top['skinMatrices']).reshape(-1,4,4)@np.linalg.inv(np.array(top['bindposes']).reshape(-1,4,4));restBones=tm[None,:,:]@np.linalg.inv(np.array(top['bindposes']).reshape(-1,4,4))
 radialMoved=np.zeros(count,bool)
 for side in ('Left','Right'):
  armIndex=top['bones'].index(side+'UpperArm');lower=top['bones'].index(side+'LowerArm');a=liveBones[armIndex,:3,3];axis=liveBones[lower,:3,3]-a;length=np.linalg.norm(axis);axis/=length;a0=restBones[armIndex,:3,3];restAxis=restBones[lower,:3,3]-a0;restLength=np.linalg.norm(restAxis);restAxis/=restLength
  t=((gRest-a0)@restAxis)/restLength;topMass=(topWeights*np.isin(topIds,[top['bones'].index(side+'UpperArm'),top['bones'].index(side+'Shoulder')])).sum(1);gm=np.zeros(count);np.add.at(gm,parent,topMass);gm/=sizes
  bmass=(bodyWeights*np.isin(bodyIds,[body['bones'].index(side+'UpperArm'),body['bones'].index(side+'Shoulder')])).sum(1);bt0=((bodyRest-a0)@restAxis)/restLength;axial=(bp-a)@axis;bodyRadial=bp-a-axial[:,None]*axis;radius=np.linalg.norm(bodyRadial,axis=1);valid=(bmass>.20)&(bt0>-.08)&(bt0<1.08)&(radius<.13)
  for i in np.where(allowed&(gm>.12)&(t>.035)&(t<1.03))[0]:
   q=gBefore[i]-a;along=q@axis;rvec=q-axis*along;r=np.linalg.norm(rvec)
   if r<1e-5:continue
   section=valid&(np.abs(axial-along)<.022)
   if not section.any():continue
   # Use one section radius in every angular direction; this expands the
   # inherited cuff as a coherent ring rather than independently nudging
   # neighboring cloth vertices into differently directed triangle normals.
   desired=float(np.quantile(radius[section],.98))+.006;amount=max(0,desired-r)
   fade=S(.035,.16,t[i])*(1-S(.82,1.03,t[i]))*S(.12,.55,gm[i])
   if seeds[i]:fade=max(fade,.9)
   delta[i]+=rvec/r*min(.045,amount)*fade;radialMoved[i]=True
 # Torso-owned gusset below the arm joins the expanded ring with its own
 # existing body-facing field; all cuff and arm-owned points stay radial.
 for i in np.where(seeds&~radialMoved)[0]:
  h,n,gap,_,_=hit(gBefore[i]);delta[i]=n*max(0,.006-gap)"""
assert old in defs;defs=defs.replace(old,new)
old2="for _ in range(5):\n  for i in np.where(seeds)[0]:\n   h,n,gap,_,_=hit(target[i])\n   if gap<.006:target[i]+=n*(.006-gap)"
new2="for _ in range(5):\n  for i in np.where(seeds&~radialMoved)[0]:\n   h,n,gap,_,_=hit(target[i])\n   if gap<.006:target[i]+=n*(.006-gap)"
assert old2 in defs;defs=defs.replace(old2,new2);exec(defs)
for sex in ('Male','Female'):
 profile=json.loads((BASE/f'SleeveFit_{sex}.json').read_text());staged=json.loads(json.dumps(profile))
 for i in range(3):
  label=f'{sex.lower()}_Forehand_{i}';author(sex,label,profile);replacement=json.loads((W/(label+'-anchor.json')).read_text());index=next(k for k,a in enumerate(staged['anchors']) if a['shape']==label);staged['anchors'][index]=replacement
 assert all(a==b for a,b in zip(profile['anchors'],staged['anchors']) if '_Forehand_' not in a['shape']);assert all(profile[k]==staged[k] for k in profile if k!='anchors');(W/f'SleeveFit_{sex}.json').write_text(json.dumps(staged,separators=(',',':')))
(W/'stroke-source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')

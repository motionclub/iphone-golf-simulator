import bpy,pathlib,json,numpy as np,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();BASE=R/'work/reference-rebuild/garment-stroke-coverage';W=BASE/'v2-panels';D=R/'proof/reference-rebuild/character-cloth14-control/poses';REPORT={}
text=(BASE/'v2/author_cuff_expansion.py').read_text();prefix=text[:text.rindex("for sex in ('Male','Female'):")].replace("W=BASE/'v2'","W=BASE/'v2-panels'");exec(prefix)
old="for i in np.where(seeds)[0]:\n  h,n,gap,_,_=hit(gBefore[i]);delta[i]=n*max(0,.006-gap)"
new="""# One outward translation per connected exposed-side patch. Direction
 # classes stop opposed inner/outer cuff faces averaging to zero. This
 # moves existing neighboring rings smoothly instead of changing their
 # circumference or reproducing each noisy Body triangle normal.
 normalAt=np.array([hit(p)[1] for p in gBefore]);dominant=np.argmax(np.abs(normalAt),axis=1);code=dominant*2+(normalAt[np.arange(count),dominant]>0)
 pending=set(np.where(seeds)[0]);clusters=[]
 while pending:
  first=pending.pop();cluster={first};stack=[first]
  while stack:
   i=stack.pop()
   for j in adj[i]:
    if j in pending and code[j]==code[first]:pending.remove(j);cluster.add(j);stack.append(j)
  clusters.append(cluster)
 accumulated=np.zeros_like(delta);total=np.zeros(count)
 for cluster in clusters:
  ids=np.array(sorted(cluster));outward=normalAt[ids].mean(0);outward/=max(np.linalg.norm(outward),1e-10);amount=float(np.max((.006-signed[ids])/np.maximum(normalAt[ids]@outward,.55)));translation=outward*min(.050,max(0,amount))
  distances=np.full(count,np.inf);q=[]
  for i in ids:distances[i]=0;heapq.heappush(q,(0.,int(i)))
  while q:
   d,i=heapq.heappop(q)
   if d!=distances[i] or d>.075:continue
   for j in adj[i]:
    nd=d+np.linalg.norm(gRest[j]-gRest[i])
    if allowed[j] and nd<distances[j]:distances[j]=nd;heapq.heappush(q,(nd,j))
  influence=1-S(.012,.075,distances);accumulated+=translation[None,:]*influence[:,None];total+=influence
 delta=accumulated/np.maximum(total[:,None],1);support=np.maximum(support,np.clip(total,0,1))*allowed"""
assert old in defs;defs=defs.replace(old,new)
defs=defs.replace("for _ in range(20):","for _ in range(8):")
old2="for _ in range(5):\n  for i in np.where(seeds)[0]:\n   h,n,gap,_,_=hit(target[i])\n   if gap<.006:target[i]+=n*(.006-gap)"
assert old2 in defs;defs=defs.replace(old2,"# Keep the coherent patch translation; no independent reprojection.")
exec(defs)
for sex in ('Male','Female'):
 profile=json.loads((BASE/f'SleeveFit_{sex}.json').read_text());staged=json.loads(json.dumps(profile))
 for i in range(3):
  label=f'{sex.lower()}_Forehand_{i}';author(sex,label,profile);replacement=json.loads((W/(label+'-anchor.json')).read_text());index=next(k for k,a in enumerate(staged['anchors']) if a['shape']==label);staged['anchors'][index]=replacement
 assert all(a==b for a,b in zip(profile['anchors'],staged['anchors']) if '_Forehand_' not in a['shape']);assert all(profile[k]==staged[k] for k in profile if k!='anchors');(W/f'SleeveFit_{sex}.json').write_text(json.dumps(staged,separators=(',',':')))
(W/'stroke-source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')

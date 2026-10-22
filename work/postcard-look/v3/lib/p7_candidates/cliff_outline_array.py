"""Same-point numerical silhouette trial, not a production geometry PASS."""
import os,json,hashlib,sys
import numpy as np
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
OUT=os.path.dirname(__file__)
variant=sys.argv[1] if len(sys.argv)>1 else 'arc'
SRC=ROOT+'/work/postcard-look/v3/hole09/stage/phase3_build.json'
original=json.load(open(SRC))['cliff_outline']
def longest(xy):
 n=len(xy);seg=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1);best=0.
 for start in range(n):
  chain=[];walk=0.
  for count in range(1,min(n,100)):
   end=(start+count)%n;chain.append(xy[end]);walk+=seg[(end-1)%n]
   if count>1:
    delta=xy[end]-xy[start];d=float(np.linalg.norm(delta))
    if d<1e-8:break
    mid=np.asarray(chain)-xy[start]
    if (np.abs(mid[:,0]*delta[1]-mid[:,1]*delta[0])/d).max()>.10:break
   best=max(best,walk)
 return float(best)
rows=[];arrays=[]
for entry in original:
 xy=np.array(entry['xy']);s=np.array(entry['sample_arc']);n=len(xy)
 # Estimate only the local outward direction for the array feasibility trial.
 # Authorized source implementation must use its exact original Pc/N instead.
 tangent=np.roll(xy,-2,axis=0)-np.roll(xy,2,axis=0)
 tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-9)
 area=(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)).sum()
 normal=np.stack([tangent[:,1],-tangent[:,0]],1)*(1 if area>0 else -1)
 depth=.55*(1-np.abs(2*((s/2.6+.137)%1)-1)) if variant=='arc' else .20+.65*(np.arange(n)%2)+np.random.default_rng(7211).uniform(-.10,.10,n)
 carved=xy-normal*depth[:,None]
 before=longest(xy);after=longest(carved)
 rows.append(dict(loop=entry['loop'],points_before=n,points_after=len(carved),before_m=before,after_m=after,numeric_ok=bool(after<=4),variant=variant,depth_max_m=float(depth.max()),topology_budget_change=0))
 arrays.append(dict(loop=entry['loop'],xy=carved.tolist(),sample_arc=s.tolist()))
result=dict(scope='Same2800-point array feasibility only. Not a final clamped source mesh, not a library or Unity PASS.',source=SRC,source_sha256=hashlib.sha256(open(SRC,'rb').read()).hexdigest(),rows=rows,numeric_ok=all(r['numeric_ok'] for r in rows),unchanged_predicate=dict(chord_deviation_m=.10,maximum_run_m=4.0),candidate=arrays)
with open(OUT+'/cliff_array_'+variant+'_result.json','w') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='candidate'},indent=2))

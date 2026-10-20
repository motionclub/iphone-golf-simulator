import sys,json,numpy as np
from collections import Counter,defaultdict
sys.path.insert(0,'work/reference-rebuild/golf-garment-panel1');from common import *
W=R/'work/reference-rebuild/golf-garment-mask1';report={}
for sex in ('Male','Female'):
 body,top,raw=source(sex);v=arr(top,'vertices',3);rt=np.array(top['rendererToRoot']).reshape(4,4);rv=xf(rt,v);tri=arr(top,'triangles',3).astype(int);lookup={};w=np.array([lookup.setdefault(tuple(np.round(p*1e5).astype(int)),len(lookup)) for p in v]);p=np.zeros((len(lookup),3));p[w]=rv;tt=w[tri];parent=np.arange(len(p))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(a,b):
  a=find(a);b=find(b)
  if a!=b:parent[b]=a
 for t in tt:
  join(int(t[0]),int(t[1]));join(int(t[0]),int(t[2]))
 comp=np.array([find(i) for i in range(len(p))]);fc=Counter(int(comp[t[0]]) for t in tt);ec=Counter(tuple(sorted((int(t[j]),int(t[(j+1)%3])))) for t in tt for j in range(3));boundary=[e for e,c in ec.items() if c==1];adj=defaultdict(set)
 for a,b in boundary:adj[a].add(b);adj[b].add(a)
 seen=set();loops=[]
 for start in adj:
  if start in seen:continue
  nodes=set([start]);stack=[start]
  while stack:
   k=stack.pop();seen.add(k)
   for j in adj[k]:
    if j not in nodes:nodes.add(j);stack.append(j)
  closed=all(len(adj[j])==2 for j in nodes);ordered=[]
  if closed:
   k=start;prior=-1
   while not ordered or k!=start:
    ordered.append(k);nexts=adj[k]-{prior};n=min(nexts);prior,k=k,n
    if len(ordered)>len(nodes):raise ValueError('loop overrun')
  else:ordered=sorted(nodes)
  q=p[ordered];c=q.mean(0);span=q.max(0)-q.min(0);axilla=((abs(q[:,0])>.08)&(abs(q[:,0])<(.30 if sex=='Male' else .225))&(q[:,1]>1.095)&(q[:,1]<(1.385 if sex=='Male' else 1.345))).any()
  if not axilla:continue
  side='Left' if c[0]<0 else 'Right';cb=rt[None]@np.linalg.inv(arr(top,'bindposes',16).reshape(-1,4,4));a=cb[top['bones'].index(side+'UpperArm'),:3,3];b=cb[top['bones'].index(side+'LowerArm'),:3,3];along=float((c-a)@(b-a)/sum((b-a)**2))
  if along>.66 and fc[int(comp[start])]<100:continue
  area=.5*np.cross(q,np.roll(q,-1,axis=0)).sum(0) if closed else np.zeros(3)
  loops.append({'closedDegree2':closed,'vertexCount':len(nodes),'connectedGarmentFaceCount':fc[int(comp[start])],'centerRoot':c.tolist(),'spanMm':(span*1000).tolist(),'upperArmFraction':along,'planarAreaMm2':float(np.linalg.norm(area)*1e6),'orderedSourceIndices':[int(np.where(w==i)[0][0]) for i in ordered],'rootPoints':q.tolist(),'classification':'main garment hole candidate' if closed and fc[int(comp[start])]>100 and len(nodes)>3 else 'separate/open decorative or lining piece; do not cap blindly'})
 loops.sort(key=lambda x:-x['planarAreaMm2']);report[sex]={'axillaBoundaryComponents':loops,'componentFaceCounts':sorted(fc.values(),reverse=True)};print(sex,[(q['vertexCount'],q['connectedGarmentFaceCount'],q['closedDegree2'],q['spanMm'],q['classification']) for q in loops],flush=True)
(W/'open-loop-audit.json').write_text(json.dumps(report,indent=2)+'\n')

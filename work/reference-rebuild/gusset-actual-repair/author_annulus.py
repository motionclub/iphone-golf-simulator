from pathlib import Path
from collections import defaultdict,Counter
import json,os
import numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair'
variant=os.environ.get('BAND_DETAIL','Full');p=json.loads((R/f'work/reference-rebuild/garment-gusset1/runtime-reviewed/UnderarmGusset_Female_{variant}.json').read_text())
v=np.array(p['sourceVertices']).reshape(-1,3);tri=np.array(p['sourceTriangles']).reshape(-1,3);N=len(v)
bi=np.array(p['boneIndices']).reshape(-1,4)[:N];bw=np.array(p['weights']).reshape(-1,4)[:N];bones=p['bones']
_,physical=np.unique(np.round(v,7),axis=0,return_inverse=True)
faceadj=defaultdict(list)
for f,t in enumerate(tri):
 for j in physical[t]:faceadj[int(j)].append(f)
seen=set();comps=[]
for f in range(len(tri)):
 if f in seen:continue
 stack=[f];seen.add(f);c=[]
 while stack:
  z=stack.pop();c.append(z)
  for j in physical[tri[z]]:
   for k in faceadj[int(j)]:
    if k not in seen:seen.add(k);stack.append(k)
 comps.append(c)
main=set(max(comps,key=len))
M=np.stack([(bw*(bi==bones.index(s+'UpperArm'))).sum(1) for s in ['Left','Right']])
low=.15;high=.90
verts=list(v);maps=[{i:1.} for i in range(N)];cache={};newtris=[];parents=[]
def blend(a,b,t):
 d=defaultdict(float)
 for j,w in maps[a].items():d[j]+=(1-t)*w
 for j,w in maps[b].items():d[j]+=t*w
 key=tuple((j,round(w,12)) for j,w in sorted(d.items()) if abs(w)>1e-10)
 if key not in cache:cache[key]=len(verts);maps.append(dict(key));verts.append(sum(v[j]*w for j,w in key))
 return cache[key]
def scalar(i,side):return sum(M[side,j]*w for j,w in maps[i].items())
def clip(poly,side,threshold,above):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  sa=scalar(a,side);sb=scalar(b,side);ina=(sa>=threshold) if above else (sa<=threshold);inb=(sb>=threshold) if above else (sb<=threshold)
  if ina:out.append(a)
  if ina!=inb:out.append(blend(a,b,(threshold-sa)/(sb-sa)))
 return out
for f,t in enumerate(tri):
 if f in main:
  side=int(v[t,0].mean()>0);polys=([list(t)] if M[side,t].max()<=low else [])+[clip(list(t),side,high,True)]
 else:polys=[list(t)]
 for poly in polys:
  for j in range(1,len(poly)-1):newtris.append([poly[0],poly[j],poly[j+1]]);parents.append(f)
verts=np.array(verts);newtris=np.array(newtris);parents=np.array(parents)
# Clip noise creates tiny retained islands inside the replacement. Keep the three
# connected torso/sleeve pieces; retain every separate original trim component.
_,alias=np.unique(np.round(verts,8),axis=0,return_inverse=True)
def components(ts):
 adj=defaultdict(list)
 for i,t in enumerate(ts):
  for x in alias[t]:adj[x].append(i)
 seen=set();out=[]
 for i in range(len(ts)):
  if i in seen:continue
  stack=[i];seen.add(i);group=[]
  while stack:
   f=stack.pop();group.append(f)
   for x in alias[ts[f]]:
    for j in adj[x]:
     if j not in seen:seen.add(j);stack.append(j)
  out.append(group)
 return sorted(out,key=len,reverse=True)
mi=np.where(np.isin(parents,list(main)))[0];cs=components(newtris[mi]);keep=np.ones(len(newtris),bool)
for c in cs[3:]:keep[mi[c]]=False
print('retained main components',list(map(len,cs)))
newtris=newtris[keep];parents=parents[keep];mi=np.where(np.isin(parents,list(main)))[0]
edge=defaultdict(list)
for f in mi:
 t=newtris[f]
 for a,b in zip(t,np.roll(t,-1)):edge[tuple(sorted((int(alias[a]),int(alias[b]))))].append((int(a),int(b),int(f)))
bound=[es[0] for es in edge.values() if len(es)==1]
nexts={int(alias[a]):(a,b,f) for a,b,f in bound};loops=[]
while nexts:
 first=next(iter(nexts));cur=first;loop=[]
 while True:
  a,b,f=nexts.pop(cur);loop.append(a);cur=int(alias[b])
  if cur==first:break
 loops.append(np.array(loop))
print('boundary loops',[(len(l),verts[l].mean(0).tolist(),np.mean([scalar(i,int(verts[l,0].mean()>0)) for i in l])) for l in loops])
# Four annuli: torso boundary to corresponding outer/inner sleeve boundary.
rings=[];added=[];addedparents=[];records=[]
def arclength(loop):
 d=np.linalg.norm(verts[np.roll(loop,-1)]-verts[loop],axis=1);return np.r_[0,np.cumsum(d)]/sum(d)
def sample(loop,s,u):
 j=np.minimum(np.searchsorted(s,u,side='right')-1,len(loop)-1);w=(u-s[j])/(s[j+1]-s[j]);return loop[j],loop[(j+1)%len(loop)],w
def points(loop,s,u):
 a,b,w=sample(loop,s,u);return verts[a]*(1-w[:,None])+verts[b]*w[:,None]
def ziprings(a,sa,b,sb):
 i=j=0;out=[]
 while i<len(a) or j<len(b):
  ni=sa[i+1] if i<len(a) else 2;nj=sb[j+1] if j<len(b) else 2
  if ni<nj:out.append([a[i%len(a)],a[(i+1)%len(a)],b[j%len(b)]]);i+=1
  else:out.append([a[i%len(a)],b[(j+1)%len(b)],b[j%len(b)]]);j+=1
 return out
for side in [0,1]:
 ls=[l for l in loops if int(verts[l,0].mean()>0)==side];lo=[l for l in ls if abs(np.mean([scalar(i,side) for i in l])-low)<1e-4];hi=[l for l in ls if abs(np.mean([scalar(i,side) for i in l])-high)<1e-4]
 assert len(lo)==len(hi)==2
 # Outer surface has wider y/z perimeter; pair by circumference rank.
 def perimeter(l):return np.linalg.norm(verts[np.roll(l,-1)]-verts[l],axis=1).sum()
 lo.sort(key=perimeter);hi.sort(key=perimeter)
 for l,h in zip(lo,hi):
  l=l[::-1];l=np.roll(l,-int(np.argmax(verts[l,2])));sl=arclength(l)
  u=np.arange(96)/96;lp=points(l,sl,u)
  options=[]
  for k in range(len(h)):
   hh=np.roll(h,-k);sh=arclength(hh);hp=points(hh,sh,u);options.append(np.linalg.norm(lp-hp,axis=1).mean())
  h=np.roll(h,-int(np.argmin(options)));sh=arclength(h);hp=points(h,sh,u)
  la,lb,lw=sample(l,sl,u);ha,hb,hw=sample(h,sh,u)
  seq=[l];seqs=[sl];panel=[]
  # New clean bands have longitudinal segmentation, unlike collapsed original
  # faces which jump directly from 97% arm to 2% arm ownership.
  for t in np.arange(1,8)/8:
   ids=[]
   for j in range(len(u)):
    idx=len(verts);pos=lp[j]*(1-t)+hp[j]*t;verts=np.vstack([verts,pos]);ids.append(idx)
    records.append([idx,int(la[j]),int(lb[j]),float(lw[j]),int(ha[j]),int(hb[j]),float(hw[j]),float(t)])
   seq.append(np.array(ids));seqs.append(np.r_[u,1]);panel+=ids
  seq.append(h);seqs.append(sh)
  facebegin=len(added)
  for a,sa,b,sb in zip(seq[:-1],seqs[:-1],seq[1:],seqs[1:]):added+=ziprings(a,sa,b,sb)
  rings.append({'side':side,'low':l.tolist(),'high':h.tolist(),'vertices':panel,'faceStart':facebegin,'faceEnd':len(added)})
# Source face material ownership chosen geometrically within its original layer.
# The source bands all belong to the same cloth submesh; owner verifies actual2.
centers=v[tri].mean(1);bandfaces=np.array([f for f in main if low<M[int(centers[f,0]>0),tri[f]].mean()<high])
for t in added:
 c=verts[t].mean(0);addedparents.append(int(bandfaces[np.argmin(np.linalg.norm(centers[bandfaces]-c,axis=1))]))
result={'vertices':verts.tolist(),'triangles':np.vstack([newtris,added]).tolist(),'sourceMaps':[{str(k):w for k,w in m.items()} for m in maps],'records':records,'rings':rings,'triangleSourceFaces':np.r_[parents,addedparents].tolist(),'retainedTriangleCount':len(newtris),'sourceVertexCount':N}
(O/'annulus-prototype.json').write_text(json.dumps(result,separators=(',',':')))
print('new vertices',len(verts),'faces',len(newtris)+len(added),'panel vertices',len(records))

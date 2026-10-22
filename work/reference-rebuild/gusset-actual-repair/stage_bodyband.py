from pathlib import Path
import json,os,numpy as np
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';P=R/'work/reference-rebuild/garment-gusset1/runtime-reviewed'
variant=os.environ.get('BAND_DETAIL','Full');p=json.loads((P/f'UnderarmGusset_Female_{variant}.json').read_text());a=json.loads((O/f'bodyband-prototype-{variant}.json').read_text());g=np.load(O/f'bodyband-prototype-{variant}.npz');v=g['vertices'];tri=g['triangles'];src=np.array(p['sourceVertices']).reshape(-1,3);N=len(src);n=len(v);b=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json').read_text())['parts'][0];bv=np.array(b['vertices']).reshape(-1,3);bt=np.array(b['triangles']).reshape(-1,3);bbi=np.array(b['indices']).reshape(-1,4);bw=np.array(b['weights']).reshape(-1,4);bind=np.array(b['bindposes']).reshape(-1,4,4)
gm=[{int(k):w for k,w in m.items()} for m in a['garmentMaps']];bm=[{int(k):w for k,w in m.items()} for m in a['bodyMaps']]
# Replace the distinct malformed left cuff component with the intact right cuff.
# This changes neither Body nor the sewn shoulder surface correspondence.
from collections import defaultdict
st=np.array(p['sourceTriangles']).reshape(-1,3);_,ca=np.unique(np.round(src,7),axis=0,return_inverse=True);adj=defaultdict(list)
for f,t in enumerate(st):
 for j in ca[t]:adj[int(j)].append(f)
seen=set();components=[]
for f in range(len(st)):
 if f in seen:continue
 stack=[f];seen.add(f);c=[]
 while stack:
  z=stack.pop();c.append(z)
  for j in ca[st[z]]:
   for k in adj[int(j)]:
    if k not in seen:seen.add(k);stack.append(k)
 components.append(c)
def cuff(side):
 candidates=[]
 for c in components:
  points=src[np.unique(st[c])];mn=points.min(0);mx=points.max(0)
  if 1.12<mn[2]<1.22 and 1.21<mx[2]<1.23 and (points[:,0].mean()>0)==(side=='Right'):candidates.append(c)
 return max(candidates,key=len)
left=cuff('Left');right=cuff('Right');keep=~np.isin(a['triangleSourceFaces'],left);tri=tri[keep];a['triangleSourceFaces']=np.array(a['triangleSourceFaces'])[keep].tolist()
rightIds=np.unique(st[right]);mirrored=src[rightIds].copy();mirrored[:,0]*=-1;begin=n;v=np.vstack([v,mirrored]);mirrorFlags=np.r_[np.zeros(n,int),np.ones(len(rightIds),int)];lookupMirror={int(j):begin+k for k,j in enumerate(rightIds)}
tri=np.vstack([tri,[[lookupMirror[int(j)] for j in t[::-1]] for t in st[right]]]);a['triangleSourceFaces']+=list(map(int,right));gm.extend({int(j):1.} for j in rightIds);bm.extend({} for _ in rightIds);n=len(v)
boneMirror={i:p['bones'].index('Left'+name[5:]) if name.startswith('Right') else p['bones'].index('Right'+name[4:]) if name.startswith('Left') else i for i,name in enumerate(p['bones'])}
print('cuff source repair',variant,'left faces',len(left),'right faces',len(right),'new cuff vertices',len(rightIds))

needed={j for m in bm for j in m};faces=bt[np.any(np.isin(bt,list(needed)),axis=1)];proxyids=np.unique(faces);lookup={int(x):i for i,x in enumerate(proxyids)}
si=np.zeros((n,3),int);sw=np.zeros((n,3));bodyidx=np.zeros((n,3),int);bodyw=np.zeros((n,3));offset=np.zeros(n);pbi=np.zeros((n,4),int);pbw=np.zeros((n,4));oldbi=np.array(p['boneIndices']).reshape(-1,4)[:N];oldw=np.array(p['weights']).reshape(-1,4)[:N];dense=np.zeros((N,53));bdense=np.zeros((len(bv),53))
for k in range(4):dense[np.arange(N),oldbi[:,k]]+=oldw[:,k];bdense[np.arange(len(bv)),bbi[:,k]]+=bw[:,k]
for i in range(n):
 m=gm[i]
 if m:
  for k,(j,w) in enumerate(m.items()):si[i,k]=j;sw[i,k]=w
  dw=sum(dense[j]*w for j,w in m.items())
  if mirrorFlags[i]:
   mirroredWeights=np.zeros(53)
   for k,w in enumerate(dw):mirroredWeights[boneMirror[k]]=w
   dw=mirroredWeights
 else:
  # Nearest garment sample is for UV/color attribute transfer only. Anatomical
  # deformation comes from the connected Body triangle patch and barycentrics.
  j=int(np.linalg.norm(src-v[i],axis=1).argmin());si[i]=j;sw[i,0]=1
  for k,(j,w) in enumerate(bm[i].items()):bodyidx[i,k]=lookup[j];bodyw[i,k]=w
  dw=sum(bdense[j]*w for j,w in bm[i].items())
  offset[i]=next(.004 if l['layer']==1 else .0025 for l in a['layers'] if l['vertexStart']<=i<l['vertexStart']+l['vertexCount'])
 ix=np.argsort(dw)[-4:][::-1];pbi[i]=ix;pbw[i]=dw[ix]/sum(dw[ix])
local=[]
for j in proxyids:
 local.extend([(bind[bbi[j,k],:3,:3]@bv[j]+bind[bbi[j,k],:3,3]).tolist() for k in range(4)])
_,aliases=np.unique(np.round(v,8),axis=0,return_inverse=True)
p.update(vertexCount=n,sourceIndices=si.ravel().tolist(),sourceWeights=sw.ravel().tolist(),boneIndices=pbi.ravel().tolist(),weights=pbw.ravel().tolist(),triangles=tri.ravel().tolist(),triangleSourceFaces=a['triangleSourceFaces'],freeVertices=[i for i in range(N,n) if not mirrorFlags[i]],mirroredVertices=mirrorFlags.tolist(),aliases=aliases.tolist(),authoredVertices=v.ravel().tolist(),bodyIndices=bodyidx.ravel().tolist(),bodyWeights=bodyw.ravel().tolist(),bodyOffsets=offset.tolist(),proxyBoneIndices=bbi[proxyids].ravel().tolist(),proxyWeights=bw[proxyids].ravel().tolist(),proxyBoneLocalPositions=np.array(local).ravel().tolist(),proxyTriangles=np.array([[lookup[int(i)] for i in t] for t in faces]).ravel().tolist())
for key in ['cageStrengths','cageIndices','cageWeights','contactTriangles','proxyRestPositions']:p.pop(key,None)
(O/f'UnderarmGusset_Female_{variant}.json').write_text(json.dumps(p,separators=(',',':')))
print({'vertices':n,'faces':len(tri),'bodyBound':int((offset>0).sum()),'cutVertices':n-N-int((offset>0).sum()),'proxyVertices':len(proxyids),'proxyFaces':len(faces)})

# Coherent anatomical panel: retain whole connected source Body triangle patch,
# including adjacency and its own bone roles. Only connectors join the old shirt.
exec(__import__('pathlib').Path('work/reference-rebuild/gusset-actual-repair/author_annulus.py').read_text().split('rings=[]')[0])
gverts=verts.copy();gmaps=maps.copy();gtri=newtris.copy();gparents=parents.copy();gloops=loops
b=json.loads((R/'proof/reference-rebuild/character-motion-matrices17/poses/female_intro.json').read_text())['parts'][0]
bv=np.array(b['vertices']).reshape(-1,3);bn=np.array(b['normals']).reshape(-1,3);bt=np.array(b['triangles']).reshape(-1,3);bbi=np.array(b['indices']).reshape(-1,4);bbw=np.array(b['weights']).reshape(-1,4)
assert b['bones']==bones
BM=np.stack([(bbw*(bbi==bones.index(s+'UpperArm'))).sum(1) for s in ['Left','Right']])
# Generic clipped mesh, retaining source triangle barycentric surface binding.
def bodyclip(side):
 vv=[];mm=[];tt=[];cache={}
 def add(d):
  key=tuple((int(j),round(float(w),12)) for j,w in sorted(d.items()) if abs(w)>1e-10)
  if key not in cache:cache[key]=len(vv);vv.append(sum(bv[j]*w for j,w in key));mm.append(dict(key))
  return cache[key]
 def clip(poly,threshold,above):
  out=[]
  for a,c in zip(poly,poly[1:]+poly[:1]):
   sa=sum(BM[side,j]*w for j,w in a.items());sc=sum(BM[side,j]*w for j,w in c.items());ina=sa>=threshold if above else sa<=threshold;inc=sc>=threshold if above else sc<=threshold
   if ina:out.append(a)
   if ina!=inc:
    t=(threshold-sa)/(sc-sa);d=defaultdict(float)
    for j,w in a.items():d[j]+=(1-t)*w
    for j,w in c.items():d[j]+=t*w
    out.append(d)
  return out
 for t in bt:
  if bv[t,2].max()<1.13:continue
  poly=clip(clip([{int(j):1.} for j in t],low,True),high,False)
  ids=[add(d) for d in poly]
  for j in range(1,len(ids)-1):tt.append([ids[0],ids[j],ids[j+1]])
 vv=np.array(vv);tt=np.array(tt);_,aa=np.unique(np.round(vv,8),axis=0,return_inverse=True);edge=defaultdict(list)
 for t in tt:
  for a,c in zip(t,np.roll(t,-1)):edge[tuple(sorted((aa[a],aa[c])))].append((a,c))
 edges=[es[0] for es in edge.values() if len(es)==1];nx={aa[a]:(a,c) for a,c in edges};loops=[]
 while nx:
  first=next(iter(nx));cur=first;l=[]
  while True:
   a,c=nx.pop(cur);l.append(a);cur=aa[c]
   if cur==first:break
  loops.append(np.array(l))
 assert len(loops)==2,(side,list(map(len,loops)))
 return vv,mm,tt,loops
# Compact source correspondence: garment-source for retained/cut vertices,
# Body-source for authored patch vertices. The latter is continuous by topology.
verts=list(gverts);gmap=gmaps.copy();bmap=[{} for _ in verts];newtri=list(gtri);parent=list(gparents);layers=[];bridgeEvidence=[]
sourceNormal=np.array(p['sourceNormals']).reshape(-1,3);garmentNormal=np.array([sum(sourceNormal[j]*w for j,w in m.items()) for m in gmaps])
def length(l):
 p=np.array([verts[i] for i in l]);d=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1);return np.r_[0,np.cumsum(d)]/sum(d)
def sample(l,s,u):
 j=np.minimum(np.searchsorted(s,u,side='right')-1,len(l)-1);w=(u-s[j])/(s[j+1]-s[j]);p=np.array(verts);return p[l[j]]*(1-w[:,None])+p[l[(j+1)%len(l)]]*w[:,None]
def bridge(a,c):
 a=a[::-1];sa=length(a);u=np.arange(96)/96;ap=sample(a,sa,u);scores=[]
 points=np.array(verts);av=points[a]-points[a].mean(0);cv=points[c]-points[c].mean(0);an=np.cross(av,np.roll(av,-1,axis=0)).sum(0);cn=np.cross(cv,np.roll(cv,-1,axis=0)).sum(0);orientation=float(an@cn/(np.linalg.norm(an)*np.linalg.norm(cn)))
 if orientation<=0:raise RuntimeError('Crossed shell/lining boundary orientations: '+str(orientation))
 bridgeEvidence.append({'garmentBoundaryVertices':len(a),'bodyBoundaryVertices':len(c),'orientedAreaCosine':orientation})
 for k in range(len(c)):
  cc=np.roll(c,-k);sc=length(cc);scores.append(np.linalg.norm(ap-sample(cc,sc,u),axis=1).mean())
 c=np.roll(c,-int(np.argmin(scores)));sc=length(c);i=j=0;out=[]
 while i<len(a) or j<len(c):
  ni=sa[i+1] if i<len(a) else 2;nj=sc[j+1] if j<len(c) else 2
  if ni<nj:out.append([a[i%len(a)],a[(i+1)%len(a)],c[j%len(c)]]);i+=1
  else:out.append([a[i%len(a)],c[(j+1)%len(c)],c[j%len(c)]]);j+=1
 return out
for side in [0,1]:
 vv,mm,tt,bl=bodyclip(side)
 norms=np.array([sum(bn[j]*w for j,w in m.items()) for m in mm]);norms/=np.linalg.norm(norms,axis=1)[:,None]
 ls=[l for l in gloops if int(gverts[l,0].mean()>0)==side];lo=[l for l in ls if np.mean([scalar(i,side) for i in l])<low+.001];hi=[l for l in ls if abs(np.mean([scalar(i,side) for i in l])-high)<1e-4]
 def facing(l):
  radial=gverts[l]-gverts[l].mean(0);radial[:,0]=0;radial/=np.maximum(np.linalg.norm(radial,axis=1)[:,None],1e-12);return float(np.mean((garmentNormal[l]*radial).sum(1)))
 lo.sort(key=facing);hi.sort(key=facing)
 assert len(lo)==len(hi)==2 and facing(lo[0])<-.4 and facing(lo[1])>.4 and facing(hi[0])<-.4 and facing(hi[1])>.4
 print('verified shell normals',side,[facing(l) for l in lo],[facing(l) for l in hi])
 for layer,(cl,ch) in enumerate(zip(lo,hi)):
  offset=.004 if layer==1 else .0025;start=len(verts);verts.extend(vv+norms*offset);bmap.extend(mm);gmap.extend({} for _ in vv)
  ids=np.arange(start,len(verts));faces=ids[tt[:,::-1] if layer==0 else tt]
  bandstart=len(newtri);newtri.extend(faces);parent.extend([0]*len(faces));connections=[]
  for bound in bl:
   mass=np.mean([sum(BM[side,j]*w for j,w in mm[i].items()) for i in bound]);cloth=cl if abs(mass-low)<1e-4 else ch
   bb=ids[bound[::-1] if layer==0 else bound];connections+=bridge(cloth,bb)
  newtri.extend(connections);parent.extend([0]*len(connections));layers.append({'side':side,'layer':layer,'vertexStart':start,'vertexCount':len(vv),'faceStart':bandstart,'faceCount':len(faces),'connectorFaces':len(connections)})
verts=np.array(verts);newtri=np.array(newtri);centers=v[tri].mean(1)
# Attribute only new faces to geometrically corresponding original cloth faces.
for f in range(len(gtri),len(newtri)):
 c=verts[newtri[f]].mean(0);ids=np.array(list(main));parent[f]=int(ids[np.argmin(np.linalg.norm(centers[ids]-c,axis=1))])
np.savez_compressed(O/f'bodyband-prototype-{variant}.npz',vertices=verts,triangles=newtri)
(O/f'bodyband-prototype-{variant}.json').write_text(json.dumps({'garmentMaps':gmap,'bodyMaps':bmap,'layers':layers,'triangleSourceFaces':list(map(int,parent)),'retainedTriangleCount':len(gtri),'sourceVertexCount':N,'bridgeOrientationEvidence':bridgeEvidence},separators=(',',':')))
print('Body band',len(verts),'vertices',len(newtri),'faces',layers)

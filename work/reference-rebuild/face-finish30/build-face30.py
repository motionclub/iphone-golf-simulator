"""Bounded head-surface fairing + conforming local edge refinement from frozen Smooth1.
Original points keep exact weights/morph deltas; new points interpolate same edge endpoints.
Lip pigment/geometry and eyelid-active geometry/triangles remain fixed. Work only.
"""
import bpy,pathlib,numpy as np,json,hashlib,collections,math
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30';results={}
def digest(v):return hashlib.sha256(repr(v).encode()).hexdigest()
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*t*(t*(t*6-15)+10)
def kd_for(p):
 kd=KDTree(len(p))
 for i,x in enumerate(p):kd.insert(Vector(x),i)
 kd.balance();return kd
for sex in ('Male','Female'):
 source=R/f'work/reference-rebuild/face-finish29/smooth-mouth1/{sex}_OriginalFaceFinish29Smooth1.blend';bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body'];me=body.data;feat=bpy.data.objects['ReferenceFeatures'];rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.data.pose_position='REST'
 original=np.array([tuple(v.co)for v in me.vertices]);shapes={k.name:np.array([tuple(v.co)for v in k.data])for k in me.shape_keys.key_blocks};n0=len(original);me.calc_loop_triangles();triangles=[tuple(t.vertices)for t in me.loop_triangles];triLoops=[tuple(t.loops)for t in me.loop_triangles];triMaterials=[t.material_index for t in me.loop_triangles];uvs={a.name:np.array([tuple(v.uv)for v in a.data])for a in me.uv_layers};oldNormals=np.array([tuple(c.vector)for c in me.corner_normals]);colors={a.name:(a.domain,a.data_type,np.array([tuple(v.color)for v in a.data]))for a in me.color_attributes};groups=[g.name for g in body.vertex_groups];weights=[{g.group:g.weight for g in v.groups}for v in me.vertices];materials=list(me.materials);blink=np.any(np.array([np.linalg.norm(a-original,axis=1)>1e-7 for name,a in shapes.items()if name!='Basis']),axis=0);featureHash=digest(([tuple(v.co)for v in feat.data.vertices],[[tuple(v.co)for v in k.data]for k in feat.data.shape_keys.key_blocks]));boneHash=digest([(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row))for b in rig.data.bones])
 # Positional weld for fairing only. Original mesh seams are retained in output.
 _,first,inv=np.unique(np.round(original,6),axis=0,return_index=True,return_inverse=True);unique=original[first].copy();uN=len(unique);adj=[set()for _ in unique];area=np.zeros(uN);norm=np.zeros((uN,3))
 for t in triangles:
  a,b,c=t;cross=np.cross(original[b]-original[a],original[c]-original[a])
  for i,j,k in [(a,b,c),(b,a,c),(c,a,b)]:adj[inv[i]].update((int(inv[j]),int(inv[k])));area[inv[i]]+=np.linalg.norm(cross)/6;norm[inv[i]]+=cross
 norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-15);x,y,z=unique.T
 protected=set(np.flatnonzero(blink));lip=set();anatomy=set()
 for gi,name in enumerate(groups):
  ids={i for i,w in enumerate(weights)if w.get(gi,0)>.25}
  if any(s in name for s in ('mouth','lip','seam')):lip.update(ids)
  if any(s in name for s in ('nostril','ala')):anatomy.update(ids)
 protected.update(lip);protected.update(anatomy);protKD=kd_for(original[sorted(protected)]);distance=np.array([protKD.find(Vector(p))[2]for p in unique]);protectUnique=set(inv[list(protected)])
 # Fair broad surfaces in a tangent frame. Shape projection and its derivative
 # are calculated together, so broad geometric cleanup is visible under gloss.
 eyeIds=np.flatnonzero(blink);eyeKD=kd_for(original[eyeIds]);ed=np.array([eyeKD.find(Vector(q))[2]for q in unique]);
 lipKD=kd_for(original[sorted(lip)]);ld=np.array([lipKD.find(Vector(q))[2]for q in unique]);noseKD=kd_for(original[sorted(anatomy)]);nd=np.array([noseKD.find(Vector(q))[2]for q in unique])
 front=ss(-.035,-.080,y);scalp=ss(1.590,1.625,z)
 head=ss(1.420,1.450,z)*np.maximum(front,scalp)
 earGuard=(1-ss(.073,.088,abs(x)))*(1-ss(1.592,1.620,z))+ss(1.592,1.620,z)
 guard=ss(.004,.012,ed)*ss(.0005,.009,ld)*ss(.002,.008,nd)
 # Preserve the complete nose volume while fairing its surrounding cheek.
 nz=float(np.median(original[sorted(anatomy),2]))
 noseVolume=(1-ss(.022,.037,abs(x)))*ss(nz-.018,nz-.009,z)*(1-ss(nz+.043,nz+.062,z))
 field=head*earGuard*guard*(1-noseVolume);field[list(protectUnique)]=0
 curve=field.copy();chin=ss(1.423,1.443,z)*(1-ss(1.489,1.515,z))*front
 kd=kd_for(unique)
 # A softly filtered frame avoids perpetuating a bad source triangle normal.
 frame=norm.copy()
 for i in np.flatnonzero(head>.001):
  ns=kd.find_range(Vector(unique[i]),.014);js=np.array([j for _,j,d in ns if np.dot(norm[j],norm[i])>.35]);
  if len(js):
   w=np.maximum(0,1-np.sum((unique[js]-unique[i])**2,axis=1)/.014**2)**2*np.maximum(area[js],1e-12);v=np.sum(norm[js]*w[:,None],axis=0);frame[i]=v/max(np.linalg.norm(v),1e-12)
 def frameAxes(n):
  a=np.array([0.,0.,1.])if abs(n[2])<.85 else np.array([1.,0.,0.]);u=np.cross(n,a);u/=max(np.linalg.norm(u),1e-12);return u,np.cross(n,u)
 hood={}
 for i in np.flatnonzero(field>.0001):
  n=frame[i];u,v=frameAxes(n);radius=.030 if sex=='Male' else .026
  js=np.array([j for _,j,d in kd.find_range(Vector(unique[i]),radius)if np.dot(frame[j],n)>.35]);q=unique[js]-unique[i];uv=np.c_[q@u,q@v]/radius;d2=np.sum(uv*uv,axis=1);w=np.maximum(0,1-d2)**2*np.maximum(area[js],1e-12);A=np.c_[np.ones(len(js)),uv[:,0],uv[:,1],uv[:,0]**2,uv[:,0]*uv[:,1],uv[:,1]**2];hood[i]=(js,A,w,n)
 current=unique.copy()
 for passno in range(5):
  proposal=current.copy()
  for i,(js,A,w,n)in hood.items():
   if len(js)<9:continue
   c=np.linalg.lstsq(A*np.sqrt(w)[:,None],((current[js]-unique[i])@n)*np.sqrt(w),rcond=None)[0];d=(current[i]-unique[i])@n;cap=.0035 if scalp[i]>.9 else .006;proposal[i]=unique[i]+n*np.clip(d+(c[0]-d)*.85*field[i],-cap*field[i],cap*field[i])
  current=proposal
 delta=current[inv]-original;delta[list(protected)]=0;points=original+delta
 # Select long scalp/chin edges only; protected eye/lip faces cannot subdivide.
 refine={};triProtected=[any(i in protected for i in t)for t in triangles]
 for fi,t in enumerate(triangles):
  if triProtected[fi]:continue
  for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
   if min(curve[inv[a]],curve[inv[b]])>.15 and np.linalg.norm(points[a]-points[b])>.005:
    refine[tuple(sorted((a,b)))]=None
 # Do not split an edge also adjacent to a protected face.
 for fi,t in enumerate(triangles):
  if triProtected[fi]:
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:refine.pop(tuple(sorted((a,b))),None)
 # Project inserted edge samples onto the same local smooth surface, with a
 # small bounded arc sag. This rounds the actual scalp and chin silhouettes.
 currentKD=kd_for(current)
 def localFit(pos,n,radius):
  u,v=frameAxes(n);js=np.array([j for _,j,d in currentKD.find_range(Vector(pos),radius)if np.dot(frame[j],n)>.35]);q=current[js]-pos;uv=np.c_[q@u,q@v]/radius;d2=np.sum(uv*uv,axis=1);w=np.maximum(0,1-d2)**2*np.maximum(area[js],1e-12)
  if len(js)<9:return 0.,n
  A=np.c_[np.ones(len(js)),uv[:,0],uv[:,1],uv[:,0]**2,uv[:,0]*uv[:,1],uv[:,1]**2];c=np.linalg.lstsq(A*np.sqrt(w)[:,None],(q@n)*np.sqrt(w),rcond=None)[0];nn=n-u*c[1]/radius-v*c[2]/radius;return c[0],nn/max(np.linalg.norm(nn),1e-12)
 originalPointNormals=np.zeros_like(original)
 for li,loop in enumerate(me.loops):originalPointNormals[loop.vertex_index]+=oldNormals[li]
 originalPointNormals/=np.maximum(np.linalg.norm(originalPointNormals,axis=1)[:,None],1e-15)
 fitted={}
 for i in np.flatnonzero(field>.0001):
  shift,nn=localFit(current[i],frame[i],.018);fitted[i]=nn
 sampleNormals=[]
 for vi in range(n0):
  ui=inv[vi];f=field[ui];old=originalPointNormals[vi];target=fitted.get(ui,old);nn=old*(1-f)+target*f;nn/=max(np.linalg.norm(nn),1e-12);sampleNormals.append(nn)
 def project(mid,a,b):
  na=sampleNormals[a];nb=sampleNormals[b];n=na+nb;n/=max(np.linalg.norm(n),1e-12);sag=np.dot(nb-na,points[b]-points[a])/8
  return mid+n*np.clip(sag,-.00065,.00065)
 newPoints=list(points);parents={};newWeights=list(weights);newShapes={name:list(a+delta)for name,a in shapes.items()}
 for (a,b)in sorted(refine):
  i=len(newPoints);refine[(a,b)]=i;mid=(points[a]+points[b])/2;pos=project(mid,a,b);extra=pos-mid;newPoints.append(pos);nn=sampleNormals[a]+sampleNormals[b];sampleNormals.append(nn/max(np.linalg.norm(nn),1e-12));parents[i]=(a,b);w={g:(weights[a].get(g,0)+weights[b].get(g,0))/2 for g in set(weights[a])|set(weights[b])};newWeights.append(w)
  for name in shapes:newShapes[name].append((shapes[name][a]+delta[a]+shapes[name][b]+delta[b])/2+extra)
 faces=[];outMaterials=[];corners=[];sourceFaces=[]
 for fi,(a,b,c)in enumerate(triangles):
  ab=refine.get(tuple(sorted((a,b))));bc=refine.get(tuple(sorted((b,c))));ca=refine.get(tuple(sorted((c,a))));splits=sum(i is not None for i in (ab,bc,ca))
  bary={a:np.array([1.,0,0]),b:np.array([0.,1,0]),c:np.array([0.,0,1])}
  if ab is not None:bary[ab]=np.array([.5,.5,0])
  if bc is not None:bary[bc]=np.array([0,.5,.5])
  if ca is not None:bary[ca]=np.array([.5,0,.5])
  if splits==0:subs=[(a,b,c)]
  elif splits==3:subs=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
  elif splits==1:
   if ab is not None:subs=[(a,ab,c),(ab,b,c)]
   elif bc is not None:subs=[(b,bc,a),(bc,c,a)]
   else:subs=[(c,ca,b),(ca,a,b)]
  elif ab is None:subs=[(c,ca,bc),(a,b,ca),(b,bc,ca)]
  elif bc is None:subs=[(a,ab,ca),(b,c,ab),(c,ca,ab)]
  else:subs=[(b,bc,ab),(c,a,bc),(a,ab,bc)]
  for f in subs:faces.append(f);outMaterials.append(triMaterials[fi]);corners.extend([(triLoops[fi],bary[i])for i in f]);sourceFaces.append(fi)
 # Refine the scalp a second time to keep its visible outline smoothly curved.
 # Every new corner keeps barycentrics into the exact original triangle.
 for refinePass in range(2):
  midEdges={};pointArray=np.array(newPoints)
  for fi,t in enumerate(faces):
   if any(v in protected for v in t):continue
   for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):
    if min(pointArray[a,2],pointArray[b,2])>1.610 and np.linalg.norm(pointArray[a]-pointArray[b])>.0045:midEdges[tuple(sorted((a,b)))]=None
  if not midEdges:break
  for (a,b)in sorted(midEdges):
   i=len(newPoints);midEdges[(a,b)]=i;mid=(pointArray[a]+pointArray[b])/2;na=sampleNormals[a];nb=sampleNormals[b];nn=na+nb;nn/=max(np.linalg.norm(nn),1e-12);sag=np.dot(nb-na,pointArray[b]-pointArray[a])/8;pos=mid+nn*np.clip(sag,-.00045,.00045);extra=pos-mid;newPoints.append(pos);sampleNormals.append(nn);parents[i]=(a,b);wa=newWeights[a];wb=newWeights[b];newWeights.append({g:(wa.get(g,0)+wb.get(g,0))/2 for g in set(wa)|set(wb)})
   for name in shapes:newShapes[name].append((newShapes[name][a]+newShapes[name][b])/2+extra)
  nextFaces=[];nextMats=[];nextCorners=[];nextSources=[]
  for fi,(a,b,c)in enumerate(faces):
   ab=midEdges.get(tuple(sorted((a,b))));bc=midEdges.get(tuple(sorted((b,c))));ca=midEdges.get(tuple(sorted((c,a))));splits=sum(v is not None for v in (ab,bc,ca));loops=corners[3*fi][0];bary={a:corners[3*fi][1],b:corners[3*fi+1][1],c:corners[3*fi+2][1]}
   if ab is not None:bary[ab]=(bary[a]+bary[b])/2
   if bc is not None:bary[bc]=(bary[b]+bary[c])/2
   if ca is not None:bary[ca]=(bary[c]+bary[a])/2
   if splits==0:subs=[(a,b,c)]
   elif splits==3:subs=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
   elif splits==1:
    if ab is not None:subs=[(a,ab,c),(ab,b,c)]
    elif bc is not None:subs=[(b,bc,a),(bc,c,a)]
    else:subs=[(c,ca,b),(ca,a,b)]
   elif ab is None:subs=[(c,ca,bc),(a,b,ca),(b,bc,ca)]
   elif bc is None:subs=[(a,ab,ca),(b,c,ab),(c,ca,ab)]
   else:subs=[(b,bc,ab),(c,a,bc),(a,ab,bc)]
   for f in subs:nextFaces.append(f);nextMats.append(outMaterials[fi]);nextCorners.extend([(loops,bary[v])for v in f]);nextSources.append(sourceFaces[fi])
  faces=nextFaces;outMaterials=nextMats;corners=nextCorners;sourceFaces=nextSources
 new=bpy.data.meshes.new('Body_Face30');new.from_pydata(newPoints,[],faces);new.update()
 for mat in materials:new.materials.append(mat)
 for i,p in enumerate(new.polygons):p.material_index=outMaterials[i];p.use_smooth=True
 for name,data in uvs.items():
  layer=new.uv_layers.new(name=name)
  for j,(loops,bary)in enumerate(corners):layer.data[j].uv=bary@data[list(loops)]
 for name,(domain,dtype,data)in colors.items():
  col=new.color_attributes.new(name=name,type=dtype,domain=domain)
  if domain=='POINT':
   for i in range(len(newPoints)):col.data[i].color=data[i]if i<n0 else (np.array(col.data[parents[i][0]].color)+np.array(col.data[parents[i][1]].color))/2
  elif domain=='CORNER':
   for j,(loops,bary)in enumerate(corners):col.data[j].color=bary@data[list(loops)]
 body.data=new
 body.vertex_groups.clear()
 for name in groups:body.vertex_groups.new(name=name)
 for i,w in enumerate(newWeights):
  for gi,value in w.items():
   if value>0:body.vertex_groups[gi].add([i],value,'REPLACE')
 for name,array in newShapes.items():
  key=body.shape_key_add(name=name,from_mix=False)
  for i,v in enumerate(array):key.data[i].co=v
 new.update();actual=np.array([tuple(v.co)for v in new.vertices]);ds=np.linalg.norm(actual[:n0]-original,axis=1);assert ds[list(protected)].max()==0;assert groups==[g.name for g in body.vertex_groups]
 for i,w in enumerate(weights):assert {g.group:g.weight for g in new.vertices[i].groups}==w
 err={name:float(np.max(abs((np.array([tuple(v.co)for v in key.data])[:n0]-actual[:n0])-(shapes[name]-original))))for name,key in zip(newShapes,new.shape_keys.key_blocks)};assert max(err.values())<1e-7
 assert featureHash==digest(([tuple(v.co)for v in feat.data.vertices],[[tuple(v.co)for v in k.data]for k in feat.data.shape_keys.key_blocks]));assert boneHash==digest([(b.name,b.parent.name if b.parent else None,tuple(x for row in b.matrix_local for x in row))for b in rig.data.bones]);assert len(rig.data.bones)==53
 for name,data in uvs.items():
  for j,(loops,bary)in enumerate(corners):
   if np.count_nonzero(bary)==1:assert np.array_equal(np.array(new.uv_layers[name].data[j].uv),data[loops[int(np.argmax(bary))]])
 # Derivative-consistent head normals; midpoint samples use exact endpoint
 # interpolation so triangle subdivision cannot introduce a new shading field.
 normalVectors=[]
 for j,(loops,bary)in enumerate(corners):
  vi=new.loops[j].vertex_index;old=bary@oldNormals[list(loops)];old/=max(np.linalg.norm(old),1e-12)
  if vi<n0:
   ui=inv[vi];f=field[ui];target=fitted.get(ui,old);nn=old*(1-f)+target*f;nn/=max(np.linalg.norm(nn),1e-12)
  else:nn=sampleNormals[vi]
  normalVectors.append(tuple(nn))
 new.normals_split_custom_set(normalVectors);new.update()
 candidate=O/f'{sex}_OriginalFaceFinish30.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
 r={'source':str(source),'candidate':str(candidate),'originalVertices':n0,'candidateVertices':len(actual),'originalTriangles':len(triangles),'candidateTriangles':len(faces),'insertedVertices':len(parents),'protectedVertices':len(protected),'blinkActiveVertices':int(blink.sum()),'blinkActiveAndLipPositionsMaxDeltaMetres':float(ds[list(protected)].max()),'originalVertexWeightError':0,'shapeDeltaMaxErrorMetres':err,'bonesRestAndFeaturesExact':True,'sourceUvMaskPreservedAtOriginalCorners':True,'lip3Palette':'unchanged root shader','maxOriginalDeltaMm':float(ds.max()*1000),'meanMovedDeltaMm':float(ds[ds>1e-8].mean()*1000),'movedOriginalVertices':int((ds>1e-8).sum()),'maxOriginalXZShiftMm':(np.max(abs(actual[:n0,[0,2]]-original[:,[0,2]]),axis=0)*1000).tolist(),'refinement':'tangent MLS broad fairing; continuous head normals; long broad-surface edges split, scalp refined to4.5mm; exact protected eyelid/lip/nostril positions; recursive barycentric UV/colors/weights/shape interpolation','recipe':{'broadTangentFitRadiusMm':30 if sex=='Male' else 26,'depthPasses':5,'maximumNormalShiftMm':6,'scalpNormalShiftCapMm':3.5,'refineBroadEdgesOverMm':5,'refineScalpEdgesOverMm':4.5,'midpointHermiteSagCapMm':.65,'originalScalpPointsFixed':False,'normalInterpolation':'derivative-consistent MLS normals over broad head; protected authored normals retained; Unity geometric field active'},'export':'not yet; source preview first'}
 results[sex]=r;np.savez_compressed(O/(sex.lower()+'-candidate.npz'),p=actual,t=np.array(faces),sourceFace=np.array(sourceFaces),parents=np.array([(i,a,b)for i,(a,b)in parents.items()]),original=original);print('FACE30',sex,r,flush=True)
(O/'SOURCE_GATE.json').write_text(json.dumps({'status':'SOURCE INVARIANTS PASS; ART PENDING','results':results},indent=2)+'\n')

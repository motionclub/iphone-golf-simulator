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
 # Broader fit than held shallow candidate: 32mm supported surface, 3 passes,
 # 7mm depth cap. Fixed source feature contours fade back over 4..11mm.
 front=ss(-.065,-.100,y)*(1-ss(.073,.096,abs(x)));field=front*ss(1.445,1.470,z)*(1-ss(1.625,1.650,z))*ss(.004,.011,distance)
 # Entire lips and nose are frozen broad forms, rather than only sparse
 # contour vertices; quintic transition leaves zero first/second derivatives.
 lipPs=original[sorted(lip)];lz=float(np.median(lipPs[:,2]));lw=float(np.max(abs(lipPs[:,0])));nz=float(np.median(original[sorted(anatomy),2]));
 mouthProtect=(1-ss(lw+.005,lw+.023,abs(x)))*(1-ss(.020,.039,abs(z-lz)))
 noseProtect=(1-ss(.020,.044,abs(x)))*ss(nz-.020,nz-.006,z)*(1-ss(nz+.047,nz+.079,z))
 field*=1-np.maximum(mouthProtect,noseProtect)
 if sex=='Female':field*=0 # broad facial forms already clean; refine head/jaw only
 field[list(protectUnique)]=0;kd=kd_for(unique);hood={}
 for i in np.flatnonzero(field>.001):
  js=np.array([j for _,j,d in kd.find_range(Vector(unique[i]),.038) if norm[j,1]<-.25 and abs(unique[j,1]-unique[i,1])<.044]);q=(unique[js][:,[0,2]]-unique[i,[0,2]])/.032;d2=np.sum(q*q,axis=1);keep=d2<1.0;js=js[keep];q=q[keep];d2=d2[keep];w=(1-d2)**3*np.maximum(area[js],1e-12);A=np.c_[np.ones(len(js)),q[:,0],q[:,1],q[:,0]**2,q[:,0]*q[:,1],q[:,1]**2];hood[i]=(js,A,w)
 current=unique.copy()
 for passno in range(3):
  proposal=current.copy()
  for i,(js,A,w)in hood.items():
   if len(js)<10:continue
   c=np.linalg.lstsq(A*np.sqrt(w)[:,None],current[js,1]*np.sqrt(w),rcond=None)[0];proposal[i,1]=unique[i,1]+np.clip((current[i,1]-unique[i,1])+(c[0]-current[i,1])*.94*field[i],-.007*field[i],.007*field[i])
  current=proposal
 # Scalp and chin curvature fairing uses the original connected shell. Full
 # coordinates may change <=3mm, broad fade excludes eyes/lips/ears/neck.
 scalp=ss(1.605,1.635,z);chin=ss(1.429,1.450,z)*(1-ss(1.485,1.505,z))*front
 curve=np.maximum(scalp,chin)*ss(.005,.014,distance);curve[(abs(x)>.078)&(z<1.620)]=0;curve[list(protectUnique)]=0
 for passno in range(8):
  proposal=current.copy()
  for i in np.flatnonzero((curve>.001)&(scalp<.01)):
   js=list(adj[i]);
   if not js:continue
   v=current[i]+(current[js].mean(axis=0)-current[i])*.48*curve[i];d=v-unique[i];ln=np.linalg.norm(d);proposal[i]=unique[i]+d*min(1,.003*curve[i]/max(ln,1e-15))
  current=proposal
 delta=current[inv]-original;delta[list(protected)]=0;points=original+delta
 # Select long scalp/chin edges only; protected eye/lip faces cannot subdivide.
 refine={};triProtected=[any(i in protected for i in t)for t in triangles]
 for fi,t in enumerate(triangles):
  if triProtected[fi]:continue
  for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
   if min(curve[inv[a]],curve[inv[b]])>.15 and np.linalg.norm(points[a]-points[b])>.0065:
    refine[tuple(sorted((a,b)))]=None
 # Do not split an edge also adjacent to a protected face.
 for fi,t in enumerate(triangles):
  if triProtected[fi]:
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:refine.pop(tuple(sorted((a,b))),None)
 # Fit local quadratic height over existing curved surface. New midpoint
 # projection adds curvature to the long polygonal outline, cap1.8mm.
 currentKD=kd_for(current)
 # Hermite sag from endpoint normals: bounded local circular arc. The old
 # midpoint MLS projected as much as1.8mm and introduced scalloping; circle
 # sag for a10mm edge on a100mm radius is only0.125mm.
 originalPointNormals=np.zeros_like(original)
 for li,loop in enumerate(me.loops):originalPointNormals[loop.vertex_index]+=oldNormals[li]
 originalPointNormals/=np.maximum(np.linalg.norm(originalPointNormals,axis=1)[:,None],1e-15)
 def project(mid,a,b):
  na=originalPointNormals[a];nb=originalPointNormals[b];n=na+nb;n/=max(np.linalg.norm(n),1e-12);sag=np.dot(nb-na,points[b]-points[a])/8
  return mid+n*np.clip(sag,0,.00065)
 newPoints=list(points);parents={};newWeights=list(weights);newShapes={name:list(a+delta)for name,a in shapes.items()}
 for (a,b)in sorted(refine):
  i=len(newPoints);refine[(a,b)]=i;mid=(points[a]+points[b])/2;pos=project(mid,a,b);extra=pos-mid;newPoints.append(pos);parents[i]=(a,b);w={g:(weights[a].get(g,0)+weights[b].get(g,0))/2 for g in set(weights[a])|set(weights[b])};newWeights.append(w)
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
 new=bpy.data.meshes.new('Body_Face30');new.from_pydata(newPoints,[],faces);new.update()
 for mat in materials:new.materials.append(mat)
 for i,p in enumerate(new.polygons):p.material_index=outMaterials[i];p.use_smooth=True
 for name,data in uvs.items():
  layer=new.uv_layers.new(name=name)
  for j,(loops,bary)in enumerate(corners):layer.data[j].uv=bary@data[list(loops)]
 for name,(domain,dtype,data)in colors.items():
  col=new.color_attributes.new(name=name,type=dtype,domain=domain)
  if domain=='POINT':
   for i in range(len(newPoints)):col.data[i].color=data[i]if i<n0 else (data[parents[i][0]]+data[parents[i][1]])/2
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
 # Preserve authored non-face and protected feature corner normals. Only
 # changed head points / added curvature samples use geometric normals.
 normalVectors=[]
 for j,(loops,bary)in enumerate(corners):
  i=new.loops[j].vertex_index
  if i<n0 and ds[i]<=1e-8:normalVectors.append(tuple(bary@oldNormals[list(loops)]))
  else:normalVectors.append(tuple(bary@oldNormals[list(loops)]))
 new.normals_split_custom_set(normalVectors);new.update()
 candidate=O/f'{sex}_OriginalFaceFinish30.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
 r={'source':str(source),'candidate':str(candidate),'originalVertices':n0,'candidateVertices':len(actual),'originalTriangles':len(triangles),'candidateTriangles':len(faces),'insertedVertices':len(parents),'protectedVertices':len(protected),'blinkActiveVertices':int(blink.sum()),'blinkActiveAndLipPositionsMaxDeltaMetres':float(ds[list(protected)].max()),'originalVertexWeightError':0,'shapeDeltaMaxErrorMetres':err,'bonesRestAndFeaturesExact':True,'sourceUvMaskPreservedAtOriginalCorners':True,'lip3Palette':'unchanged root shader','maxOriginalDeltaMm':float(ds.max()*1000),'meanMovedDeltaMm':float(ds[ds>1e-8].mean()*1000),'movedOriginalVertices':int((ds>1e-8).sum()),'maxOriginalXZShiftMm':(np.max(abs(actual[:n0,[0,2]]-original[:,[0,2]]),axis=0)*1000).tolist(),'refinement':'only long scalp/chin edges; original scalp points fixed; bounded Hermite circular sag; no protected eyelid/lip/nostril faces; barycentric UV/colors/weights/shape interpolation','recipe':{'broadDepthFitRadiusMm':32,'depthPasses':3,'maximumDepthMm':7,'scalpChinRelaxPasses':8,'contourPositionCapMm':3,'refineEdgesOverMm':6.5,'midpointHermiteSagCapMm':.65,'originalScalpPointsFixed':True,'normalInterpolation':'authored corner field retained with barycentric interpolation; Unity geometric field active'},'export':'not yet; source preview first'}
 results[sex]=r;np.savez_compressed(O/(sex.lower()+'-candidate.npz'),p=actual,t=np.array(faces),sourceFace=np.array(sourceFaces),parents=np.array([(i,a,b)for i,(a,b)in parents.items()]),original=original);print('FACE30',sex,r,flush=True)
(O/'SOURCE_GATE.json').write_text(json.dumps({'status':'SOURCE INVARIANTS PASS; ART PENDING','results':results},indent=2)+'\n')

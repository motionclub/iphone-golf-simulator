"""Fair only outer ordered eyelid strip depth over the smooth original head.
Rim and first two new rows, all X/Z, connectivity, weights and materials stay fixed.
The original broad surface is the reference; constrained harmonic residuals remove
arbitrary spoke dependence introduced by a radial arclength loft.
"""
import bpy,numpy as np,pathlib,json,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30-lids/ordered-surface1'

def make_reference(sex):
 path=R/f'work/reference-rebuild/face-finish30/ears/{sex}_OriginalFaceFinish30Ears.blend'
 if sex=='Female':path=R/'work/reference-rebuild/face-finish30/forehead-check/Female_OriginalFaceFinish30Forehead.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path));m=bpy.data.objects['Body'].data;p=np.array([v.co[:]for v in m.vertices]);t=np.array([q.vertices[:]for q in m.polygons]);_,first,inv=np.unique(np.round(p,6),axis=0,return_index=True,return_inverse=True);u=p[first];area=np.zeros(len(u));n=np.zeros_like(u)
 for f in t:
  cr=np.cross(p[f[1]]-p[f[0]],p[f[2]]-p[f[0]])
  for i in f:area[inv[i]]+=np.linalg.norm(cr)/6;n[inv[i]]+=cr
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-15);selected=np.flatnonzero((u[:,2]>1.44)&(u[:,2]<1.69)&(u[:,1]<-.035)&(n[:,1]<-.15));kd=KDTree(len(selected))
 for i in selected:kd.insert(Vector((u[i,0],0,u[i,2])),int(i))
 kd.balance();bvh=BVHTree.FromPolygons([Vector(q)for q in p],t.tolist(),all_triangles=True);cache={};radius=.018 if sex=='Male'else .016
 def field(q):
  key=(round(float(q[0]),6),round(float(q[2]),6))
  if key in cache:return cache[key]
  nearby=kd.find_range(Vector((q[0],0,q[2])),radius);ids=np.array([j for _,j,d in nearby],int)
  if len(ids)<9:
   hit=bvh.ray_cast(Vector((q[0],-.50,q[2])),Vector((0,1,0)),1.)[0];v=float(hit.y)if hit is not None else float(q[1]);cache[key]=v;return v
  uv=(u[ids][:,[0,2]]-q[[0,2]])/radius;w=np.maximum(0,1-np.sum(uv*uv,axis=1))**2*np.maximum(area[ids],1e-12);A=np.c_[np.ones(len(ids)),uv[:,0],uv[:,1],uv[:,0]**2,uv[:,0]*uv[:,1],uv[:,1]**2];w/=max(w.sum(),1e-15);c=np.linalg.solve(A.T@(A*w[:,None])+np.diag([1e-10,1e-5,1e-5,.003,.003,.003]),A.T@(u[ids,1]*w));value=float(np.clip(c[0],np.percentile(u[ids,1],10)-.003,np.percentile(u[ids,1],90)+.003));cache[key]=value;return value
 def surface(q):
  hit=bvh.ray_cast(Vector((q[0],-.50,q[2])),Vector((0,1,0)),1.)[0];return float(hit.y)if hit is not None else field(q)
 return {'p':p,'t':t,'field':field,'surface':surface,'source':str(path)}

def finish_transition(body,sex,ref):
 m=body.data;p=np.array([v.co[:]for v in m.vertices]);keys={k.name:np.array([v.co[:]for v in k.data])for k in m.shape_keys.key_blocks};original={k:v.copy()for k,v in keys.items()};prefix=43900 if sex=='Male'else 34366;assert len(p)==prefix+2880;T=np.array([q.vertices[:]for q in m.polygons]);newmask=np.any(T>=prefix,axis=1);patch=T[newmask];oldEncoded=[tuple(v.value)for v in m.attributes['custom_normal'].data]
 # Compose the independent local forehead repair into the old prefix first.
 if sex=='Female':
  ears=np.load(R/'work/reference-rebuild/face-finish30/forehead-check/ears.npz')['p'];delta=ref['p']-ears
  for name in keys:keys[name][:prefix]+=delta
  p[:prefix]+=delta
 used=np.unique(patch);local=np.full(len(p),-1,int);local[used]=np.arange(len(used));tri=local[patch];rows=(used-prefix)//96%15;fixed=(used<prefix)|((used>=prefix)&(rows<2))|((used>=prefix)&(rows>=13));innerFixed=(used<prefix)|((used>=prefix)&(rows<2));outerSupport=(used>=prefix)&(rows>=13)
 # Positive cotangent weights of the valid constrained Delaunay annulus in X/Z.
 coords=p[used][:,[0,2]];edge={}
 for a,b,c in tri:
  for i,j,k in ((a,b,c),(b,c,a),(c,a,b)):
   va=coords[i]-coords[k];vb=coords[j]-coords[k];cross=abs(va[0]*vb[1]-va[1]*vb[0]);weight=max(.00001,float(va@vb)/max(cross,1e-12));e=tuple(sorted((int(i),int(j))));edge[e]=edge.get(e,0)+weight
 ia=np.array([a for a,b in edge]+[b for a,b in edge],int);ib=np.array([b for a,b in edge]+[a for a,b in edge],int);ww=np.array(list(edge.values())*2);den=np.bincount(ia,weights=ww,minlength=len(used));unknown=~fixed;report={}
 features=bpy.data.objects['ReferenceFeatures'];features.data.calc_loop_triangles();ft=np.array([t.vertices[:]for t in features.data.loop_triangles if 'Brow'not in features.data.materials[t.material_index].name]);fb=np.array([v.co[:]for v in features.data.shape_keys.key_blocks['Basis'].data])
 for name,q in keys.items():
  fv=np.array([v.co[:]for v in features.data.shape_keys.key_blocks[name].data]);fv=fb+2*(fv-fb)if name=='Hero_Blink'else fv;fq=fv[ft];a=fq[:,0][:,[0,2]];b=fq[:,1][:,[0,2]]-a;c=fq[:,2][:,[0,2]]-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];valid=abs(det)>1e-12;limit=np.full(len(used),np.inf)
  for j,i in enumerate(used):
   v=q[i,[0,2]]-a;u=np.divide(v[:,0]*c[:,1]-v[:,1]*c[:,0],det,out=np.zeros(len(det)),where=valid);w=np.divide(b[:,0]*v[:,1]-b[:,1]*v[:,0],det,out=np.zeros(len(det)),where=valid);hit=valid&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1+1e-7)
   if hit.any():limit[j]=float((fq[:,0,1]*(1-u-w)+fq[:,1,1]*u+fq[:,2,1]*w)[hit].min()-.00035)
  base=np.array([ref['field'](q[i])for i in used]);residual=q[used,1]-base
  for j in np.flatnonzero(outerSupport):residual[j]=min(ref['surface'](q[used[j]]),limit[j])-base[j]
  # Initial unknown residual is zero: old spoke interpolation is discarded.
  residual[unknown]=np.minimum(0,limit[unknown]-base[unknown]);last=0
  for it in range(6000):
   target=np.bincount(ia,weights=ww*residual[ib],minlength=len(used))/np.maximum(den,1e-15);target=np.minimum(target,limit-base);change=(target-residual)*.85;last=float(abs(change[unknown]).max());residual[unknown]+=change[unknown]
   if last<2e-8:break
  result=base+residual;q[used[~innerFixed],1]=result[~innerFixed];report[name]={'iterations':it+1,'lastStepMm':last*1000,'maxStripDepthChangeMm':float(abs(q[prefix:,1]-original[name][prefix:,1]).max()*1000)}
 for name,key in zip(keys,m.shape_keys.key_blocks):
  for i,v in enumerate(key.data):v.co=keys[name][i]
 for i,v in enumerate(m.vertices):v.co=keys['Basis'][i]
 m.update()
 # Geometric normals on the corrected strip and its shared join; exact authored
 # normals elsewhere. Runtime coherent shape-normal transport remains required.
 m.normals_split_custom_set([(0,0,0)]*len(m.loops))
 join=set(used.tolist())
 for li,l in enumerate(m.loops):
  if l.vertex_index not in join:m.attributes['custom_normal'].data[li].value=oldEncoded[li]
 # Restore the already-reviewed derivative forehead normals after composition.
 if sex=='Female':
  d=np.load(R/'work/reference-rebuild/face-finish30/forehead-check/repair.npz');n=d['n'];normalVectors=[v.vector[:]for v in m.corner_normals];dirty=[]
  for li,l in enumerate(m.loops):
   i=l.vertex_index
   if i<prefix and p[i,2]>1.595 and p[i,1]<-.020 and i not in join:normalVectors[li]=n[i];dirty.append(li)
  encoded=[tuple(v.value)for v in m.attributes['custom_normal'].data];m.normals_split_custom_set(normalVectors)
  dirty=set(dirty)
  for li in range(len(m.loops)):
   if li not in dirty:m.attributes['custom_normal'].data[li].value=encoded[li]
 m.update()
 protected=used[(used>=prefix)&(rows<2)];rim=np.unique(patch[np.any(patch<prefix,axis=1)]);rim=rim[rim<prefix]
 errs={name:float(np.max(abs(keys[name][protected]-original[name][protected])))for name in keys};assert max(errs.values())==0
 for name in keys:assert np.max(abs(keys[name][:,[0,2]]-original[name][:,[0,2]]))==0
 return {'sex':sex,'vertices':len(p),'triangles':len(T),'originalPrefix':prefix,'protectedFirstTwoRowsErrorMetres':errs,'xzMaxErrorMetres':0,'reference':ref['source'],'shapes':report,'foreheadComposed':sex=='Female'}

if __name__=='__main__':
 report={}
 for sex in ('Male','Female'):
  ref=make_reference(sex);bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/face-finish30-lids/ordered-strip1/{sex}_Face30OrderedLids.blend'));body=bpy.data.objects['Body'];features=bpy.data.objects['ReferenceFeatures']
  spec=importlib.util.spec_from_file_location('clearance',R/'work/reference-rebuild/face-finish30-lids/ordered-strip1/apply-corneal-clearance.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);first=mod.apply_corneal_clearance(body,features,sex);r=finish_transition(body,sex,ref);last=mod.apply_corneal_clearance(body,features,sex);r['cornealGuardBefore']=first;r['cornealGuardAfter']=last
  m=body.data;encoded=[tuple(v.value)for v in m.attributes['custom_normal'].data];prefix=43900 if sex=='Male'else 34366;join=set(i for poly in m.polygons if any(v>=prefix for v in poly.vertices)for i in poly.vertices);m.normals_split_custom_set([(0,0,0)]*len(m.loops))
  for li,l in enumerate(m.loops):
   if l.vertex_index not in join:m.attributes['custom_normal'].data[li].value=encoded[li]
  m.update();out=O/f'{sex}_Face30OrderedSurface.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));report[sex]=r;print('ORDERED_SURFACE',r,flush=True)
 (O/'SOURCE_REPORT.json').write_text(json.dumps(report,indent=2))

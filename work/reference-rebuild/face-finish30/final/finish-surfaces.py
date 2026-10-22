import bpy,pathlib,numpy as np,json,hashlib
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();B=R/'work/reference-rebuild/face-finish30';O=B/'final';report={};caps=json.loads((B/'SCALP_FIT.json').read_text())
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*t*(t*(t*6-15)+10)
def kdfor(p):
 k=KDTree(len(p))
 for i,v in enumerate(p):k.insert(Vector(v),i)
 k.balance();return k
def axes(n):
 a=np.array([0.,0.,1.])if abs(n[2])<.85 else np.array([1.,0.,0.]);u=np.cross(n,a);u/=max(np.linalg.norm(u),1e-12);return u,np.cross(n,u)
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(B/f'{sex}_OriginalFaceFinish30.blend'));body=bpy.data.objects['Body'];m=body.data;original=np.array([tuple(v.co)for v in m.vertices]);oldN=np.array([tuple(v.vector)for v in m.corner_normals]);shapes={k.name:np.array([tuple(v.co)for v in k.data])for k in m.shape_keys.key_blocks};m.calc_loop_triangles();tris=np.array([tuple(t.vertices)for t in m.loop_triangles]);
 _,first,inv=np.unique(np.round(original,6),axis=0,return_index=True,return_inverse=True);p=original[first];norm=np.zeros_like(p);area=np.zeros(len(p))
 for t in tris:
  cr=np.cross(original[t[1]]-original[t[0]],original[t[2]]-original[t[0]])
  for v in t:norm[inv[v]]+=cr;area[inv[v]]+=np.linalg.norm(cr)/6
 norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
 def gp(name):
  gi=body.vertex_groups[name].index;return original[[v.index for v in m.vertices if any(g.group==gi and g.weight>.25 for g in v.groups)]]
 lip=gp('LOOP_mouth_lip_upper'if sex=='Male'else'LOOP_lip_up');nose=np.r_[gp('LOOP_nostril_L'),gp('LOOP_nostril_R')];lz=np.median(lip[:,2]);nz=np.median(nose[:,2]);x,y,z=p.T
 mask=ss(lz+.001,lz+.005,z)*(1-ss(nz+.002,nz+.010,z))*(1-ss(.022,.035,abs(x)))*ss(-.080,-.115,y)
 kd=kdfor(p);hood={}
 for i in np.flatnonzero(mask>.001):
  n=norm[i];u,v=axes(n);radius=.009;js=np.array([j for _,j,d in kd.find_range(Vector(p[i]),radius)if np.dot(norm[j],n)>.20]);q=p[js]-p[i];uv=np.c_[q@u,q@v]/radius;w=np.maximum(0,1-np.sum(uv*uv,axis=1))**2*np.maximum(area[js],1e-12);A=np.c_[np.ones(len(js)),uv[:,0],uv[:,1],uv[:,0]**2,uv[:,0]*uv[:,1],uv[:,1]**2];hood[i]=(js,A,w,n,u,v)
 current=p.copy()
 for repeat in range(4):
  nxt=current.copy()
  for i,(js,A,w,n,u,v)in hood.items():
   if len(js)<9:continue
   c=np.linalg.lstsq(A*np.sqrt(w)[:,None],((current[js]-p[i])@n)*np.sqrt(w),rcond=None)[0];d=(current[i]-p[i])@n;nxt[i]=p[i]+n*np.clip(d+(c[0]-d)*.85*mask[i],-.0009*mask[i],.0009*mask[i])
  current=nxt
 newN={}
 for i,(js,A,w,n,u,v)in hood.items():
  if len(js)<9:continue
  c=np.linalg.lstsq(A*np.sqrt(w)[:,None],((current[js]-p[i])@n)*np.sqrt(w),rcond=None)[0];nn=n-u*c[1]/.009-v*c[2]/.009;newN[i]=nn/max(np.linalg.norm(nn),1e-12)
 result=current[inv].copy();cap=np.zeros(len(result));capNormals=np.zeros_like(result)
 if sex=='Female':
  center=np.array(caps['female']['center']);radii=np.array(caps['female']['radii']);cap=ss(1.605,1.644,result[:,2]);vec=result-center;normed=np.sqrt(np.sum((vec/radii)**2,axis=1));projection=center+vec/np.maximum(normed[:,None],1e-12);diff=projection-result;result+=diff*cap[:,None];capNormals=(projection-center)/(radii*radii);capNormals/=np.maximum(np.linalg.norm(capNormals,axis=1)[:,None],1e-12)
 delta=result-original
 for i,v in enumerate(m.vertices):v.co=result[i]
 for key in m.shape_keys.key_blocks:
  for i,v in enumerate(key.data):v.co=shapes[key.name][i]+delta[i]
 m.update();normals=[]
 for j,loop in enumerate(m.loops):
  i=loop.vertex_index;ui=inv[i];n=oldN[j];f=mask[ui]
  if ui in newN:n=n*(1-f)+newN[ui]*f
  n=n*(1-cap[i])+capNormals[i]*cap[i];n/=max(np.linalg.norm(n),1e-12);normals.append(tuple(n))
 m.normals_split_custom_set(normals);m.update();out=O/f'{sex}_OriginalFaceFinish30Final.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));actual=np.array([tuple(v.co)for v in m.vertices]);err={k.name:float(np.max(abs((np.array([tuple(v.co)for v in k.data])-actual)-(shapes[k.name]-original))))for k in m.shape_keys.key_blocks};assert max(err.values())<2e-7
 report[sex]={'blend':str(out),'lipUpperZ':float(lz),'nostrilZ':float(nz),'subnasalMovedVertices':int(np.count_nonzero(np.linalg.norm(current[inv]-original,axis=1)>1e-8)),'subnasalMaxMm':float(np.max(np.linalg.norm(current[inv]-original,axis=1))*1000),'scalpMaxMm':float(np.max(np.linalg.norm(result-current[inv],axis=1))*1000),'capFullFromZ':1.644,'shapeDeltaErrors':err,'prefixAndTopologyUnchangedFromBroad30':True};print('FINAL_SURFACE',sex,report[sex],flush=True)
(O/'SOURCE_GATE.json').write_text(json.dumps(report,indent=2)+'\n')

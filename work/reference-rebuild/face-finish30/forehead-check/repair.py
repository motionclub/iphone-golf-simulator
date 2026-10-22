import bpy,pathlib,numpy as np,json
from mathutils import Vector
from mathutils.kdtree import KDTree
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/face-finish30/forehead-check';source=R/'work/reference-rebuild/face-finish30/ears/Female_OriginalFaceFinish30Ears.blend';bpy.ops.wm.open_mainfile(filepath=str(source));body=bpy.data.objects['Body'];m=body.data;original=np.array([v.co[:]for v in m.vertices]);baseline=np.load(O/'broad.npz')['p'];assert len(original)==len(baseline);shapes={k.name:np.array([v.co[:]for v in k.data])for k in m.shape_keys.key_blocks};oldN=np.array([v.vector[:]for v in m.corner_normals])
def ss(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*t*(t*(t*6-15)+10)
x,y,z=original.T;front=ss(.10,.60,(-.007932170344725913-y)/.12066881005824304);fade=ss(1.599,1.611,z)*(1-ss(1.668,1.689,z))*front;delta=np.zeros_like(original);delta[:,1]=(baseline[:,1]-original[:,1])*fade;result=original+delta
# Eye operation has an exact unchanged original-index contract.
d=np.load(R/'work/reference-rebuild/face-finish30-lids/female-operation.npz');count=len(d['mask']);assert np.linalg.norm(delta[:count][d['mask']>0],axis=1).max()==0
for i,v in enumerate(m.vertices):v.co=result[i]
for key in m.shape_keys.key_blocks:
 for i,v in enumerate(key.data):v.co=shapes[key.name][i]+delta[i]
m.update();_,first,inv=np.unique(np.round(result,6),axis=0,return_index=True,return_inverse=True);p=result[first];m.calc_loop_triangles();area=np.zeros(len(p))
for t in m.loop_triangles:
 a,b,c=t.vertices;size=np.linalg.norm(np.cross(result[b]-result[a],result[c]-result[a]))/6
 for i in (a,b,c):area[inv[i]]+=size
kd=KDTree(len(p))
for i,q in enumerate(p):kd.insert(Vector(q),i)
kd.balance();fitted={};normalFade=ss(1.595,1.607,p[:,2])*(1-ss(1.680,1.695,p[:,2]))*ss(.1,.65,(-.007932170344725913-p[:,1])/.12066881005824304)
for i in np.flatnonzero(normalFade>.001):
 radius=.014;js=np.array([j for _,j,dist in kd.find_range(Vector(p[i]),radius)if abs(p[j,1]-p[i,1])<.018]);uv=(p[js][:,[0,2]]-p[i,[0,2]])/radius;w=np.maximum(0,1-np.sum(uv*uv,axis=1))**2*np.maximum(area[js],1e-12)
 if len(js)<9:continue
 A=np.c_[np.ones(len(js)),uv[:,0],uv[:,1],uv[:,0]**2,uv[:,0]*uv[:,1],uv[:,1]**2];c=np.linalg.lstsq(A*np.sqrt(w)[:,None],p[js,1]*np.sqrt(w),rcond=None)[0];nn=np.array([c[1]/radius,-1,c[2]/radius]);fitted[i]=nn/np.linalg.norm(nn)
ns=[]
for li,loop in enumerate(m.loops):
 i=inv[loop.vertex_index];f=normalFade[i] if i in fitted else 0;n=oldN[li]*(1-f)+fitted.get(i,oldN[li])*f;n/=max(np.linalg.norm(n),1e-12);ns.append(tuple(n))
m.normals_split_custom_set(ns);m.update();out=O/'Female_OriginalFaceFinish30Forehead.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out));normal=np.zeros_like(result)
for li,loop in enumerate(m.loops):normal[loop.vertex_index]+=ns[li]
normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12);np.savez_compressed(O/'repair.npz',p=result,t=np.array([t.vertices[:]for t in m.loop_triangles]),n=normal)
report={'source':str(source),'candidate':str(out),'movedVertices':int((np.linalg.norm(delta,axis=1)>1e-8).sum()),'maxDepthCorrectionMm':float(abs(delta[:,1]).max()*1000),'maxXZCorrectionMm':0,'eyeActivePositionErrorMm':0,'method':'Restore original smooth front-depth profile locally, retaining ellipse XZ round silhouette; recompute matching front normals','bounds':[[float(v)for v in original[np.linalg.norm(delta,axis=1)>1e-8].min(axis=0)],[float(v)for v in original[np.linalg.norm(delta,axis=1)>1e-8].max(axis=0)]]};(O/'SOURCE_GATE.json').write_text(json.dumps(report,indent=2));print(report)

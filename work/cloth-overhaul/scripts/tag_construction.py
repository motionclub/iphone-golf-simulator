"""Construction regions follow actual component geometry rather than bounding boxes on the upper."""
import bpy,sys,numpy as np
from pathlib import Path
W=Path(sys.argv[sys.argv.index('--')+1])/'work/cloth-overhaul'
def components(m):
 adj=[[] for v in m.vertices]
 for e in m.edges:
  a,b=e.vertices;adj[a].append(b);adj[b].append(a)
 seen=set();out=[]
 for i in range(len(adj)):
  if i in seen:continue
  q=[i];seen.add(i);c=[]
  while q:
   v=q.pop();c.append(v)
   for j in adj[v]:
    if j not in seen:seen.add(j);q.append(j)
  out.append(c)
 return out
for sex in ['Male','Female']:
 bpy.ops.wm.open_mainfile(filepath=str(W/f'export/Cloth_{sex}.blend'))
 for o in bpy.data.objects:
  path=W/f'export/{sex}_{o.name}.npz'
  if o.type!='MESH' or not path.exists():continue
  z=np.load(path);data={k:z[k] for k in z.files};P=data['P'];zone=np.full(len(P),-1,np.float32);tr=np.zeros(len(P),np.float32)
  for ids in components(o.data):
   q=P[ids];lo=q.min(0);hi=q.max(0)
   if o.name=='Kit_Top' and 200<len(ids)<300 and lo[2]>1.08 and np.abs(q[:,0].mean())>.12:
    zone[ids]=1
    # The cuff's narrow thickness axis follows the sleeve opening plane.
    _,v=np.linalg.eigh(np.cov(q.T));axis=v[:,0]
    if axis[2]>0:axis=-axis
    t=q@axis;distance=t.max()-t;tr[ids]=1  # entire existing 7 mm turned cuff is the thin rib trim band
   if 'Shoe' in o.name and hi[1]<.05 and lo[2]>.025 and len(ids)<=80:
    zone[ids]=3 if len(ids)==14 else 5
    if len(ids)==14:tr[ids]=1
  if o.name=='Kit_Bottom' and sex=='Male':
   tips=(np.abs(P[:,0])<.04)&(P[:,1]<-.185)&(P[:,2]<.902)&(P[:,2]>.886);tr[tips]=1
  data['zone']=zone;data['zoneTrim']=tr;np.savez(path,**data)
 print('TAGGED',sex,flush=True)

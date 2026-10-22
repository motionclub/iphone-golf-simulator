"""Composable operation. Import and call apply_lids(body, sex); caller saves/exports.
No topology changes. Requires frozen Smooth1 original vertex prefix and its eyelid region unchanged.
"""
import bpy,numpy as np
from pathlib import Path
O=Path(__file__).resolve().parent

def apply_lids(body,sex):
 d=np.load(O/f'{sex.lower()}-operation.npz');me=body.data;count=len(d['before']);assert len(me.vertices)>=count
 mask=d['mask'];ids=np.flatnonzero(mask>0);before=np.array([v.co[:] for v in me.vertices[:count]])
 error=float(np.linalg.norm(before[ids]-d['before'][ids],axis=1).max());assert error<1e-6,('Eyelid source conflict',sex,error)
 originalCustom=[tuple(x.value) for x in me.attributes['custom_normal'].data]
 for key in me.shape_keys.key_blocks:
  if key.name not in d.files:continue
  delta=d[key.name]
  for i in np.flatnonzero(np.linalg.norm(delta,axis=1)>1e-10):key.data[int(i)].co+=__import__('mathutils').Vector(delta[i])
 for i in np.flatnonzero(np.linalg.norm(d['Basis'],axis=1)>1e-10):me.vertices[int(i)].co+=__import__('mathutils').Vector(d['Basis'][i])
 me.update();me.normals_split_custom_set([(0,0,0)]*len(me.loops))
 for li,loop in enumerate(me.loops):
  i=loop.vertex_index
  if i>=count or mask[i]<=0:me.attributes['custom_normal'].data[li].value=originalCustom[li]
  if i<count and d['rimPigment'][i]>0:
   old=np.clip((np.array(me.uv_layers[0].data[li].uv)*64-.5)/63,0,1);old[1]=max(old[1],d['rimPigment'][i]);me.uv_layers[0].data[li].uv=(.5+63*old)/64
 me.update();return {'sex':sex,'originalPrefix':count,'activeEyelidSourceConflictMetres':error,'changedBasisVertices':int(np.count_nonzero(np.linalg.norm(d['Basis'],axis=1)>1e-10))}

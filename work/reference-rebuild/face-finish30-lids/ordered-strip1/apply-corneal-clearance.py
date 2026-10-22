"""Ensure the authored lid surface covers the actual curved eye sheets.
Local source operation; no eye-part, X/Z, weight, rig, material or topology edits.
Body front is negative Y in the original model. Full is checked against runtime's
existing doubled eye-part retreat. Compose after surface fairing.
"""
import numpy as np
from pathlib import Path
O=Path(__file__).resolve().parents[1]
def apply_corneal_clearance(body,features,sex):
 prefix=43900 if sex=='Male'else 34366
 inner=np.unique(np.load(O/f'{sex.lower()}-lids.npz')['edges']);ids=np.r_[inner,np.arange(prefix,len(body.data.vertices))]
 features.data.calc_loop_triangles();tri=np.array([t.vertices[:]for t in features.data.loop_triangles if 'Brow'not in features.data.materials[t.material_index].name],int)
 report={};fkeys=features.data.shape_keys.key_blocks;bkeys=body.data.shape_keys.key_blocks
 for name in ['Basis','Hero_Blink_Half','Hero_Blink']:
  f=np.array([v.co[:]for v in fkeys[name].data]);base=np.array([v.co[:]for v in fkeys['Basis'].data])
  if name=='Hero_Blink':f=base+2*(f-base)
  q=f[tri];a=q[:,0][:,[0,2]];b=q[:,1][:,[0,2]]-a;c=q[:,2][:,[0,2]]-a;den=b[:,0]*c[:,1]-b[:,1]*c[:,0];valid=abs(den)>1e-12
  changed=0;maximum=0
  for i in ids:
   point=bkeys[name].data[int(i)].co;v=np.array([point.x,point.z])-a
   u=np.divide(v[:,0]*c[:,1]-v[:,1]*c[:,0],den,out=np.zeros(len(den)),where=valid);w=np.divide(b[:,0]*v[:,1]-b[:,1]*v[:,0],den,out=np.zeros(len(den)),where=valid)
   hit=valid&(u>=-1e-7)&(w>=-1e-7)&(u+w<=1+1e-7)
   if not hit.any():continue
   eyeY=(q[:,0,1]*(1-u-w)+q[:,1,1]*u+q[:,2,1]*w)[hit].min();target=eyeY-.00035
   if point.y>target:
    maximum=max(maximum,point.y-target);point.y=float(target);changed+=1
  report[name]={'changed':changed,'maxForwardMm':maximum*1000}
 # Basis shape and mesh point arrays are separate storage in this source contract.
 for i in ids:body.data.vertices[int(i)].co=bkeys['Basis'].data[int(i)].co
 body.data.update();return {'sex':sex,'frames':report,'featureGeometryUnchanged':True,'otherAxesUnchanged':True}

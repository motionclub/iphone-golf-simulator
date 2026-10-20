from pathlib import Path
import json,ctypes
import numpy as np
from PIL import Image
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';p=json.loads((O/'UnderarmGusset_Female_Full.json').read_text());top=next(x for x in json.loads((R/'proof/reference-rebuild/gusset-bodyband-connect4/poses/female_intro.json').read_text())['parts'] if x['name']=='Kit_Top');m=np.array(top['rendererToRoot']).reshape(4,4);v=np.array(top['posedVertices']).reshape(-1,3)@m[:3,:3].T+m[:3,3];n=np.array(top['posedNormals']).reshape(-1,3)@m[:3,:3].T;t=np.array(top['triangles']).reshape(-1,3).astype(np.int32);pt=np.array(p['triangles']).reshape(-1,3);lookup={tuple(x):i for i,x in enumerate(pt)}
cam=np.array([0,.94,3.6]);target=np.array([0,.88,0]);fw=target-cam;fw/=np.linalg.norm(fw);right=np.cross([0,1,0],fw);right/=np.linalg.norm(right);up=np.cross(fw,right);z=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32);d=v-cam;dp=d@fw;scale=600/np.tan(np.deg2rad(15));xy=np.ascontiguousarray(np.column_stack([450+d@right/dp*scale,600-d@up/dp*scale,dp]));lib=ctypes.CDLL(str(R/'work/reference-rebuild/garment-weight-transition/mask3/raster-front.dylib'));lib.draw.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int];lib.draw(xy.ctypes.data,t.ctypes.data,len(t),900,1200,z.ctypes.data,ids.ctypes.data,0)
im=np.array(Image.open(R/'proof/reference-rebuild/gusset-bodyband-connect4/female_current_intro.png').convert('RGB'));roi=np.zeros(ids.shape,bool);roi[410:446,545:582]=True;dark=roi&(im[:,:,1]<255)&(im[:,:,1]>im[:,:,0])&(ids>=0);faces,cnt=np.unique(ids[dark],return_counts=True);order=np.argsort(-cnt);a=json.loads((O/'bodyband-prototype-Full.json').read_text());bodyoff=np.array(p['bodyOffsets']);rows=[]
for j in order[:15]:
 f=int(faces[j]);source=lookup[tuple(t[f])];vv=t[f];gn=np.cross(v[vv[1]]-v[vv[0]],v[vv[2]]-v[vv[0]]);gn/=np.linalg.norm(gn);nn=n[vv]/np.linalg.norm(n[vv],axis=1)[:,None];group='retained'
 if np.all(bodyoff[vv]>.003):group='copied Body outer'
 elif np.all((bodyoff[vv]>0)&(bodyoff[vv]<.003)):group='copied Body lining'
 elif np.any(bodyoff[vv]>.003):group='outer connector'
 elif np.any(bodyoff[vv]>0):group='lining connector'
 rows.append({'actualFace':f,'profileFace':source,'pixels':int(cnt[j]),'group':group,'vertices':vv.tolist(),'bodyOffsets':bodyoff[vv].tolist(),'originalSourceParent':int(p['triangleSourceFaces'][source]),'normalVsFaceDegrees':np.degrees(np.arccos(np.clip(nn@gn,-1,1))).tolist(),'maximumEdgeMetres':float(np.linalg.norm(v[vv]-v[np.roll(vv,1)],axis=1).max())})
(O/'remaining-connect4-fold.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))

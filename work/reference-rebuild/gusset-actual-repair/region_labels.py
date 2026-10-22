from pathlib import Path
import json,ctypes
import numpy as np
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'work/reference-rebuild/gusset-actual-repair';p=json.loads((O/'UnderarmGusset_Female_Full.json').read_text());pt=np.array(p['triangles']).reshape(-1,3);lookup={tuple(x):i for i,x in enumerate(pt)};off=np.array(p['bodyOffsets']);mirror=np.array(p['mirroredVertices']);cats=[]
for t in pt:
 if np.all(mirror[t]):c=5
 elif np.all(off[t]>.003):c=1
 elif np.all((off[t]>0)&(off[t]<.003)):c=2
 elif np.any(off[t]>.003):c=3
 elif np.any(off[t]>0):c=4
 else:c=0
 cats.append(c)
cats=np.array(cats);colors=np.array([[100,145,200],[112,190,88],[241,151,53],[43,219,220],[207,90,218],[242,218,65]],np.uint8);names=['Retained source','Body outer','Body lining','Outer connector','Lining connector','Mirrored cuff'];lib=ctypes.CDLL(str(R/'work/reference-rebuild/garment-weight-transition/mask3/raster-front.dylib'));lib.draw.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int]
for label in ['female_intro','female_Forehand_0','female_Forehand_1']:
 top=next(x for x in json.loads((R/f'proof/reference-rebuild/gusset-bodyband-cuff2/poses/{label}.json').read_text())['parts'] if x['name']=='Kit_Top');m=np.array(top['rendererToRoot']).reshape(4,4);v=np.array(top['posedVertices']).reshape(-1,3)@m[:3,:3].T+m[:3,3];t=np.array(top['triangles']).reshape(-1,3).astype(np.int32);mapping=np.array([lookup[tuple(x)] for x in t]);c=cats[mapping]
 cam=np.array([0,.94,3.6]) if label=='female_intro' else np.array([2.4,1.3,4.1]);target=np.array([0,.88,0]) if label=='female_intro' else np.array([0,.83,.1]);fov=15 if label=='female_intro' else 17;fw=target-cam;fw/=np.linalg.norm(fw);right=np.cross([0,1,0],fw);right/=np.linalg.norm(right);up=np.cross(fw,right);z=np.full((1200,900),np.inf);ids=np.full((1200,900),-1,np.int32);d=v-cam;dp=d@fw;scale=600/np.tan(np.deg2rad(fov));xy=np.ascontiguousarray(np.column_stack([450+d@right/dp*scale,600-d@up/dp*scale,dp]));lib.draw(xy.ctypes.data,t.ctypes.data,len(t),900,1200,z.ctypes.data,ids.ctypes.data,0);im=np.full((1200,900,3),230,np.uint8);hit=ids>=0;im[hit]=colors[c[ids[hit]]]
 # Flat labeled render uses actual baked vertices and actual face visibility.
 plate=Image.fromarray(im);draw=ImageDraw.Draw(plate)
 for k,name in enumerate(names):draw.rectangle((20,20+k*22,34,34+k*22),fill=tuple(colors[k]));draw.text((42,20+k*22),name,fill=(0,0,0))
 plate.save(O/f'region_{label}.png')

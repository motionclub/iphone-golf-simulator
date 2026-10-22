"""Paired cast/no-cast foot support using exact shoe IDs, not actor bounds."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
w=Path(__file__).resolve().parents[1];sys.path.insert(0,str(w/'python-deps'));import cv2
d=w/'proof/course_kit_final_r34';out=w/'proof/contact_shadow_r34';out.mkdir(exist_ok=True);rows=[]
for hole in [7,8,9,10]:
 for sex in ['male','female']:
  stem=f'hole{hole:02}_{sex}_fullbody';a=np.asarray(Image.open(d/(stem+'.png')).convert('RGB'));b=np.asarray(Image.open(d/(stem+'_nocast.png')).convert('RGB'))
  actor=np.asarray(Image.open(d/(stem+'_semantic.png')).convert('RGB'));ids=np.asarray(Image.open(d/(stem+'_shoes_semantic.png')).convert('RGB'))
  dark=(b.astype(float)-a.astype(float)).mean(2);occluder=np.max(actor,2)>5;overlay=a.copy();feet=[]
  for label,c in [('left',[255,0,0]),('right',[0,255,0])]:
   m=np.max(abs(ids.astype(int)-np.array(c)),2)<4
   roi=(cv2.dilate(m.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(71,71)))>0)&~occluder
   mask=roi&(dark>1.0);overlay[mask]=[255,0,255]
   feet.append(dict(foot=label,shoePixels=int(m.sum()),contactPixels=int(mask.sum()),meanDarkeningBytes=float(dark[mask].mean()) if mask.any() else None,status='PASS' if mask.sum()>=10 else 'FAIL'))
  Image.fromarray(overlay).save(out/(stem+'_contact_overlay.png'));row=dict(hole=hole,sex=sex,feet=feet,status='PASS' if all(f['status']=='PASS' for f in feet) else 'FAIL');rows.append(row);print(row,flush=True)
(w/'data/contact_shadow_r34.json').write_text(json.dumps(dict(protocol='exact visible left/right shoe identities, 35px dilation, excludes every hero surface, paired shadow-cast-only difference >1 mean RGB byte, minimum10 contact pixels per foot',rows=rows),indent=2))

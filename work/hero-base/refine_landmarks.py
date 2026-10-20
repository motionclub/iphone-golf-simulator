from pathlib import Path
import sys,numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,'Tools/HeroBase')
from plate_profiles import MALE,FEMALE
# Source polygons are untouched. Only authoring profiles are refitted to the front/back measurements.
out=['\n# Refined shared limb profiles measured from the locked front/back polygon traces.']
for name,pr,start,end,step in [('MALE',MALE,425,680,15),('FEMALE',FEMALE,410,676,15)]:
 masks=[]
 for view in ['front','back']:
  im=Image.new('L',(1280,720));ImageDraw.Draw(im).polygon(pr[view+'_outline'],fill=255);a=np.array(im)>0;cx=pr['cx' if view=='front' else 'back_cx'];masks.append((a,cx))
 rows=[]
 for y in list(range(start,end-5,step))+[end-10,end-5,end-2,end]:
  bounds=[]
  for a,cx in masks:
   yy=y
   while not a[yy].any() and yy>start:yy-=1
   ids=np.where(a[yy])[0]-cx;sp=np.where(np.diff(ids)>1)[0]+1
   for group in np.split(ids,sp):
    if len(group)<2:continue
    if group[-1]<0:bounds.append((-float(group[-1]),-float(group[0])))
    elif group[0]>0:bounds.append((float(group[0]),float(group[-1])))
  if len(bounds)<2:continue
  inner,outer=np.mean(bounds,axis=0);c=(inner+outer)/2;w=(outer-inner)/2
  depth=float(np.interp(y,[r[0] for r in pr['leg']],[r[3] for r in pr['leg']]))
  if y==end:w=8 if name=='MALE' else 5
  rows.append((y,round(c,2),round(w,2),round(depth,2)))
 prefix=[(397,42,40,39),(410,44,42,42)] if name=='MALE' else [(382,33,28,33),(397,33,29,34)]
 out.append(name+"['leg']="+repr(prefix+rows))
out.append("MALE['torso']=[(175,33,24),(184,45,31),(194,77,42),(208,92,52),(228,92,53),(248,84,54),(273,80,50),(300,78,44),(330,73,40),(355,74,42),(381,81,48),(402,86,48)]")
out.append("FEMALE['torso']=[(198,17,18),(205,26,22),(213,43,30),(226,55,34),(242,53,38),(260,48,38),(278,44,34),(298,40,29),(315,41,28),(333,45,33),(350,50,40),(371,56,46),(389,61,44)]")
out.append("MALE['arm_sections']=[(190,65,1,1),(200,82,18,23),(210,93,18,30),(230,104,19,32),(250,113,24,30),(270,120,32,29),(290,130,37,28),(300,139,37,27),(315,151,37,26),(330,164,35,25),(350,182,31,23),(370,208,22,18),(385,223,15,14),(395,236,11,10),(412,247,4,4),(417,249,1,1)]")
out.append("FEMALE['arm_sections']=[(211,43,1,1),(220,53,10,13),(240,60,12,16),(270,62,13,15),(300,66,14,14),(330,72,14,14),(350,77,13,13),(370,82,11,12),(385,85,10,10),(394,85,8,9),(400,85,1,1)]")
p=Path('Tools/HeroBase/plate_profiles.py');p.write_text(p.read_text()+'\n'.join(out)+'\n')
print('\n'.join(out))

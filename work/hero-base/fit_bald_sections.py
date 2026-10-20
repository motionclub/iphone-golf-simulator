from pathlib import Path
import numpy as np,sys
from PIL import Image,ImageDraw
sys.path.insert(0,'Tools/HeroBase');from plate_profiles import MALE,FEMALE
out=['\n# Further authoring-section measurements; the two source target polygons remain unchanged.']
for name,p in [('MALE',MALE),('FEMALE',FEMALE)]:
 masks=[]
 for view in ['front','back']:
  im=Image.new('L',(1280,720));ImageDraw.Draw(im).polygon(p[view+'_outline'],fill=255);masks.append((np.array(im)>0,p['cx' if view=='front' else 'back_cx']))
 def groups(a,y,cx):
  ids=np.where(a[y])[0]-cx;sp=np.where(np.diff(ids)>1)[0]+1;return [t for t in np.split(ids,sp) if len(t)]
 lr=p['leg'][:2]
 for y in list(range(410 if name=='MALE' else 420,p['sole']-12,15))+[p['sole']-10,p['sole']-5,p['sole']-2,p['sole']]:
  vals=[]
  for a,cx in masks:
   yy=y
   while not a[yy].any() and yy>400:yy-=1
   for q in groups(a,yy,cx):
    if q[-1]<0:vals.append((-float(q[-1]),-float(q[0])))
    elif q[0]>0:vals.append((float(q[0]),float(q[-1])))
  if len(vals)<2:continue
  inner,outer=np.mean(vals,axis=0);c=float((inner+outer)/2);w=float((outer-inner)/2)
  d=float(np.interp(y,[r[0] for r in p['leg']],[r[3] for r in p['leg']]))
  lr.append((y,round(c,2),round(w if y<p['sole'] else 6,2),round(d,2)))
 if lr[-1][0]<p['sole']:lr.append((p['sole'],lr[-1][1],6,lr[-1][3]))
 out.append(name+"['leg']="+repr(lr))
 arms=p['arm_sections'];start=240 if name=='MALE' else 240;end=340 if name=='MALE' else 360
 ar=[r for r in arms if r[0]<start]
 for y in range(start,end+1,10):
  vals=[]
  for a,cx in masks:
   qs=groups(a,y,cx)
   if len(qs)<3:continue
   for q in (qs[0],qs[-1]):
    if q[-1]<0:vals.append((-float(q[-1]),-float(q[0])))
    elif q[0]>0:vals.append((float(q[0]),float(q[-1])))
  if len(vals)<2:continue
  inner,outer=np.mean(vals,axis=0);c=float((inner+outer)/2);w=float((outer-inner)/2);d=float(np.interp(y,[r[0] for r in arms],[r[3] for r in arms]))
  ar.append((y,round(c,2),round(w,2),round(d,2)))
 ar += [r for r in arms if r[0]>end]
 out.append(name+"['arm_sections']="+repr(ar))
out += ["MALE['torso']=[(159,20,20),(167,42,28),(177,65,37),(189,83,43),(209,88,46),(230,76,47),(251,69,46),(278,64,41),(300,62,36),(322,66,39),(342,70,42),(363,72,46),(380,74,45)]", "FEMALE['torso']=[(137,15,17),(147,32,24),(157,49,30),(172,60,36),(190,59,38),(211,53,37),(235,45,35),(258,42,31),(281,43,31),(306,50,36),(329,57,43),(350,63,46),(365,65,42)]", "MALE.update(eye_r=6.5,eye_ry=4.0,iris_x=3.6,iris_y=4.0,pupil_x=2.3,pupil_y=2.7,nose_depth=8.7,nose_w=6.0)", "FEMALE.update(iris_x=5.8,iris_y=6.8,pupil_x=3.8,pupil_y=4.4,nose_depth=6.5,nose_w=5.0)"]
q=Path('Tools/HeroBase/plate_profiles.py');q.write_text(q.read_text()+'\n'.join(out)+'\n')
q=Path('Tools/HeroBase/build_static.py');s=q.read_text();s=s.replace("material('Iris_Dark',(.19,.13,.085),.31)","material('Iris_Dark',(.10,.062,.035),.52)").replace("material('Pupil',(.026,.024,.022),.22)","material('Pupil',(.006,.006,.005),.40)")
s=s.replace("g=Geo('Body_'+suffix,mats);n=48", "mats[3].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.08; mats[4].node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.05\n    g=Geo('Body_'+suffix,mats);n=48")
s=s.replace("        return base\n    for j", "        base+=1.8*math.exp(-(x/9)**2-((y-(profile['mouth_y']-1))/2.8)**2)+1.2*math.exp(-(x/10)**2-((y-(profile['mouth_y']+2.2))/2.4)**2)\n        base+=(13 if not female else 18)*max(0,min(1,(y-(profile['mouth_y']+6))/17))**2\n        return base\n    for j")
s=s.replace("scene.world.node_tree.nodes['Background'].inputs[1].default_value=.50", "scene.world.node_tree.nodes['Background'].inputs[1].default_value=.34")
s=s.replace("area('Neutral_Key',(-2.8,-3.4,4),260,4);area('Neutral_Fill',(2.6,-1.8,2),120,3);area('Neutral_Back',(0,2.6,3),180,3)", "area('Neutral_Key',(-2.8,-3.4,4),300,4);area('Neutral_Fill',(2.6,-1.8,2),145,3);area('Neutral_Back',(0,2.6,3),70,3)")
q.write_text(s)

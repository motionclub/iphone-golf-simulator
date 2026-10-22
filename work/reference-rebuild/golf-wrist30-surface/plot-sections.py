from section_analysis import *
from PIL import Image,ImageDraw
im=Image.new('RGB',(1200,1000),'white');draw=ImageDraw.Draw(im)
for panel,label in enumerate(['female_Putter_address','female_Driver_top','male_Putter_address','male_Driver_top']):
 p,v,posed,w,ix,b,m,n,tr,rest,cur,dense=load(label);posed/=1.0936;L,H,M=[n.index('Right'+x) for x in ['LowerArm','Hand','MiddleProximal']];axis=rest[H,:3,3]-rest[L,:3,3];axis/=np.linalg.norm(axis);along=(v-rest[H,:3,3])@axis;sel=(dense[:,L]+dense[:,H]>.99)&(along>-.13)&(along<.08);u=cur[H,:3,3]-cur[L,:3,3];u/=np.linalg.norm(u);pp=cur[M,:3,3]-cur[H,:3,3];yy=pp-u*(pp@u);yy/=np.linalg.norm(yy)
 xy=np.stack([u,yy],axis=1);points=(posed-cur[H,:3,3])@xy*1000;
 def screen(pt): return tuple((np.array([40+(panel%2)*600+pt[0]*2.1+300,450+(panel//2)*500-pt[1]*2.1])).astype(int))
 draw.text((20+(panel%2)*600,20+(panel//2)*500),label,fill='black')
 for pt,wgt in zip(points[sel],dense[sel,H]):
  x,y=screen(pt);draw.ellipse((x-2,y-2,x+2,y+2),fill=(int(40+215*wgt),30,int(255-215*wgt)))
 bone=(cur[[L,H,M],:3,3]-cur[H,:3,3])@xy*1000;draw.line([screen(pt) for pt in bone],fill='black',width=3)
 for s in [-.08,-.06,-.04,-.02,0,.02,.04,.06]:
  cross=[]
  for face in tr:
   if not sel[face].any():continue
   st=along[face]-s
   if st.min()>0 or st.max()<0:continue
   for i,j in [(0,1),(1,2),(2,0)]:
    if st[i]*st[j]<0:
     q=st[i]/(st[i]-st[j]);cross.append(posed[face[i]]*(1-q)+posed[face[j]]*q)
  if cross:
   pts=(np.array(cross)-cur[H,:3,3])@xy*1000;ct=pts.mean(0);draw.text(screen(ct),str(round(s*1000)),fill='black')
im.save(O/'actual-wrist-sections.png')

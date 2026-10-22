"""World-space front/side motion trails, orthographic millimetre coordinates, no synthetic art."""
from pathlib import Path
import sys,json,math,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont
W=Path(os.environ.get('FLUID_WORK',str(Path(__file__).resolve().parents[1])))
FONT='/System/Library/Fonts/Menlo.ttc'
def font(s):return ImageFont.truetype(FONT,s)
COL={'LeftHand':'#1da6ff','RightHand':'#f4a024','HeadTop':'#ef64ba','Hips':'#77dc89'}
phase=sys.argv[1] if len(sys.argv)>1 else 'before';out=W/'film'/('trails_'+phase);out.mkdir(exist_ok=True)
for path in sorted((W/'data'/phase).glob('trace_*.npz')):
 z=np.load(path);meta=json.loads(str(z['meta']));
 if meta.get('clip')=='ReadyIdle':continue
 ix={n:i for i,n in enumerate(meta['bones'])};pts={n:z['M'][:,ix[n],:3,3] for n in ['LeftHand','RightHand','Hips']};pts['HeadTop']=z['HEADTOP'];im=Image.new('RGB',(1400,900),'#121b28');d=ImageDraw.Draw(im)
 d.text((30,20),f"{phase.upper()} / {meta['hero']} / {meta['clip']} / 30 fps / frame markers every 6",font=font(21),fill='white')
 for view,(u,v) in enumerate([(0,2),(1,2)]):
  left=35+view*700;top=100;width=650;height=690;allp=np.concatenate(list(pts.values()));mn=allp[:,[u,v]].min(0)-.08;mx=allp[:,[u,v]].max(0)+.08;scale=min(width/(mx[0]-mn[0]),height/(mx[1]-mn[1]))
  def xy(p):return (left+(p[u]-mn[0])*scale,top+height-(p[v]-mn[1])*scale)
  d.text((left,67),'FRONT (world X/Z)' if view==0 else 'SIDE (world Y/Z)',font=font(20),fill='white')
  for meter in np.arange(math.floor(mn[1]*10)/10,mx[1],.1):
   yy=top+height-(meter-mn[1])*scale;d.line((left,yy,left+width,yy),fill='#273344');d.text((left,yy),f'{meter*1000:.0f} mm',font=font(10),fill='#8190a6')
  for nm,p in pts.items():
   pp=[xy(x) for x in p];d.line(pp,fill=COL[nm],width=2)
   for f in range(0,len(p),6):
    x,y=pp[f];d.ellipse((x-3,y-3,x+3,y+3),fill=COL[nm]);d.text((x+4,y+3),str(f),font=font(9),fill=COL[nm])
   x,y=pp[0];d.rectangle((x-5,y-5,x+5,y+5),outline='white',width=2)
 for j,(nm,c) in enumerate(COL.items()):d.text((35+340*j,840),nm,font=font(20),fill=c)
 im.save(out/(meta['hero']+'_'+meta['clip']+'.png'))
print('TRAIL_SHEETS',phase,12)

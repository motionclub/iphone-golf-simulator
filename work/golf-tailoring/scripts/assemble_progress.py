from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
W=Path(__file__).resolve().parents[1];D=W/'proof/followthrough/swing';O=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-3/outputs');O.mkdir(exist_ok=True);(D/'combined').mkdir(exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',28);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
sequence=[0]*12+list(range(105))+[104]*18;gif=[];bounds=[]
for n,i in enumerate(sequence):
 frame=Image.new('RGB',(1800,1080),(40,47,55));draw=ImageDraw.Draw(frame)
 for x,sex in [(0,'Male'),(900,'Female')]:
  im=Image.open(D/sex/f'{i:04}.png').convert('RGB');frame.paste(im,(x,60));draw.text((x+34,18),sex+' golf outfit',font=font,fill='#eef2f4')
  if n>=12 and n<117:
   diff=ImageChops.difference(im,Image.new('RGB',im.size,im.getpixel((0,0))));bbox=diff.getbbox();bounds.append((sex,i,bbox))
 draw.line((900,12,900,1060),fill=(66,74,82),width=2)
 frame.save(D/'combined'/f'{n:04}.png')
 preview=frame.resize((1000,600),Image.Resampling.LANCZOS);gif.append(preview.quantize(colors=128,method=Image.Quantize.MEDIANCUT))
# A repeating 30/30/40ms cadence retains the source's 30 fps in GIF's centisecond clock.
gif[0].save(O/'Golf_progress_01.gif',save_all=True,append_images=gif[1:],duration=[30,30,40]*(len(gif)//3)+[30]*(len(gif)%3),loop=0,optimize=False,disposal=2)
for sex in ['Male','Female']:
 rows=[x for x in bounds if x[0]==sex];clipped=[x for x in rows if x[2] and (x[2][0]<2 or x[2][1]<2 or x[2][2]>898 or x[2][3]>998)]
 print(sex,'frames',len(rows),'edge contacts',clipped[:10])
print('ASSEMBLED',len(sequence))

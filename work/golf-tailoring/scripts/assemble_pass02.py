from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[1];D=W/'proof/pass02';font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',27)
for view,mode,sequence in [('swing','full',[0]*12+list(range(105))+[104]*18),('side','transition',[70]*12+[i for i in range(70,96) for _ in range(4)]+[95]*18)]:
 out=D/mode;out.mkdir(exist_ok=True)
 for n,i in enumerate(sequence):
  frame=Image.new('RGB',(1800,1080),(40,47,55));draw=ImageDraw.Draw(frame)
  for x,sex in [(0,'Male'),(900,'Female')]:
   frame.paste(Image.open(D/view/sex/f'{i:04}.png').convert('RGB'),(x,60))
   speed='normal speed' if mode=='full' else 'side · quarter speed'
   draw.text((x+25,18),f'Pass 2 · {sex} · F{i+1:03} · {speed}',font=font,fill='#f5d179' if 76<=i<=89 else '#eef2f4')
  draw.line((900,12,900,1060),fill=(66,74,82),width=2)
  frame.save(out/f'{n:04}.png')
 print('ASSEMBLED',mode,len(sequence),flush=True)

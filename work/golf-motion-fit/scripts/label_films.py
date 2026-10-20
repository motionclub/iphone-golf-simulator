from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,sys
W=Path(__file__).resolve().parents[1];font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',13)
sheets='--sheets' in sys.argv
for folder in sorted((W/('sheet-frames' if sheets else 'film-frames')).iterdir()):
 filters=[x for x in sys.argv[1:] if not x.startswith('--')]
 if filters and not any(x in folder.name for x in filters):continue
 meta=folder/'metadata.json'
 if not meta.exists():continue
 frames=sorted(folder.glob('[0-9][0-9][0-9][0-9].png'))
 for i,p in enumerate(frames):
  img=Image.open(p).convert('RGB');draw=ImageDraw.Draw(img)
  for view,label in enumerate(['0°','45°','90°','135°','180°','225°','270°','315°','Overhead','Hands','Waist','360°']):
   col,row=view%4,view//4;x,y=col*240,row*240
   if view in [9,10]:
    close=W/('sheet-scratch' if sheets else 'film-scratch')/folder.name/(p.stem+'_'+('hands' if view==9 else 'waist')+'.png')
    if close.exists():img.paste(Image.open(close).convert('RGB'),(x,y))
   draw.rectangle((x,y,x+239,y+21),fill=(22,29,38));draw.text((x+7,y+3),label,font=font,fill='white')
  draw.rectangle((0,696,960,720),fill=(22,29,38));draw.text((8,699),folder.name+'  ·  '+(f"{json.loads(meta.read_text())['labels'][i]} · {json.loads(meta.read_text())['times'][i]:.3f} s" if sheets else f'{i/15:.2f} s'),font=font,fill='white');img.save(p)
 if sheets:
  target=W/'sheets';target.mkdir(exist_ok=True);canvas=Image.new('RGB',(1920,1440))
  for i,p in enumerate(frames):canvas.paste(Image.open(p).convert('RGB'),((i%2)*960,(i//2)*720))
  canvas.save(target/(folder.name+'.png'))
 print('LABELLED',folder.name,len(frames),flush=True)

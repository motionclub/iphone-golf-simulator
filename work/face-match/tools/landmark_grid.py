from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
r=Path(__file__).resolve().parents[1];stage=sys.argv[1]
f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12)
for sex in ['male','female']:
 ref=Image.open('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/reference-check/'+sex+'-target.png').convert('RGB')
 raw=Image.open(r/stage/'raw'/f'{sex}_front.png')
 scale=202/592 if sex=='male' else 195/625;crown=208 if sex=='male' else 155;center=132 if sex=='male' else 173
 ours=raw.transform(ref.size,Image.Transform.AFFINE,(1/scale,0,450-center/scale,0,1/scale,crown-24/scale),Image.Resampling.BICUBIC)
 ours.save(r/stage/f'{sex}_registered.png')
 box=(60,85,205,225) if sex=='male' else (110,90,238,215)
 plots=[]
 for im in [ref,ours]:
  im=im.crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4))
  d=ImageDraw.Draw(im,'RGBA')
  for x in range((box[0]//10+1)*10,box[2],10):
   sx=(x-box[0])*4;d.line((sx,0,sx,im.height),fill=(0,150,220,75));d.text((sx+1,0),str(x),fill=(0,60,100),font=f)
  for y in range((box[1]//10+1)*10,box[3],10):
   sy=(y-box[1])*4;d.line((0,sy,im.width,sy),fill=(0,150,220,75));d.text((0,sy+1),str(y),fill=(0,60,100),font=f)
  plots.append(im)
 board=Image.new('RGB',(plots[0].width*2+10,plots[0].height),'white');board.paste(plots[0],(0,0));board.paste(plots[1],(plots[0].width+10,0));board.save(r/stage/f'{sex}_landmark_grid.png')

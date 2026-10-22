from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
R=Path.cwd();O=R/'work/reference-rebuild/original-refinement';A=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/visual-overhaul/after')
canvas=Image.new('RGB',(1800,1500),'#f3ede4');d=ImageDraw.Draw(canvas)
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',24);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
d.text((28,18),'Original character: source-only facial seam candidate',fill='#362b25',font=font)
d.text((28,52),'Not installed in the game. Existing facial volumes and eye proportions retained.',fill='#60564e',font=small)
cases=[('male',(662,77,928,359)),('female',(540,61,820,351))]
for row,(sex,crop) in enumerate(cases):
 y=100+row*700
 reference=Image.open(A/f'{sex}-character-target.png').convert('RGB').crop(crop)
 for col,(label,im) in enumerate([('Approved target',reference),('Original mesh / front',Image.open(O/f'{sex}_seam_pilot_front.png').convert('RGB')),('Original mesh / three-quarter',Image.open(O/f'{sex}_seam_pilot_threequarter.png').convert('RGB'))]):
  box=(col*600,y+34,col*600+600,y+675)
  if col==0:
   ratio=min(500/im.width,610/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS);canvas.paste(im,(col*600+(600-im.width)//2,y+34+(641-im.height)//2))
  else:
   im=im.resize((549,641),Image.Resampling.LANCZOS);canvas.paste(im,(col*600+25,y+34))
  d.text((col*600+25,y),sex.title()+' — '+label,fill='#362b25',font=small)
canvas.save(O/'original-seam-pilot-vs-target.png')

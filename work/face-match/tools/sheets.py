from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
refs=Path('/Users/adnanyonathan/Documents/Codex/2026-10-06/open-4/outputs/reference-check')
folder=root/sys.argv[1]
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
for sex in ['male','female']:
 for angle in ['front','threequarter','gameplay']:
  ref=Image.open(refs/f'{sex}-target.png').convert('RGB')
  current=Image.open(folder/'raw'/f'{sex}_{angle}.png').convert('RGB')
  if angle=='gameplay':
   canvas=Image.new('RGB',(1560,760),'#ece8df');d=ImageDraw.Draw(canvas)
   ref.thumbnail((380,590));canvas.paste(ref,(20,85))
   current.thumbnail((1120,630));canvas.paste(current,(420,85))
   d.text((20,25),f'{sex.upper()} / GAMEPLAY — {sys.argv[1]}',fill='#222222',font=font)
   d.text((20,700),'Locked FRONT reference left. Actual gameplay camera right (player faces away).',fill='#333333',font=small)
  else:
   # Uniform resize only; no retouching, relighting, stretching or generated pixels.
   canvas=Image.new('RGB',(1090,750),'#ece8df');d=ImageDraw.Draw(canvas)
   scale=(226-24)/(800-208) if sex=='male' else (219-24)/(780-155)
   crown=208 if sex=='male' else 155
   center=132 if sex=='male' else 173
   factor=min(515/ref.width,625/ref.height)
   size=(round(ref.width*factor),round(ref.height*factor))
   ref=ref.resize(size,Image.Resampling.LANCZOS);current=current.transform(size,Image.Transform.AFFINE,(1/scale/factor,0,450-center/scale,0,1/scale/factor,crown-24/scale),Image.Resampling.BICUBIC,fillcolor='#ece8df')
   canvas.paste(ref,(20+(515-ref.width)//2,85));canvas.paste(current,(555+(515-current.width)//2,85))
   d.text((20,20),f'{sex.upper()} / {angle.upper()} — {sys.argv[1]}',fill='#222222',font=font)
   d.text((20,53),'LOCKED REFERENCE',fill='#333333',font=small)
   d.text((555,53),'UNITY / UNCHANGED COURT LIGHTS',fill='#333333',font=small)
   d.text((20,722),'Front reference only; additional reference angles were not supplied.' if angle!='front' else 'Unretouched source pixels. Both debug flags UNSET.',fill='#333333',font=small)
  canvas.save(folder/f'{sex}_{angle}_sheet.png')
print(folder)

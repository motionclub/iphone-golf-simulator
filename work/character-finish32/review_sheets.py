from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import re,math
w=Path('work/character-finish32');root=w/'sleeve';clips=re.findall(r'Cloth review male (\w+):', (root/'audit.txt').read_text())
for page in range(3):
 subset=clips[page*11:(page+1)*11];W=1400;H=len(subset)*215;im=Image.new('RGB',(W,H),'#eeeae4');draw=ImageDraw.Draw(im)
 for row,clip in enumerate(subset):
  draw.text((6,row*215+5),clip,fill='#18232e')
  for col,suffix in enumerate(['0','1','2','3','4','1_rear','4_rear']):
   p=root/f'male_{clip}_{suffix}.png';shot=Image.open(p);shot.thumbnail((195,194));im.paste(shot,(col*200,row*215+20))
 im.save(w/f'motion-review-{page+1}.jpg',quality=95)

from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat
from pathlib import Path
import json
O=Path(__file__).parent;canvas=Image.new('RGB',(1200,1520),'#f2ece4');d=ImageDraw.Draw(canvas);font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',24);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
d.text((24,18),'Male original head — one bounded surface cleanup',font=font,fill='#342921');d.text((24,52),'CPU Blender source proof; same camera, materials and lighting. Actual Unity art gate pending.',font=small,fill='#67584d')
for col,case in enumerate(('before','after')):
 d.text((col*600+24,94),'Accepted source' if case=='before' else 'Local depth fairing candidate 1',font=font,fill='#342921')
 for row,angle in enumerate(('front','threequarter')):
  im=Image.open(O/f'male_source_{case}_{angle}.png').convert('RGB');canvas.paste(im,(col*600,132+row*675))
canvas.save(O/'male-source-before-after.png')
crop=Image.new('RGB',(1200,410),'#f2ece4');dc=ImageDraw.Draw(crop)
for col,case in enumerate(('before','after')):
 im=Image.open(O/f'male_source_{case}_front.png').convert('RGB').crop((130,325,470,535)).resize((580,358),Image.Resampling.LANCZOS);crop.paste(im,(col*600+10,42));dc.text((col*600+16,10),'Accepted source' if case=='before' else 'One local surface candidate',font=small,fill='#342921')
crop.save(O/'male-cheek-jaw-before-after.png')
stats={}
for angle in ('front','threequarter'):
 before=Image.open(O/f'male_source_before_{angle}.png').convert('RGB');after=Image.open(O/f'male_source_after_{angle}.png').convert('RGB');diff=ImageChops.difference(before,after);st=ImageStat.Stat(diff.crop((130,325,470,535)));stats[angle]={'cheekJawPixelMeanAbsDifference255':st.mean,'sameCameraLightingMaterial':True}
(O/'source-pixel-difference.json').write_text(json.dumps(stats,indent=2)+'\n')

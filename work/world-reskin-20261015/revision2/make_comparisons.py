from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
root=Path(__file__).resolve().parent;proof=root/'proof';out=proof/'comparisons';out.mkdir(exist_ok=True)
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def board(name,title,a,b,width,left='PREVIOUS PASS',right='DREAM COAST / REVISION 2'):
 a=Image.open(a).convert('RGB');b=Image.open(b).convert('RGB');assert a.size==b.size
 h=round(a.height*width/a.width);pad=24;gap=20;top=115
 im=Image.new('RGB',(width*2+gap+pad*2,h+top+55),'#10232e');d=ImageDraw.Draw(im)
 d.text((pad,16),title,font=ImageFont.truetype(font,28),fill='#eff2e8')
 d.text((pad,66),left,font=ImageFont.truetype(font,18),fill='#acc8d6');d.text((pad+width+gap,66),right,font=ImageFont.truetype(font,18),fill='#f4bacc')
 im.paste(a.resize((width,h),Image.Resampling.LANCZOS),(pad,top));im.paste(b.resize((width,h),Image.Resampling.LANCZOS),(pad+width+gap,top))
 d.text((pad,top+h+18),'Actual Unity renders / same camera / animated water phase may differ',font=ImageFont.truetype(font,16),fill='#a6bdc8');im.save(out/name)
previous=root.parent/'proof/after/golf';final=proof/'final';baseline=proof/'baseline-matched'
board('01_previous_vs_dream.png','GOLF / A NEW WORLD AROUND THE HOLE',previous/'hole12_showcase_070.png',final/'hole12_showcase_070.png',600)
board('02_whole_hole.png','GOLF / WHOLE HOLE',previous/'hole12_preview.png',final/'hole12_preview.png',900)
board('03_gameplay.png','GOLF / MATCHED GAMEPLAY VIEW',baseline/'hole12_gameplay.png',final/'hole12_gameplay.png',600,'ORIGINAL ART / NEW TEE CAMERA')
board('04_lighthouse.png','GOLF / LIGHTHOUSE AND FLOWERING GROVE',previous/'hole12_showcase_085.png',final/'hole12_showcase_085.png',600)

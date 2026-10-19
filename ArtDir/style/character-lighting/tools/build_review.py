"""Build review grids and W1-W4 directly from rendered captures, without retouching.
Usage: python3 build_review.py CAPTURE_DIR REVIEW_DIR
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,shutil,json
src=Path(sys.argv[1]);out=Path(sys.argv[2]);evidence=Path(__file__).resolve().parent.parent
out.mkdir(parents=True,exist_ok=True)
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',16)
small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
rows=json.loads((src/'metrics.json').read_text());metrics={r['shot']:r for r in rows}
for folder in ['captures','paired-before','masks','sheets']:(out/folder).mkdir(exist_ok=True)
for f in src.glob('*.png'):
 if '.mask.' in f.name:shutil.copy2(f,out/'masks'/f.name)
 else:Image.open(f).convert('RGB').save(out/'captures'/(f.stem+'.jpg'),quality=94)
for f in (src/'paired-before').glob('*.png'):Image.open(f).convert('RGB').save(out/'paired-before'/(f.stem+'.jpg'),quality=94)
for f in src.glob('*.tsv'):shutil.copy2(f,out/f.name)
for f in ['metrics.json','boxes.csv']:shutil.copy2(src/f,out/f)

def caption(shot):
 r=metrics[shot]['after'];face=r['face'];s=face.get('L');t=f"face L {s:.1f}" if s is not None else 'face hidden';return f"{t} | edge dL {r['silhouetteDeltaL']:.1f}"
def grid(names,title,dest,width=480):
 h=width*9//16;im=Image.new('RGB',(2*width,50+len(names)*(h+42)),'#f2f3f5');d=ImageDraw.Draw(im);d.text((10,8),title,fill='black',font=font);d.text((10,29),'Gameplay camera (left) | companion close-up (right)',fill='#444444',font=small)
 for row,base in enumerate(names):
  y=50+row*(h+42)
  for col,suffix in enumerate(['__a_gameplay','__b_close']):
   n=base+suffix;p=src/(n+'.png')
   if not p.exists():continue
   im.paste(Image.open(p).convert('RGB').resize((width,h),Image.Resampling.LANCZOS),(col*width,y));d.text((col*width+6,y+h+3),base.split('__')[-1],fill='black',font=small);d.text((col*width+6,y+h+20),caption(n),fill='#333333',font=small)
 im.save(dest,quality=94)
for hero in ['MatchHero_Male','MatchHero_Female','GolfKitHero_Male','GolfKitHero_Female']:
 cases=['hub','tennis_resort','tennis_skyscraper','tennis_volcano'] if hero.startswith('Match') else ['golf_07_clear','golf_07_fog','golf_07_rain','golf_07_storm','golf_16_clear','golf_17_clear','golf_20_clear']
 grid([hero+'__'+c for c in cases],hero+' — AFTER',out/('grid_'+hero+'_after.jpg'))
 if hero.startswith('Golf'):
  for weather in ['clear','gusty','rain','storm','fog']:
   names=sorted({r['shot'].rsplit('__',1)[0] for r in rows if r['shot'].startswith(hero+'__') and '__golf_' in r['shot'] and '_'+weather+'__' in r['shot']})
   if names:grid(names,hero+' — all holes / '+weather,out/'sheets'/(hero+'_'+weather+'.jpg'),400)
ws=[('W1_tennis_volcano_gameplay','MatchHero_Male__tennis_volcano__a_gameplay'),('W2_tennis_skyscraper_gameplay','MatchHero_Male__tennis_skyscraper__a_gameplay'),('W3_golf_16_volcano_rim_gameplay','GolfKitHero_Male__golf_16_clear__a_gameplay'),('W4_golf_close_face_cap_shadow','GolfKitHero_Male__golf_07_clear__b_close')]
for tag,name in ws:
 im=Image.new('RGB',(1920,440),'#f2f3f5');d=ImageDraw.Draw(im)
 for i,key in enumerate(['before','after']):
  f=src/('paired-before' if key=='before' else '')/(name+'.png');im.paste(Image.open(f).convert('RGB').resize((640,360),Image.Resampling.LANCZOS),(i*640,42));r=metrics[name][key];face=r['face'];text='Face hidden' if 'L' not in face else 'Face Lab %.1f / %.1f / %.1f'%(face['L'],face['a'],face['b']);d.text((i*640+8,8),key.upper()+' — '+text,fill='black',font=font);d.text((i*640+8,410),f"Median edge/ring dL {r['silhouetteDeltaL']:.1f}",fill='black',font=font)
 old=Image.open(evidence/(tag+'.jpg'));ref=old.crop((810,40,1610,490));im.paste(ref.resize((640,360),Image.Resampling.LANCZOS),(1280,42));d.text((1288,8),'MODERN REFERENCE — same image as original W sheet',fill='black',font=font);im.save(out/(tag+'_before_after_ref.jpg'),quality=95)
# Eight fixed-pose look-dev shots: four heroes in both environments.
names=sorted(n for n in metrics if n.startswith('lookdev_'))
if names:
 im=Image.new('RGB',(1920,660),'#f2f3f5');d=ImageDraw.Draw(im)
 for i,n in enumerate(names):
  x=(i%4)*480;y=(i//4)*330;d.text((x+5,y+5),n.replace('__b_close','').replace('lookdev_',''),fill='black',font=small);im.paste(Image.open(src/(n+'.png')).convert('RGB').resize((480,270)),(x,y+27));d.text((x+5,y+303),caption(n),fill='black',font=small)
 im.save(out/'lookdev_four_heroes_both_environments.jpg',quality=94)
print(out)
# Identical pixel crop rectangles for before/after, enlarged only for inspection.
import numpy as np
cases=['MatchHero_Male__tennis_resort__b_close','MatchHero_Female__tennis_resort__b_close','GolfKitHero_Male__golf_07_clear__b_close','GolfKitHero_Female__golf_07_clear__b_close']
if all(n in metrics for n in cases):
 im=Image.new('RGB',(800,4*465),'#f2f3f5');d=ImageDraw.Draw(im)
 for row,n in enumerate(cases):
  mask=np.array(Image.open(src/(n+'.mask.png')).convert('RGB'));yy,xx=np.where((mask[:,:,0]>240)&(mask[:,:,1]<10)&(mask[:,:,2]<10));cx=int(np.median(xx));cy=int(np.median(yy));box=(cx-110,cy-130,cx+110,cy+110)
  for col,key in enumerate(['before','after']):
   p=src/('paired-before' if key=='before' else '')/(n+'.png');face=metrics[n][key]['face'];x=col*400;y=row*465
   d.text((x+5,y+5),n.split('__')[0]+' '+key.upper(),fill='black',font=font);im.paste(Image.open(p).convert('RGB').crop(box).resize((385,420),Image.Resampling.LANCZOS),(x+7,y+25));d.text((x+5,y+445),'Lab %.1f / %.1f / %.1f'%(face['L'],face['a'],face['b']),fill='black',font=small)
 im.save(out/'face_detail_before_after.jpg',quality=95)

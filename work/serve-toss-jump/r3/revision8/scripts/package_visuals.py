"""Compose the measured candidate keys, event-matched references and Unity view films."""
from pathlib import Path
import sys,subprocess
from PIL import Image,ImageDraw,ImageFont,ImageOps
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'scripts'))
from read_trace import load
font=lambda n:ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',n)
bg=(19,25,34);fg=(238,241,245);muted=(180,191,205)
events=[('stance',6,.2),('mid-toss','13p5',.45),('release',21,.7),('trophy',40,40/30),('take-off',48,1.6),('contact',51,1.7),('apex',53,53/30),('left touch',61,61/30),('squash',64,64/30),('end',75,2.5)]
raw=lambda s,f:W/'proof/raw_keys'/f'{s}_f{f:03d}_side_hi.png' if isinstance(f,int) else W/'proof/raw_keys'/f'{s}_f{f}_side_hi.png'
cw,ch=360,520
sheet=Image.new('RGB',(cw*10,1140),bg);dr=ImageDraw.Draw(sheet)
dr.text((18,12),'CANDIDATE: FAIL — authored Blender poses, racket 1.3x, fixed side camera',font=font(23),fill=fg)
dr.text((18,45),'Unity Serve exits at 1.9783 s; its film contains 0 Serve rows for left touch, squash or end.',font=font(19),fill=muted)
for row,sex in enumerate(['male','female']):
 y=80+row*ch
 for col,(name,f,t) in enumerate(events):
  x=col*cw;sheet.paste(Image.open(raw(sex,f)).convert('RGB'),(x,y))
  dr.text((x+8,y+483),f'{sex} | {name} {t:.3f}s',font=font(16),fill=fg)
sheet.save(W/'proof/serve_keys.jpg',quality=94)
refinfo=[('alcaraz','Alcaraz · rear',(290,56,610,607),[179.446,179.696,180.180,180.496]),('federer','Federer · side',(430,56,830,607),[4.30,5.680,7.373,8.520]),('djokovic','Djokovic · rear',(610,56,985,607),[4.679,10.887,14.387,17.720])]
cw,rh=340,480
sheet=Image.new('RGB',(cw*5,80+rh*4),bg);dr=ImageDraw.Draw(sheet)
dr.text((12,10),'Event order comparison — selected reference frame times are slow-motion playback seconds',font=font(19),fill=fg)
heads=['Male candidate','Female candidate']+[x[1] for x in refinfo]
for i,h in enumerate(heads):dr.text((i*cw+8,44),h,font=font(18),fill=fg)
for row,(event,f,t) in enumerate([events[i] for i in [2,3,5,7]]):
 y=80+row*rh
 for col,sex in enumerate(['male','female']):
  im=ImageOps.contain(Image.open(raw(sex,f)).convert('RGB'),(330,430));x=col*cw;sheet.paste(im,(x+(cw-im.width)//2,y))
  dr.text((x+8,y+435),f'{event}: {t:.3f}s',font=font(17),fill=fg)
 for col,(tag,label,crop,times) in enumerate(refinfo,2):
  im=ImageOps.contain(Image.open(W/'refs'/f'{tag}_{event if event != "left touch" else "landing"}.jpg').crop(crop).convert('RGB'),(330,430));x=col*cw;sheet.paste(im,(x+(cw-im.width)//2,y))
  dr.text((x+8,y+435),f'{event}: ~{times[row]:.3f}s',font=font(17),fill=fg)
sheet.save(W/'proof/serve_reference_comparison.jpg',quality=94)
enc=str(W/'scripts/enc')
for sex in ['male','female']:
 d=W/f'film_{sex}';rows=load(str(d/'trace.csv'));m={};n=0
 for i,r in enumerate(rows):
  if i%2==0 and (r['flow'] in ['PlayerServeHold','PlayerServeToss'] or r['state'].startswith('Serve')):m[i]=n;n+=1
 wind=next(i for i,r in enumerate(rows) if r['prep']>.0005 and r['flow']!='Rally');start=max(0,wind-30);sel=[i for i in range(start-start%2,max(m)+1,2) if i in m]
 for view in ['side','back']:
  paths=[str(d/f'{view}_{m[i]:05d}.png') for i in sel]
  for fps,suffix in [(30,''),(15,'_half_speed')] if view=='side' else [(30,'')]:
   subprocess.run([enc,str(W/'film'/f'serve_toss_jump_{sex}_{view}{suffix}.mp4'),str(fps),'720','720']+paths,check=True)
print('PACKAGED sheets + side, back and half-speed films for both heroes; Unity front views=0')

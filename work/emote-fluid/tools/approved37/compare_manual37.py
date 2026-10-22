from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,hashlib,json,sys
from PIL import Image,ImageDraw,ImageFont
C=Path('/Users/adnanyonathan/Documents/Codex/2026-10-05/read-artdir-hero-base-lock-parallel')
R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W=R/'work/emote-fluid'
O=C/'outputs/fluidity/manual-review/revision37/comparisons';O.mkdir(parents=True,exist_ok=True)
camera=sys.argv[1]
CLIPS=['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
def movie(job):
 hero,clip=job
 before=sorted((W/'film/before'/hero/clip).glob(camera+'_*.png'))
 base='manual37_frames' if camera=='front' else 'manual37_game_frames'
 after=sorted((C/'work'/base/hero/clip).glob(camera+'_*.png'))
 if not before or len(before)!=len(after):raise RuntimeError(f'Cannot pair captures for {hero} {clip} {camera}: {len(before)} / {len(after)}')
 width,height=(720,720) if camera=='front' else (960,540)
 scratch=C/'work/comparison37_frames'/hero/clip/camera;scratch.mkdir(parents=True,exist_ok=True)
 font=ImageFont.load_default(size=20);frames=[]
 for i,(bp,ap) in enumerate(zip(before,after)):
  canvas=Image.new('RGB',(width*2,height+48),(18,21,30));draw=ImageDraw.Draw(canvas)
  for j,(label,path) in enumerate([('ORIGINAL',bp),('REVISION 37',ap)]):
   with Image.open(path) as im:canvas.paste(im.convert('RGB').resize((width,height),Image.Resampling.LANCZOS),(j*width,48))
   draw.text((j*width+18,13),label,font=font,fill=(245,245,245))
  draw.text((width-180,13),hero.title()+' '+clip.replace('_',' '),font=font,fill=(210,215,230))
  fp=scratch/f'{i:05d}.png';canvas.save(fp);frames.append(str(fp))
 rows=[]
 source=W/'iterations/37/candidate/fbx'/f'{hero.title()}_{clip}.fbx'
 original=W/'rollback/fbx'/f'{hero.title()}_{clip}.fbx'
 for speed in ['full','half']:
  output=O/f'{hero}_{clip}_{camera}_{speed}.mp4';seq=frames if speed=='full' else [f for f in frames for _ in range(2)]
  run=subprocess.run([str(R/'work/emotes/scripts/enc'),str(output),'30',str(width*2),str(height+48),*seq],check=True,capture_output=True,text=True)
  print(run.stdout.strip(),flush=True)
  rows.append(dict(hero=hero,clip=clip,camera=camera,speed=speed,path=str(output),revision=37,frames=len(seq),fps=30,candidate_fbx_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),original_fbx_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),user_review='PENDING'))
 for f in scratch.glob('*.png'):f.unlink()
 return rows
with ThreadPoolExecutor(max_workers=2) as pool:rows=[row for group in pool.map(movie,[(h,c) for h in ['male','female'] for c in CLIPS]) for row in group]
(O/f'{camera}_manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
allrows=[]
for f in O.glob('*_manifest.json'):allrows+=json.loads(f.read_text())
(O/'REVIEW.md').write_text('# Revision 37 comparisons\n\nOriginal on the left; revision37 on the right. Actual Unity playback. User review pending; automated verification remains stopped.\n\n'+'\n\n'.join(f'**{x["hero"].title()} {x["clip"]} — {x["camera"]}, {x["speed"]} speed**\n\n![Comparison]({x["path"]})' for x in allrows)+'\n')
print('Comparisons exported:',camera,len(rows),flush=True)

"""Build the 48 required front/game, full/half-speed BEFORE|AFTER videos.
Run after both Unity captures finish. Missing/mismatched frames fail, never truncate.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,os
from PIL import Image,ImageDraw,ImageFont
W=Path(os.environ.get('FLUID_WORK',str(Path(__file__).resolve().parents[1])));R=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
CLIPS=['Emote_Spike','Emote_Scuba','Emote_Thrust','Intro_Wave','Intro_BringIt','Intro_Pushups']
def main():
 p=argparse.ArgumentParser();p.add_argument('--hero',choices=['male','female','both'],default='both');a=p.parse_args();records=[]
 for hero in (['male','female'] if a.hero=='both' else [a.hero]):
  for clip in CLIPS:
   for camera in ['front','game']:
    before=sorted((W/'film/before'/hero/clip).glob(camera+'_*.png'));after=sorted((W/'film/after'/hero/clip).glob(camera+'_*.png'))
    if not before or len(before)!=len(after):raise RuntimeError(f'{hero}/{clip}/{camera}: BEFORE {len(before)} AFTER {len(after)}')
    scratch=W/'film/compare_frames'/hero/clip/camera;scratch.mkdir(parents=True,exist_ok=True);frames=[]
    width,height=(720,720) if camera=='front' else (960,540)
    for i,(bp,ap) in enumerate(zip(before,after)):
     canvas=Image.new('RGB',(width*2,height+44),(18,21,30));draw=ImageDraw.Draw(canvas)
     for j,(label,path) in enumerate([('BEFORE',bp),('AFTER — CANDIDATE',ap)]):
      with Image.open(path) as im:canvas.paste(im.convert('RGB').resize((width,height),Image.Resampling.LANCZOS),(j*width,44))
      draw.text((j*width+18,12),label,fill=(245,245,245))
     draw.text((width-170,12),hero.title()+' '+clip.replace('_',' '),fill=(210,215,230));fp=scratch/f'{i:05d}.png';canvas.save(fp);frames.append(str(fp))
    outdir=W/'film/compare';outdir.mkdir(exist_ok=True)
    for speed in ['full','half']:
     fp=outdir/f'{hero}_{clip}_{camera}_{speed}.mp4';seq=frames if speed=='full' else [f for f in frames for _ in range(2)]
     run=subprocess.run([str(R/'work/emotes/scripts/enc'),str(fp),'30',str(width*2),str(height+44),*seq],capture_output=True,text=True)
     if run.returncode or not fp.exists() or ' 2' not in run.stdout:raise RuntimeError(run.stdout+run.stderr)
     records.append(dict(hero=hero,clip=clip,camera=camera,speed=speed,frames=len(seq),fps=30,path=str(fp),sha256=hashlib.sha256(fp.read_bytes()).hexdigest()))
     print('ENCODED',fp.name,len(seq),flush=True)
    for fp in scratch.glob('*.png'):fp.unlink()
 manifest=W/'proof/films.json';old=json.loads(manifest.read_text()) if manifest.exists() else [];keys={(x['hero'],x['clip'],x['camera'],x['speed']) for x in records};old=[x for x in old if (x['hero'],x['clip'],x['camera'],x['speed']) not in keys];manifest.write_text(json.dumps(old+records,indent=2))
if __name__=='__main__':main()

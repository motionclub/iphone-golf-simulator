from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import csv,json,subprocess
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[1];D=W/'r3';(D/'film').mkdir(exist_ok=True);(D/'proof').mkdir(exist_ok=True)
inputs=json.loads((D/'FILM_INPUTS.json').read_text());jobs=[]
for sex,rel in inputs.items():
 for view in ['front','side','back','game']:
  frames=sorted((D/rel).glob(view+'_*.png'));assert len(frames)>200,(sex,view,len(frames))
  for half,fps in [(False,30),(True,15)]:
   name=f'serve_r3_{sex}_{view}'+('_half_speed' if half else '')+'.mp4';size=['960','540'] if view=='game' else ['640','640'];jobs.append([str(W/'scripts/enc'),str(D/'film'/name),str(fps),*size,*map(str,frames)])
def encode(cmd):
 if Path(cmd[1]).exists():return "ENCODED_ALREADY "+Path(cmd[1]).name
 r=subprocess.run(cmd,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr[:2000])
 return r.stdout.strip()
with ThreadPoolExecutor(max_workers=2) as pool:
 for r in pool.map(encode,jobs):print(r,flush=True)
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',15);sheet=Image.new('RGB',(2560,768),(17,22,30));draw=ImageDraw.Draw(sheet)
for si,(sex,rel) in enumerate(inputs.items()):
 rows=list(csv.DictReader((D/rel/'trace.csv').open()));entry=next(i for i,r in enumerate(rows) if r['state'].startswith('Serve'));sr=[r for r in rows[entry:] if r['state'].startswith('Serve') and int(r['picture'])>=0]
 chosen=[('entry',rows[entry]),('release',min(sr,key=lambda r:abs(float(r['clipTime'])-.7))),('trophy',min(sr,key=lambda r:abs(float(r['clipTime'])-1.3333334))),('takeoff',min(sr,key=lambda r:abs(float(r['clipTime'])-1.6))),('contact',min(sr,key=lambda r:abs(float(r['clipTime'])-1.7))),('apex',min(sr,key=lambda r:abs(float(r['clipTime'])-1.77))),('front touch',min(sr,key=lambda r:abs(float(r['clipTime'])-1.88))),('landing squash',min(sr,key=lambda r:abs(float(r['clipTime'])-1.92)))]
 keyrows={r['label']:r for r in csv.DictReader((D/rel/'key_frames.csv').open())}
 for col,(label,r) in enumerate(chosen):
  key={'entry':'entry','contact':'contact','landing squash':'landing'}.get(label)
  if key in keyrows:r=rows[int(keyrows[key]['frame'])]
  if key not in keyrows and int(r['picture'])<0:r=min(sr,key=lambda v:abs(int(v['frame'])-int(r['frame'])))
  path=D/rel/("key_"+key+"_side.png" if key in keyrows else f"side_{int(r['picture']):05d}.png")
  im=Image.open(path).convert('RGB');im.thumbnail((320,320));x,y=col*320,si*384+30;sheet.paste(im,(x,y));draw.text((x+6,y+323),sex+' | '+label,font=font,fill='white');draw.text((x+6,y+342),'frame '+r['frame']+' clip '+r['clipTime'],font=font,fill=(215,220,230))
draw.text((8,5),'LIVE UNITY — candidate review; human EYE pending',font=font,fill=(255,200,145));sheet.save(D/'proof/live_serve_keys.jpg',quality=94)

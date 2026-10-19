from pathlib import Path
import csv,json,shutil,collections,re,hashlib
from PIL import Image,ImageDraw
repo=Path(__file__).resolve().parents[2]
scratch=Path('/private/tmp/UnityScratch_experience_20261015/work/experience')
baseline=Path('/Users/adnanyonathan/UnityScratch_depths/work/vfxaudit')
out=repo/'ArtDir/style/experience-implementation/proof';out.mkdir(parents=True,exist_ok=True)
data=out/'data';data.mkdir(exist_ok=True)
def rows(p):return list(csv.DictReader(p.open()))
def sheet(name,items,cols=4,w=320,h=180):
 canvas=Image.new('RGB',(w*cols,((len(items)+cols-1)//cols)*(h+26)),(12,20,30));d=ImageDraw.Draw(canvas)
 for i,(path,label,crop) in enumerate(items):
  im=Image.open(path)
  if crop:im=im.crop(crop)
  im=im.resize((w,h));x=(i%cols)*w;y=(i//cols)*(h+26)
  canvas.paste(im,(x,y+26));d.text((x+8,y+7),label,fill='white')
 canvas.save(out/name,quality=94)
def tennisframe(directory,seconds):
 rs=rows(directory/'trace.csv');r=min((r for r in rs if int(r['videoFrame'])>=0),key=lambda r:abs(float(r['seconds'])-seconds))
 return directory/'frames'/f"game_{int(r['videoFrame']):05}.jpg"
# Point-end strips at fixed elapsed times; readiness is measured from CSV, not inferred from pose.
items=[]
for directory,start,label in [(baseline/'tennis_resort',7.33333,'Before'),(scratch/'tennis-after',5.2,'After')]:
 for delta in [0,.5,1,1.5]:items.append((tennisframe(directory,start+delta),f'{label}: point end +{delta:.1f}s',None))
sheet('tennis-reset.jpg',items)
summary={}
for name in ['golf-control','golf-matched-after']:
 rs=rows(scratch/name/'trace.csv');times={}
 for r in rs:
  if r['state']=='Flight':
   times.setdefault('request',float(r['time']))
   if float(r['flightTime'])>=0:times.setdefault('contact',float(r['time']))
  if r['state']=='Result':times.setdefault('result',float(r['time']))
  if r['stage']=='5':times.setdefault('aim',float(r['time']))
 meta=json.loads((scratch/name/'film.json').read_text())
 summary[name]={**times,'contactToAim':times['aim']-times['contact'],'requestToContact':times['contact']-times['request'],'resultToAim':times['aim']-times['result'],'metadata':meta}
 shutil.copy2(scratch/name/'trace.csv',data/f'{name}.csv');shutil.copy2(scratch/name/'film.json',data/f'{name}.json')
 # Strip aligned to actual contact, not impactFrame=request.
 c=next(r for r in rs if r['state']=='Flight' and float(r['flightTime'])>=0 and int(r['simulationFrame'])%2==0)
 f0=int(c['videoFrame'])-1
 if name=='golf-matched-after':
  sheet('golf-contact-strip.jpg',[(scratch/name/f'f_{f0+f:05}.jpg',f'Contact {f:+d} / 30 fps',None) for f in range(-8,13)],7,240,135)
items=[]
for name in ['golf-control','golf-matched-after']:
 rs=rows(scratch/name/'trace.csv');t=summary[name]
 for time,label in [(t['contact'],'Contact'),(t['result']-.5,'Runout'),(t['result']+.1,'Result'),(t['aim']+.05,'Next Aim')]:
  r=min((r for r in rs if int(r['simulationFrame'])%2==0),key=lambda r:abs(float(r['time'])-time))
  items.append((scratch/name/f"f_{int(r['videoFrame'])-1:05}.jpg",f'{name}: {label}',None))
sheet('golf-pace.jpg',items)
rs=rows(scratch/'tennis-after/trace.csv');counts=collections.Counter(r['phase'] for r in rs)
ends=[];resets=[]
for i,r in enumerate(rs):
 if r['phase']=='PointOver' and (i==0 or rs[i-1]['phase']!='PointOver'):ends.append(float(r['seconds']))
 if r['serveReady']=='True' and i and rs[i-1]['serveReady']!='True' and ends:resets.append(float(r['seconds'])-ends[-1])
summary['tennis']={'ticks':len(rs),'phases':dict(counts),'rallyPercent':100*counts['Rally']/len(rs),'inclusiveLivePercent':100*(counts['Rally']+counts['PlayerServeToss']+counts['OpponentServe'])/len(rs),'resetsSeconds':resets,'liveEmoteTicks':sum('Emote' in r['playerClip'] or 'FistPump' in r['playerClip'] for r in rs if r['phase']=='Rally')}
shutil.copy2(scratch/'tennis-after/trace.csv',data/'tennis-after.csv');shutil.copy2(baseline/'tennis_resort/trace.csv',data/'tennis-before.csv');shutil.copy2(baseline/'golf12/trace.csv',data/'golf-original-before.csv')
# Live contact strip using event frame IDs.
stamps=[]
for line in (scratch/'tennis-after.log').read_text().splitlines():
 if line.startswith('[Experience] '):stamps.append(json.loads(line[len('[Experience] '):]))
contacts=[s for s in stamps if s['stage']=='contact']
if contacts:
 event=contacts[0];r=min((r for r in rs if int(r['videoFrame'])>=0),key=lambda r:abs(int(r['unityFrame'])-event['frame']));f0=int(r['videoFrame'])
 sheet('tennis-contact-strip.jpg',[(scratch/'tennis-after/frames'/f'game_{f0+f:05}.jpg',f'Live contact {f:+d} / 30 fps',None) for f in range(-8,13)],7,240,135)
 summary['tennis']['contactChannelFrames']=[{'contact':s['frame'],'channel':next((x['frame'] for x in stamps if x['sequence']>s['sequence'] and x['stage']=='contact-channels-requested'),None)} for s in contacts]
(data/'tennis-events.json').write_text(json.dumps(stamps,indent=2))
for p in (scratch/'tests').glob('*'):
 if p.suffix in ['.csv','.txt']:shutil.copy2(p,data/p.name)
for p in scratch.glob('*.xml'):shutil.copy2(p,data/p.name)
sheet('cup-drop.jpg',[(scratch/'tests'/f,f.replace('.jpg',''),(410,240,850,520)) for f in ['cup-0159.jpg','cup-result-00.jpg','cup-result-04.jpg','cup-result-08.jpg']],4,320,200)
(data/'measurements.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='metadata'} for k,v in summary.items()},indent=2))

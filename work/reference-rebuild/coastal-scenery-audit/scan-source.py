from pathlib import Path
from collections import defaultdict,Counter
import json,math
OUT=Path('work/reference-rebuild/coastal-scenery-audit')
scale=json.loads(Path('ArtDir/golf/reference-hole12-manifest.json').read_text())['runtimeFitYardsPerMeter']
def warp(y):
 return y if y<=8 or y>=110 else 8+(y-8)*6/52 if y<=60 else 14+(y-60)*96/50
def half(b):return ((b[1][0]-b[0][0])+(b[1][2]-b[0][2]))*.25
def center(b):return [(a+z)*.5 for a,z in zip(*b)]
def union(bounds):return [[min(b[0][a] for b in bounds) for a in range(3)],[max(b[1][a] for b in bounds) for a in range(3)]]
def pieces(m):
 idx={};w=[]
 for v in m['localVertices']:
  k=tuple(round(a*1000) for a in v)
  if k not in idx:idx[k]=len(idx)
  w.append(idx[k])
 parent=list(range(len(idx)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for f in m['faces']:
  a=find(w[f[0]])
  for i in f[1:]:parent[find(w[i])]=a
 pts=defaultdict(list)
 for i,v in enumerate(m['worldVertices']):pts[find(w[i])].append([v[0]*scale,v[2]*scale,v[1]*scale])
 return [union([[[p[a] for a in range(3)],[p[a] for a in range(3)]] for p in ps]) for ps in pts.values()]
def standing(parts):
 parts=sorted(parts,key=half,reverse=True);groups=[];centres=[]
 for p in parts:
  mid=center(p);into=-1
  for i,(at,h) in enumerate(centres):
   if math.hypot(at[0]-mid[0],at[1]-mid[2])<min(1.2,.5*max(h,half(p))):into=i;break
  if into<0:groups.append([p]);centres.append(([mid[0],mid[2]],half(p)))
  else:groups[into].append(p)
 return groups

def scan(label):
 d=json.loads((OUT/(label+'.json')).read_text());obs=[]
 for m in d['meshes']:
  name=m['name'].upper();kind='Tree' if name.startswith('TREE') else 'Bush' if name.startswith(('BUSH','SHRUB')) else 'Rock' if name.startswith('ROCK') else 'Wall'
  ps=pieces(m)
  groups=[ps] if kind=='Wall' else standing(ps)
  for gi,group in enumerate(groups):
   b=union(group);mid=center(b);radius=.5*(min if kind=='Wall' else max)(b[1][0]-b[0][0],b[1][2]-b[0][2]);trunk=0;crownBase=0;cone=False
   if kind=='Tree':
    widest=max(map(half,group));crownBase=float('inf');radius=0
    for p in group:
     if half(p)<.35*widest:trunk=max(trunk,half(p))
     else:
      crownBase=min(crownBase,p[0][1])
      if half(p)>=radius:radius=half(p);mid=center(p)
    if trunk<=0 or math.isinf(crownBase):radius=widest;crownBase=b[0][1]+.3*(b[1][1]-b[0][1]);trunk=max(.1,min(.35,.1*widest))
    trunk=max(.08,min(.5,trunk));cone=b[1][1]-crownBase>1.25*2*radius
   elif radius<.25:continue
   obs.append({'source':m['name'],'group':gi,'kind':kind,'X':mid[0],'D':mid[2],'Base':b[0][1],'Top':b[1][1],'Radius':radius,'TrunkRadius':trunk,'CrownBase':crownBase,'Cone':cone,'pieceCount':len(group)})
 (OUT/(label+'-obstacles.json')).write_text(json.dumps(obs,indent=2)+'\n')
 return obs
original=scan('original');reference=scan('reference')
print('Counts',len(original),dict(Counter(o['kind'] for o in original)),len(reference),dict(Counter(o['kind'] for o in reference)))
changes=[]
for old in original:
 expected=warp(old['D']/scale)*scale
 matches=[(math.hypot(n['X']-old['X'],n['D']-expected),i,n) for i,n in enumerate(reference) if n['kind']==old['kind']]
 distance,i,n=min(matches,key=lambda x:x[0]);changes.append({'original':old,'expectedRigidCenterD':expected,'nearestReference':n,'nearestIndex':i,'distanceYards':distance,'shapeMaxDelta':max(abs(old[k]-n[k]) for k in ['Base','Top','Radius','TrunkRadius','CrownBase'])})
changed=[c for c in changes if c['distanceYards']>.005 or c['shapeMaxDelta']>.005]
report={'scope':'Independent CPU source-mesh replay of ObstacleScan connected/Standing groups; actual Unity stored-vs-fresh scan remains final oracle','scaleYardsPerMetre':scale,'counts':{'original':len(original),'reference':len(reference)},'countsByKind':{'original':dict(Counter(o['kind'] for o in original)),'reference':dict(Counter(o['kind'] for o in reference))},'changedBeyond5mmYards':changed,'maximumNearestCenterDeltaYards':max(c['distanceYards'] for c in changes),'allMatches':changes}
(OUT/'source-obstacle-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print('Changed>',len(changed))
for c in changed:print(json.dumps(c))

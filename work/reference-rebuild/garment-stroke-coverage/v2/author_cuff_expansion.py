import bpy,pathlib,json,numpy as np,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=pathlib.Path.cwd();BASE=R/'work/reference-rebuild/garment-stroke-coverage';W=BASE/'v2';D=R/'proof/reference-rebuild/character-cloth14-control/poses';REPORT={}
text=(BASE/'author_stroke_envelopes.py').read_text();defs=text[text.index('def arr('):text.index("for sex in ('Male','Female'):")]
old="allowed=(comp==main)&(gRest[:,1]>1.075)&(gRest[:,1]<(1.415 if sex=='Male' else 1.36))&(np.abs(gRest[:,0])>.055)&(np.abs(gRest[:,0])<.288)"
new="""cuffs=np.zeros(count,bool)
 for labelId in labels:
  q=gRest[comp==labelId];lo=q.min(0);hi=q.max(0);size=hi-lo
  if np.min(np.abs(q[:,0]))>(.18 if sex=='Male' else .115) and lo[1]>1.045 and hi[1]<(1.37 if sex=='Male' else 1.33) and size[1]<.14 and size[0]<.15:cuffs[comp==labelId]=True
 allowed=((comp==main)|cuffs)&(gRest[:,1]>1.065)&(gRest[:,1]<(1.455 if sex=='Male' else 1.415))&(np.abs(gRest[:,0])>.055)&(np.abs(gRest[:,0])<.335)
 # Neck attachment/collar/placket remain exact; cuffs and their sewn edge
 # may now fit the body while keeping all source loops and seam topology.
 allowed[(gRest[:,1]>(1.39 if sex=='Male' else 1.34))&(np.abs(gRest[:,0])<.135)]=False"""
assert old in defs;defs=defs.replace(old,new).replace("boundary=set(v for edge,n in ec.items() if n==1 for v in edge);allowed[list(boundary)]=False","boundary=set(v for edge,n in ec.items() if n==1 for v in edge) # Cuff boundary motion is explicitly authorized in v2.")
defs=defs.replace("d>.028","d>.055").replace("support=(1-S(.006,.028,distance))*allowed","support=(1-S(.008,.055,distance))*allowed").replace("for _ in range(12):","for _ in range(20):").replace("# Main sewn sleeve/gusset/side panel only. Detached cuffs, collar, placket,\n # hems and shoulder piping preserve the inherited blended geometry exactly.","# Main sewn sleeve/gusset plus existing cuffs; collar/placket untouched.")
exec(defs)
for sex in ('Male','Female'):
 profile=json.loads((BASE/f'SleeveFit_{sex}.json').read_text());staged=json.loads(json.dumps(profile))
 for i in range(3):
  label=f'{sex.lower()}_Forehand_{i}';author(sex,label,profile);replacement=json.loads((W/(label+'-anchor.json')).read_text());index=next(k for k,a in enumerate(staged['anchors']) if a['shape']==label);staged['anchors'][index]=replacement
 assert all(a==b for a,b in zip(profile['anchors'],staged['anchors']) if '_Forehand_' not in a['shape']);assert all(profile[k]==staged[k] for k in profile if k!='anchors')
 (W/f'SleeveFit_{sex}.json').write_text(json.dumps(staged,separators=(',',':')))
(W/'stroke-source-report.json').write_text(json.dumps(REPORT,indent=2)+'\n')

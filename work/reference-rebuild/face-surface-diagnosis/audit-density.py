import bpy, pathlib, json, math, collections
from mathutils import Vector
R=pathlib.Path.cwd(); O=R/'work/reference-rebuild/face-surface-diagnosis'; report={}
def percentile(a,q):
 a=sorted(a);return a[min(len(a)-1,round((len(a)-1)*q))] if a else 0
for sex in ('Male','Female'):
 bpy.ops.wm.open_mainfile(filepath=str(R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend'))
 body=bpy.data.objects['Body'];me=body.data;me.calc_loop_triangles();p=[v.co.copy() for v in me.vertices]
 ids=[];keys={};u=[]
 for v in p:
  k=tuple(round(x,6) for x in v)
  if k not in keys:keys[k]=len(u);u.append(v)
  ids.append(keys[k])
 g=[Vector() for _ in u];area=[0.0]*len(u)
 for tri in me.loop_triangles:
  a,b,c=tri.vertices;cross=(p[b]-p[a]).cross(p[c]-p[a])
  for k in (a,b,c):g[ids[k]]+=cross;area[ids[k]]+=cross.length
 g=[v.normalized() for v in g];radius=.008;grid=collections.defaultdict(list)
 def cell(v):return tuple(math.floor(x/radius) for x in v)
 for j,v in enumerate(u):grid[cell(v)].append(j)
 diffs=[];counts=[];ratios=[]
 # Only front head skin. Source is canonical metres, Z up and -Y forward.
 for i,v in enumerate(u):
  if not(1.40<v.z<1.73 and abs(v.x)<.10 and v.y<-.02):continue
  base=g[i];unit=base.copy();weighted=base*area[i];cx,cy,cz=cell(v);local=[]
  for x in range(cx-1,cx+2):
   for y in range(cy-1,cy+2):
    for z in range(cz-1,cz+2):
     for j in grid.get((x,y,z),[]):
      d=(v-u[j]).length_squared;agreement=base.dot(g[j])
      if d>=radius*radius or agreement<.5:continue
      w=(1-d/(radius*radius))**2*agreement**2
      unit+=g[j]*w;weighted+=g[j]*(w*area[j]);local.append(area[j])
  if unit.length and weighted.length:diffs.append(math.degrees(unit.angle(weighted)))
  counts.append(len(local))
  if local and min(local)>1e-12:ratios.append(max(local)/min(local))
 report[sex]={'source':str(R/f'work/reference-rebuild/original-blink-finish/{sex}_OriginalSeamBlinkFinish1.blend'),'frontUniquePoints':len(diffs),'localNeighbourCountMedian':percentile(counts,.5),'localDualAreaRatioMedian':percentile(ratios,.5),'localDualAreaRatioP95':percentile(ratios,.95),'unitVsAreaFieldAngleMean':sum(diffs)/len(diffs),'unitVsAreaFieldAngleP95':percentile(diffs,.95),'unitVsAreaFieldAngleMax':max(diffs),'pointsAngleOverTwoDegrees':sum(d>2 for d in diffs),'readOnlySource':True,'actualUnityNormalArraysNotRead':True}
(O/'density-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

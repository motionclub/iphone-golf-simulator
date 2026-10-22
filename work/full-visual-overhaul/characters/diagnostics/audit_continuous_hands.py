"""Independent local-hand preservation and welded-topology audit. No exports."""
import bpy,pathlib,sys,json,math
from mathutils import Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
def capture(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST';body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body_'));body.data.update()
 names={g.index:g.name for g in body.vertex_groups};hands={s:rig.data.bones[s+'Hand'].matrix_local.inverted()@rig.matrix_world.inverted()@body.matrix_world for s in ('Left','Right')}
 data=[]
 for v in body.data.vertices:
  groups={names[g.group]:g.weight for g in v.groups};local=False
  for side,H in hands.items():
   p=H@v.co;weight=sum(w for n,w in groups.items() if n==side+'Hand' or n==side+'LowerArm' or n.startswith(side) and any(d in n for d in ('Thumb','Index','Middle','Ring','Little')))
   local|=abs(p.x)<.14 and abs(p.z)<.10 and -.005-1e-6<p.y<.25 and weight>.2
  data.append((v.co.copy(),v.normal.copy(),groups,local))
 return body,hands,data
_,_,original=capture(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_Tennis_ThumbRigV2.blend')
body,hands,new=capture(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ContinuousHandsV2.blend')
key=lambda p:tuple(round(c,6) for c in p)
lookup={key(p):(p,n,g) for p,n,g,_ in new};outside=[v for v in original if not v[3]];missing=[];position=weight=normal=0
for p,n,g,_ in outside:
 if key(p) not in lookup:missing.append(list(p));continue
 pp,nn,gg=lookup[key(p)];position=max(position,(p-pp).length);weight=max(weight,max(abs(g.get(x,0)-gg.get(x,0)) for x in set(g)|set(gg)));normal=max(normal,math.degrees(n.angle(nn,0)))
ids={};points=[];index=[]
for v in body.data.vertices:
 k=key(v.co)
 if k not in ids:ids[k]=len(points);points.append(v.co.copy())
 index.append(ids[k])
edges={}
for f in body.data.polygons:
 verts=[index[i] for i in f.vertices]
 for a,b in zip(verts,verts[1:]+verts[:1]):
  if a==b:continue
  edge=tuple(sorted((a,b)));edges[edge]=edges.get(edge,0)+1
handBoundary={s:[] for s in hands};handNonmanifold={s:0 for s in hands}
for (a,b),uses in edges.items():
 centre=(points[a]+points[b])*.5
 for side,H in hands.items():
  p=H@centre
  if abs(p.x)<.14 and abs(p.z)<.10 and -.006<p.y<.25:
   if uses==1:handBoundary[side].append([list(points[a]),list(points[b])])
   if uses>2:handNonmanifold[side]+=1
report={'sex':sex,'originalVertices':len(original),'newVertices':len(new),'outsideHandVerticesChecked':len(outside),'missingOutsideHandVertices':len(missing),'maxOutsideHandPositionDriftMetres':position,'maxOutsideHandWeightDrift':weight,'maxOutsideHandGeometricNormalAngleDegrees':normal,'weldedHandBoundaryEdges':{s:len(v) for s,v in handBoundary.items()},'weldedHandNonmanifoldEdges':handNonmanifold,'visualGate':'UNVERIFIED: actual animated fist/grip/wrist renders required','originalOutsidePreservationGate':'PASS' if not missing and position<1e-6 and weight<1e-6 else 'FAIL','weldedTopologyGate':'PASS' if all(not v for v in handBoundary.values()) and all(v==0 for v in handNonmanifold.values()) else 'FAIL'}
(R/f'proof/full-visual-overhaul/characters/continuous-hands-preservation-{sex}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

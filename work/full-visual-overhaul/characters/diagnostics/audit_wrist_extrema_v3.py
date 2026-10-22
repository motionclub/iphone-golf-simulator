import bpy,pathlib,json,sys,math
from mathutils import Matrix,Vector
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_ClosedFistV3.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));B=rig.matrix_world.inverted()@body.matrix_world;groups={g.index:g.name for g in body.vertex_groups};bpy.context.view_layer.update()
with bpy.data.libraries.load(str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_Tennis_ThumbRigV2.blend'),link=False) as (src,dst):dst.meshes=[next(n for n in src.meshes if n.startswith('Body'))]
sourcePositions={tuple(round(c,6) for c in v.co) for v in dst.meshes[0].vertices};report={}
for side in ('Left','Right'):
 H=rig.data.bones[side+'Hand'].matrix_local.inverted()@B;posedH=rig.pose.bones[side+'Hand'].matrix.inverted();record=[]
 for v in body.data.vertices:
  p=H@v.co;weights={groups[g.group]:g.weight for g in v.groups};amount=sum(w for n,w in weights.items() if n in (side+'Hand',side+'LowerArm'))
  if amount<.8 or not(-.015<p.y<.05):continue
  m=Matrix(((0,0,0,0),)*4)
  for n,w in weights.items():m+=(rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted())*w
  actual=posedH@m@B@v.co
  record.append({'index':v.index,'restHandLocal':list(p),'posedHandLocal':list(actual),'bodyLocal':list(v.co),'weights':weights,'retainedExactOriginal':tuple(round(c,6) for c in v.co) in sourcePositions,'retainedBelowCut':p.y<=.035,'radial':math.hypot(p.x,p.z)})
 bands=[]
 for lower in (-.015,-.005,.005,.015,.025,.035,.045):
  rows=[a for a in record if lower<=a['restHandLocal'][1]<lower+.01]
  if rows:bands.append({'yBand':[lower,lower+.01],'count':len(rows),'maxX':max(a['restHandLocal'][0] for a in rows),'minX':min(a['restHandLocal'][0] for a in rows),'maxZ':max(a['restHandLocal'][2] for a in rows),'minZ':min(a['restHandLocal'][2] for a in rows),'radialExtrema':sorted(rows,key=lambda a:a['radial'],reverse=True)[:3]})
 report[side]={'bands':bands}
out=R/f'proof/full-visual-overhaul/characters/wrist-extrema-v3-{sex}.json';out.write_text(json.dumps(report,indent=2));print('WRIST_EXTREMA_COMPLETE',sex,flush=True)

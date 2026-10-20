import bpy,sys,json
from io_scene_fbx import parse_fbx
from pathlib import Path
p=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emote-fluid/rollback/fbx/Male_Emote_Scuba.fbx')
r,v=parse_fbx.parse(str(p));print('version',v,type(r))
obj=next(x for x in r.elems if x.id==b'Objects');cons=next(x for x in r.elems if x.id==b'Connections')
for x in obj.elems:
 if x.id in [b'AnimationCurve',b'AnimationCurveNode',b'Model']:
  if x.id==b'AnimationCurve':
   print('CURVE',x.props[:2],[(e.id, list(e.props[0])[:8] if e.props and hasattr(e.props[0],'__len__') and not isinstance(e.props[0],bytes) else e.props) for e in x.elems]);break
  if x.id==b'Model' and any(s in x.props[1] for s in [b'Hand',b'Head']):print('MODEL',x.props)
print('connections',[(x.id,x.props) for x in cons.elems[:12]])

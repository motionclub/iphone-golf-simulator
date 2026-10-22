import bpy,sys
from io_scene_fbx import parse_fbx
r,v=parse_fbx.parse('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/emote-fluid/rollback/fbx/Male_Emote_Scuba.fbx')
obj=next(x for x in r.elems if x.id==b'Objects');cons=next(x for x in r.elems if x.id==b'Connections')
for x in obj.elems:
 if x.id==b'Model' and x.props[1].split(b'\0')[0] in [b'Rig_Male',b'Hips',b'Spine',b'Chest',b'RightHand']:
  print(x.props);print([(e.props) for e in next(e for e in x.elems if e.id==b'Properties70').elems if e.id==b'P'])

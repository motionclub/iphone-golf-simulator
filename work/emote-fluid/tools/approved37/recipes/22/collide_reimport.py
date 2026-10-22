"""Reuse collide3's independent evaluated-mesh detector on RE-IMPORTED candidate matrices.
Arguments match collide3.py. No procedural pose substitute or generator fidelity assumption.
"""
import sys,os,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];W=Path(os.environ.get('FLUID_WORK',str(R/'work/emote-fluid')));old=R/'work/emote-overhaul/scripts/collide3.py';args=sys.argv[sys.argv.index('--')+1:];tag,clip=args[:2]
z=np.load(W/'data/after'/f'trace_{tag}_{clip}.npz');names=json.loads(str(z['meta']))['bones']
class TraceClip:
 length=(len(z['M'])-1)/30
 def grip_exempt(self,t):
  bounds={'Emote_Spike':(.4,2.85),'Emote_Scuba':(.45,4.30),'Emote_Thrust':(.5,3.05),'Intro_Wave':(.2,1.7),'Intro_BringIt':(.6,2.4),'Intro_Pushups':(.3,2.5)};a,b=bounds[clip];return t<a or t>b
 def racket_attached(self,t):return not (clip=='Emote_Scuba' and .2<=t<4.1 or clip=='Intro_Pushups' and 13/30<=t<73/30)
 def solve(self,t):return {}
s=old.read_text().replace('C = EC.build(clip, H)','C = TRACE_C')
s=s.replace("prev = PV.apply_pose(rig_o, H.rig, d['basis'], d['hips'], prev)","""mods=[(m,m.show_viewport) for ob in bpy.context.scene.objects if ob.type=='MESH' for m in ob.modifiers]
    for m,enabled in mods:m.show_viewport=False
    for nm,mm in zip(TRACE_NAMES,TRACE_Z['M'][fr]):
        rig_o.pose.bones[nm].matrix=rig_o.matrix_world.inverted()@Matrix(mm.tolist())
        bpy.context.view_layer.update()
    for m,enabled in mods:m.show_viewport=enabled
    bpy.context.view_layer.update()""")
s=s.replace("rkw = d.get('racket')","rkw = {'pos':TRACE_Z['RC'][fr,:3,3],'R':TRACE_Z['RC'][fr,:3,:3]}")
ns=dict(__name__='__main__',__file__=str(old),TRACE_C=TraceClip(),TRACE_Z=z,TRACE_NAMES=names)
exec(compile(s,str(old),'exec'),ns)
if ns.get('outp'):
 p=Path(ns['outp']);j=json.loads(p.read_text());j['fbx_sha256']=json.loads(str(z['meta']))['sha256'];j['measurement']='Original collide3 evaluated-mesh detector on candidate re-import matrices';p.write_text(json.dumps(j,indent=1))

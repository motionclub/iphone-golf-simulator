"""Original 96 thresholds, candidate re-import traces, source-layer fidelity, independent collisions.
No threshold edits. The source reference is the pre-serialization authored polish, as in original G5.
"""
import os,sys,json
from pathlib import Path
import numpy as np
W=Path(os.environ.get('FLUID_WORK',str(Path(__file__).resolve().parents[1])));R=Path(__file__).resolve().parents[3];old=R/'work/emote-overhaul/scripts/check_gates2.py';s=old.read_text();s=s[:s.rfind('\nmain()')]
ns=dict(__name__='fluid_original_gates',__file__=str(old));exec(compile(s,str(old),'exec'),ns);ns['DATA']=str(W/'data/after');ns['OL']=str(W)
# Existing G1 reads existence of the very candidate file traced, with every other G1 check unchanged.
function=s[s.index('def check_hero('):s.index('\ndef main():')];function=function.replace("fbx = f'{REPO}/work/emotes/export/fbx/{\"Male\" if h.tag == \"male\" else \"Female\"}_{c}.fbx'","fbx = T[c]['meta']['path']")
exec(compile(function,str(old),'exec'),ns)
class Layer:
 def __init__(self,C,tag,clip):
  self.C=C;self.z=np.load(W/'candidate'/f'authored_{tag}_{clip}.npz');self.base=np.load(W/'data/before'/f'trace_{tag}_{clip}.npz');self.track=C.clearance_track();self._track=self.track
 def __getattr__(self,nm):return getattr(self.C,nm)
 def clearance_track(self):return self.track
 def solve(self,t):
  f=int(round(t*30));M=self.z['M'][f];pos=M[:,:3,3].copy()
  if self._track is not None and not np.any(self._track):
   saved=self.C._track;self.C._track=np.zeros_like(saved);raw=self.C.solve(t);self.C._track=saved;pos+=raw['info']['Pos']-self.base['M'][f,:,:3,3]
  return dict(info=dict(Pos=pos,Q=M[:,:3,:3]))
res={};count=0;fails=0
for tag in ['male','female']:
 h=ns['Hero'](tag);clips={c:Layer(ns['EC'].build(c,h.H),tag,c) for c in ns['CLIPS']};res[tag]=ns['check_hero'](h,clips)
 for c,gg in res[tag].items():
  for gid,g in gg.items():
   count+=1;fails+=not g['ok'];print('GATE',gid,tag,c,'PASS' if g['ok'] else 'FAIL',json.dumps(g),flush=True)
(W/'proof/existing_96.json').write_text(json.dumps(res,indent=2));(W/'proof/existing_96.md').write_text('# Original 96 gates on candidates\n\n'+''.join(f"- {gid} {tag} {c}: {'PASS' if v['ok'] else 'FAIL'} — `{json.dumps(v)}`\n" for tag,cc in res.items() for c,gg in cc.items() for gid,v in gg.items()))
print('EXISTING_GATES',count-fails,'PASS',fails,'FAIL',count,'TOTAL')

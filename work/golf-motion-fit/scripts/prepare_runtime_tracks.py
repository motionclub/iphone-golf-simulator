"""Unity-compatible scalar track objects; retain the review manifest verbatim."""
from pathlib import Path
import json,sys,numpy as np
W=Path(__file__).resolve().parents[1];R=W.parents[1]
sys.path.insert(0,str(R/'work/match-anim-set/scripts'));sys.path.insert(0,str(W/'scripts'));import kin,motions
out=W/'candidate/Unity/Assets/Resources/Golf/Animations';(out/'Correctives').mkdir(parents=True,exist_ok=True)
for sex in ['Male','Female']:
 manifest=json.loads((W/f'export/golf_manifest_{sex}.json').read_text());traces=np.load(W/f'data/animations_{sex}.npz')
 k=kin.Rig(str(R/f'work/match-anim-set/data/rig_{sex.lower()}.json'));scale=k.J['head_top'][2]/1.70465994
 for entry in manifest['clips']:
  definition=motions.definition(entry['motion']);point=k.root_origin+kin.a2w(definition['ball']*scale)
  if entry['handedness']=='left':point[0]*=-1
  entry['contactPoint']=[float(-point[0]),float(point[2]),float(-point[1])]
  ident=entry['id'];tracks=traces[ident+'_correctives'];release=[float(motions.controls(motions.definition(entry['motion']),i/120,scale)['release']) for i in range(entry['frames'])]
  doc=dict(fps=120,tracks=[dict(name=n,values=tracks[:,c].tolist()) for c,n in enumerate(entry['correctiveTracks'])],trailRelease=release)
  (out/'Correctives'/f'{ident}.json').write_text(json.dumps(doc,separators=(',',':'))+'\n')
  entry['clipPath']='Golf/Animations/'+ident;entry['correctivePath']='Golf/Animations/Correctives/'+ident
  for key in ['backswingTop','impact','recovery']:
   if entry[key] is None:entry[key]=-1
 (out/f'golf_manifest_{sex}.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('RUNTIME_TRACKS_COMPLETE')

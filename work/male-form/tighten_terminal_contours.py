"""Local in-place finger-tip/sole corrections; preserve head and body transforms."""
from pathlib import Path
import numpy as np,json
W=Path(__file__).parent;co=np.load(W/'revised_coordinates.npy');s=1.7/593
def smooth(a,b,t):v=np.clip((t-a)/(b-a),0,1);return v*v*(3-2*v)
y=654-co[:,2]/s;x=np.abs(co[:,0])/s
# The original terminal hand is short in both fixed references. Extend the
# existing fingertip vertices along the A-pose hand direction, fading at wrist.
hand=smooth(348,373,y)*smooth(201,217,x)*(1-smooth(380,390,y))
co[:,2]-=2.4*s*hand
# Both source masks end above the current last rendered sole row. Keep the
# origin fixed and correct only the terminal foot surface, at sub-centimetre scale.
foot=smooth(641,654,y)*(1-smooth(110,140,x))
co[:,2]+=.0024*foot
np.save(W/'revised_coordinates.npy',co)
base=np.load(W/'baseline/mesh.npz')['co'];dist=np.linalg.norm(co-base,axis=1)
report=json.loads((W/'coordinate-edit.json').read_text());report.update({'terminal_contour_revision':'Existing hand tips extended by up to 6.9 mm; terminal sole rows raised by up to 2.4 mm, all with smooth fades. Object origin unchanged.',
 'maximum_displacement_metres':float(dist.max()),'changed_vertices':int((dist>1e-8).sum()),'head_vertices_unchanged':bool(np.array_equal(co[base[:,2]>1.43],base[base[:,2]>1.43])),
 'height_metres':float(np.ptp(co[:,2]))})
(W/'coordinate-edit.json').write_text(json.dumps(report,indent=2));print(json.dumps({'hand_vertices':int((hand>0).sum()),'foot_vertices':int((foot>0).sum()),'height':report['height_metres']},indent=2))

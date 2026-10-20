import numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parent; b=np.load(W/'headfit.npy');c=b.copy();x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
region=smooth(.077,.106,abs(x))*smooth(1.492,1.515,z)*(1-smooth(1.580,1.604,z))
c[:,1]+=.000*region
rho=np.sqrt(((c[:,1]+.036)/.018)**2+((z-1.558)/.031)**2)
outside=smooth(.096,.107,abs(x))*smooth(1.492,1.512,z)*(1-smooth(1.58,1.596,z))
sculpt=.0015*np.exp(-((rho-.76)/.22)**2)-.006*np.exp(-(rho/.58)**2)
c[:,0]+=np.sign(x)*sculpt*outside
np.save(W/'earvolume.npy',c)
(W/'ear-volume-edit.json').write_text(json.dumps({'part':'ear volume','method':'Local existing vertex sculpt of a shallow lateral concha and rounded outer rim. No additional depth shift, separate ear mesh or remesh.','additional_depth_metres':0,'maximum_lateral_sculpt_metres':float(abs(c[:,0]-b[:,0]).max())},indent=2))

import numpy as np,json
from pathlib import Path
W=Path(__file__).resolve().parent;b=np.load(W/'baseline/mesh.npz')['co'];c=b.copy();x,y,z=b.T
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
head=smooth(1.539,1.586,z)
c[:,1]+=.12*(.065-y)*head
front=1-smooth(-.142,-.095,y)
nose=np.exp(-(x/.024)**2-((z-1.541)/.013)**2)
lip=np.exp(-(x/.050)**2-((z-1.505)/.022)**2)
c[:,1]+=front*(.016*nose+.006*lip)
knots=np.array([[1.35,0],[1.36,0],[1.375,.006],[1.390,.018],[1.405,.020],[1.420,.019],[1.435,.013],[1.450,.006],[1.466,0],[1.475,0]])
grid=np.arange(1.33,1.49,.0005);shift=np.interp(grid,knots[:,0],knots[:,1]);kernel=np.exp(-np.arange(-42,43)**2/(2*14**2));kernel/=sum(kernel);shift=np.convolve(shift,kernel,mode='same')
throat=(1-smooth(-.076,-.030,y))*(1-smooth(.052,.084,abs(x)))*smooth(1.36,1.382,z)
c[:,1]+=np.interp(z,grid,shift)*throat
rear_knots=np.array([[1.35,0],[1.36,0],[1.38,.010],[1.395,.014],[1.410,.015],[1.425,.011],[1.44,.008],[1.455,.002],[1.470,0],[1.49,0]])
rear_shift=np.convolve(np.interp(grid,rear_knots[:,0],rear_knots[:,1]),kernel,mode='same')
rear=smooth(.010,.032,y)*(1-smooth(.055,.090,abs(x)))*smooth(1.36,1.383,z)
c[:,1]+=np.interp(z,grid,rear_shift)*rear
underchin=np.exp(-(x/.044)**2-((z-1.455)/.008)**2)*(1-smooth(-.115,-.080,y))
lowerface=np.exp(-(x/.061)**2-((z-1.487)/.014)**2)*front
c[:,1]+=.005*underchin+.004*lowerface
c[z<1.36]=b[z<1.36]
np.save(W/'depth.npy',c)
assert np.array_equal(c[:,[0,2]],b[:,[0,2]]) and np.array_equal(c[z<1.36],b[z<1.36])
(W/'depth-edit.json').write_text(json.dumps({'part':'head/jaw/neck depth proportions','baseline_sha256':json.loads((W/'baseline/invariants.json').read_text())['source_sha256'],'method':'Continuous local coordinate sculpt guided by normalized head-detail profile calipers: anterior cranial depth reduced, nose/lip plane retracted, throat moved behind the retained chin with a continuous lower-neck falloff. No remesh or direct row-profile projection.','X_Z_coordinates_unchanged':True,'body_below_1_36m_unchanged':True,'changed_vertices':int(np.sum(np.any(c!=b,axis=1))),'maximum_displacement_metres':float(np.linalg.norm(c-b,axis=1).max()),'rejected_candidate':'Direct per-layer profile projection created facial ridges and was discarded before source mutation.'},indent=2))

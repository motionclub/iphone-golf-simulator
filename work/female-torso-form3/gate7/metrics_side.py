"""Side-profile torso metrics: model silhouette (numpy raster of mesh) vs plate contour (gradient edges), torso band rows."""
import numpy as np, json, sys
sys.path.insert(0,'.')
from sil import *
S2=1.7039/288.5; V0=338.5; X0=791.5
Lj={int(k):v for k,v in json.load(open('data/left_edges_grad.json')).items()}
Rj={int(k):v for k,v in json.load(open('data/right_edges_grad.json')).items()}
def plate_contour(z):
    y=V0-z/S2; yi=int(round(y/2)*2)
    lf,lb=Lj[yi]; rf,rb=Rj[yi]
    # front: left-panel front (strong) & right-panel front(left edge rb) ; back: both
    fL=(lf[0]-X0)*S2; fR=(rb[0]-1095.0)*S2
    bL=(lb[0]-X0)*S2; bR=(rf[0]-1095.0)*S2
    return 0.5*(fL+fR),0.5*(bL+bR)
_ed=np.load('data/start.npz')['edges']
def model_contour(co,T,z):
    TE=_ed[T[_ed[:,0]]&T[_ed[:,1]]]
    za=co[TE[:,0],2]; zb=co[TE[:,1],2]; ya=co[TE[:,0],1]; yb=co[TE[:,1],1]
    m=(za-z)*(zb-z)<0
    t=(z-za[m])/(zb[m]-za[m]); y=ya[m]+t*(yb[m]-ya[m])
    return y.min(),y.max()
def table(path,label):
    d=np.load('data/start.npz'); co=np.load(path) if path.endswith('.npy') else d['co']
    T=np.load('data/zone.npz')['torso']
    rows=[]
    for z in np.arange(0.84,1.30,0.02):
        pf,pb=plate_contour(z); mf,mb=model_contour(co,T,z)
        rows.append((z,pf,pb,mf,mb))
    r=np.array(rows)
    ef=np.abs(r[:,3]-r[:,1])*1000; eb=np.abs(r[:,4]-r[:,2])*1000
    print(f"{label}: side contour |err| front mean {ef.mean():.1f} mm max {ef.max():.1f}; back mean {eb.mean():.1f} mm max {eb.max():.1f}  (rows z .84-1.30)")
    return r
if __name__=='__main__':
    table('data/start.npz','before')
    for p in sys.argv[1:]: table(p,p)

def side_xor(path,label,z0=0.82,z1=1.30):
    d=np.load('data/start.npz'); co=np.load(path) if path.endswith('.npy') else d['co']
    ed=d['edges']; 
    num=0;den=0
    for z in np.arange(z0,z1+1e-9,0.004):
        pf,pb=plate_contour(z)
        za=co[ed[:,0],2]; zb=co[ed[:,1],2]; ya=co[ed[:,0],1]; yb=co[ed[:,1],1]
        m=(za-z)*(zb-z)<0
        t=(z-za[m])/(zb[m]-za[m]); y=ya[m]+t*(yb[m]-ya[m])
        # restrict to central component (|x|<0.3): all of body at that z (arms inside torso depth anyway)
        mf,mb=y.min(),y.max()
        num+=abs(mf-pf)+abs(mb-pb); den+=max(mb,pb)-min(mf,pf)
    print(f"{label}: side-profile torso band XOR ~ {100*num/den:.1f}%")
    return num/den
if __name__=='__main__':
    side_xor('data/start.npz','before')
    for p in sys.argv[1:]: side_xor(p,p)

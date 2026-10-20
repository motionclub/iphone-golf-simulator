"""Right-side foot and hand SDFs in model coordinates. Left side = mirror x -> -x."""
import numpy as np
from sdflib import Shape, smax, mesh
def rz(deg):
    a=np.radians(deg); c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
def foot(P):
    import json
    ring=json.load(open('data/ring_params.json'))
    cx=(abs(ring['1']['cx'])+abs(ring['-1']['cx']))/2; ay=(ring['1']['cy']+ring['-1']['cy'])/2; b=(ring['1']['b']+ring['-1']['b'])/2
    a=(ring['1']['a']+ring['-1']['a'])/2
    S=Shape()
    S.ecyl((cx,ay),a,b,0.125,0.190)                                      # ankle column (cut at z=0.15728)
    S.ellipsoid((cx,ay,0.190),(a,b,0.030),k=0.0)                         # closed dome above the cut (deleted later)
    S.ellipsoid((cx,ay,0.125),(a,b,0.050),k=0.0)                         # rounded lower end of the column
    piv=np.array([cx,ay,0.0]); R=rz(P['toe_out'])                        # local->world, about the ankle axis
    kp,kn=P['k_pos'],P['k_neg']
    def Y(y): return ay+(y*kp if y>0 else y*kn)                          # y relative to the ankle centre, scaled to the plate foot length
    fs=P.get('fore_shift',0.0)
    def YL(y): return Y(y)-fs*min(1.0,max(0.0,(-y-0.09)/0.062))           # forefoot stretched forward so the free toe length is shorter
    st=P['loft']
    ws=P.get('wscale',1.0); dxs=P.get('dxs',0.0)
    S.loft([(YL(y),w*ws*(P.get('heel_w',1.0) if y>0.0 else 1.0),zb,zt,cx+dxs+xo) for (y,w,zb,zt,xo) in st],pivot=piv,R=R,n=P.get('sect_n',2.6),k=0.016)
    def rp(p): return piv+R@(np.array(p)-piv)
    S.ellipsoid(rp((cx+dxs,ay+kp*0.0375,0.047)),(P.get('heel_rx',0.0290)*ws,0.0235,0.047),k=0.012,rot=R)      # rounded heel
    for (dx,tip,r) in P['toes']:
        r=r*P.get('tr',1.0); dx=dx*P.get('tspread',1.0)
        base=rp((cx+dxs+dx,Y(-0.118)-fs*0.45,r*1.05)); tp=rp((cx+dxs+dx,Y(tip)-fs*0.0,r*1.0))
        S.capsule(base,tp,r,r*0.92,k=0.002)
    return S
def finalize_foot(S,P):
    f=lambda X: smax(S.eval(X),-(X[:,2]+0.00055),0.006)
    class W: eval=staticmethod(f)
    return W
def hand(P):
    ax=lambda z: 0.232+0.17*(0.8456-z)                                    # arm axis tilts outward going down (from the baseline rings)
    S=Shape()
    S.econe(0.835,(0.2337,0.0003),0.02820,0.0281,0.930,(0.2175,0.0003),0.03440,0.0340)   # wrist cone through the real rings
    S.ellipsoid((0.2337,0.0003,0.835),(0.0282,0.0281,0.034),k=0.0)        # rounded lower end of the wrist cone
    S.ellipsoid((0.2175,0.0003,0.930),(0.0344,0.0340,0.030),k=0.0)        # closed dome above the cuts (deleted later)
    # everything below the wrist is rotated about the vertical wrist axis by psi (palm turned toward the back, thumb forward-inward)
    piv=np.array([ax(0.84)+P.get('dx',0.0),0.0003,0.0]); R=rz(-P['psi'])
    def rp(p): return piv+R@(np.array(p)-piv)
    S.ellipsoid(rp((ax(0.805)+P.get('dx',0.0),0.0,0.805)),(P['palm_rx'],P['palm_ry'],0.050),k=0.014,rot=R)          # palm
    S.ellipsoid(rp((ax(0.812)-0.004+P.get('dx',0.0),-0.024,0.812)),(0.0155,0.0155,0.030),k=0.010,rot=R)           # thenar pad
    kz=P['knuckle_z']
    for (y,L,r) in P['fingers']:
        L=L*P.get('flen',1.0)
        pts=[np.array([ax(kz)-0.002+P.get('dx',0.0),y,kz])]; ang=0.0
        seg=[L*0.42,L*0.33,L*0.25]
        for si,(ln,fl) in enumerate(zip(seg,P['flex'])):
            ang+=np.radians(fl*P.get('fscale',1.0)); dd=np.array([-np.sin(ang),P['splay']*(y/0.0255),-np.cos(ang)]); dd/=np.linalg.norm(dd)
            pts.append(pts[-1]+dd*ln)
        rr=[r*P.get('fr',1.0),r*P.get('fr',1.0)*0.96,r*P.get('fr',1.0)*0.88,r*P.get('fr',1.0)*0.80]
        pts=[rp(p) for p in pts]
        for i in range(3): S.capsule(pts[i],pts[i+1],rr[i],rr[i+1],k=0.003)
    tp=[rp(np.array(p)+np.array([P.get('dx',0.0),0,0])) for p in P['thumb']]; tr=P['thumb_r']
    for i in range(len(tp)-1): S.capsule(tp[i],tp[i+1],tr[i],tr[i+1],k=0.004)
    return S
def _toes(radii,tips,gap=0.0006):
    W=2*sum(radii)+gap*(len(radii)-1); x=-W/2; out=[]
    for r,tp in zip(radii,tips):
        c=x+r; out.append((c,tp,r)); x=c+r+gap
    return out
FOOT=dict(k_pos=1.094,k_neg=0.90,toe_out=6.0,wscale=1.1,tr=1.0,dxs=0.012,tspread=1.0,sect_n=2.3,
          loft=[(0.0460,0.0275,0.0,0.090,0.0),(0.0400,0.0300,0.0,0.101,0.0),(0.0300,0.0310,0.0,0.108,0.0),(0.0000,0.0325,0.0,0.112,0.0),(-0.0300,0.0345,0.0,0.100,-0.001),
                (-0.0600,0.0385,0.0,0.082,-0.002),(-0.0900,0.0420,0.0,0.060,-0.001),(-0.1150,0.0440,0.0,0.047,0.0),
                (-0.1280,0.0415,0.0,0.043,0.002),(-0.1350,0.0345,0.0,0.036,0.002),(-0.1410,0.0240,0.0,0.028,0.002),(-0.1450,0.0120,0.002,0.018,0.002)],
          toes=None)
FOOT['toes']=_toes([0.0119,0.0091,0.0082,0.0074,0.0069],[-0.1835,-0.1800,-0.1770,-0.1745,-0.1730],gap=0.0025)
FOOT['fore_shift']=0.0
HAND=dict(psi=55.0,palm_rx=0.0215,palm_ry=0.0345,knuckle_z=0.770,
          fingers=[(-0.0265,0.074,0.0088),(-0.0092,0.082,0.0090),(0.0088,0.076,0.0086),(0.0245,0.062,0.0078)],
          flex=[8,20,22], splay=0.012,
          thumb=[(0.2370,-0.026,0.826),(0.2340,-0.040,0.795),(0.2290,-0.047,0.768),(0.2260,-0.048,0.742)],
          thumb_r=[0.0125,0.0112,0.0098,0.0085])
if __name__=='__main__':
    import sys,time
    t=time.time()
    which=sys.argv[1]
    if which=='foot':
        W=finalize_foot(foot(FOOT),FOOT)
        V,F=mesh(W,(0.04,-0.19,-0.01),(0.23,0.14,0.23),0.0015)
    else:
        V,F=mesh(hand(HAND),(0.12,-0.09,0.66),(0.31,0.09,0.975),0.0015)
    print(which,V.shape,F.shape,time.time()-t)
    np.savez(f'data/{which}_R_raw.npz',V=V,F=F)

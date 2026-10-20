"""Step P: sagittal-profile warp of the foot/ankle front+top contour onto the plate near-foot contour (2D thin-plate-spline in (y,z), x-independent).
python stepP.py <in.npy> <out.npy> [strength 0..1]"""
import sys; sys.path.insert(0,'.')
import numpy as np
from PIL import Image, ImageDraw
from leglib import *
Z0_MIN=np.load("data/V_start.npy")[:,2].min()
V=np.load(sys.argv[1]); out=sys.argv[2]; strength=float(sys.argv[3]) if len(sys.argv)>3 else 1.0
# ---- plate near-foot sagittal contour (y, z) from both profile plates (see notes in RESULTS): instep line + shin front line
C_NEW=np.array([(-0.2235,0.030),(-0.2215,0.045),(-0.2150,0.054),(-0.2000,0.061),(-0.1800,0.067),(-0.1600,0.0705),(-0.1400,0.079),(-0.1200,0.0905),
                (-0.1000,0.099),(-0.0850,0.110),(-0.0720,0.124),(-0.0640,0.140),(-0.0620,0.160),(-0.0640,0.190),(-0.0620,0.220),(-0.0620,0.250),(-0.0660,0.300)])
CY,CZ=0.0,0.085                       # ray centre (ankle, mid height)
# ---- old contour of the left leg in the (y,z) plane (rasterised at 1 mm)
sel=LEFT&(V[:,2]<0.40)
faces=[p for p in F if all(sel[i] for i in p)]
S=1000.0; y0,z0=-0.30,-0.01; W=int(0.45*S); H=int(0.42*S)
img=Image.new('L',(W,H),0); d=ImageDraw.Draw(img)
for p in faces: d.polygon([((V[i,1]-y0)*S,(V[i,2]-z0)*S) for i in p],fill=1)
m=np.array(img,bool)
def r_old(th):
    c,s=np.cos(th),np.sin(th); rr=np.arange(0.01,0.32,0.0005)
    py=((CY+rr*c)-y0)*S; pz=((CZ+rr*s)-z0)*S
    ok=(py>=0)&(py<W-1)&(pz>=0)&(pz<H-1)
    inside=np.zeros(len(rr),bool); inside[ok]=m[pz[ok].astype(int),py[ok].astype(int)]
    idx=np.nonzero(inside)[0]
    return rr[idx[-1]] if len(idx) else np.nan
# dense new contour in polar form
t=np.linspace(0,1,2000); seg=np.cumsum(np.r_[0,np.linalg.norm(np.diff(C_NEW,axis=0),axis=1)]); seg/=seg[-1]
Y=np.interp(t,seg,C_NEW[:,0]); Z=np.interp(t,seg,C_NEW[:,1])
TH=np.arctan2(Z-CZ,Y-CY); RR=np.hypot(Y-CY,Z-CZ)
order=np.argsort(TH); TH,RR=TH[order],RR[order]
def r_new(th): 
    th=np.arctan2(np.sin(th),np.cos(th)); return np.interp(th,TH,RR,left=np.nan,right=np.nan)
ctrl=[];disp=[]
for deg in np.arange(100,196,1.5):
    th=np.radians(deg); ro=r_old(th); rn=r_new(th)
    if np.isnan(ro) or np.isnan(rn): continue
    p=np.array([CY+ro*np.cos(th),CZ+ro*np.sin(th)]); q=np.array([CY+rn*np.cos(th),CZ+rn*np.sin(th)])
    ctrl.append(p); disp.append((q-p)*strength)
n_front=len(ctrl)
# anchors: rest of the old contour (back/heel/sole) with zero displacement, the sole line, leg ring above, and interior points
for deg in list(np.arange(196,380,4)):
    th=np.radians(deg); ro=r_old(th)
    if not np.isnan(ro): ctrl.append(np.array([CY+ro*np.cos(th),CZ+ro*np.sin(th)])); disp.append(np.zeros(2))
for y in np.arange(-0.20,0.09,0.02): ctrl.append(np.array([y,0.0025])); disp.append(np.zeros(2))
for y in (-0.07,-0.02,0.03,0.07): ctrl.append(np.array([y,0.31])); disp.append(np.zeros(2))
for y in (-0.06,0.0,0.06): ctrl.append(np.array([y,0.36])); disp.append(np.zeros(2))
# interior anchors (keep the heel/back half of the foot and the leg core fixed)
for y,z in ((0.05,0.04),(0.07,0.07),(0.06,0.12),(0.05,0.2),(0.0,0.25),(0.02,0.04)): ctrl.append(np.array([y,z])); disp.append(np.zeros(2))
ctrl=np.array(ctrl); disp=np.array(disp)
print('front controls',n_front,'total',len(ctrl),'max front disp %.1f mm'%(np.abs(disp[:n_front]).max()*1000))
sc=0.05
def phi(r2): 
    r2=np.maximum(r2,1e-12); return 0.5*r2*np.log(r2)
def kern(A,B): 
    d2=((A[:,None,:]-B[None,:,:])**2).sum(-1)/(sc*sc); return phi(d2)
K=kern(ctrl,ctrl)+1e-6*np.eye(len(ctrl)); P=np.c_[np.ones(len(ctrl)),ctrl/sc]
A=np.zeros((len(ctrl)+3,len(ctrl)+3)); A[:len(ctrl),:len(ctrl)]=K; A[:len(ctrl),len(ctrl):]=P; A[len(ctrl):,:len(ctrl)]=P.T
rhs=np.zeros((len(ctrl)+3,2)); rhs[:len(ctrl)]=disp
coef=np.linalg.solve(A,rhs)
def field(Q):
    return kern(Q,ctrl)@coef[:len(ctrl)]+np.c_[np.ones(len(Q)),Q/sc]@coef[len(ctrl):]
Vn=V.copy()
for sel0 in (LEFT,RIGHT):
    s=sel0&(V[:,2]<0.34)
    Q=V[s][:,[1,2]]; D=field(Q)
    wz=smoothstep(0.34,0.27,Q[:,1])[:,None]
    Vn[s,1]=V[s,1]+D[:,0]*wz[:,0]; Vn[s,2]=np.maximum(V[s,2]+D[:,1]*wz[:,0],V[s,2]*0+Z0_MIN)
mv=np.linalg.norm(Vn-V,axis=1)*1000
print('moved',(mv>0).sum(),'max %.1f mm  rms %.1f'%(mv.max(),np.sqrt((mv[mv>0]**2).mean())),' max z moved %.3f'%V[mv>0,2].max(),' min z %.5f'%Vn[ZONE,2].min())
np.save(out,Vn)

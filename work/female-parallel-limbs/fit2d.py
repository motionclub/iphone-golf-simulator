"""Plate-silhouette fit harness for hands/feet (numpy only).
Plate target = mean over {front,back} x {left,right} of the plate polygons, in (|dx| px, y px) at plate scale.
Model mask = orthographic front projection of the SDF (right side), same grid."""
import sys, json, numpy as np
sys.path.insert(0,'../../Tools/HeroBase')
from plate_profiles import FEMALE as F
from PIL import Image, ImageDraw
S=0.0025954198473282443
def poly(pts):
    im=Image.new('L',(1280,720),0); ImageDraw.Draw(im).polygon(pts,fill=255); return np.array(im)>0
PF=poly(F['front_outline']); PB=poly(F['back_outline'])
def plate_target(xpx,ypx,sel_fn):
    """xpx: array of |dx| px bin centres, ypx: array of image rows. Returns mean mask over views/sides, shape (len(ypx),len(xpx))."""
    acc=np.zeros((len(ypx),len(xpx))); n=0
    for P,cx in ((PF,440),(PB,847)):
        for sd in (-1,1):
            cols=np.clip(np.round(cx+sd*xpx).astype(int),0,1279)
            m=P[np.ix_(ypx,cols)]
            acc+=m; n+=1
    return acc/n
def hand_zone():
    xpx=np.arange(64,118,1.0); ypx=np.arange(352,422,1)
    T=plate_target(xpx,ypx,None)
    # exclude hip/thigh: legs occupy |dx|<~72 for y>=372; keep |dx|>=76 for y>=372; arms above
    keep=np.ones_like(T,bool)
    for j,y in enumerate(ypx):
        if y>=372: keep[j,xpx<76]=False
        else: keep[j,xpx<60]=False
    return xpx,ypx,T,keep
def foot_zone():
    xpx=np.arange(4,90,1.0); ypx=np.arange(630,682,1)
    T=plate_target(xpx,ypx,None)
    keep=np.ones_like(T,bool)
    return xpx,ypx,T,keep
def model_mask(evalfn,xpx,ypx,ys,xsub=3):
    """front projection: for each (x,z) cell any y with f<0."""
    xs=xpx*S; zs=(679-ypx)*S
    X,Z=np.meshgrid(xs,zs)             # (nz,nx)
    out=np.zeros(X.shape)
    # supersample x/z by xsub for smooth coverage fraction
    off=(np.arange(xsub)+0.5)/xsub-0.5
    cnt=0
    for ox in off:
        for oz in off:
            Xs=X+ox*S; Zs=Z+oz*S
            hit=np.zeros(X.shape,bool)
            for y in ys:
                P=np.stack([Xs.ravel(),np.full(Xs.size,y),Zs.ravel()],1)
                hit|=(evalfn(P)<0).reshape(X.shape)
            out+=hit; cnt+=1
    return out/cnt
def err(M,T,keep):
    a=np.abs(M-T)[keep].sum(); u=np.maximum(M,T)[keep].sum(); return a/u

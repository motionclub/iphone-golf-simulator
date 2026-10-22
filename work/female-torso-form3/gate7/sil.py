"""Pure numpy/PIL silhouette tools at the project's frozen plate framing (S m/px)."""
import numpy as np
from PIL import Image, ImageDraw
S=0.0025954198473282443
FRONT_CX,BACK_CX,SOLE=440,847,679
def project(co,view):
    x,y,z=co[:,0],co[:,1],co[:,2]
    if view=='front': u=FRONT_CX+x/S
    elif view=='back': u=BACK_CX-x/S
    else: raise ValueError
    v=SOLE-z/S
    return np.stack([u,v],1)
def raster(uv,tri,size=(1280,720),sel=None,ss=4):
    """supersampled coverage mask (bool, alpha>=.5)"""
    W,H=size
    im=Image.new('L',(W*ss,H*ss),0); d=ImageDraw.Draw(im)
    P=uv*ss
    T=tri if sel is None else tri[sel]
    for t in T:
        d.polygon([tuple(P[t[0]]),tuple(P[t[1]]),tuple(P[t[2]])],fill=255)
    im=im.resize((W,H),Image.BOX)
    return np.asarray(im)>=128
def xor_iou(A,B,rows=None):
    if rows is not None:
        A=A[rows[0]:rows[1]]; B=B[rows[0]:rows[1]]
    u=(A|B).sum(); return float((A^B).sum()/max(u,1))

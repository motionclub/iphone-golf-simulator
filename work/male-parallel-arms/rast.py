import numpy as np
from PIL import Image, ImageDraw
def rot_z(V,yaw_deg):
    a=np.radians(yaw_deg); c,s=np.cos(a),np.sin(a)
    X=V[:,0]*c+V[:,1]*s       # camera right axis
    Y=-V[:,0]*s+V[:,1]*c      # depth (toward +Y = away from camera for yaw 0)
    return X,Y,V[:,2]
def raster(V,T,yaw,scale_pxm,tx,ty,shape,ss=2,sel=None):
    """orthographic mask. screen x = tx + scale*X ; screen y = ty - scale*Z. yaw: rotate camera around z (0=front)."""
    X,Y,Z=rot_z(V,yaw)
    sx=(tx+scale_pxm*X)*ss; sy=(ty-scale_pxm*Z)*ss
    H,W=shape
    im=Image.new('L',(W*ss,H*ss),0); d=ImageDraw.Draw(im)
    TT=T if sel is None else T[sel]
    P=np.stack([sx[TT[:,0]],sy[TT[:,0]],sx[TT[:,1]],sy[TT[:,1]],sx[TT[:,2]],sy[TT[:,2]]],1)
    for p in P: d.polygon([(p[0],p[1]),(p[2],p[3]),(p[4],p[5])],fill=255)
    im=im.resize((W,H),Image.BOX)
    return np.array(im)>127

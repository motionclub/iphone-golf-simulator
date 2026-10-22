"""python plot_profile.py <V1.npy> [<V2.npy> ...] -> proof/profile_overlay.png : sagittal (y,z) silhouette of the left leg (z<0.34) for each vertex set vs the plate near-foot contour"""
import sys; sys.path.insert(0,'.')
import numpy as np
from PIL import Image, ImageDraw
from leglib import *
import importlib
C_NEW=[(-0.2235,0.030),(-0.2215,0.045),(-0.2150,0.054),(-0.2000,0.061),(-0.1800,0.067),(-0.1600,0.0705),(-0.1400,0.079),(-0.1200,0.0905),(-0.1000,0.099),(-0.0850,0.110),(-0.0720,0.124),(-0.0640,0.140),(-0.0620,0.160),(-0.0640,0.190),(-0.0620,0.220),(-0.0620,0.250),(-0.0660,0.300)]
S=3000; y0,z0=-0.26,-0.01; W=int(0.38*S); H=int(0.36*S)
cols=[(80,160,255),(255,90,90),(255,200,60),(120,255,120)]
files=sys.argv[1:]
img=Image.new('RGB',(W,H),(30,30,34)); d=ImageDraw.Draw(img)
# grid
for z in np.arange(0,0.36,0.05): yy=H-(z-z0)*S; d.line([0,yy,W,yy],fill=(60,60,40)); d.text((2,yy-10),'z%.2f'%z,fill=(180,180,60))
for y in np.arange(-0.25,0.12,0.05): xx=(y-y0)*S; d.line([xx,0,xx,H],fill=(40,60,60)); d.text((xx+2,2),'y%.2f'%y,fill=(80,180,180))
for k,f in enumerate(files):
    V=np.load(f); sel=LEFT&(V[:,2]<0.34); faces=[p for p in F if all(sel[i] for i in p)]
    m=Image.new('L',(W,H),0); dd=ImageDraw.Draw(m)
    for p in faces: dd.polygon([((V[i,1]-y0)*S,H-(V[i,2]-z0)*S) for i in p],fill=1)
    a=np.array(m,bool); e=a&~(np.roll(a,1,0)&np.roll(a,-1,0)&np.roll(a,1,1)&np.roll(a,-1,1))
    ys,xs=np.nonzero(e); 
    px=np.array(img); px[ys,xs]=cols[k%4]; img=Image.fromarray(px); d=ImageDraw.Draw(img)
pts=[((y-y0)*S,H-(z-z0)*S) for y,z in C_NEW]; d.line(pts,fill=(255,255,255),width=2)
for p in pts: d.ellipse([p[0]-3,p[1]-3,p[0]+3,p[1]+3],outline=(255,255,255))
img.save('proof/profile_overlay.png'); print(img.size)

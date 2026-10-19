"""preview_shoe.py <tag> <design> <side> [out] : 6-view sheet of a shoe4 build (numpy painter), panels coloured from the design polygons."""
import sys, os, json, math; sys.path.insert(0,'tools'); sys.path.insert(0,'../clothing-v2/py')
import numpy as np
from PIL import Image, ImageDraw
from raster import render
tag, design, side = sys.argv[1:4]; out = sys.argv[4] if len(sys.argv)>4 else f'build/{tag}_sheet.png'
d = np.load(f'build/{tag}.npz'); P, T = d['P'], d['T']; kind = d['f_face_kind']; mat = d['f_mat']
import importlib.util
src=open('../clothing-v2/py/shoe4.py').read().split('\ndef prof(')[0]   # design functions only (no bpy)
import re as _re; ns={'__file__':'../clothing-v2/py/shoe4.py'}; exec(_re.sub(r'(?m)^(import bpy.*|from polo2 .*|from shoe2 .*)$', '', src), ns)
D = ns['DESIGNS'][design]()
s4 = d['v_s4'][T].mean(1); h4 = d['v_h4'][T].mean(1)
def inpoly(x,y,poly):
    poly=np.asarray(poly); c=np.zeros(len(x),bool)
    for i in range(len(poly)):
        (x1,y1),(x2,y2)=poly[i],poly[(i+1)%len(poly)]
        c^=((y1>y)!=(y2>y))&(x<(x2-x1)*(y-y1)/(y2-y1+1e-12)+x1)
    return c
WHITE=(242,242,240); NAVY=(34,48,90); GREY=(160,160,160); HW=(170,175,182)
col=np.tile(np.array(WHITE),(len(T),1))
up=kind==19
trim=np.zeros(len(T),bool)
for poly in D['panels']['trim']: trim|=inpoly(s4,h4,poly)
col[up&trim & (mat!=1)]=NAVY
col[up&(mat==1)]=NAVY if D['colours']['collar_trim'] else WHITE      # lining
col[(kind==12)|(kind==17)]=NAVY
sole=kind==9
z=P[T][:,:,2].mean(1)
Ls=D['Ls']; zb=D['zb']
os_top = zb + np.interp(s4, *np.array(sorted(D['os_top'])).T)*Ls
if D['colours']['sole_trim']: col[sole]=NAVY
else: col[sole & (z<os_top+.0004)] = GREY
col[kind==10]=HW
# perforations hint: darker dots on faces inside the perf polygon
pf=D['panels'].get('perf')
items=[(P,T,None)]
def draw(view, scale, org, size):
    W,H=size; img=Image.new('RGB',size,(214,212,208)); dr=ImageDraw.Draw(img)
    V=np.asarray(view,float); Q=(P-org)@V.T
    n=np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]); n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
    Lg=np.array([.35,-.45,.82]); Lg/=np.linalg.norm(Lg)
    nv=n@V.T
    sh=np.clip(n@Lg,0,1)*.55+.45
    dep=Q[T,2].mean(1); xs=W/2+Q[T,0]*scale; ys=H/2-Q[T,1]*scale
    for i in np.argsort(dep):
        c=tuple(int(v) for v in col[i]*sh[i]); dr.polygon([(xs[i,0],ys[i,0]),(xs[i,1],ys[i,1]),(xs[i,2],ys[i,2])],fill=c)
    return img
c=P.mean(0); sc=1150
# frame axes: shoe long axis ~ -Y (toe toward -y), right shoe lateral = +x
lat = np.array([1,0,0]) if side=='R' else np.array([-1,0,0])
views = {
 'lateral': [[0,-1,0],[0,0,1],[1,0,0]] if side=='R' else [[0,1,0],[0,0,1],[-1,0,0]],
 'medial':  [[0,1,0],[0,0,1],[-1,0,0]] if side=='R' else [[0,-1,0],[0,0,1],[1,0,0]],
 'front': [[1,0,0],[0,0,1],[0,-1,0]],
 'back': [[-1,0,0],[0,0,1],[0,1,0]],
 'top': [[0,-1,0],[-1,0,0],[0,0,1]],
 'sole': [[0,-1,0],[1,0,0],[0,0,-1]]}
tiles=[]
for nm in ['lateral','medial','front','back','top','sole']:
    im=draw(views[nm],sc,c,(560,360)); ImageDraw.Draw(im).text((8,6),nm,fill=(0,0,0)); tiles.append(im)
sheet=Image.new('RGB',(560*3,360*2))
for i,t in enumerate(tiles): sheet.paste(t,((i%3)*560,(i//3)*360))
sheet.save(out); print(out, len(T),'tris')

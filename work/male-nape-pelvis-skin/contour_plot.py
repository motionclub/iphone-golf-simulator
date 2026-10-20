"""rear contour curves (plate L/R px-edge, start, candidates at 4x) in the glute band: python3.13 contour_plot.py out.png z0 z1 tag..."""
import sys, json
sys.path.insert(0,'.')
import numpy as np
from PIL import Image, ImageDraw
from contours import CAM, mask, M, Path
out=sys.argv[1]; z0=float(sys.argv[2]); z1=float(sys.argv[3]); tags=sys.argv[4:]
S=2400  # px per metre in plot
def edge(img, view, rp, zs):
    c=CAM[view]; m=img; res=[]
    for z in zs:
        r=int(round((c['sole_y']-z/c['metres_per_pixel'])*rp)); xs=np.where(m[r])[0]
        if len(xs)==0: res.append(np.nan); continue
        if view=='left': res.append((xs[-1]+1)/rp-c['centre_x']) if True else None
        else: res.append(c['centre_x']-(xs[0])/rp)
    return np.array(res)*c['metres_per_pixel']
zs=np.arange(z0,z1,0.001)
W=int(0.14*S); H=int((z1-z0)*S); im=Image.new('RGB',(W+40,H+20),(18,18,22)); d=ImageDraw.Draw(im)
def col(y): return 20+(y-0.03)*S
def row(z): return 10+(z1-z)*S
for z in np.arange(np.ceil(z0*20)/20,z1,0.05): d.line([(20,row(z)),(W+20,row(z))],fill=(50,50,70)); d.text((22,row(z)-10),f'{z:.2f}',fill=(120,120,160))
for y in np.arange(0.03,0.17,0.02): d.line([(col(y),10),(col(y),H+10)],fill=(50,50,70)); d.text((col(y)+2,12),f'{y*1000:.0f}',fill=(120,120,160))
# plate masks (1x)
for view,colr in (('left',(255,200,60)),('right',(255,130,40))):
    e=edge(mask(M/f'{view}_target.png'),view,1,zs); pts=[(col(e[i]),row(zs[i])) for i in range(len(zs)) if np.isfinite(e[i])]; d.line(pts,fill=colr,width=2)
cols={'start':(120,200,255)}
pal=[(120,200,255),(90,255,140),(255,90,200),(200,160,255)]
for k,t in enumerate(tags):
    for view,dash in (('left',0),):
        img=np.asarray(Image.open(f'r/{t}_sil4/{view}@4.png'))[...,3]>127
        e=edge(img,view,4,zs); pts=[(col(e[i]),row(zs[i])) for i in range(len(zs)) if np.isfinite(e[i])]; d.line(pts,fill=pal[k%4],width=2)
        d.text((W-60,14+14*k),t,fill=pal[k%4])
d.text((W-60,14+14*len(tags)),'plate L',fill=(255,200,60)); d.text((W-60,28+14*len(tags)),'plate R',fill=(255,130,40))
im.save(out); print(im.size)

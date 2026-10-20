"""2-D prototype: ring cross-section (x,y) at a given z with base ellipse + dome/lobe fields; look at the shape quality."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
def bump(rho,p): return np.clip(1-rho**2,0,1)**p
def smax(a,b,k):
    h=np.clip(k-np.abs(a-b),0,None)/k
    return np.maximum(a,b)+h*h*k/4
def ring_y(x,a,cy,b,front):    # half ellipse
    s=np.sqrt(np.clip(1-(x/a)**2,0,1)); return cy-b*s if front else cy+b*s
def draw(curves,box,scale=2600,title=''):
    W,H=box; im=Image.new('RGB',(W,H),(20,20,24)); d=ImageDraw.Draw(im); cx=W//2; cy=H//2
    for xm in np.arange(-0.2,0.201,0.05): d.line([(cx+xm*scale,0),(cx+xm*scale,H)],fill=(45,45,55))
    for ym in np.arange(-0.2,0.201,0.05): d.line([(0,cy+ym*scale),(W,cy+ym*scale)],fill=(45,45,55))
    for pts,col in curves:
        d.line([(cx+x*scale,cy+y*scale) for x,y in pts],fill=col,width=2)
    d.text((6,4),title,font=FONT,fill=(255,255,255)); return im
x=np.linspace(-0.175,0.175,700)
# -------- glutes at z=0.865: base ellipse a=0.175 (hip), front -0.1088, back base 0.085 ; lobes
def glute_section(zc_ratio=1.0,xc=0.075,rx=0.085,A=0.041,p=1.5,k=0.012,sumlobes=False):
    a=0.175; F=-0.1088; Bb=0.085; cy=0.5*(F+Bb); b=0.5*(Bb-F)
    base=ring_y(x,a,cy,b,False)
    l1=A*zc_ratio*bump((x-xc)/rx,p); l2=A*zc_ratio*bump((x+xc)/rx,p)
    lob=l1+l2 if sumlobes else smax(l1,l2,k)
    return base,base+lob,base+l1
curves=[]
cols=[(120,200,255),(255,160,60),(120,255,140)]
for i,(xc,rx,A,p) in enumerate([(0.075,0.085,0.041,1.5),(0.065,0.080,0.041,1.5),(0.075,0.085,0.041,2.0),(0.07,0.09,0.045,1.2)]):
    base,tot,_=glute_section(xc=xc,rx=rx,A=A,p=p)
    curves.append((list(zip(x,tot)),cols[i%3]))
base,tot,_=glute_section(); curves.append((list(zip(x,base)),(160,160,160)))
# plate: envelope 0.1165 at lobe apex
im=draw(curves,(900,500),title='glute section z=0.865 (back down? y>0 down): colours = param sets; grey = base ellipse')
im.save('data/proto_glute.png')
for xc,rx,A,p in [(0.075,0.085,0.041,1.5),(0.065,0.080,0.041,1.5),(0.075,0.085,0.041,2.0),(0.07,0.09,0.045,1.2)]:
    base,tot,_=glute_section(xc=xc,rx=rx,A=A,p=p)
    i0=np.argmin(np.abs(x)); ia=np.argmax(tot)
    print(f'xc {xc} rx {rx} A {A} p {p}: apex y {tot.max():.4f} at x={x[ia]:+.3f}; cleft(x=0) y {tot[i0]:.4f} -> depth {1000*(tot.max()-tot[i0]):.1f} mm; width at half depth {1000*2*abs(x[np.argmin(np.abs(tot[x>0]-(tot.max()+tot[i0])/2))+len(x)//2]) :.0f} mm')

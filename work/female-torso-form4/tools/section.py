"""exact-height cross sections of the zone surface (edge crossings -> ordered polyline).  python3 tools/section.py back|front out.png z1,z2,.. a.npy[:color] b.npy ..."""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
WD='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/'
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
O=np.load(WD+'data/orig.npz'); ED=O['edges']; T=np.load(WD+'data/zone_chat7.npz')['torso']
TE=ED[T[ED[:,0]]&T[ED[:,1]]]
def crossing(co,z):
    a,b=co[TE[:,0]],co[TE[:,1]]
    m=(a[:,2]-z)*(b[:,2]-z)<0
    t=(z-a[m,2])/(b[m,2]-a[m,2]); p=a[m]+t[:,None]*(b[m]-a[m])
    return p[:,0],p[:,1]
def section_plot(side,zs,arrs,out,xr=(-0.18,0.18),scale=2400,cell=(760,520)):
    cols=min(3,len(zs)); rows=(len(zs)+cols-1)//cols
    im=Image.new('RGB',(cell[0]*cols,cell[1]*rows),(20,20,24)); d=ImageDraw.Draw(im)
    yr=(0.0,0.14) if side=='back' else (-0.14,0.0)
    for k,z in enumerate(zs):
        ox=(k%cols)*cell[0]; oy=(k//cols)*cell[1]
        d.rectangle([ox,oy,ox+cell[0]-1,oy+cell[1]-1],outline=(60,60,70))
        cx=ox+cell[0]//2
        def U(x): return cx+x*scale
        def V(y): return oy+30+((y-yr[0]) if side=='back' else (yr[1]-y))*scale   # back: back=down ; front: front=down
        for xm in np.arange(-0.2,0.201,0.02): d.line([(U(xm),oy+22),(U(xm),oy+cell[1])],fill=(38,38,48)); 
        for xm in np.arange(-0.2,0.201,0.04): d.text((U(xm)+2,oy+cell[1]-16),f'{xm*100:.0f}',font=FONT,fill=(110,110,120))
        for ym in np.arange(0.0,0.141,0.02):
            yy=ym if side=='back' else -ym
            d.line([(ox,V(yy)),(ox+cell[0],V(yy))],fill=(38,38,48)); d.text((ox+3,V(yy)+1),f'{abs(ym)*100:.0f}',font=FONT,fill=(110,110,120))
        d.text((ox+6,oy+4),f'z={z:.3f}  {side} contour (cm grid)',font=FONT,fill=(255,255,255))
        for co,col,lab in arrs:
            x,y=crossing(co,z)
            sel=(y>0) if side=='back' else (y<0)
            x,y=x[sel],y[sel]
            o=np.argsort(x)
            pts=[(U(x[i]),V(y[i])) for i in o]
            if len(pts)>1: d.line(pts,fill=col,width=2)
            for p in pts: d.ellipse([p[0]-2,p[1]-2,p[0]+2,p[1]+2],fill=col)
    im.save(WD+out); print(WD+out,im.size)
if __name__=='__main__':
    side=sys.argv[1]; out=sys.argv[2]; zs=[float(v) for v in sys.argv[3].split(',')]
    palette=[(255,140,60),(120,220,255),(130,255,140),(255,120,200)]
    arrs=[]
    for i,a in enumerate(sys.argv[4:]):
        name,_,lab=a.partition(':')
        co=np.load(WD+name) if name.endswith('.npy') else np.load(WD+name)['co'].astype(np.float64)
        arrs.append((co,palette[i%4],lab or name))
    section_plot(side,zs,arrs,out)

"""sagittal sections: python3 tools/sag.py out.png zlo zhi side(back|front) x1,x2,.. a.npy:label ... """
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
WD='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/'
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
O=np.load(WD+'data/orig.npz'); ED=O['edges']; CO0=O['co'].astype(np.float64)
def crossing_x(co,x,sel=None):
    a,b=co[ED[:,0]],co[ED[:,1]]
    m=(a[:,0]-x)*(b[:,0]-x)<0
    if sel is not None: m&=sel
    t=(x-a[m,0])/(b[m,0]-a[m,0]); p=a[m]+t[:,None]*(b[m]-a[m]); return p
def plot(out,zlo,zhi,side,xs,arrs,scale=3200,cell=(520,820)):
    cols=len(xs); im=Image.new('RGB',(cell[0]*cols,cell[1]),(20,20,24)); d=ImageDraw.Draw(im)
    yr=(0.04,0.13) if side=='back' else (-0.14,-0.05)
    from targets import curves
    (FZ,F1),(BZ,B1)=curves()
    plate_front=lambda z: np.interp(z,FZ,F1); plate_back=lambda z: np.interp(z,BZ,B1)
    for k,x in enumerate(xs):
        ox=k*cell[0]
        d.rectangle([ox,0,ox+cell[0]-1,cell[1]-1],outline=(60,60,70))
        def U(y): return ox+30+((y-yr[0]) if side=='back' else (yr[1]-y))*scale
        def V(z): return cell[1]-30-(z-zlo)*scale
        for zz in np.arange(np.ceil(zlo*50)/50,zhi,0.02):
            d.line([(ox,V(zz)),(ox+cell[0],V(zz))],fill=(38,38,48)); d.text((ox+3,V(zz)-14),f'{zz:.2f}',font=FONT,fill=(110,110,120))
        for yy in np.arange(0.04,0.14,0.01):
            yv=yy if side=='back' else -yy
            d.line([(U(yv),0),(U(yv),cell[1])],fill=(38,38,48)); d.text((U(yv)+2,cell[1]-16),f'{yy*100:.0f}',font=FONT,fill=(110,110,120))
        d.text((ox+6,4),f'x={x:+.3f}  {side} sagittal',font=FONT,fill=(255,255,255))
        # plate envelope
        zz=np.arange(zlo,zhi,0.004); pe=[plate_back(v) if side=='back' else plate_front(v) for v in zz]
        d.line([(U(y),V(z)) for y,z in zip(pe,zz)],fill=(255,215,0),width=1)
        for ai,(co,col,lab) in enumerate(arrs):
            p=crossing_x(co,x)
            sel=(p[:,1]>0) if side=='back' else (p[:,1]<0)
            p=p[sel]; p=p[(p[:,2]>zlo)&(p[:,2]<zhi)]
            o=np.argsort(p[:,2]); pts=[(U(p[i,1]),V(p[i,2])) for i in o]
            if len(pts)>1: d.line(pts,fill=col,width=2)
            for q in pts: d.ellipse([q[0]-2,q[1]-2,q[0]+2,q[1]+2],fill=col)
            d.text((ox+8,22+16*ai),lab,font=FONT,fill=col)
    im.save(WD+out); print(WD+out,im.size)
if __name__=='__main__':
    out=sys.argv[1]; zlo,zhi=float(sys.argv[2]),float(sys.argv[3]); side=sys.argv[4]; xs=[float(v) for v in sys.argv[5].split(',')]
    pal=[(255,140,60),(120,220,255),(130,255,140),(255,120,200)]; arrs=[]
    for i,a in enumerate(sys.argv[6:]):
        name,_,lab=a.partition(':'); arrs.append((np.load(WD+name),pal[i%4],lab or name))
    plot(out,zlo,zhi,side,xs,arrs)

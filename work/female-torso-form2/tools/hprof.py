"""horizontal luminance profiles at given z: plate vs plate-lit renders.  python3 tools/hprof.py out.png view z1,z2,.. tag ..."""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from platelit import *
from PIL import Image, ImageDraw, ImageFont
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
def run(out,view,zs,tags,xr=(-0.15,0.15)):
    bald=gblur(BALD,1.5); pl={t:gblur(np.asarray(Image.open(W/f'proof/scratch/pl_{t}_{view}.png').convert('L')).astype(float),1.5) for t in tags}
    cols=[(255,255,255),(255,140,60),(120,220,255),(130,255,140)]
    Wd,H=1500,330; n=len(zs); im=Image.new('RGB',(Wd,H*((n+2)//3)),(20,20,24)); d=ImageDraw.Draw(im)
    cx=FRONT_CX if view=='front' else BACK_CX; sg=1 if view=='front' else -1
    for k,z in enumerate(zs):
        ox=(k%3)*(Wd//3); oy=(k//3)*H
        d.rectangle([ox,oy,ox+Wd//3-1,oy+H-1],outline=(60,60,70)); d.text((ox+6,oy+4),f'{view}  z={z:.3f}  luminance vs x (cm; +x viewer-{"right" if view=="front" else "left"})',font=FONT,fill=(255,255,255))
        xs=np.arange(xr[0],xr[1],0.002); row=int(round(SOLE-z/S))
        def X(x): return ox+30+(x-xr[0])/(xr[1]-xr[0])*(Wd//3-50)
        for xm in np.arange(-0.14,0.141,0.02): d.line([(X(xm),oy+20),(X(xm),oy+H-20)],fill=(45,45,55)); d.text((X(xm)-8,oy+H-18),f'{xm*100:.0f}',font=FONT,fill=(150,150,160))
        series=[('plate',bald,cols[0])]+[(t,pl[t],cols[1+i]) for i,t in enumerate(tags)]
        allv=[]
        for lab,img,col in series:
            L=np.array([img[row-1:row+2,int(round(cx+sg*x/S))].mean() for x in xs]); allv.append(L)
        lo=min(a.min() for a in allv); hi=max(a.max() for a in allv)
        for i,((lab,img,col),L) in enumerate(zip(series,allv)):
            pts=[(X(x),oy+H-30-(l-lo)/(hi-lo+1e-6)*(H-60)) for x,l in zip(xs,L)]; d.line(pts,fill=col,width=2); d.text((ox+10,oy+22+i*15),lab,font=FONT,fill=col)
    im.save(W/out); print(out)
if __name__=='__main__':
    run(sys.argv[1],sys.argv[2],[float(v) for v in sys.argv[3].split(',')],sys.argv[4:])

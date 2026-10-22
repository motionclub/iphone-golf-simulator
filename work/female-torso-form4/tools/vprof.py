"""vertical luminance profiles: plate vs plate-lit renders.  python3 tools/vprof.py out.png tag [tag ...]"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from platelit import *
from PIL import Image, ImageDraw, ImageFont
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
def gb(a,s): return gblur(a,s)
def profiles(tags,out):
    bald=gb(BALD,1.5)
    specs=[('front',[('dome L',440-0.072/S),('sternum',440.0),('dome R',440+0.072/S)],(1.10,1.34)),('back',[('lobe',847-0.072/S),('cleft',847.0),('lobe',847+0.072/S)],(0.78,1.04))]
    cols=[(255,255,255),(255,140,60),(120,220,255),(130,255,140),(255,120,200)]
    Wd,H=1500,420
    im=Image.new('RGB',(Wd,H*2),(20,20,24)); d=ImageDraw.Draw(im)
    for ri,(view,cs,(z0,z1)) in enumerate(specs):
        pl={t:gb(np.asarray(Image.open(W/f'proof/scratch/pl_{t}_{view}.png').convert('L')).astype(float),1.5) for t in tags}
        for ci,(name,u) in enumerate(cs):
            ox=ci*(Wd//3); oy=ri*H
            d.rectangle([ox,oy,ox+Wd//3-1,oy+H-1],outline=(60,60,70)); d.text((ox+6,oy+4),f'{view} {name} (u={u:.0f})  luminance vs z',font=FONT,fill=(255,255,255))
            def X(z): return ox+40+(z-z0)/(z1-z0)*(Wd//3-60)
            def Y(l): return oy+H-30-(l-120)/(255-120)*(H-60)
            for zz in np.arange(np.ceil(z0*20)/20,z1,0.05): d.line([(X(zz),oy+20),(X(zz),oy+H-20)],fill=(45,45,55)); d.text((X(zz)-12,oy+H-22),f'{zz:.2f}',font=FONT,fill=(150,150,160))
            zs=np.arange(z0,z1,0.004)
            rows=SOLE-zs/S
            def samp(img,u): return np.array([img[int(round(r)),int(round(u))-1:int(round(u))+2].mean() for r in rows])
            for lab,img,col in [('plate',bald,cols[0])]+[(t,pl[t],cols[1+i]) for i,t in enumerate(tags)]:
                if lab=='plate': L=samp(img,u)
                else: L=samp(img,u)
                pts=[(X(z),Y(l)) for z,l in zip(zs,L)]; d.line(pts,fill=col,width=2)
            for i,(lab,col) in enumerate([('plate',cols[0])]+[(t,cols[1+i]) for i,t in enumerate(tags)]):
                d.text((ox+10,oy+24+i*16),lab,font=FONT,fill=col)
    im.save(W/out); print(out)
if __name__=='__main__': profiles(sys.argv[2:],sys.argv[1])

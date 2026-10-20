"""zoomed plate profile panels with model envelope overlay.  python3 tools/profile_zoom.py out.png coords.npy z0 z1 side(back|front)"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from torso2 import *
from fplate import SHEET
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',14)
S2=1.7039/288.5; V0=338.5; X0={'L':791.5,'R':1095.0}
def run(out,co,z0,z1,side,scale=9):
    fe,be=section_extents(co); fe,be=fillnan(fe),fillnan(be)
    panels=[]
    for pn in ('L','R'):
        x0=X0[pn]; sg=1 if pn=='L' else 1          # both profile panels face left (front on the left of the picture)
        y_lo,y_hi=(0.0,0.16) if side=='back' else (-0.16,0.0)
        u0=x0+y_lo/S2; u1=x0+y_hi/S2; v0=V0-z1/S2; v1=V0-z0/S2
        crop=SHEET.astype(np.uint8); im=Image.fromarray(crop).crop((int(u0),int(v0),int(u1),int(v1))).convert('RGB')
        im=ImageEnhance.Contrast(im).enhance(1.8).resize((im.width*scale,im.height*scale),Image.BICUBIC)
        d=ImageDraw.Draw(im)
        def U(y): return (x0+y/S2-int(u0))*scale
        def Vz(z): return (V0-z/S2-int(v0))*scale
        for zz in np.arange(np.ceil(z0*50)/50,z1,0.02): d.line([(0,Vz(zz)),(im.width,Vz(zz))],fill=(0,255,120)); d.text((2,Vz(zz)+1),f'{zz:.2f}',font=FONT,fill=(0,255,120))
        for yy in np.arange(np.ceil(y_lo*50)/50,y_hi,0.02): d.line([(U(yy),0),(U(yy),im.height)],fill=(255,255,0)); d.text((U(yy)+2,2),f'{yy*100:.0f}',font=FONT,fill=(255,255,0))
        zs=np.arange(z0,z1,0.002); idx=np.round((zs-0.80)/0.002).astype(int); idx=np.clip(idx,0,len(fe)-1)
        env=be[idx] if side=='back' else fe[idx]
        d.line([(U(y),Vz(z)) for y,z in zip(env,zs)],fill=(80,200,255),width=2)
        tab=np.array([plate_back(z) if side=='back' else plate_front(z) for z in zs])
        for z,y in list(zip(zs,tab))[::6]: d.ellipse([U(y)-4,Vz(z)-4,U(y)+4,Vz(z)+4],outline=(255,220,0),width=2)
        d.text((8,im.height-20),f'{pn} profile panel; cyan = model envelope; yellow rings = plate table (chat7)',font=FONT,fill=(255,255,255))
        panels.append(im)
    Wd=panels[0].width+panels[1].width; S_=Image.new('RGB',(Wd,panels[0].height)); S_.paste(panels[0],(0,0)); S_.paste(panels[1],(panels[0].width,0)); S_.save(WD/out); print(out,S_.size)
if __name__=='__main__':
    co=np.load(WD/sys.argv[2]); run(sys.argv[1],co,float(sys.argv[3]),float(sys.argv[4]),sys.argv[5])

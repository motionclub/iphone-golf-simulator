"""python gridcmp.py <renderdir> <view> <x0,x1,z0,z1 in metres> <out.png> [zoom]
plate crop | mesh render crop, both with a world grid (1 cm minor, 5 cm major, labelled) for the locked orthographic views (bald_front, bald_back, sheet_front, sheet_back, left, right).
x is the camera's horizontal axis in metres from the body origin (positive = image right), z height."""
import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
D,view,box,outp=sys.argv[1:5]; zoom=int(sys.argv[5]) if len(sys.argv)>5 else 8
x0,x1,z0,z1=map(float,box.split(','))
cams={v['name']:v for v in json.load(open(R+'/work/male-silhouette/reference-cameras.json'))['views']}
c=cams[view]; mpp=c['metres_per_pixel']; sole=c['sole_y']; cx=c['centre_x']
plate=Image.open(R+'/ArtDir/hero/base_lock/'+('male_body_bald.jpg' if view.startswith('bald') else 'male_multiangle_body.jpg')).convert('RGB')
mesh=Image.open(f'{D}/{view}.png').convert('RGBA')
bg=Image.new('RGBA',mesh.size,(54,54,58,255)); bg.alpha_composite(mesh); mesh=bg.convert('RGB')
sign=-1 if view in ('bald_back','sheet_back') else 1      # back cameras look the other way: image right = -x
def px(x,z): return cx+sign*x/mpp, sole-z/mpp
pa=px(x0,z1); pb=px(x1,z0)
xl,xr=sorted((pa[0],pb[0])); yt,yb=pa[1],pb[1]
def crop(im):
    return im.crop((int(xl),int(yt),int(xr),int(yb))).resize((int((int(xr)-int(xl))*zoom),int((int(yb)-int(yt))*zoom)),Image.LANCZOS)
tiles=[]
for im in (plate,mesh):
    t=crop(im)
    # grid: faint major (5 cm) lines + edge ticks every cm
    ov=Image.new('RGBA',t.size,(0,0,0,0)); od=ImageDraw.Draw(ov)
    for zz in np.arange(np.ceil(z0*100)/100,z1+1e-9,0.01):
        _,y=px(0,zz); yy=(y-int(yt))*zoom; maj=abs(round(zz*100)%5)<1e-6
        if maj: od.line([(0,yy),(t.width,yy)],fill=(255,255,0,70),width=1); od.text((2,yy+1),f'z{zz*100:.0f}',fill=(255,255,0,255))
        od.line([(0,yy),(8 if not maj else 16,yy)],fill=(255,255,0,255),width=1)
    for xx in np.arange(np.ceil(min(x0,x1)*100)/100,max(x0,x1)+1e-9,0.01):
        xp,_=px(xx,0); xxp=(xp-int(xl))*zoom; maj=abs(round(xx*100)%5)<1e-6
        if maj: od.line([(xxp,0),(xxp,t.height)],fill=(0,255,255,70),width=1); od.text((xxp+2,12),f'x{xx*100:.0f}',fill=(0,255,255,255))
        od.line([(xxp,0),(xxp,8 if not maj else 16)],fill=(0,255,255,255),width=1)
    t=Image.alpha_composite(t.convert('RGBA'),ov).convert('RGB')
    tiles.append(t)
sh=Image.new('RGB',(tiles[0].width*2+6,tiles[0].height)); sh.paste(tiles[0],(0,0)); sh.paste(tiles[1],(tiles[0].width+6,0)); sh.save(outp); print(sh.size)

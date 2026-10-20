import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
D=R+'work/male-parallel-legs/proof/full/plate/'
BGC=(54,54,58)
def load_render(name):
    im=Image.open(D+name+'.png').convert('RGBA'); bg=Image.new('RGBA',im.size,BGC+(255,)); bg.alpha_composite(im); return bg.convert('RGB'),np.array(im)[:,:,3]>127
def edge(m):
    e=np.zeros_like(m); e[1:-1,1:-1]=m[1:-1,1:-1]&~(m[:-2,1:-1]&m[2:,1:-1]&m[1:-1,:-2]&m[1:-1,2:]); return e
def label(im,txt):
    d=ImageDraw.Draw(im); d.rectangle([0,0,len(txt)*7+10,16],fill=(0,0,0)); d.text((4,2),txt,fill=(255,255,0)); return im
cams={v['name']:v for v in json.load(open(R+'work/male-silhouette/reference-cameras.json'))['views']}
plate_b=Image.open(R+'ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB')
rows=[]
for v,roi in (('bald_front',(100,40,610,665)),('bald_back',(670,40,1165,665))):
    x0,y0,x1,y1=roi
    rn,mask=load_render(v)                       # 2x render
    S=2
    plate=plate_b.crop(roi).resize(((x1-x0)*S,(y1-y0)*S),Image.LANCZOS)
    mod=rn.crop((x0*S,y0*S,x1*S,y1*S))
    # outline overlay of the model silhouette on the plate
    pm=np.array(plate).copy(); mm=mask[y0*S:y1*S,x0*S:x1*S]; pm[edge(mm)]=(255,50,50)
    ov=Image.fromarray(pm)
    z=0.62
    tiles=[label(t.resize((int(t.width*z),int(t.height*z)),Image.LANCZOS),l) for t,l in ((plate,'REFERENCE PLATE '+v),(mod,'MODEL (installed: torso+arms+legs; head = Micro1i)'),(ov,'model outline (red) on plate'))]
    W=sum(t.width for t in tiles)+8; H=tiles[0].height
    row=Image.new('RGB',(W,H),(20,20,24)); xx=0
    for t in tiles: row.paste(t,(xx,0)); xx+=t.width+4
    rows.append(row)
sh=Image.new('RGB',(rows[0].width,sum(r.height for r in rows)+6),(20,20,24)); yy=0
for r in rows: sh.paste(r,(0,yy)); yy+=r.height+6
sh.save(R+'work/male-parallel-legs/proof/full/FULL_01_front_back_vs_plate.png'); print(sh.size)

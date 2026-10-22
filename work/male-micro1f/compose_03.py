from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1f')
ROOT=W.parents[1]; P=ROOT/'ArtDir/hero/base_lock/proof'; U=P/'male_form_d/unity'; D=ROOT/'ArtDir/hero/base_lock'
FONT='/System/Library/Fonts/Helvetica.ttc'; f=lambda s: ImageFont.truetype(FONT,s)
FG=(236,236,240); DIM=(170,170,178)
st=json.load(open(W/'final/stats.json'))
def fit(im,w,h,bg=(40,40,44)):
    im=im.convert('RGB'); s=min(w/im.width,h/im.height); r=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    o=Image.new('RGB',(w,h),bg); o.paste(r,((w-r.width)//2,(h-r.height)//2)); return o
def fig(name,pad=30,aspect=0.8):
    im=Image.open(U/f'{name}.png').convert('RGB'); mk=Image.open(U/f'{name}_mask.png').convert('L').point(lambda v:255 if v>127 else 0)
    x0,y0,x1,y1=mk.getbbox(); h=(y1-y0)+2*pad; w=int(h*aspect); cx=(x0+x1)//2; cy=(y0+y1)//2
    return im.crop((cx-w//2,cy-h//2,cx+w//2,cy+h//2))
def cc(im,w,h): return im.crop(((im.width-w)//2,(im.height-h)//2,(im.width+w)//2,(im.height+h)//2))
Wd=2000; m=16; S=Image.new('RGB',(Wd,2000),(36,36,40)); d=ImageDraw.Draw(S)
d.text((m,12),f"Male Micro1f · unity · GATE: MALE_FORM {st['gate']} · saved FBX {st['fbx_sha'][:8]}…",font=f(34),fill=FG)
d.text((m,56),f"bald front {st['sil_front']:.4f}% / back {st['sil_back']:.4f}% · required each ≤ 5.0% · height {st['height_m']:.4f} m · {st['tris']:,} tris · URP Lit opaque skin (sRGB .74/.555/.435, smoothness .40 = roughness .60), no texture, no hair",font=f(22),fill=DIM)
views=[('front','front'),('back','back'),('left','left'),('right','right'),('threequarter','three-quarter')]
colw=(Wd-2*m)//5; y=100
for i,(v,lab) in enumerate(views):
    t=fit(fig(v),colw-8,560); S.paste(t,(m+i*colw+4,y+34)); d.text((m+i*colw+4,y),lab,font=f(24),fill=FG)
y+=34+560+16
d.text((m,y),'skin read + hands (actual Unity captures, locked studio)',font=f(26),fill=FG); y+=40
tiles=[('chin_front','chin / skin front'),('chin_threequarter','chin / skin 3/4'),('head_side','head side'),('hand_front','R hand front'),('hand_threequarter','R hand 3/4'),('hand_side','R hand side'),('handL_front','L hand')]
tw=(Wd-2*m)//7
for i,(v,lab) in enumerate(tiles):
    t=fit(cc(Image.open(U/f'{v}.png').convert('RGB'),720,720),tw-6,tw-6); S.paste(t,(m+i*tw+3,y+30)); d.text((m+i*tw+6,y+4),lab,font=f(20),fill=DIM)
y+=30+tw+12
d.text((m,y),'authority plates',font=f(26),fill=FG); y+=38
hd=Image.open(D/'male_head_detail.jpg').convert('RGB'); ba=Image.open(D/'male_body_bald.jpg').convert('RGB')
refs=[(hd.crop((22,66,432,352)),'head-detail front (skin tone)'),(hd.crop((440,388,834,668)),'head-detail 3/4'),(ba.crop((500,280,640,400)),'plate R hand'),(ba.crop((100,280,240,400)),'plate L hand'),(ba.crop((280,40,440,200)),'plate head on grey body')]
tw2=(Wd-2*m)//5
for i,(im,lab) in enumerate(refs):
    S.paste(fit(im,tw2-8,300),(m+i*tw2+4,y+28)); d.text((m+i*tw2+8,y+2),lab,font=f(20),fill=DIM)
y+=28+300+14
d.text((m,y),'Face is a blank blockout (not in scope). Native gate images unchanged in scale; cameras, masks and plates untouched.',font=f(21),fill=DIM)
S=S.crop((0,0,Wd,y+44)); S.save(P/'03_unity_m.png'); print(S.size)

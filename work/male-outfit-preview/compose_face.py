from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, sys
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-outfit-preview'); R=W/'r'
ROOT=W.parents[1]; O=ROOT/'ArtDir/hero/base_lock/preview/face_example'; D=ROOT/'ArtDir/hero/base_lock'
tag=sys.argv[1]; meta=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
f=lambda s: ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',s)
BG=(30,31,35); FG=(238,238,242); DIM=(170,172,182)
def fit(im,w,h):
    im=im.convert('RGB'); s=min(w/im.width,h/im.height); r=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    o=Image.new('RGB',(w,h),(40,40,44)); o.paste(r,((w-r.width)//2,(h-r.height)//2)); return o
def pill(S,xy,s,sz=24):
    d=ImageDraw.Draw(S); ff=f(sz); w=int(d.textlength(s,font=ff))+20
    d.rounded_rectangle((xy[0],xy[1],xy[0]+w,xy[1]+sz+14),radius=9,fill=(14,14,18)); d.text((xy[0]+10,xy[1]+6),s,font=ff,fill=FG)
hd=Image.open(D/'male_head_detail.jpg').convert('RGB')
plates=[hd.crop((22,66,432,352)),hd.crop((440,388,834,668)),hd.crop((440,66,834,352))]
mine=[Image.open(R/f'{tag}_{k}.png') for k in ('front','q3','side')]
tw=640; th=640
S=Image.new('RGB',(tw*3+40,130+th*2+20+th+60),BG); d=ImageDraw.Draw(S)
d.text((30,18),'Male HeroBase — facial structure + random hairstyle (preview, not a gate item)',font=f(44),fill=FG)
hair=meta.get('hair',{})
d.text((30,74),f"sculpted on a copy of the lock: brow ridge, eye sockets, cheekbones, narrower cheeks, nose bridge/tip/alae, lips, chin · hairstyle: {hair.get('style','?')} ({hair.get('color','?')}, seed {hair.get('seed','?')}) · face layers: happy",font=f(24),fill=DIM)
y=130
for i,(im,lab) in enumerate(zip(plates,['plate front','plate 3/4','plate profile'])):
    S.paste(fit(im,tw,th),(20+i*(tw+10),y)); pill(S,(28+i*(tw+10),y+8),lab)
y+=th+10
for i,(im,lab) in enumerate(zip(mine,['mesh front','mesh 3/4','mesh profile'])):
    S.paste(fit(im,tw,th),(20+i*(tw+10),y)); pill(S,(28+i*(tw+10),y+8),lab)
y+=th+20
ex=[Image.open(R/f'{tag}_expr_{k}.png') for k in ('happy','cheer','focus','surprise')]
tw2=(tw*3+20)//4
for i,(im,lab) in enumerate(zip(ex,['happy','cheer','focus','surprise'])):
    S.paste(fit(im,tw2-8,th),(20+i*tw2,y)); pill(S,(28+i*tw2,y+8),lab)
S=S.crop((0,0,S.width,y+th+20)); S.save(O/'01_face_example.png'); print(S.size)

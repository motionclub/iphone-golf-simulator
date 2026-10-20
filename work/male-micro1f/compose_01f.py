from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
W=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1f'); R=W/'r'
P=W.parents[1]/'ArtDir/hero/base_lock/proof'
FONT='/System/Library/Fonts/Helvetica.ttc'
f=lambda s: ImageFont.truetype(FONT,s)
BG=(34,34,38); FG=(236,236,240); DIM=(170,170,178)
st=json.load(open(W/'final/stats.json'))
def fit(im,w,h):
    im=im.convert('RGB'); s=min(w/im.width,h/im.height); r=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    o=Image.new('RGB',(w,h),(40,40,44)); o.paste(r,((w-r.width)//2,(h-r.height)//2)); return o
def label(S,xy,s,sz=22):
    d=ImageDraw.Draw(S); ff=f(sz); w=int(d.textlength(s,font=ff))+14
    d.rectangle((xy[0],xy[1],xy[0]+w,xy[1]+sz+10),fill=(18,18,22)); d.text((xy[0]+7,xy[1]+4),s,font=ff,fill=FG)
Wd=2400; S=Image.new('RGB',(Wd,2700),BG); d=ImageDraw.Draw(S)
d.text((30,16),f"Micro1f · male HANDS · Blender · GATE: MALE_FORM {st['gate']}",font=f(44),fill=FG)
d.text((30,74),f"saved HeroBase_Male_Silhouette.blend {st['blend_sha'][:8]}… · bald front {st['sil_front']:.4f}% / back {st['sil_back']:.4f}% (gate each ≤ 5.0%) · {st['tris']:,} tris · coordinate-only edit on the Micro1e hand topology (same face list), {st['moved']} hand vertices moved, 0 elsewhere",font=f(24),fill=DIM)
d.text((30,106),"added: thenar + hypothenar bulk, dorsal knuckle ridge + MCP/PIP/DIP pads, finger taper + joint curl, fingertip pads, closer fingers with readable gaps, thumb opposition + fatter thumb root",font=f(24),fill=DIM)
y=150
d.text((30,y),"BOTH HANDS (final) — palm · back · front · side · 3/4",font=f(28),fill=FG); y+=40
ks=['palm','back','front','side','q3']; tw=(Wd-60-40)//5
for r_i,h in enumerate('RL'):
    for c,k in enumerate(ks):
        t=fit(Image.open(R/f'k5_hand{h}_{k}.png'),tw,tw); x=30+c*(tw+10); yy=y+r_i*(tw+10); S.paste(t,(x,yy)); label(S,(x+6,yy+6),f'{h} · {k}')
y+=2*(tw+10)+10
d.text((30,y),"BEFORE (Micro1e lock)  vs  AFTER — right hand: palm · back · side · 3/4",font=f(28),fill=FG); y+=40
tw2=(Wd-60-70)//8
for c,k in enumerate(['palm','back','side','q3']):
    a=fit(Image.open(R/f'lock_handR_{k}.png'),tw2,tw2); b=fit(Image.open(R/f'k5_handR_{k}.png'),tw2,tw2)
    x=30+c*(2*tw2+20); S.paste(a,(x,y)); S.paste(b,(x+tw2+4,y)); label(S,(x+4,y+4),'before',18); label(S,(x+tw2+8,y+4),'after',18)
y+=tw2+20
d.text((30,y),"PLATE (left) vs MESH (right) at plate framing — bald plate R hand front · L hand front · R hand back  |  multi-angle plate side",font=f(28),fill=FG); y+=40
hc=Image.open(R/'k5_handcmp.png').convert('RGB'); hc=hc.resize((900,int(hc.height*900/hc.width)))
S.paste(hc,(30,y)); label(S,(38,y+6),'plate',20); label(S,(38+450,y+6),'mesh',20)
sh=Image.open(R/'k5_side_hand.png').convert('RGB'); sh=sh.resize((1380,int(sh.height*1380/sh.width)))
S.paste(sh,(960,y)); label(S,(968,y+6),'plate side',20); label(S,(968+690,y+6),'mesh side',20)
yb=y+sh.height+20
d.text((960,yb),"Known: plate hand reads more mitt-like (fingers fused further toward the tips); mesh keeps readable gaps per the goal.",font=f(22),fill=DIM)
d.text((960,yb+30),"Not touched: chin/jaw, shoulders, waist, arms above the wrist weld, feet, torso, scalp.",font=f(22),fill=DIM)
y=y+hc.height+30
S=S.crop((0,0,Wd,y)); S.save(P/'01f_hands_m.png'); print(S.size)

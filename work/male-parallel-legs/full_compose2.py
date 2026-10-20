import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
D=R+'work/male-parallel-legs/proof/full/'
BGC=(54,54,58); S=2
def rend(name):
    im=Image.open(D+'plate/'+name+'.png').convert('RGBA'); bg=Image.new('RGBA',im.size,BGC+(255,)); bg.alpha_composite(im); return bg.convert('RGB')
# ---- multi-angle sheet: model figures pasted where the plate has them
ROI={'sheet_front':(55,45,318,350),'sheet_back':(348,45,622,350),'left':(735,45,830,350),'right':(1030,45,1142,350),
     'q3FL':(55,372,320,684),'q3FR':(348,372,628,684),'q3BL':(652,372,908,684),'q3BR':(958,372,1218,684)}
canvas=Image.new('RGB',(1280*S,720*S),BGC)
for v,(x0,y0,x1,y1) in ROI.items():
    r=rend(v); canvas.paste(r.crop((x0*S,y0*S,x1*S,y1*S)),(x0*S,y0*S))
plate=Image.open(R+'ArtDir/hero/base_lock/male_multiangle_body.jpg').convert('RGB').resize((1280*S,720*S),Image.LANCZOS)
def lab(im,t,pos=(8,8)):
    d=ImageDraw.Draw(im); d.rectangle([pos[0]-4,pos[1]-3,pos[0]+len(t)*8+6,pos[1]+14],fill=(0,0,0)); d.text(pos,t,fill=(255,255,0)); return im
lab(plate,'REFERENCE PLATE (male_multiangle_body.jpg)'); lab(canvas,'MODEL as installed (torso+arms+legs; head = Micro1i) - same layout; 3/4 cameras fitted to the plate silhouette, yaw approximate')
both=Image.new('RGB',(1280*S,720*S*2+8),(20,20,24)); both.paste(plate,(0,0)); both.paste(canvas,(0,720*S+8))
both=both.resize((1920,int(both.height*1920/both.width)),Image.LANCZOS); both.save(D+'FULL_02_multiangle_vs_plate.png'); print(both.size)
# ---- turnaround of the model alone
names=['front','q3_front_R','side_R','q3_back_R','back','q3_back_L','side_L','q3_front_L']
def rt(n):
    im=Image.open(D+f'turn/turn_{n}.png').convert('RGBA'); bg=Image.new('RGBA',im.size,BGC+(255,)); bg.alpha_composite(im); return bg.convert('RGB')
tiles=[rt(n) for n in names]
tw,th=tiles[0].size; sh=Image.new('RGB',(tw*4,th*2),BGC)
for i,t in enumerate(tiles): sh.paste(t,((i%4)*tw,(i//4)*th))
d=ImageDraw.Draw(sh)
for i,n in enumerate(names): d.text(((i%4)*tw+8,(i//4)*th+6),n,fill=(255,255,0))
sh=sh.resize((2000,int(sh.height*2000/sh.width)),Image.LANCZOS); sh.save(D+'FULL_03_turnaround.png'); print(sh.size)

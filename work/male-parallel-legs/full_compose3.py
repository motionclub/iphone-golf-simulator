import sys, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/male-micro1i/pylib')
import numpy as np
from PIL import Image, ImageDraw
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
D=R+'work/male-parallel-legs/proof/full/'
BGC=(54,54,58); S=2
def rend(name):
    im=Image.open(D+'plate/'+name+'.png').convert('RGBA'); bg=Image.new('RGBA',im.size,BGC+(255,)); bg.alpha_composite(im); return bg.convert('RGB')
plate=Image.open(R+'ArtDir/hero/base_lock/male_body_bald.jpg').convert('RGB')
def lab(im,t):
    d=ImageDraw.Draw(im); d.rectangle([0,0,len(t)*7+10,16],fill=(0,0,0)); d.text((4,2),t,fill=(255,255,0)); return im
cols=[]
for v,(x0,x1) in (('bald_front',(190,520)),('bald_back',(750,1085))):
    y0,y1=300,665
    p=plate.crop((x0,y0,x1,y1)).resize(((x1-x0)*S,(y1-y0)*S),Image.LANCZOS)
    m=rend(v).crop((x0*S,y0*S,x1*S,y1*S))
    z=1.05
    col=Image.new('RGB',(int(p.width*z)*2+6,int(p.height*z)),(20,20,24))
    col.paste(lab(p.resize((int(p.width*z),int(p.height*z)),Image.LANCZOS),'PLATE '+v),(0,0)); col.paste(lab(m.resize((int(m.width*z),int(m.height*z)),Image.LANCZOS),'MODEL '+v),(int(p.width*z)+6,0))
    cols.append(col)
sh=Image.new('RGB',(cols[0].width+cols[1].width+10,cols[0].height),(20,20,24)); sh.paste(cols[0],(0,0)); sh.paste(cols[1],(cols[0].width+10,0))
sh.save(D+'FULL_04_legs_in_context_front_back.png'); print(sh.size)

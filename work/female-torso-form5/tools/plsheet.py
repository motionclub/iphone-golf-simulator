"""python3 tools/plsheet.py out.png tag=coords.npy ...  -> plate | plate-lit renders (contrast boosted identically), front chest + back pelvis crops"""
import sys; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form5/tools')
from platelit import *
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
FB=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',20)
def boost(im,k=3.0):
    a=np.asarray(im.convert('L')).astype(float); return Image.fromarray(np.clip((a-185)*k+150,0,255).astype(np.uint8)).convert('RGB')
def lab(im,t):
    d=ImageDraw.Draw(im); w=d.textlength(t,font=FB); d.rectangle([4,4,w+14,32],fill=(0,0,0)); d.text((8,6),t,font=FB,fill=(255,255,255)); return im
if __name__=='__main__':
    out=sys.argv[1]; vs=[a.split('=') for a in sys.argv[2:]]
    for tag,npy in vs: render(str(W/npy),tag)
    bald=Image.open(ROOT/'ArtDir/hero/base_lock/female_body_bald.jpg').convert('L')
    fb=(340,128,540,268); bb=(747,235,947,375); sc=3
    def crop(im,box): c=im.crop(box); return c.resize((c.width*sc,c.height*sc),Image.LANCZOS)
    cols=[(lab(boost(crop(bald,fb)),'plate'),lab(boost(crop(bald,bb)),'plate'))]
    for tag,_ in vs:
        f=crop(Image.open(W/f'proof/scratch/pl_{tag}_front.png').convert('L'),fb); b=crop(Image.open(W/f'proof/scratch/pl_{tag}_back.png').convert('L'),bb)
        cols.append((lab(boost(f),tag+' (plate-lit)'),lab(boost(b),tag+' (plate-lit)')))
    Wd=cols[0][0].width; H=cols[0][0].height
    S_=Image.new('RGB',(Wd*len(cols),H*2))
    for i,(f,b) in enumerate(cols): S_.paste(f,(i*Wd,0)); S_.paste(b,(i*Wd,H))
    S_.save(W/out); print(out,S_.size)

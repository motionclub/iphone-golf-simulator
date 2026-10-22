"""Plate close-ups with local-contrast enhancement (CLAHE-like via unsharp + gamma) so soft mounds are visible."""
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
B='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/'
bald=Image.open(B+'female_body_bald.jpg').convert('L'); sheet=Image.open(B+'female_multiangle_body.jpg').convert('L')
def enh(im,clip=2.0):
    a=np.asarray(im).astype(float)
    # band-pass: image minus heavy blur -> shows soft forms
    bl=np.asarray(im.filter(ImageFilter.GaussianBlur(14))).astype(float)
    hp=a-bl
    out=np.clip(128+hp*clip*4,0,255).astype(np.uint8)
    return Image.fromarray(out)
def crop(img,box,scale):
    c=img.crop(box); return c.resize((int(c.width*scale),int(c.height*scale)),Image.LANCZOS)
tiles=[]
# bald plate front chest (440,~200) and back glute
f_chest=(340,110,540,260); b_glute=(747,250,947,400)
for name,im,box,sc in [('front chest',bald,f_chest,5),('back glute',bald,b_glute,5)]:
    c=crop(im,box,sc); e=enh(c.resize((c.width//sc,c.height//sc),Image.LANCZOS)).resize(c.size,Image.LANCZOS)
    tiles.append((name,c,e))
W=Image.new('L',(1000*2,750*2),0)
for i,(n,c,e) in enumerate(tiles):
    W.paste(c,(i*1000,0)); W.paste(e,(i*1000,750))
W.save('data/plate_zoom_bald.png'); print('ok')

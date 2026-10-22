import sys
from PIL import Image, ImageOps, ImageFilter
import numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
im=Image.open(R+'ArtDir/hero/base_lock/male_body_plain.jpg').convert('L')
def enh(box,z=4):
    c=im.crop(box); a=np.asarray(c).astype(float)
    # local contrast: subtract heavy blur, stretch
    b=np.asarray(c.filter(ImageFilter.GaussianBlur(14))).astype(float)
    d=(a-b)*5+128
    out=Image.fromarray(np.clip(d,0,255).astype('uint8')).resize((c.width*z,c.height*z),Image.LANCZOS)
    o2=ImageOps.autocontrast(c,cutoff=1).resize((c.width*z,c.height*z),Image.LANCZOS)
    s=Image.new('L',(out.width*2+10,out.height)); s.paste(o2,(0,0)); s.paste(out,(out.width+10,0)); return s
enh((250,150,460,390),3).save('r/enh_front.png'); enh((820,150,1015,390),3).save('r/enh_back.png')

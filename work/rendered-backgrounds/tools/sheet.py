#!/usr/bin/env python3
"""Contact sheet: tools/sheet.py out.jpg cols width img1 img2 ... (labels = file stems)."""
import sys,os
from PIL import Image,ImageDraw
out,cols,w=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]);fs=sys.argv[4:]
ims=[Image.open(f).convert('RGB') for f in fs]
h=int(w*ims[0].height/ims[0].width)
rows=(len(ims)+cols-1)//cols
s=Image.new('RGB',(w*cols,h*rows),'black');d=ImageDraw.Draw(s)
for i,(f,im) in enumerate(zip(fs,ims)):
    x,y=(i%cols)*w,(i//cols)*h;s.paste(im.resize((w,h),Image.LANCZOS),(x,y))
    lab=os.path.splitext(os.path.basename(f))[0];d.rectangle([x,y,x+8*len(lab)+8,y+16],fill=(0,0,0));d.text((x+4,y+2),lab,fill=(255,255,0))
s.save(out,quality=88)

import sys
from PIL import Image, ImageDraw
# pair.py out.jpg labelA a.png labelB b.png [...]  -> side-by-side with labels
out=sys.argv[1]; items=list(zip(sys.argv[2::2],sys.argv[3::2]))
ims=[Image.open(p).convert("RGB") for _,p in items]
w=sum(i.width for i in ims); h=max(i.height for i in ims)+28
s=Image.new("RGB",(w,h),(235,235,235)); d=ImageDraw.Draw(s); x=0
for (lab,_),im in zip(items,ims):
    s.paste(im,(x,28)); d.text((x+8,8),lab,fill=(20,20,20)); x+=im.width
s.save(out,quality=88)

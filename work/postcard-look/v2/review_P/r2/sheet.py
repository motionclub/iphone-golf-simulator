import sys
from PIL import Image
tag=sys.argv[1]
ims=[Image.open(f"{tag}_{a}.png") for a in (0,90,180,270)]
w,h=ims[0].size
s=Image.new("RGB",(w*4,h))
for i,im in enumerate(ims): s.paste(im,(i*w,0))
s.save(f"{tag}_sheet.png")

import sys
from PIL import Image
out=sys.argv[1]
ims=[Image.open(f"{out}_{az}.png").convert("RGB") for az in (0,60,120)]
w,h=ims[0].size
sheet=Image.new("RGB",(w,h*len(ims)))
for i,im in enumerate(ims): sheet.paste(im,(0,i*h))
sheet.save(out+"_sheet.png")
import os
for az in (0,60,120): os.remove(f"{out}_{az}.png")

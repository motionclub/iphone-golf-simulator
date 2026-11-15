# compose.py <label>: bg + HUD -> <name>.jpg, and how much of each hero the HUD covers (alpha > .6 inside the hero's screen box)
import sys, json, glob, os, numpy as np
from PIL import Image
L=sys.argv[1]; D=f"shots/{L}"; out={}
for bg in sorted(glob.glob(f"{D}/*_bg.jpg")):
    n=os.path.basename(bg)[:-7]
    im=Image.open(bg).convert("RGBA"); ui=Image.open(f"{D}/{n}_ui.png").convert("RGBA")
    a=np.asarray(ui)[...,3].astype(float)/255
    cov=[]
    for r in json.load(open(f"{D}/{n}_heroes.json")):
        x0,y0,x1,y1=[int(round(v*(1920 if i%2==0 else 1080))) for i,v in enumerate(r)]
        x0,x1=max(0,x0),min(1920,x1); y0,y1=max(0,y0),min(1080,y1)
        if x1<=x0 or y1<=y0: continue
        # the body below the head: name plates float over the head by design
        yb=y0+int((y1-y0)*.12)
        cov.append(round(float((a[yb:y1,x0:x1]>.6).mean()*100),1))
    out[n]=cov
    im.alpha_composite(ui); im.convert("RGB").save(f"{D}/{n}.jpg",quality=88)
json.dump(out,open(f"{D}/coverage.json","w"),indent=1); print(json.dumps(out))

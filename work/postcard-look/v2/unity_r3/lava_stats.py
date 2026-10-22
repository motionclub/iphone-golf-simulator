import sys, numpy as np
sys.path.insert(0,"../proof")
import measure as M
from PIL import Image
def stats(full,idm,tag):
    f=np.asarray(Image.open(full).convert("RGB")); i=np.asarray(Image.open(idm).convert("RGB")).astype(int)
    m=(abs(i[...,0]-120)<6)&(abs(i[...,1]-40)<6)&(abs(i[...,2]-40)<6)
    if m.sum()<500: print(tag,"lava px",m.sum()); return
    h,s,v=M.rgb2hsv(f[m]); inb=((h>=8)&(h<=28)&(s>=.75)&(v>=.70)).mean()
    mean=f[m].mean(0); hh,ss,vv=M.mean_hsv(mean)
    print(f"{tag}: lava {m.sum()} px mean {tuple(int(x) for x in mean)} h{hh:.0f} S{ss:.2f} V{vv:.2f} in band {inb*100:.1f}%  (h only {((h>=8)&(h<=28)).mean()*100:.0f}%, S>=.75 {(s>=.75).mean()*100:.0f}%, V>=.7 {(v>=.7).mean()*100:.0f}%) G>=250 {(f[m][:,1]>=250).mean()*100:.1f}%")
if __name__=="__main__":
    a=sys.argv[1:]
    for k in range(0,len(a),2): stats(a[k],a[k+1],a[k].split("/")[-1])

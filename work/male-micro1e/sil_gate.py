"""Native gate measurement vs frozen masks. usage: python3 sil_gate.py renderdir"""
import sys
from PIL import Image, ImageChops
d=sys.argv[1]; M='../male-silhouette/'
res={}
for v in ['bald_front','bald_back']:
    t=Image.open(M+v+'_target.png'); r=Image.open(d+'/'+v+'.png')
    tm=t.split()[3] if t.mode=='RGBA' else t.convert('L')
    rm=r.split()[3]
    tp=tm.load(); rp=rm.load(); W,H=rm.size
    assert tm.size==rm.size,(tm.size,rm.size)
    diff=0;uni=0
    for y in range(H):
        for x in range(W):
            a=tp[x,y]>127; b=rp[x,y]>127
            if a!=b: diff+=1
            if a or b: uni+=1
    res[v]=(diff,uni,100*diff/uni)
    print(v,diff,uni,f'{100*diff/uni:.4f}%')

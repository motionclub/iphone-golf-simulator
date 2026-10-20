"""python3 tools/cmp.py chest|glute out.png tagA=coordsA.npy tagB=coordsB.npy ...   -> columns: plate | variants ; rows: front/back, 3/4, profile
"""
import sys, os, subprocess
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form2/tools')
from look import *
def main():
    kind=sys.argv[1]; out=sys.argv[2]; vs=[a.split('=') for a in sys.argv[3:]]
    TS=520
    sheet=Image.open(ROOT+'/ArtDir/hero/base_lock/female_multiangle_body.jpg').convert('RGB')
    S2=1.7039/288.5; V0=338.5
    if kind=='chest': zc,half,views,vn,cxs,pkind=1.22,0.20,('front','y-25','side'),('front','3/4','profile'),(None,472,790),'front'
    else: zc,half,views,vn,cxs,pkind=0.90,0.24,('back','y155','side'),('back','3/4','profile'),(None,1078,790),'back'
    # plate tiles
    P=[]
    P.append(plate_crop(pkind,zc,half,TS))
    P.append(sheet_tile(sheet,cxs[1],zc,half,TS))
    y0=V0-(zc+half)/S2; y1=V0-(zc-half)/S2; w=half/S2
    P.append(ImageEnhance.Contrast(sheet.crop((int(cxs[2]-w),int(y0),int(cxs[2]+w),int(y1))).resize((TS,TS),Image.LANCZOS)).enhance(1.6))
    cols=[[label(p,'plate '+n) for p,n in zip(P,vn)]]
    for tag,npy in vs:
        blend=f'{WD}/proof/scratch/{tag}.blend'
        apply(npy,blend)
        pre=f'{WD}/proof/scratch/{tag}_{kind}'
        render(blend,pre,zc,half*2.0,','.join(views),res=f'{TS}x{TS}')
        cols.append([label(Image.open(f'{pre}_{v}.png').convert('RGB'),f'{tag} {n}') for v,n in zip(views,vn)])
    W=Image.new('RGB',(TS*len(cols),TS*3))
    for ci,c in enumerate(cols):
        for ri,im in enumerate(c): W.paste(im,(ci*TS,ri*TS))
    W.save(out); print(out,W.size)
if __name__=='__main__': main()

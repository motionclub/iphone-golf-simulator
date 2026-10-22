import numpy as np
from PIL import Image
from collections import deque
L='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
C=np.asarray(Image.open(L+'Lava_C.png').convert('RGB').resize((512,512),Image.BOX)).astype(float)
lum=C.max(2)
for thr in (60,90,110):
    dark=lum<thr
    print('thr',thr,'dark frac %.3f'%dark.mean())
dark=lum<90
H,W=dark.shape; lab=np.zeros((H,W),int); n=0; regs=[]
for y in range(H):
  for x in range(W):
    if dark[y,x] and not lab[y,x]:
        n+=1; q=deque([(y,x)]); lab[y,x]=n; pts=[]
        while q:
            a,b=q.popleft(); pts.append((a,b))
            for da,db in ((1,0),(-1,0),(0,1),(0,-1)):
                aa,bb=a+da,b+db
                if 0<=aa<H and 0<=bb<W and dark[aa,bb] and not lab[aa,bb]: lab[aa,bb]=n; q.append((aa,bb))
        regs.append(np.array(pts))
big=[r for r in regs if len(r)>=30]
asp=[]
for r in big:
    c=np.cov((r-r.mean(0)).T); ev=np.sort(np.linalg.eigvalsh(c))[::-1]; asp.append(np.sqrt(ev[0]/max(ev[1],1e-6)))
asp=np.array(asp); sz=np.array([len(r) for r in big])
print('regions>=30px',len(big),'median aspect %.2f'%np.median(asp),'compact(<1.5) area share %.2f'%(sz[asp<1.5].sum()/sz.sum()),'total dark',sz.sum()/(H*W))
# periodicity: autocorr peaks excluding 0
g=lum-lum.mean(); F=np.fft.fft2(g); ac=np.fft.ifft2(np.abs(F)**2).real; ac/=ac[0,0]
ac[0:6,0:6]=0
for k in (1,2): pass
# check the 1/2-tile shifts correlation
for s in (256,128,170):
    print('shift',s,'corr x %.3f y %.3f diag %.3f'%(ac[0,s],ac[s,0],ac[s,s]))
# isotropy of edge network: gradient orientation hist
gy,gx=np.gradient(lum); mag=np.hypot(gx,gy); ang=np.arctan2(gy,gx)%np.pi
h,_=np.histogram(ang,bins=12,weights=mag); print('edge orientation hist (12 bins) rel',(h/h.mean()).round(2))
# hexagonal peaks: ring of spectrum
P=np.abs(np.fft.fftshift(F))**2; yy,xx=np.indices(P.shape); rr=np.hypot(yy-H/2,xx-W/2)
rad=np.array([P[(rr>=i)&(rr<i+1)].mean() for i in range(1,100)]); print('ring peak/mean %.1f at r=%d'%(rad.max()/rad.mean(),rad.argmax()+1))

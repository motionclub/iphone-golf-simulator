import numpy as np, sys
from PIL import Image
from collections import deque
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/'
E=np.asarray(Image.open(R+'Basalt_E.png').convert('RGB')).astype(int)
C=np.asarray(Image.open(R+'Basalt_C.png').convert('RGB')).astype(int)
H,W,_=E.shape; print(H,W)
lum=E.max(2)
for thr in (8,20,40):
    m=lum>thr; print('thr',thr,'cov %.2f%%'%(m.mean()*100))
m=lum>20
lab=-np.ones((H,W),int); comps=[]
for y in range(H):
  for x in range(W):
    if m[y,x] and lab[y,x]<0:
      q=deque([(y,x)]); lab[y,x]=len(comps); pts=[]
      while q:
        cy,cx=q.popleft(); pts.append((cy,cx))
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
          ny,nx=(cy+dy)%H,(cx+dx)%W
          if m[ny,nx] and lab[ny,nx]<0: lab[ny,nx]=len(comps); q.append((ny,nx))
      comps.append(pts)
print('components',len(comps))
st=[]
for p in comps:
    a=np.array(p); 
    if len(a)<30: continue
    # unwrap relative to first
    a=a.astype(float); ref=a[0]
    for k,sz in ((0,H),(1,W)):
        d=a[:,k]-ref[k]; d=(d+sz/2)%sz-sz/2; a[:,k]=ref[k]+d
    h=a[:,0].max()-a[:,0].min()+1; w=a[:,1].max()-a[:,1].min()+1
    st.append((len(a),h,w,a[:,1].mean()%W))
st.sort(key=lambda t:-t[0])
print('n>=30px',len(st))
for s in st[:40]: print('px %d  h %d  w %d  x %.0f  aspect %.1f'%(s[0],s[1],s[2],s[3],s[1]/max(s[2],1)))
hs=np.array([s[1] for s in st]); ws=np.array([s[2] for s in st])
print('vertical-elongated (h>=2w):',(hs>=2*ws).sum(),'of',len(st),'; median h %d w %d'%(np.median(hs),np.median(ws)))
# column x positions of glow
cols=np.histogram(np.nonzero(m)[1],bins=W,range=(0,W))[0]
xs=np.nonzero(cols>0)[0]
# group
g=[];cur=[xs[0]]
for x in xs[1:]:
    if x-cur[-1]<=6: cur.append(x)
    else: g.append(cur);cur=[x]
g.append(cur)
print('glow x-bands',[(int(np.mean(c)),len(c)) for c in g])
# horizontal run lengths
mx=0
for y in range(H):
    r=0
    row=np.concatenate([m[y],m[y]])
    run=0
    for v in row:
        run=run+1 if v else 0; mx=max(mx,run)
print('longest horizontal run px',min(mx,W))
print('glow hot peak',E.reshape(-1,3).max(0), 'cream (all>230)',((E.min(2))>=230).sum())

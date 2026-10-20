"""Source-only silhouette masks for the 8 panels of female_multiangle_body.jpg (row-wise background subtraction)."""
import sys; sys.path.insert(0,'tools')
from fplate import *
from PIL import Image
from collections import deque
img=SHEET
# panel boxes (x0,y0,x1,y1)
PAN={'front':(0,0,320,360),'back':(320,0,640,360),'Lprof':(640,0,960,360),'Rprof':(960,0,1280,360),
     'q3FL':(0,360,320,720),'q3FR':(320,360,640,720),'q3BL':(640,360,960,720),'q3BR':(960,360,1280,720)}
def largest_cc(m):
    h,w=m.shape; seen=np.zeros_like(m,bool); best=None
    for y in range(h):
        for x in range(w):
            if m[y,x] and not seen[y,x]:
                q=deque([(y,x)]); seen[y,x]=True; comp=[]
                while q:
                    cy,cx=q.popleft(); comp.append((cy,cx))
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        ny,nx=cy+dy,cx+dx
                        if 0<=ny<h and 0<=nx<w and m[ny,nx] and not seen[ny,nx]: seen[ny,nx]=True; q.append((ny,nx))
                if best is None or len(comp)>len(best): best=comp
    out=np.zeros_like(m)
    for y,x in best: out[y,x]=True
    return out
def fill_holes(m):
    h,w=m.shape; bg=~m; seen=np.zeros_like(m,bool); q=deque()
    for x in range(w):
        for y in (0,h-1):
            if bg[y,x] and not seen[y,x]: seen[y,x]=True; q.append((y,x))
    for y in range(h):
        for x in (0,w-1):
            if bg[y,x] and not seen[y,x]: seen[y,x]=True; q.append((y,x))
    while q:
        cy,cx=q.popleft()
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=cy+dy,cx+dx
            if 0<=ny<h and 0<=nx<w and bg[ny,nx] and not seen[ny,nx]: seen[ny,nx]=True; q.append((ny,nx))
    return m|(~seen&bg)
masks={}
for name,(x0,y0,x1,y1) in PAN.items():
    P=img[y0:y1,x0:x1]; m=np.zeros(P.shape,bool)
    for r in range(P.shape[0]):
        row=P[r]; bgl=np.median(row[:12]); bgr=np.median(row[-12:])
        bg=np.linspace(bgl,bgr,len(row))
        m[r]=np.abs(row-bg)>7.5
    # remove label text region (top-left of the sheet) and floor shadow below the soles: keep rows with the figure only
    m=largest_cc(m); m=fill_holes(m)
    masks[name]=m
    Image.fromarray((m*255).astype(np.uint8)).save(f'data/mask_{name}.png')
    ys,xs=np.where(m); print(name,'bbox',xs.min()+x0,ys.min()+y0,xs.max()+x0,ys.max()+y0,'px',m.sum())

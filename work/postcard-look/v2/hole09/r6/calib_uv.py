import bpy, sys, numpy as np, random, os
sys.path.insert(0, "/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_lib as P, postcard_look_lib as L, postcard_props_lib as PL
import hole09_masonry as HM
segs = HM.brick_segments()
print("segments", len(segs))
for s in segs[:8]: print([round(x,3) for x in s])
img = bpy.data.images.load(os.path.join(L.LOOK_DIR,"Masonry_C.png"))
W,H = img.size
a=np.empty(W*H*4,np.float32); img.pixels.foreach_get(a)
lum=a.reshape(H,W,4)[...,:3].mean(-1)
print("lum stats", lum.min(), lum.max(), np.median(lum))
def prof_range(u0,u1,v0,v1):
    cs=[int(u0*W), int(np.ceil(u1*W))]; rs=[int(v0*H), int(np.ceil(v1*H))]
    cols=[c%W for c in range(cs[0],cs[1]+1)]; rows=[r%H for r in range(rs[0],rs[1]+1)]
    sub=lum[np.ix_(rows,cols)]
    p=sub.mean(0)
    return float(p.max()-p.min()), float(sub.min())
rng=random.Random(5)
inside=[];cross=[]
for _ in range(4000):
    w=rng.uniform(0.04,0.14); h=rng.uniform(0.03,0.085)
    # window within a row interior
    k=rng.randrange(8); y0=(31+64*k+9)/512; 
    v0=y0+rng.uniform(0,(46/512-h)); u0=rng.uniform(0.0,1-w)
    r,mn=prof_range(u0,u0+w,v0,v0+h)
    ins=any(s[0]<=u0 and u0+w<=s[1] and s[2]<=v0 and v0+h<=s[3] for s in segs)
    (inside if ins else cross).append(r)
inside=np.array(inside);cross=np.array(cross)
print("inside-brick windows",len(inside),"profile range pct 50/90/99/max",np.percentile(inside,[50,90,99,100]).round(3))
print("other windows",len(cross),"profile range pct 1/10/50/90",np.percentile(cross,[1,10,50,90]).round(3), "share > 0.06:", (cross>0.06).mean().round(3), "share>0.07",(cross>0.07).mean().round(3))
# actual windows chosen by module
rg=random.Random(1); mine=[]
for _ in range(3000):
    w=rg.uniform(0.3,1.5); h=rg.uniform(0.26,0.6)
    u0,v0,k=HM.uv_window(rg,w,h,0.3*0.25,1.5*0.25)
    r,mn=prof_range(u0,u0+k*w,v0,v0+k*h); mine.append(r)
mine=np.array(mine); print("module windows range pct 50/90/99/max",np.percentile(mine,[50,90,99,100]).round(3))

print("---- dip statistic")
def max_dip(u0,u1,v0,v1):
    c0=int(u0*W)-9; c1=int(np.ceil(u1*W))+9
    cols=[c%W for c in range(c0,c1+1)]; rows=[r%H for r in range(int(v0*H), int(np.ceil(v1*H))+1)]
    p=lum[np.ix_(rows,cols)].mean(0)
    p=np.convolve(p,np.ones(3)/3,mode='same')
    best=0.0
    for c in range(9, len(p)-9):
        if not (int(u0*W) <= c-9+int(u0*W) ): pass
        d=0.5*(p[c-8]+p[c+8])-p[c]
        # only centres inside the window
        best=max(best,d)
    return best
rng=random.Random(5)
inside=[];cross=[]
for _ in range(4000):
    w=rng.uniform(0.04,0.14); h=rng.uniform(0.03,0.085)
    k=rng.randrange(8); y0=(31+64*k+9)/512
    v0=y0+rng.uniform(0,(46/512-h)); u0=rng.uniform(0.0,1-w)
    d=max_dip(u0,u0+w,v0,v0+h)
    ins=any(s[0]<=u0 and u0+w<=s[1] and s[2]<=v0 and v0+h<=s[3] for s in segs)
    (inside if ins else cross).append(d)
inside=np.array(inside);cross=np.array(cross)
print("inside dip pct 50/90/99/max",np.percentile(inside,[50,90,99,100]).round(3))
print("other dip pct 1/10/25/50",np.percentile(cross,[1,10,25,50]).round(3))
for th in (0.03,0.04,0.05,0.06):
    print(th,"inside>th",(inside>th).mean().round(3),"other<th",(cross<th).mean().round(3))
rg=random.Random(1); mine=[]
for _ in range(3000):
    w=rg.uniform(0.3,1.5); h=rg.uniform(0.26,0.6)
    u0,v0,k=HM.uv_window(rg,w,h,0.3*0.25,1.5*0.25)
    mine.append(max_dip(u0,u0+k*w,v0,v0+k*h))
mine=np.array(mine); print("module windows dip pct 50/90/99/max",np.percentile(mine,[50,90,99,100]).round(3))

import bpy, sys, numpy as np, math
sys.path.insert(0,"/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts")
import postcard_lib as P, postcard_look_lib as L, hole09_masonry as HM
def J(seed=1001, courses=8):
    rng_ = np.random.default_rng([seed, 1]); out=[]
    for k in range(courses):
        nb=int(rng_.integers(4,8)); w=rng_.uniform(0.6,1.4,nb); cb=np.concatenate([[0.0],np.cumsum(w)/w.sum()]); ph=float(rng_.random())
        out.append(sorted(((cb[i]-ph)%1.0) for i in range(nb)))
    return out
JJ=J()
segs=HM.brick_segments()
for j in range(8):
    print("gen course",j,"joints px",[round(x*512) for x in JJ[j]])
    rows=[s for s in segs if abs(((s[2]+s[3])/2)*8 - j) < 0.5 or abs(((s[2]+s[3])/2)*8 - (j+8)) < 0.5]
    print("   detected segs px", [(round(s[0]*512),round(s[1]*512)) for s in rows])

import numpy as np, bpy, sys
E = bpy.data.images.load("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/Basalt_E.png")
w,h = E.size
px = np.array(E.pixels[:]).reshape(h,w,4)[:,:,:3]   # bottom-up rows
lum = px.max(axis=2)
col = lum.mean(axis=0)  # per u
# find glow lines: contiguous u ranges where col mean > 0.02
thr = 0.02
on = col > thr
runs=[]; s=None
for i,v in enumerate(on):
    if v and s is None: s=i
    if (not v) and s is not None: runs.append((s,i-1)); s=None
if s is not None: runs.append((s,w-1))
print("glow runs u:", [(round(a/w,3), round(b/w,3), round(float(col[a:b+1].max()),3)) for a,b in runs])
# per run: coverage along v
for a,b in runs:
    m = lum[:, a:b+1].max(axis=1) > 0.2
    # stretch lengths
    L=[];c=0
    for v in m:
        if v: c+=1
        else:
            if c: L.append(c); c=0
    if c: L.append(c)
    print("run", round(a/w,3), round(b/w,3), "coverage", round(float(m.mean()),3), "stretches (v len)", [round(l/h,3) for l in L])
# albedo gap lines: darkest columns
C = bpy.data.images.load("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/Basalt_C.png")
cp = np.array(C.pixels[:]).reshape(h,w,4)[:,:,:3].mean(axis=2)
cm = cp.mean(axis=0)
# local minima
mins=[i for i in range(2,w-2) if cm[i]==cm[max(0,i-12):i+13].min() and cm[i]<np.percentile(cm,25)]
print("dark gap u:", [round(i/w,3) for i in mins])

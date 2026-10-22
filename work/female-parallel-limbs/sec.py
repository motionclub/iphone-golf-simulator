import bpy, numpy as np
b=bpy.data.objects['Body_F']; v=np.array([tuple(x.co) for x in b.data.vertices])
S=0.0025954198473282443
def y2z(y): return (679-y)*S
print('crotch z', y2z(367), 'armpit z', y2z(220), 'shoulder', y2z(165))
for zpx in list(range(150,260,10))+list(range(300,680,20)):
    z=y2z(zpx); m=np.abs(v[:,2]-z)<0.008
    xs=np.sort(v[m,0]);
    if len(xs)==0: continue
    # cluster by gaps > 0.02
    cl=[];s=xs[0];p=xs[0]
    for x in xs[1:]:
        if x-p>0.025: cl.append((round(s,3),round(p,3))); s=x
        p=x
    cl.append((round(s,3),round(p,3)))
    print(zpx, round(z,3), len(xs), cl)

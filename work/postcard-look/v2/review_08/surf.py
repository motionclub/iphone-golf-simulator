import bpy, sys, math, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D
YD=0.9144
def wv(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
shore=np.array(D.SHORE)*YD
seg=np.linalg.norm(np.roll(shore,-1,0)-shore,axis=1); cum=np.r_[0,np.cumsum(seg)]; L=cum[-1]
def arc(p):
    a=shore; b=np.roll(shore,-1,0); ab=b-a; ap=p[None]-a
    t=np.clip((ap*ab).sum(1)/(ab*ab).sum(1),0,1); d=np.linalg.norm(p[None]-(a+ab*t[:,None]),axis=1); i=d.argmin(); return cum[i]+t[i]*seg[i], d[i]
runs=[]
for o in bpy.data.objects:
    if o.name.startswith('WATER_SURF'):
        V=wv(o); arcs=[];ds=[]
        for v in V: a,d=arc(v[:2]); arcs.append(a); ds.append(d)
        arcs=np.array(arcs)
        # handle wrap: span
        lo,hi=arcs.min(),arcs.max()
        runs.append((lo,hi,max(ds),o.name))
runs.sort()
print('shore perimeter %.0f m'%L)
cover=sum(h-l for l,h,_,_ in runs)
print('surf runs',len(runs),'covered %.0f m = %.0f%%'%(cover,100*cover/L),'longest %.1f'%max(h-l for l,h,_,_ in runs),'max dist from shore %.1f'%max(m for *_,m,_ in [(0,0,r[2],0) for r in runs]))
gaps=[runs[i+1][0]-runs[i][1] for i in range(len(runs)-1)]
print('min gap %.1f'%min(gaps),'gaps',[round(g,1) for g in gaps])
# any other white/foam-ish: materials named
print([m.name for m in bpy.data.materials])
# surf material: LK_SURF alpha/colour
m=bpy.data.materials['LK_SURF']; print('LK_SURF blend',getattr(m,'blend_method',None))
print('--- circular, alpha-weighted')
iv=[]
for o in bpy.data.objects:
    if o.name.startswith('WATER_SURF'):
        V=wv(o); me=o.data
        ca=me.color_attributes.active_color if me.color_attributes else None
        al=[]
        if ca is not None:
            for i,v in enumerate(me.vertices):
                pass
            vals=np.array([d.color[3] for d in ca.data]) if ca.domain=='POINT' else None
        arcs=np.array([arc(v[:2])[0] for v in V])
        # unwrap around circular mean
        c=np.angle(np.exp(1j*arcs/L*2*np.pi).mean())/(2*np.pi)*L%L
        rel=(arcs-c+L/2)%L-L/2
        iv.append((c+rel.min(),c+rel.max(),o.name,ca.name if ca else None, None if vals is None else (round(vals.min(),2),round(vals.max(),2))))
iv.sort()
print(iv[0])
lens=[b-a for a,b,*_ in iv]; print('run lengths',[round(x,1) for x in lens])
gaps=[(iv[(i+1)%len(iv)][0]-iv[i][1])%L for i in range(len(iv))]
print('gaps',[round(g,1) for g in gaps],'min %.1f'%min(gaps),'covered %.1f%%'%(100*sum(lens)/L))

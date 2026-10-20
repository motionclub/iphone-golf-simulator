"""numeric feature gates for bust / glutes measured on a built mesh (coords npy) against the base surface (features off, same params)"""
import sys,json; sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/female-torso-form4/tools')
from torso2 import *
from footprint import grid_surface
def metrics(co,P):
    base=build2({**P,'b_on':0.0,'g_on':0.0})
    out={}
    # ---------------- bust
    xs=np.arange(-0.14,0.1401,0.002); zs=np.arange(1.10,1.34,0.002)
    fa=grid_surface(co,'front',xs,zs); fb=grid_surface(base,'front',xs,zs)
    d=(fb-fa)                                    # forward growth (m)
    zi=lambda z:int(round((z-zs[0])/0.002)); xi=lambda x:int(round((x-xs[0])/0.002))
    # mound apex: most forward point on each side (final surface), z in [1.15,1.32]
    res={}
    for side,sgn in (('L',-1),('R',1)):
        cols=np.where(np.sign(xs)==sgn)[0]; sub=fa[zi(1.15):zi(1.32)+1][:,cols]
        iz,ix=np.unravel_index(np.argmin(sub),sub.shape); res[side]=dict(apex_x=float(xs[cols[ix]]),apex_z=float(zs[zi(1.15)+iz]),apex_y=float(sub[iz,ix]))
        # dome height above the base wall at the apex
        res[side]['height_above_wall_mm']=float(d[zi(1.15)+iz,cols[ix]]*1000)
        # footprint lower edge: lowest z (along the apex column) where growth >3 mm
        col=cols[ix]; g=d[:,col]; zz=np.where(g>0.003)[0]; res[side]['footprint_z_range']=[float(zs[zz.min()]),float(zs[zz.max()])]
        row=zi(res[side]['apex_z']); gg=d[row]; xx=np.where(gg>0.003)[0]; xxs=xs[xx[np.sign(xs[xx])==sgn]]
        res[side]['footprint_x_range_abs']=[float(np.abs(xxs).min()),float(np.abs(xxs).max())]
    out['bust']=res
    # sternal valley: front surface at |x|<0.012 vs mean apex, at apex height
    za=0.5*(res['L']['apex_z']+res['R']['apex_z']); iz=zi(za)
    ster=fa[iz][np.abs(xs)<0.012].min(); apex=0.5*(res['L']['apex_y']+res['R']['apex_y'])
    out['bust']['sternal_valley_mm']=float((ster-apex)*1000)
    out['bust']['apex_envelope_front_m']=float(apex)
    # ---------------- glutes
    xs2=np.arange(-0.19,0.1901,0.002); zs2=np.arange(0.78,1.06,0.002)
    ba=grid_surface(co,'back',xs2,zs2); bb=grid_surface(base,'back',xs2,zs2)
    gl={}
    for side,sgn in (('L',-1),('R',1)):
        cols=np.where((np.sign(xs2)==sgn)&(np.abs(xs2)<0.16))[0]; sub=ba[int(round((0.84-0.78)/0.002)):int(round((0.96-0.78)/0.002))+1][:,cols]
        iz,ix=np.unravel_index(np.argmax(sub),sub.shape); gl[side]=dict(apex_x=float(xs2[cols[ix]]),apex_z=float(0.84+iz*0.002),apex_y=float(sub[iz,ix]))
    out['glute']=gl
    # cleft depth vs z : apex ridge y (max over lobes at that z) minus central strip y
    rows=[]
    for z in (0.84,0.86,0.88,0.90,0.92,0.94,0.96,0.98):
        i=int(round((z-0.78)/0.002)); line=ba[i]; cen=line[np.abs(xs2)<0.008].min(); lob=line[np.abs(xs2)<0.16].max()
        rows.append(dict(z=z,cleft_depth_mm=float((lob-cen)*1000),lobe_y=float(lob),centre_y=float(cen)))
    out['glute']['cleft']=rows
    # shelf: envelope rise between z=1.0 and 0.94
    def env(z): i=int(round((z-0.78)/0.002)); return float(ba[i][np.abs(xs2)<0.16].max())
    out['glute']['shelf_rise_1.00_to_0.94_mm']=float((env(0.94)-env(1.0))*1000)
    # lobe cross-section curvature radius at apex (fit parabola over +-3 cm around apex x at apex z)
    for side in ('L','R'):
        a=gl[side]; i=int(round((a['apex_z']-0.78)/0.002)); line=ba[i]; sel=np.abs(xs2-a['apex_x'])<0.03
        c=np.polyfit(xs2[sel]-a['apex_x'],line[sel],2); gl[side]['curv_radius_cm']=float(abs(1/(2*c[0]))*100) if abs(c[0])>1e-9 else 999.0
    return out
if __name__=='__main__':
    P={**DEFAULT2,**json.load(open(WD/sys.argv[2]))}
    co=np.load(WD/sys.argv[1]); print(json.dumps(metrics(co,P),indent=1))

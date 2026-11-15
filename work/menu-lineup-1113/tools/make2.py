# v2 lighting: each venue's own sun + sky/equator/ground light (from Resources/Menu/Backdrops/<venue>_light.json),
# a readability floor on the fill so the shadow side never goes black, then a warm game grade on the heroes.
import json, subprocess, sys, math, numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
def proj(cam,look,fov,p,W=1920,H=1080):
    cam,look,p=map(np.array,(cam,look,p)); f=look-cam; f=f/np.linalg.norm(f)
    r=np.cross(f,[0,1,0]); r=r/np.linalg.norm(r); u=np.cross(r,f); d=p-cam
    x,y,z=d@r,d@u,d@f; t=np.tan(np.radians(fov/2))
    return (0.5+x/(z*t*W/H)/2, 0.5-y/(z*t)/2)
W,H=1920,1080
REPO='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator'
BD=REPO+'/Unity/Assets/Resources/Menu/Backdrops/'
T=dict(sun=720,minEl=28,sky=330,fill=420,fillFloor=0.55,gnd=200,rim=260,amb=110,sat=1.18,con=1.10,warm=0.05,expo=1.0)
def c3(d): return [d['r'],d['g'],d['b']]
def lum(c): return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def lights(venue):
    L=json.load(open(BD+venue+'_light.json')); s=L['sunDirCam']
    ray=np.array([s['x'],s['y'],-s['z']]); ray/=np.linalg.norm(ray)
    if T.get('sunAzEl'):   # override: azimuth (0 = from the camera, +90 = from camera-left, 180 = from behind), elevation in degrees
        az,el=[math.radians(v) for v in T['sunAzEl']]
        frm=np.array([-math.sin(az)*math.cos(el), math.sin(el), math.cos(az)*math.cos(el)]); ray=-frm
    el=math.degrees(math.asin(-ray[1]))
    if el<T['minEl']:   # keep the sun's side, lift it so faces are not half black
        h=np.array([ray[0],0,ray[2]]); h/=np.linalg.norm(h); e=math.radians(T['minEl'])
        ray=np.array([h[0]*math.cos(e),-math.sin(e),h[2]*math.cos(e)])
    sky,eq,gnd=c3(L['ambientSky']),c3(L['ambientEquator']),c3(L['ambientGround'])
    # readability floor: the fill from the camera side never drops below fillFloor of a neutral fill
    k=max(1.0,T['fillFloor']/max(lum(eq),1e-3)); eqf=[min(1,x*k) for x in eq]
    side=-np.sign(ray[0]) if abs(ray[0])>0.1 else 1.0
    fillray=[0.35*(-side)*-1,-0.25,-1.0]   # from the camera, a touch from the side opposite the sun
    rimray=[-side*-0.6*-1,-0.45,1.0]       # from behind, opposite the sun: separates hero from backdrop
    return dict(lights=[
        dict(ray=ray.tolist(),color=T.get('sunColor',c3(L['sunColor'])),intensity=T['sun']*T.get('sunNorm',L['sunIntensity']),shadow=True,shadowAlpha=T.get('shadowAlpha',min(0.62,L['shadowStrength']+0.1))),
        dict(ray=[0,-1,0],color=sky,intensity=T['sky']),
        dict(ray=fillray,color=eqf,intensity=T['fill']),
        dict(ray=[0,1,0],color=gnd,intensity=T['gnd']),
        dict(ray=rimray,color=T.get('rimColor',sky),intensity=T['rim'])],
        ambientColor=eqf,ambient=T['amb'],exposure=T.get('heroExpo',1.0))
def grade(img):
    rgb=img.convert('RGB'); a=img.getchannel('A')
    rgb=ImageEnhance.Color(rgb).enhance(T['sat'])
    x=np.asarray(rgb).astype(float)/255
    lin=np.where(x<=0.04045,x/12.92,((x+0.055)/1.055)**2.4)*T['expo']
    kn=0.75; lin=np.where(lin>kn, kn+(1-kn)*(1-np.exp(-(lin-kn)/(1-kn))), lin)   # soft shoulder: lifts without clipping whites
    x=np.where(lin<=0.0031308,lin*12.92,1.055*np.clip(lin,0,None)**(1/2.4)-0.055)
    x=0.5+(x-0.5)*T['con']
    x[...,0]*=1+T['warm']; x[...,1]*=1+T['warm']*0.35; x[...,2]*=1-T['warm']
    out=Image.fromarray((np.clip(x,0,1)*255).astype(np.uint8)).convert('RGBA'); out.putalpha(a); return out
def render(name,venue,spec,out_dir='../renders'):
    spec=dict(spec,**lights(venue),width=W,height=H,out=f"{out_dir}/{name}_heroes.png")
    json.dump(spec,open(f"/tmp/_{name}.json","w"))
    sh=dict(spec,out=f"{out_dir}/{name}_sh.png",shadowPass=True); json.dump(sh,open(f"/tmp/_{name}_sh.json","w"))
    for j in (f"/tmp/_{name}.json",f"/tmp/_{name}_sh.json"): subprocess.run(["./lineup_render",j],capture_output=True)
    main=Image.open(f"{out_dir}/{name}_heroes.png").convert("RGBA"); M=np.asarray(main)[...,3].astype(float)/255
    S=np.asarray(Image.open(f"{out_dir}/{name}_sh.png").convert("RGB")).astype(float).mean(2)/255
    floor=(M<0.01)&(S<0.995); ref=np.percentile(S[floor],97)
    a=np.clip((ref-S)/ref*1.5,0,0.7); a[M>0.5]=0; a[S>=0.995]=0
    ao=Image.new("L",(W,H),0); d=ImageDraw.Draw(ao)
    for h in spec["heroes"]:
        cx,cy=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],0,h["z"]]); l,_=proj(spec["cam"],spec["look"],spec["fov"],[h["x"]-0.32,0,h["z"]])
        _,ty=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],0,h["z"]-0.22]); rx=(cx-l)*W; ry=max(6,(cy-ty)*H)
        d.ellipse([cx*W-rx,cy*H-ry,cx*W+rx,cy*H+ry],fill=150)
    ao=np.asarray(ao.filter(ImageFilter.GaussianBlur(14))).astype(float)/255; a=np.maximum(a,ao*0.65); a[M>0.5]=0
    sha=np.zeros((H,W,4),np.uint8); sha[...,1]=6; sha[...,2]=24; sha[...,3]=(a*255).astype(np.uint8)
    shadow=Image.fromarray(sha,"RGBA").filter(ImageFilter.GaussianBlur(1.5))
    # auto exposure: same leader brightness in every venue (the venue keeps its light direction and colour)
    if T.get('target'):
        best=None
        for e in np.arange(0.6,2.2,0.05):
            T['expo']=float(e); g=grade(main); m=measure(g,(930,405,980,450))['median']
            if best is None or abs(m-T['target'])<abs(best[1]-T['target']): best=(float(e),m)
        T['expo']=best[0]; print(name,'auto expo',round(best[0],2))
    heroes=grade(main)
    bg=Image.open(BD+venue+".jpg").convert("RGBA"); bg.alpha_composite(shadow); bg.alpha_composite(heroes)
    pts=[]
    for h in spec["heroes"]:
        hx,hy=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],1.86,h["z"]]); pts.append([round(hx*100,2),round(hy*100,2)])
    return bg.convert("RGB"), heroes, pts
def measure(heroes, box):
    """leader in box: face brightness/warmth, dark tail, crushed share, clipped share"""
    x=np.asarray(heroes).astype(float); a=x[...,3]>200
    l,t,r,b=box; sub=x[t:b,l:r]; m=a[t:b,l:r]; px=sub[m][:,:3]
    L=0.2126*px[:,0]+0.7152*px[:,1]+0.0722*px[:,2]
    return dict(p5=round(float(np.percentile(L,5))),median=round(float(np.median(L))),crushed=round(float((L<35).mean()*100),1),clipped=round(float((px.max(1)>=252).mean()*100),1))
def face(img, box):
    x=np.asarray(img.convert('RGB')).astype(float)[box[1]:box[3],box[0]:box[2]].reshape(-1,3); r,g,b=x.mean(0)
    return dict(luma=round(0.2126*r+0.7152*g+0.0722*b),r_minus_b=round(r-b))

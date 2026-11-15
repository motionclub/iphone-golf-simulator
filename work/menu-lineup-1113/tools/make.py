import json, subprocess, sys, numpy as np
from PIL import Image, ImageFilter, ImageDraw
W,H=1920,1080
def proj(cam,look,fov,p):
    cam,look,p=map(np.array,(cam,look,p)); f=look-cam; f/=np.linalg.norm(f)
    r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f); d=p-cam
    x,y,z=d@r,d@u,d@f; t=np.tan(np.radians(fov/2))
    return (0.5+x/(z*t*W/H)/2, 0.5-y/(z*t)/2)
def render(name, spec):
    spec=dict(spec,width=W,height=H,out=f"out/{name}_heroes.png"); json.dump(spec,open(f"{name}.json","w"))
    s2=dict(spec,out=f"out/{name}_sh.png",shadowPass=True); json.dump(s2,open(f"{name}_sh.json","w"))
    for j in (f"{name}.json",f"{name}_sh.json"): subprocess.run(["./lineup_render",j],capture_output=True)
    main=np.asarray(Image.open(f"out/{name}_heroes.png").convert("RGBA")).astype(float)/255
    sh=np.asarray(Image.open(f"out/{name}_sh.png").convert("RGB")).astype(float)/255
    L=sh.mean(2); M=main[...,3]
    # floor rows only: below the horizon; reference = unshadowed lambert floor
    floor=(M<0.01)&(L<0.995)
    ref=np.percentile(L[floor],97) if floor.any() else 1
    a=np.clip((ref-L)/ref*1.6,0,0.75); a[M>0.5]=0; a[L>=0.995]=0
    # contact AO blobs under feet
    ao=Image.new("L",(W,H),0); d=ImageDraw.Draw(ao)
    lift=0.07 if spec.get("pads") else 0
    for h in spec["heroes"]:
        if spec.get("heroesOff"): break
        cx,cy=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],lift,h["z"]])
        l,_=proj(spec["cam"],spec["look"],spec["fov"],[h["x"]-0.32,lift,h["z"]]); 
        _,ty=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],lift,h["z"]-0.22])
        rx=(cx-l)*W; ry=max(6,(cy-ty)*H)
        d.ellipse([cx*W-rx,cy*H-ry,cx*W+rx,cy*H+ry],fill=150)
    ao=np.asarray(ao.filter(ImageFilter.GaussianBlur(14))).astype(float)/255
    a=np.maximum(a,ao*0.7); a[M>0.5]=0
    out=np.zeros((H,W,4),np.uint8); out[...,0]=0; out[...,1]=8; out[...,2]=40; out[...,3]=(a*255).astype(np.uint8)
    Image.fromarray(out,"RGBA").filter(ImageFilter.GaussianBlur(1.5)).save(f"out/{name}_shadow.png")
    pts=[]
    for h in spec["heroes"]:
        hx,hy=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],1.86+lift,h["z"]])
        fx,fy=proj(spec["cam"],spec["look"],spec["fov"],[h["x"],lift,h["z"]+0.25])
        pts.append(dict(head=[round(hx*100,2),round(hy*100,2)],feet=[round(fx*100,2),round(fy*100,2)]))
    pads=[]
    for p in spec.get("pads",[]):
        cx,cy=proj(spec["cam"],spec["look"],spec["fov"],[p[0],0.07,p[1]]); pads.append([round(cx*100,2),round(cy*100,2)])
    return dict(points=pts,pads=pads)
S={}
S["squad"]=render("squad",dict(cam=[0,0.98,5.3],look=[0,1.03,0],fov=32,rimL="FFE2B8",rimR="CFE0FF",key=1250,ambient=320,heroes=[
 dict(female=False,kit="tennis",clip="relaxed",t=3.0,x=0,z=0,yaw=0,racketBack=True),
 dict(female=True,kit="tennis",skin="E6AE7E",shirt="2F6FD6",shorts="F4F0E6",clip="relaxed",t=5.2,x=-1.2,z=-0.75,yaw=-12,racketBack=True),
 dict(female=False,kit="tennis",skin="74432C",shirt="7BC043",shorts="23344D",shoes="FFFFFF",clip="wave",t=0.9,x=1.2,z=-0.75,yaw=12,racketBack=True),
 dict(female=True,kit="tennis",skin="3E2317",shirt="F5C542",shorts="FFFFFF",clip="relaxed",t=7.5,x=-2.4,z=-1.75,yaw=-18,racketBack=True)]))
S["row"]=render("row",dict(cam=[0,1.25,7.8],look=[0,1.18,0],fov=30,rimL="FFE7C2",rimR="D6E6FF",key=1250,ambient=320,
 pads=[[-1.0,0,0.55],[0.25,0,0.55],[1.5,0,0.55],[2.75,0,0.55]],heroes=[
 dict(female=True,kit="golf",skin="E6AE7E",clip="idle",t=0.3,x=-1.0,z=0,yaw=-6),
 dict(female=False,kit="golf",clip="idle",t=1.0,x=0.25,z=0,yaw=-2),
 dict(female=True,kit="golf",skin="74432C",clip="wave",t=0.9,x=1.5,z=0,yaw=2),
 dict(female=False,kit="golf",skin="B7744A",clip="cheer",t=0.8,x=2.75,z=0,yaw=6)]))
S["solo"]=render("solo",dict(cam=[0,0.98,5.3],look=[0,1.03,0],fov=32,rimL="FF6BDD",rimR="52E6FF",rim=800,key=1300,ambient=330,padColor="1A1240",padRing="52E6FF",
 pads=[[0,0,0.6],[-1.2,-0.75,0.5],[1.2,-0.75,0.5],[-2.4,-1.75,0.5]],heroes=[
 dict(female=True,kit="bowling",skin="B7744A",clip="relaxed",t=3.0,x=0,z=0,yaw=0)]))
json.dump(S,open("out/points.json","w"),indent=1); print(json.dumps(S))

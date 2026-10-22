import bpy, numpy as np
img = bpy.data.images.load("/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Resources/Course/Look/Basalt_E.png")
w,h=img.size; px=np.empty(w*h*4,np.float32); img.pixels.foreach_get(px); E=px.reshape(h,w,4)[:,:,:3].max(axis=2); G=E>0.2
print("tex lit mean", G.mean(), "col profile peaks", np.nonzero(G.mean(axis=0)>0.25)[0][:20]/w)
for name in ("ROCK_WALL_BASALT_N1_V1","ROCK_WALL_BASALT_F1_V2","ROCK_CRUST_03"):
    me=bpy.data.meshes.get(name)
    if me is None:
        ob=bpy.data.objects.get(name); me=ob.data if ob else None
    print(name, me is not None)
    if me is None: continue
    uv=me.uv_layers.active; u=np.empty(len(me.loops)*2); uv.data.foreach_get("uv",u); u=u.reshape(-1,2)
    nside=0; nlit=0; nlinein=0
    for p in me.polygons:
        if abs(p.normal.z)>=0.8: continue
        l=u[p.loop_start:p.loop_start+p.loop_total]
        nside+=1
        umin,umax=l[:,0].min(),l[:,0].max()
        # is any glow line (strong) within the u range (mod 1)?
        lines=[0.123,0.446,0.534,0.718,0.806,0.93]
        inr=any(((g-umin)%1.0)<= (umax-umin) for g in lines)
        nlinein+=inr
        # sampled lit: 5x5 grid inside uv bbox
        uu=np.linspace(umin,umax,15); vv=np.linspace(l[:,1].min(),l[:,1].max(),15)
        UU,VV=np.meshgrid(uu,vv)
        lit=G[(np.floor((VV%1.0)*h).astype(int))%h,(np.floor((UU%1.0)*w).astype(int))%w].any()
        nlit+=lit
    print(" side polys",nside,"with a glow line in u-range",nlinein,"with lit texel in bbox grid",nlit)

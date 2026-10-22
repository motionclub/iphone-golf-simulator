import bpy, sys, numpy as np
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
H=PC.Hole(D); YD=0.9144
for o in bpy.data.objects:
    if o.name.startswith('ROCK_SKIN'):
        M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]); V=(np.c_[V,np.ones(len(V))]@M.T)[:,:3]
        inw=[v for v in V if v[2]>0.3 and any(H.in_ellipse(h,(v[0]/YD,v[1]/YD)) for h in H.hazards if h[0]=='water')]
        # up-facing faces over ellipse
        up=0;area=0
        for p in o.data.polygons:
            c=V[list(p.vertices)].mean(0)
            if p.normal.z>0.3 and any(H.in_ellipse(h,(c[0]/YD,c[1]/YD)) for h in H.hazards if h[0]=='water') and c[2]>0.3: up+=1; area+=p.area
        # beyond shore (land polygon): up-facing skin faces over water outside polygon
        out=0;oa=0;maxz=0
        for p in o.data.polygons:
            c=V[list(p.vertices)].mean(0)
            if p.normal.z>0.3 and not H.on_land((c[0]/YD,c[1]/YD)) and c[2]>0.3: out+=1; oa+=p.area; maxz=max(maxz,c[2])
        print(o.name,'verts in ellipse z>0.3:',len(inw),'upfaces in ellipse',up,'%.1f m2'%area,'| upfaces outside shore',out,'%.1f m2'%oa,'maxz %.2f'%maxz)

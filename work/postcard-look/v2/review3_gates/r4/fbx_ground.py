import bpy,sys,numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
def load(p):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.fbx(filepath=p); d={}
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith(PFX):
            me=o.data;M=np.array(o.matrix_world);co=np.array([v.co[:] for v in me.vertices]);w=co@M[:3,:3].T+M[:3,3]
            ups=set()
            for pl in me.polygons:
                if (M[:3,:3]@np.array(pl.normal))[2]>0: ups.add(tuple(sorted(tuple(np.round(w[i],3)) for i in pl.vertices)))
            d[o.name]=(set(map(tuple,np.round(w,3))),ups)
    return d
for n in ('08','09','10'):
    a=load(R+f'work/postcard-look/baseline/fbx/hole_{n}.fbx'); b=load(R+f'Unity/Assets/Resources/Course/hole_{n}.fbx')
    ok=sorted(a)==sorted(b) and all(a[k][0]==b[k][0] and a[k][1]==b[k][1] for k in a if k in b)
    print('FBXGROUND',n,'names equal',sorted(a)==sorted(b),'verts+upfaces identical (1mm)',ok,'n objs',len(a),'nverts',sum(len(v[0]) for v in a.values()),'nup',sum(len(v[1]) for v in a.values()))

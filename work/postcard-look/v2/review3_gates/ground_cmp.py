import bpy,sys,numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
PFX=('TERRAIN','FAIRWAY','GREEN','TEE_BOX','BUNKER')
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    d={}
    for o in bpy.data.objects:
        if o.type=='MESH' and o.name.startswith(PFX):
            me=o.data; M=np.array(o.matrix_world)
            n=len(me.vertices); co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(-1,3)
            w=(co@M[:3,:3].T)+M[:3,3]
            ups=[]
            for pl in me.polygons:
                nz=(np.array(o.matrix_world.to_3x3())@np.array(pl.normal))[2]
                if nz>0.0:
                    pts=sorted(tuple(np.round(w[i],4)) for i in pl.vertices)
                    ups.append(tuple(pts))
            d[o.name]=(w,sorted(ups))
    return d
for n in ('08','09','10'):
    a=load(R+f'work/postcard-look/baseline/blender/hole_{n}.blend')
    b=load(R+f'blender/hole_{n}.blend')
    print('hole',n,'baseline names',sorted(a),'installed names',sorted(b))
    for k in sorted(set(a)|set(b)):
        if k not in a or k not in b: print('  MISSING',k, k in a, k in b); continue
        wa,ua=a[k]; wb,ub=b[k]
        same_v = wa.shape==wb.shape and np.abs(wa-wb).max()<1e-5
        # set compare of vertices
        sa=set(map(tuple,np.round(wa,4))); sb=set(map(tuple,np.round(wb,4)))
        print('  ',k,'verts',len(wa),len(wb),'ordered-identical',same_v,'set-identical',sa==sb,'upfaces',len(ua),len(ub),'up-identical',ua==ub)

import bpy,numpy as np
R='/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/'
def load(p):
    bpy.ops.wm.open_mainfile(filepath=p)
    d={}
    for o in bpy.data.objects:
        if o.name.startswith(('MARKER','BALL','HOLE_CUP','FLAG','TEE_MARKER','CART')) or o.type=='EMPTY':
            d[o.name]=tuple(np.round(o.matrix_world.translation,5))+((len(o.data.vertices),) if o.type=='MESH' else ())
    names=sorted(o.name for o in bpy.data.objects if o.name.startswith(('CART','COLL','HAZ','OB_','WATER_')))
    return d,names
for n in ('08','09','10'):
    a,na=load(R+f'work/postcard-look/baseline/blender/hole_{n}.blend'); b,nb=load(R+f'blender/hole_{n}.blend')
    print('hole',n,'markers equal:',a==b, {k:(a.get(k),b.get(k)) for k in set(a)|set(b) if a.get(k)!=b.get(k)})
    print('  baseline special names',na[:40]); print('  installed special names',[x for x in nb if not x.startswith('WATER_SURF')][:40])

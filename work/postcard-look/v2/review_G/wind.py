import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index("--")+1])
from collections import defaultdict
st=defaultdict(lambda:[0,0,0.0])
for o in bpy.data.objects:
    if o.type!='MESH': continue
    k=None
    for pre in ('WATER_OCEAN','WATER_SHELF','WATER_SURF','WATER_LAVA','DRESS_PATH','ROCK_SKIN'):
        if o.name.startswith(pre): k=pre
    if not k: continue
    M=o.matrix_world.to_3x3()
    for p in o.data.polygons:
        n=M@p.normal
        if k.startswith('ROCK_SKIN'): continue
        if n.z>0: st[k][0]+=1
        else:
            st[k][1]+=1; st[k][2]+=p.area
for k,v in st.items(): print(k,"up",v[0],"down",v[1],"down area %.2f"%v[2])

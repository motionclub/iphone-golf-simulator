import bpy, bmesh, numpy as np, sys
a=sys.argv[sys.argv.index('--')+1:]
Zn=np.load('data/zones_cur.npz'); arm=Zn['arm']
def run(p):
    bpy.ops.wm.open_mainfile(filepath=p); me=bpy.data.objects['Body_F'].data; bm=bmesh.new(); bm.from_mesh(me); bm.edges.ensure_lookup_table()
    out=[]
    for e in bm.edges:
        if len(e.link_faces)==2:
            m=(e.verts[0].co+e.verts[1].co)/2
            out.append((np.degrees(e.link_faces[0].normal.angle(e.link_faces[1].normal)),e.index,e.verts[0].index,e.verts[1].index,tuple(m)))
    return out
S=run(a[0]); F=run(a[1])
n=len(F)
rows=[]
for s,f in zip(S,F):
    if arm[s[2]] or arm[s[3]]:
        rows.append((f[0]-s[0],f[0],s[0],f[2],f[3],np.round(f[4],3)))
rows.sort(key=lambda r:-r[0])
for r in rows[:14]: print(round(r[0],1),round(r[1],1),round(r[2],1),r[3],r[4],r[5], 'pin' )

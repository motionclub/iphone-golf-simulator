import bpy, numpy as np, sys
exec(open('tools/render_npz.py').read().split("bl.studio(")[0].replace("a = sys.argv[sys.argv.index('--') + 1:]","a = ['x','out/MatchHero_Male/unity','Kit_Shoe_R:ShoeR']"))
me=objs[0].data
im=[i for i in bpy.data.images if i.name.startswith('ShoeR_M')][0]; W,H=im.size; px=np.array(im.pixels[:]).reshape(H,W,4)
for fi in (8845,8846,8874):
    p=me.polygons[fi]; uvs=[tuple(me.uv_layers[0].data[l].uv) for l in p.loop_indices]
    c=np.mean(uvs,0); print('DBG', fi, p.material_index, c, 'B', px[int(c[1]*H), int(c[0]*W), 2])

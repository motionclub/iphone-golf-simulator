exec(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/review_08/path.py').read().split("paths=[o")[0])
import time
for nm in ('DRESS_PATH_01','DRESS_PATH_02'):
    o=bpy.data.objects[nm]; pb=mk([o]); V=wv(o)
    lo=V[:,:2].min(0); hi=V[:,:2].max(0)
    step=0.02; n=0; over=[]; tot=0
    xs=np.arange(lo[0],hi[0],step); ys=np.arange(lo[1],hi[1],step)
    for y in ys:
        for x in xs:
            r=pb.ray_cast(Vector((x,y,40)),Vector((0,0,-1)))
            if r[0] is None: continue
            tot+=1
            t=top(x,y)
            if t is None: continue
            dz=r[0].z-t
            if dz>0.012: over.append((x/YD,y/YD,dz))
    print(nm,'path samples',tot,'over 1.2cm',len(over),'area m2 %.3f'%(len(over)*step*step), 'max dz', max([d for _,_,d in over]) if over else 0)
    if over:
        a=np.array(over); print(' x,y yd range',a[:,0].min(),a[:,0].max(),a[:,1].min(),a[:,1].max(),'dz>2cm',int((a[:,2]>0.02).sum()))

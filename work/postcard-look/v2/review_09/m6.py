import bpy, numpy as np, math
res=0.4
def tris(objs):
    out=[]
    for o in objs:
        me=o.data; me.calc_loop_triangles(); mw=o.matrix_world
        V=np.array([tuple(mw@v.co) for v in me.vertices]) if len(me.vertices) else np.zeros((0,3))
        for t in me.loop_triangles:
            out.append(V[list(t.vertices)])
    return out
x0,x1,y0,y1=-190,150,-60,600
nx=int((x1-x0)/res); ny=int((y1-y0)/res)
def raster(T):
    m=np.zeros((ny,nx),bool)
    for t in T:
        xs=t[:,0];ys=t[:,1]
        i0=max(int((xs.min()-x0)/res),0); i1=min(int((xs.max()-x0)/res)+1,nx-1)
        j0=max(int((ys.min()-y0)/res),0); j1=min(int((ys.max()-y0)/res)+1,ny-1)
        if i1<i0 or j1<j0: continue
        gx,gy=np.meshgrid(x0+(np.arange(i0,i1+1)+0.5)*res, y0+(np.arange(j0,j1+1)+0.5)*res)
        d=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(d)<1e-9: continue
        a=((ys[1]-ys[2])*(gx-xs[2])+(xs[2]-xs[1])*(gy-ys[2]))/d
        b=((ys[2]-ys[0])*(gx-xs[2])+(xs[0]-xs[2])*(gy-ys[2]))/d
        c=1-a-b
        m[j0:j1+1,i0:i1+1] |= (a>=0)&(b>=0)&(c>=0)
    return m
sh=[o for o in bpy.data.objects if o.name.startswith('WATER_SHELF')]
land=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('TERRAIN','ROCK_SKIN','FAIRWAY','GREEN','TEE_BOX','BUNKER'))]
S=raster(tris(sh)); L=raster(tris(land))
vis=S&~L
print('shelf visible px area m2',vis.sum()*res*res,'shelf total',S.sum()*res*res)
# distance from cover in px by dilation
dist=np.full((ny,nx),999.0); cur=L.copy(); d=0
front=L.copy()
for k in range(1,40):
    nxt=np.zeros_like(cur)
    nxt[1:,:]|=cur[:-1,:]; nxt[:-1,:]|=cur[1:,:]; nxt[:,1:]|=cur[:,:-1]; nxt[:,:-1]|=cur[:,1:]
    nxt|=cur
    new=nxt&~cur
    dist[new]=k*res
    cur=nxt
w=dist[vis]
print('visible shelf: n',len(w),'median',np.median(w),'p90',np.percentile(w,90),'p95',np.percentile(w,95),'p99',np.percentile(w,99),'max',w.max())
# shore length: boundary px of L adjacent to water
edge=(dist<=res*1.01)&(dist>0)
print('shore edge length approx m',edge.sum()*res)
print('mean visible width = area/edge', vis.sum()*res*res/(edge.sum()*res))
# widest areas
big=np.argwhere(vis&(dist>4.0))
print('pixels >4 m from cover',len(big))
if len(big):
    ys_=y0+big[:,0]*res; xs_=x0+big[:,1]*res
    print('around',np.round([xs_.mean(),ys_.mean()],1), 'range',xs_.min(),xs_.max(),ys_.min(),ys_.max())
print('---- surf')
surf=[o for o in bpy.data.objects if o.name.startswith('WATER_SURF')]
ext=[]
for o in surf:
    d=o.dimensions; ext.append(max(d.x,d.y))
print('n surf',len(surf),'max extent',max(ext),'median',np.median(ext), 'total tris', sum(len(o.data.polygons) for o in surf))
M=raster(tris(surf))
def dil(m,n):
    cur=m.copy()
    for _ in range(n):
        nxt=cur.copy(); nxt[1:,:]|=cur[:-1,:]; nxt[:-1,:]|=cur[1:,:]; nxt[:,1:]|=cur[:,:-1]; nxt[:,:-1]|=cur[:,1:]; cur=nxt
    return cur
Md=dil(M,int(3/res))
cov=(edge&Md).sum()/edge.sum()
print('shore edge px within 3 m of surf: %.3f'%cov, 'surf area m2',M.sum()*res*res)
# materials
m=surf[0].data.materials[0]; print(m.name, [ (n.type, [ (i.name, tuple(i.default_value)[:3] if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if i.name in ('Base Color','Alpha','Emission Color','Emission Strength')]) for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'])
print('blend_method', getattr(m,'blend_method',None), m.diffuse_color[:])

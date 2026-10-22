from pathlib import Path
p=Path('Tools/HeroBase/build_static.py');s=p.read_text().replace('round(n*.78)','round(n*.70)').replace('round(k*.78)','round(k*.70)').replace('round(n*.70));steps=max(8,round(steps*.64))','round(n*.64));steps=max(8,round(steps*.58))').replace('N=80;K=38','N=72;K=34').replace('female,step=4.7','female,step=5.2 if female else 6.35')
s=s.replace('me.update();return o','''me.update()
        if hasattr(self,'custom_normals'):
            normals=[tuple(self.custom_normals.get(i,me.vertices[i].normal)) for i in range(len(me.vertices))]
            me.normals_split_custom_set_from_vertices(normals)
        return o''')
p.write_text(s)
p=Path('Tools/HeroBase/measured_volume.py');s=p.read_text().replace('for x,depth,y in points:g.vert(pix(float(x),float(y),float(depth)))','''for x,depth,y in points:g.vert(pix(float(x),float(y),float(depth)))
    # Analytic field normals avoid visible cell facets without moving the silhouette.
    gradient=np.gradient(field,step)
    gridcoords=(points-np.array([xs[0],ds[0],ys[0]]))/step
    lo=np.floor(gridcoords).astype(int);fr=gridcoords-lo;norm=np.zeros_like(points)
    for a,b,c in corner_offsets:
        wt=(fr[:,0] if a else 1-fr[:,0])*(fr[:,1] if b else 1-fr[:,1])*(fr[:,2] if c else 1-fr[:,2])
        idx=lo+np.array([a,b,c]);idx=np.minimum(np.maximum(idx,0),np.array(field.shape)-1)
        for ax in range(3):norm[:,ax]+=gradient[ax][idx[:,0],idx[:,1],idx[:,2]]*wt
    norm/=np.maximum(np.linalg.norm(norm,axis=1),1e-9)[:,None]
    if not hasattr(g,'custom_normals'):g.custom_normals={}
    for i,n in enumerate(norm):g.custom_normals[base+i]=(float(n[0]),float(n[1]),float(-n[2]))''');p.write_text(s)

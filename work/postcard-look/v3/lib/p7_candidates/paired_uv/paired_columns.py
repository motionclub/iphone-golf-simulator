"""One scratch paired-side chart variant. Geometry and texture are immutable.

Each real column receives one continuous chart across two neighboring exposed
vertical planes. u follows its actual counterclockwise footprint perimeter;
v follows world z and shares one phase on both planes. Original plain windows
remain on every other face and cap. No production script is imported by path
replacement or edited, and no missing geometry is synthesized.
"""
import json,random
import numpy as np
import hole10_look as H


def author_paired_columns(ob,seed=0,uf=.38,vf=.32):
    me=ob.data
    H.author_uv(me,random.Random(seed),uf=uf,vf=vf,p_glow=0.)
    uv=me.uv_layers.active
    specs=json.loads(ob['lk_v3_columns'])
    centers=(.113,.435,.532,.728,.825,.946)
    records=[]
    phase_rng=random.Random(seed+941)
    for ci,spec in enumerate(specs):
        a,b=spec['faces']
        polys=list(me.polygons)[a:b]
        cap=min(polys,key=lambda p:p.center.z)
        xy=np.array([tuple(me.vertices[i].co)[:2] for i in cap.vertices])
        area=(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1)).sum()
        if area<0:xy=xy[::-1]
        edge=np.roll(xy,-1,axis=0)-xy
        length=np.linalg.norm(edge,axis=1)
        tangent=edge/length[:,None]
        arc=np.r_[0.,np.cumsum(length)]
        # The shared corner is a real frontmost vertex, not a camera crop.
        corner=int(np.argmin(xy[:,1]))
        pair=((corner-1)%len(xy),corner)
        chosen={}
        for pi in range(a,b):
            poly=me.polygons[pi]
            pts=np.array([tuple(me.vertices[i].co) for i in poly.vertices])
            if abs(H._newell(pts)[2])>.01:continue
            bottom=pts[np.abs(pts[:,2]-spec['bottom'])<1e-5,:2]
            if len(bottom)!=2:continue
            for j in pair:
                endpoints=np.array([xy[j],xy[(j+1)%len(xy)]])
                if max(min(np.linalg.norm(pt-en,axis=1)) for pt in bottom for en in (endpoints,))<1e-5:
                    chosen[j]=pi
        if len(chosen)!=2:
            raise RuntimeError('column has no actual neighboring vertical front planes')
        # Fit a whole real hot tree across the pair. All six original glow
        # lines remain in the frozen contract; narrow hex faces have fewer
        # physically fitting corridors and are not stretched to manufacture one.
        eligible=[]
        left=length[pair[0]]*uf/8;right=length[pair[1]]*uf/8
        for j,g in enumerate(H.GLOW_U):
            reach=.022 if j==4 else .028
            if g-left<=centers[j]-reach-.003 and g+right>=centers[j]+reach+.003:
                eligible.append(j)
        if not eligible:raise RuntimeError('no unchanged glow corridor fits the actual paired perimeter')
        gi=eligible[ci%len(eligible)];g=H.GLOW_U[gi]
        phase=phase_rng.random()
        continuity=[]
        for j in pair:
            poly=me.polygons[chosen[j]]
            # Arc coordinates are centered at the real shared corner, with
            # the preceding edge unwrapped to negative distance across seam0.
            origin=-length[j] if j==pair[0] else 0.
            for li in poly.loop_indices:
                pt=np.array(tuple(me.vertices[me.loops[li].vertex_index].co))
                station=origin+float((pt[:2]-xy[j])@tangent[j])
                uv.data[li].uv=(g+station*uf/8,phase+pt[2]*vf/8)
            for li in poly.loop_indices:
                pt=np.array(tuple(me.vertices[me.loops[li].vertex_index].co))
                if np.linalg.norm(pt[:2]-xy[corner])<1e-5:
                    continuity.append((float(pt[2]),tuple(uv.data[li].uv)))
        by_z={}
        for z,co in continuity:by_z.setdefault(round(z,5),[]).append(np.array(co))
        seam=max((float(np.linalg.norm(q[0]-q[1])) for q in by_z.values() if len(q)==2),default=0.)
        records.append(dict(column=ci,polygons=[chosen[j] for j in pair],footprint_sides=len(xy),glow_index=gi,corner_u=g,v_phase=phase,paired_perimeter_m=float(sum(length[j] for j in pair)),shared_edge_uv_delta=seam))
    me.update()
    return dict(uf=uf,vf=vf,records=records,glow_lines_used=sorted({r['glow_index'] for r in records}),max_shared_edge_uv_delta=max(r['shared_edge_uv_delta'] for r in records))

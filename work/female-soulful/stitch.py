"""Join the polo's thin sewing panels before thickness and skin transfer."""
import bpy,bmesh,numpy as np

def sleeves_into_shell(shirt,sleeves,cuffs,width):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in [shirt]+sleeves:ob.select_set(True)
    bpy.context.view_layer.objects.active=shirt;bpy.ops.object.join()
    bm=bmesh.new();bm.from_mesh(shirt.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00005)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    # Turn the sleeve ends into separate substantial cuff bands.
    dc=bm.verts.layers.float.get('d_cuff');panel=bm.faces.layers.int.get('panel')
    cut=[f for f in bm.faces if f[panel] in (2,3) and all(v[dc]<width for v in f.verts)]
    cb=bmesh.new();vertices={};cp=cb.faces.layers.int.new('panel')
    for face in cut:
        vv=[]
        for v in face.verts:
            if v not in vertices:vertices[v]=cb.verts.new(v.co+v.normal*.001)
            vv.append(vertices[v])
        cf=cb.faces.new(vv);cf[cp]=6
    cb.to_mesh(cuffs.data);cb.free()
    # Cuffs carry their own planar UVs and construction fields.
    me=cuffs.data
    uv=me.uv_layers.new(name='UVMap')
    for f in me.polygons:
        for li in f.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v.x*4,v.z*4)
    for name in ['d_cuff','d_hem','d_neck','d_seam','d_arm']:
        attr=me.attributes.new(name,'FLOAT','POINT');attr.data.foreach_set('value',np.full(len(me.vertices),.01 if name=='d_cuff' else 1,np.float32))
    bmesh.ops.delete(bm,geom=cut,context='FACES');print('THIN SHELL max edge mm',max(e.calc_length()for e in bm.edges)*1000,flush=True);bm.to_mesh(shirt.data);bm.free();shirt.data.update()
    print('STITCHED sleeves; cuff faces',len(me.polygons),flush=True)

def fair_sleeve(R,D,side):
    """Smooth collision clearance at the torso/upper-arm union, avoiding per-triangle push noise."""
    sg=np.array([side,1,1]);start=np.array(D['arm_joint'])*sg
    axis=np.array(D['arm_dir'])*sg;axis/=np.linalg.norm(axis);end=start+axis*.30
    center=np.array([0,D['yc'],1.18]);radius=np.array([.128,.110,.205])
    def distance(p):
        q=(p-center)/radius;torso=(np.linalg.norm(q,axis=1)-1)*min(radius)
        v=end-start;t=np.clip(((p-start)@v)/(v@v),0,1);arm=np.linalg.norm(p-(start+t[:,None]*v),axis=1)-.047
        k=.018;h=np.clip(.5+.5*(arm-torso)/k,0,1)
        return arm*(1-h)+torso*h-k*h*(1-h)
    shape=R.shape;original=R.copy();p=R.reshape(-1,3).copy();fixed=np.zeros(len(p),bool);fixed[:shape[1]]=True
    for rep in range(4):
        d=distance(p);eps=1e-4;g=np.zeros_like(p)
        for a in range(3):
            dp=np.zeros(3);dp[a]=eps;g[:,a]=(distance(p+dp)-distance(p-dp))/(2*eps)
        g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-12
        p+=g*np.clip(.0045-d,0,.010)[:,None]*(~fixed[:,None])
    R=p.reshape(shape)
    for _ in range(12):
        R[1:]+=.22*((np.roll(R[1:],-1,1)+np.roll(R[1:],1,1))*.5-R[1:])
        R[1:-1]+=.20*((R[:-2]+R[2:])*.5-R[1:-1])
    R[0]=original[0]
    from pathlib import Path
    np.savez(Path(__file__).resolve().parent/f'sleeve-pattern-{side}.npz',R=R)
    import json
    pattern=Path(__file__).resolve().parent/'source/golf_sleeve_pattern.json'
    patterns=json.loads(pattern.read_text())if pattern.exists()else {}
    patterns[str(side)]=R.tolist();pattern.write_text(json.dumps(patterns,separators=(',',':'))+'\n')
    return R

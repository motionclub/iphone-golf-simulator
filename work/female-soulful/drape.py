"""Settle a thin garment surface over the existing body before constructing its trims."""
import bpy,numpy as np
from mathutils import Vector

def settle(shell,hero,polo=False):
    from polo2 import apply_modifier,polys,smoothstep,boundary_loops_poly,dist_to_polyline
    import glib as G
    bpy.context.view_layer.objects.active=shell
    if bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    # Collider is a disposable simplified copy, never a replacement body asset.
    body=G.body_no_arms(G.Body(hero),.35)
    p=body.pos;tri=body.tri;c=p[tri].mean(1);tri=tri[(c[:,2]>.88)&(c[:,2]<1.48)]
    me=bpy.data.meshes.new('Drape collider');me.from_pydata(p.tolist(),[],tri.tolist());me.update()
    ob=bpy.data.objects.new('Drape collider',me);bpy.context.scene.collection.objects.link(ob)
    dec=ob.modifiers.new('Collision resolution','DECIMATE');dec.ratio=.35;apply_modifier(ob,dec)
    ob.modifiers.new('Collision','COLLISION');ob.collision.thickness_outer=.003;ob.collision.thickness_inner=.001
    pos,faces=polys(shell);group=shell.vertex_groups.new(name='PIN_Cloth')
    pin=np.maximum(smoothstep(1.26 if polo else 1.30,1.34 if polo else 1.36,pos[:,2]),1-smoothstep(.985,1.015,pos[:,2]))
    loops=boundary_loops_poly(faces)
    edge_distance=np.minimum.reduce([dist_to_polyline(pos,pos[loop])for loop in loops if len(loop)>3])
    pin=np.maximum(pin,1-smoothstep(.006,.030,edge_distance))
    for i,w in enumerate(pin):
        if w>0:group.add([i],float(w),'REPLACE')
    cloth=shell.modifiers.new('Gravity drape','CLOTH');s=cloth.settings
    s.quality=8;s.mass=.15;s.tension_stiffness=18;s.compression_stiffness=18;s.shear_stiffness=8;s.bending_stiffness=.18
    s.air_damping=2;s.vertex_group_mass=group.name;s.pin_stiffness=1
    cloth.collision_settings.use_collision=True;cloth.collision_settings.distance_min=.003
    cloth.collision_settings.use_self_collision=False;cloth.collision_settings.self_distance_min=.003
    cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=45
    scene=bpy.context.scene;scene.frame_set(1)
    for frame in range(1,46):scene.frame_set(frame)
    ev=shell.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();q=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
    if q.shape!=pos.shape:raise RuntimeError('Drape topology changed')
    delta=q-pos;length=np.linalg.norm(delta,axis=1)
    if not np.isfinite(q).all():raise RuntimeError('Drape became unstable')
    # Retain the authored silhouette and trim construction while accepting the settle folds.
    triangles=np.array([t for face in faces for t in [(face[0],face[k],face[k+1])for k in range(1,len(face)-1)]])
    nb=G.neighbours(len(pos),triangles)
    for _ in range(40):delta+=.5*G.umbrella(delta,nb)
    delta*=1-pin[:,None]
    length=np.linalg.norm(delta,axis=1)
    delta*=np.minimum(1,.018/np.maximum(length,1e-9))[:,None]
    shell.modifiers.remove(cloth);shell.data.vertices.foreach_set('co',(pos+delta).astype(np.float32).ravel());shell.data.update()
    bpy.data.objects.remove(ob,do_unlink=True);scene.frame_set(1)
    print('DRAPE max raw mm',float(length.max()*1000),'accepted cap 18mm',flush=True)

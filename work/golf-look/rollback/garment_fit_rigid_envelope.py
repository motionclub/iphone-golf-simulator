"""Proof-pose envelopes for isolated garment modelling; no source writes."""
import bpy, numpy as np, hashlib
from mathutils import Matrix

def hip_envelope(rig,body,proof_path):
    """Body points mapped back through Hips' rigid transform in all eight poses.

    Only existing static proof actions are imported. They are removed after
    sampling, so no duplicated action names or new rig bones are exported.
    """
    group_names={g.index:g.name for g in body.vertex_groups}
    ids=[v.index for v in body.data.vertices if .60<v.co.z<1.025 and abs(v.co.x)<.32 and
         sum(g.weight for g in v.groups if group_names[g.group] in ['Hips','Spine','LeftUpperLeg','RightUpperLeg'])>.35]
    imported=[]
    with bpy.data.libraries.load(str(proof_path),link=False) as (src,dst):
        dst.actions=[n for n in src.actions if n.startswith('GolfProof_') and '.' not in n]
    imported=[a for a in dst.actions if a is not None]
    acts=[bpy.data.actions['ReadyIdle']]+imported
    assert len(acts)==8,'Eight proof poses required for the skirt envelope'
    rest=np.array(rig.matrix_world@rig.data.bones['Hips'].matrix_local)
    clouds=[];names=[];sc=bpy.context.scene
    rig.data.pose_position='POSE';rig.animation_data_create()
    for act in acts:
        rig.animation_data.action=act
        if act.slots:rig.animation_data.action_slot=act.slots[0]
        sc.frame_set(0);bpy.context.view_layer.update()
        dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh()
        co=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',co)
        ev.to_mesh_clear();co=co.reshape(-1,3)[ids].astype(float)
        world=np.array(ev.matrix_world);co=co@world[:3,:3].T+world[:3,3]
        pose=np.array(rig.matrix_world@rig.pose.bones['Hips'].matrix)
        tr=rest@np.linalg.inv(pose)
        clouds.append(co@tr[:3,:3].T+tr[:3,3]);names.append(act.name)
    rig.animation_data.action=None
    for a in imported:bpy.data.actions.remove(a)
    for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
    rig.data.pose_position='REST';bpy.context.view_layer.update()
    return np.concatenate(clouds),dict(source=str(proof_path),source_sha256=hashlib.sha256(proof_path.read_bytes()).hexdigest(),poses=names,body_vertices_per_pose=len(ids),space='world bind coordinates after inverse rigid Hips deformation')

def ring(cloud,z,margin=.024):
    near=cloud[np.abs(cloud[:,2]-z)<.035]
    if len(near)<20:near=cloud[np.argsort(np.abs(cloud[:,2]-z))[:200]]
    cy=(near[:,1].min()+near[:,1].max())/2
    rx=np.abs(near[:,0]).max();ry=np.abs(near[:,1]-cy).max()
    q=np.sqrt((near[:,0]/rx)**2+((near[:,1]-cy)/ry)**2).max()
    # Circumscribe the point cloud before adding clearance and folded pleats.
    return float(rx*q+margin),float(ry*q+margin),float(cy),len(near)

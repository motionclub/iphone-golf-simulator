"""Assemble export/racket_classic_socket.json (socket conventions + per-body hand-frame data) from the on-hand run results."""
import json
from pathlib import Path
W = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/classic-tennis-racket')
bodies = {}
for tag, blend in (('male', 'HeroBase_Male_Silhouette.blend'), ('female', 'HeroBase_Female.blend')):
    d = json.load(open(W / 'data' / 'onhand_run' / f'onhand_{tag}.json'))
    bodies[tag] = dict(
        hero_blend=f'ArtDir/hero/base_lock/blender/{blend}',
        hand_object='right hand (character right = world -X in Blender, +X in Unity)',
        hand_frame_blender=d['socket']['hand_frame_blender'],
        hand_frame_unity=d['socket']['hand_frame_unity'],
        grip_in_hand_frame=d['socket']['grip_in_hand_frame'],
        socket_bind_pose_blender=d['socket']['apose_world_blender'],
        socket_bind_pose_unity=d['socket']['apose_world_unity'],
        ready_stance_proof_pose=d['ready']['pose'],
        notes=({'A-pose bind': 'unposed locked hero hand; racket clears hand and body (0 overlapping triangles, min clearance %.2f mm)' % d['apose']['min_clearance_body_mm']}
               if tag == 'male' else
               {'A-pose bind': 'racket clears the hand pieces (0 overlapping triangles) but the arm hangs flush to the thigh with a pronated placeholder hand, so the racket crosses the thigh in the static bind pose; fit is shown in the ready-stance proof pose.'}))
out = dict(
    asset='Racket_Classic',
    units='metres',
    racket_local_frame=dict(origin='centre of the usable grip (palm hold point)', Y='shaft, towards the head', Z='hitting-face normal (palm side)', X='Y x Z, across the face'),
    unity_axis_mapping=dict(blender_to_unity='(x, y, z) -> (-x, z, -y)  (verified in Unity 6000.3.24f1: same conversion as the HeroBase FBXs)',
                            rotation_conversion='R_unity = C R_blender C^T with C = [[-1,0,0],[0,0,1],[0,-1,0]]',
                            fbx_import='Racket_Classic.fbx imports with prefab-root Euler (270,0,0), scale 1, file scale 1 - keep that local rotation when parenting'),
    unity_usage=['socket = new GameObject("Hand_Racket"); socket.transform.SetParent(rightHandBone, false)  // bind-pose world pose below',
                 'socket.transform.position = <position>; socket.transform.rotation = Quaternion.LookRotation(<forward>, <up>)  (bind pose world values; then parent to the hand bone with worldPositionStays = true)',
                 'racket = Instantiate(Racket_Classic prefab); racket.transform.SetParent(socket.transform, false)  // local position 0, keep the imported local rotation (270,0,0)'],
    bodies=bodies,
)
(W / 'export' / 'racket_classic_socket.json').write_text(json.dumps(out, indent=1))
print('socket json written')

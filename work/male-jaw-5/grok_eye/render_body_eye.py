"""Headless full-body + closeup eye renders. Does not save the opened blend."""
import bpy, math, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np

argv = sys.argv[sys.argv.index('--')+1:]
blend_path = Path(argv[0])
out_dir = Path(argv[1])
prefix = argv[2] if len(argv) > 2 else 'body'
out_dir.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=str(blend_path))
scene = bpy.context.scene
body = bpy.data.objects['Body_M']
me = body.data
co = np.array([v.co[:] for v in me.vertices], float)

# Prefer Workbench clay; keep existing Blockout_Grey
scene.render.engine = 'BLENDER_WORKBENCH'
wb = scene.display.shading
try:
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (0.55, 0.55, 0.55)
except Exception:
    pass
# Workbench render settings
try:
    scene.render.use_high_quality_normals = True
except Exception:
    pass
rd = scene.render
rd.film_transparent = True
rd.image_settings.file_format = 'PNG'
rd.image_settings.color_mode = 'RGBA'

# Hide non-body meshes if any
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body_M':
        o.hide_render = True

# Transient camera from locked bald_front if present
src_cam = bpy.data.objects.get('Locked_bald_front') or scene.camera
cam = bpy.data.objects.new('Transient_GrokEye', src_cam.data.copy())
scene.collection.objects.link(cam)
cam.data.type = 'ORTHO'
cam.data.background_images.clear()
scene.camera = cam

def shot(name, angle_deg, height, scale, width=1280, height_px=720, look_at=None):
    a = math.radians(angle_deg)
    target = Vector(look_at) if look_at is not None else Vector((0.0, 0.0, height))
    cam.location = target + Vector((math.sin(a) * 5.0, -math.cos(a) * 5.0, 0.0))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale
    rd.resolution_x = width
    rd.resolution_y = height_px
    path = out_dir / f'{prefix}_{name}.png'
    rd.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    print('WROTE', path)

# Full-body framing (matches Form D / silhouette plates)
body_scale = 1280 * 1.7 / 593  # ~3.676
mid_z = 0.84
for name, ang in [('front', 0), ('side_left', 90), ('threequarter', 45), ('back', 180)]:
    shot(name, ang, mid_z, body_scale, 1280, 720)

# Chin / jaw side profile
shot('chin_side', 90, 1.49, 0.52, 900, 900)

# Feet side
shot('feet_side', 90, 0.12, 0.52, 900, 900)

# Hands: estimate right hand centroid (positive X in A-pose)
hand_mask = (co[:, 2] > 0.75) & (co[:, 2] < 1.15) & (co[:, 0] > 0.25)
if hand_mask.sum() < 50:
    hand_mask = (co[:, 2] > 0.7) & (co[:, 2] < 1.2) & (np.abs(co[:, 0]) > 0.2) & (co[:, 0] > 0)
hand_c = co[hand_mask].mean(axis=0) if hand_mask.any() else np.array([0.45, -0.02, 0.95])
print('HAND_CENTER', hand_c.tolist(), 'n', int(hand_mask.sum()))
shot('hand_front', 0, float(hand_c[2]), 0.42, 900, 900, look_at=(float(hand_c[0]), float(hand_c[1]), float(hand_c[2])))
shot('hand_side', 90, float(hand_c[2]), 0.42, 900, 900, look_at=(float(hand_c[0]), float(hand_c[1]), float(hand_c[2])))

# Geometry notes JSON
def region_stats(mask):
    pts = co[mask]
    if len(pts) == 0:
        return None
    return {
        'n': int(len(pts)),
        'min': pts.min(0).tolist(),
        'max': pts.max(0).tolist(),
        'mean': pts.mean(0).tolist(),
        'width_x': float(pts[:, 0].max() - pts[:, 0].min()),
        'depth_y': float(pts[:, 1].max() - pts[:, 1].min()),
        'height_z': float(pts[:, 2].max() - pts[:, 2].min()),
    }

# torso slices excluding arms (narrow x at shoulder height of torso only is hard;
# use |x| bands relative to body)
shoulder_band = (co[:, 2] > 1.28) & (co[:, 2] < 1.42) & (np.abs(co[:, 0]) < 0.35)
waist_band = (co[:, 2] > 0.92) & (co[:, 2] < 1.02) & (np.abs(co[:, 0]) < 0.22)
arm_side = (co[:, 2] > 0.95) & (co[:, 2] < 1.25) & (co[:, 0] > 0.28)
chin_band = (co[:, 2] > 1.38) & (co[:, 2] < 1.55) & (co[:, 1] < -0.02)
feet_band = co[:, 2] < 0.08
fingers = (co[:, 2] > 0.85) & (co[:, 2] < 1.12) & (co[:, 0] > 0.35)

meta = {
    'blend': str(blend_path),
    'sha256': hashlib.sha256(blend_path.read_bytes()).hexdigest(),
    'verts': int(len(co)),
    'bounds_min': co.min(0).tolist(),
    'bounds_max': co.max(0).tolist(),
    'height_m': float(co[:, 2].max() - co[:, 2].min()),
    'shoulders': region_stats(shoulder_band),
    'waist': region_stats(waist_band),
    'arm_side_right': region_stats(arm_side),
    'chin': region_stats(chin_band),
    'feet': region_stats(feet_band),
    'fingers_right': region_stats(fingers),
    'hand_center': hand_c.tolist(),
}
(out_dir / f'{prefix}_geometry.json').write_text(json.dumps(meta, indent=2))
print('GEOMETRY', json.dumps(meta, indent=2))
print('RENDER_BODY_EYE_DONE', prefix)

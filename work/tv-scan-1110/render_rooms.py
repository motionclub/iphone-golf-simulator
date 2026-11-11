# Scan bench renders (Blender, background): living rooms with a TV, seen from a hand-held phone.
# Per pose two linear EXRs: the room with the TV screen black and glossy (reflections only), and a UV pass of the screen alone
# (R=u, G=v, B=coverage), so any screen content can be composited exactly later (emission adds linearly).
# Usage: Blender -b -P render_rooms.py -- <out_dir> <rooms> <positives_per_room> <negatives_per_room> <seed> <assets_dir>
import bpy, math, random, json, os, sys
from mathutils import Vector, Matrix, Quaternion
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index('--') + 1:]
OUT, ROOMS, POS, NEG, SEED, ASSETS = argv[0], int(argv[1]), int(argv[2]), int(argv[3]), int(argv[4]), argv[5]
os.makedirs(OUT, exist_ok=True)
rng = random.Random(SEED)
HFOV = math.radians(70.0)
W, H = 1280, 960

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = engine; break
    except TypeError:
        pass
try: scene.eevee.taa_render_samples = 24
except Exception: pass
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
scene.render.image_settings.color_mode = 'RGB'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'

def mat_diffuse(name, color, rough=0.85, spec=0.3):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Roughness'].default_value = rough
    try: b.inputs['Specular IOR Level'].default_value = spec
    except KeyError: pass
    return m

def mat_image(name, path, emission=0.0, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    if emission > 0:
        nt.links.new(tex.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = emission
    return m

def box(name, size, loc, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = size
    o.data.materials.append(mat); return o

def plane(name, size, loc, rot, mat):
    bpy.ops.mesh.primitive_plane_add(size=2, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, 1)
    o.data.materials.append(mat); return o

# screen materials: glossy black panel (room pass) and the UV pass
screen_gloss = bpy.data.materials.new('ScreenGloss'); screen_gloss.use_nodes = True
sb = screen_gloss.node_tree.nodes['Principled BSDF']
sb.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1); sb.inputs['Roughness'].default_value = 0.12
screen_uv = bpy.data.materials.new('ScreenUV'); screen_uv.use_nodes = True
nt = screen_uv.node_tree; nt.nodes.clear()
tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); comb = nt.nodes.new('ShaderNodeCombineXYZ')
em = nt.nodes.new('ShaderNodeEmission'); outn = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(tc.outputs['UV'], sep.inputs[0]); nt.links.new(sep.outputs[0], comb.inputs[0]); nt.links.new(sep.outputs[1], comb.inputs[1])
comb.inputs[2].default_value = 1.0
nt.links.new(comb.outputs[0], em.inputs['Color']); em.inputs['Strength'].default_value = 1.0
nt.links.new(em.outputs[0], outn.inputs['Surface'])

world_room = bpy.data.worlds.new('Room'); world_room.use_nodes = True
world_room.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.025, 1)
world_black = bpy.data.worlds.new('Black'); world_black.use_nodes = True
world_black.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)

cam_data = bpy.data.cameras.new('Phone'); cam_data.sensor_fit = 'HORIZONTAL'; cam_data.angle = HFOV
cam_data.clip_start = 0.05; cam_data.clip_end = 50
cam = bpy.data.objects.new('Phone', cam_data); scene.collection.objects.link(cam); scene.camera = cam

WALLS = [(0.78, 0.72, 0.62), (0.9, 0.9, 0.88), (0.45, 0.47, 0.5), (0.12, 0.16, 0.26), (0.28, 0.2, 0.15), (0.55, 0.62, 0.55)]
TVS = [0.95, 1.21, 1.43, 1.66]   # 43, 55, 65, 75 inch widths (16:9)
A = lambda n: os.path.join(ASSETS, n)

def clear_room():
    for o in list(bpy.data.objects):
        if o.name != 'Phone': bpy.data.objects.remove(o, do_unlink=True)

def build_room(rid):
    clear_room()
    wall = mat_diffuse(f'Wall{rid}', rng.choice(WALLS)); floor = mat_diffuse(f'Floor{rid}', rng.choice([(0.35, 0.22, 0.12), (0.55, 0.45, 0.35), (0.2, 0.2, 0.22)]), 0.5)
    ceil = mat_diffuse(f'Ceil{rid}', (0.9, 0.9, 0.9)); black = mat_diffuse(f'Bezel{rid}', (0.01, 0.01, 0.01), 0.3)
    wood = mat_diffuse(f'Wood{rid}', rng.choice([(0.08, 0.05, 0.03), (0.4, 0.3, 0.2), (0.9, 0.9, 0.9)]), 0.5)
    frame = mat_diffuse(f'Frame{rid}', rng.choice([(0.05, 0.05, 0.05), (0.85, 0.85, 0.85), (0.35, 0.22, 0.1)]), 0.4)
    room = {'x': 4.0, 'depth': 7.0, 'h': 2.7}
    plane('Floor', (8, 8), (0, 3.5, 0), (0, 0, 0), floor)
    plane('Ceiling', (8, 8), (0, 3.5, room['h']), (math.pi, 0, 0), ceil)
    plane('Back', (8, room['h']), (0, 0, room['h'] / 2), (math.pi / 2, 0, 0), wall)
    plane('Front', (8, room['h']), (0, 7, room['h'] / 2), (math.pi / 2, 0, 0), wall)
    plane('Left', (8, room['h']), (-4, 3.5, room['h'] / 2), (math.pi / 2, 0, math.pi / 2), wall)
    plane('Right', (8, room['h']), (4, 3.5, room['h'] / 2), (math.pi / 2, 0, math.pi / 2), wall)
    tvw = rng.choice(TVS); tvh = tvw * 9 / 16
    tx = rng.uniform(-0.8, 0.8)
    wall_mount = rng.random() < 0.4
    tz = 1.35 if wall_mount else 0.55 + 0.06 + tvh / 2
    if not wall_mount: box('Cabinet', (max(1.4, tvw + 0.3), 0.45, 0.55), (tx, 0.23, 0.275), wood)
    box('Bezel', (tvw + 0.02, 0.04, tvh + 0.02), (tx, 0.06 if not wall_mount else 0.03, tz), black)
    sy = 0.081 if not wall_mount else 0.051
    screen = plane('Screen', (tvw, tvh), (tx, sy, tz), (math.pi / 2, 0, math.pi), screen_gloss)
    # decoys: a window (outdoor picture, bright by day), framed pictures, a door, shelves
    side = rng.choice([-1, 1]); wx = tx + side * (tvw / 2 + rng.uniform(0.7, 1.4))
    wx = max(-3.3, min(3.3, wx))
    box('WindowFrame', (1.3, 0.06, 1.5), (wx, 0.03, 1.45), frame)
    plane('Window', (1.2, 1.4), (wx, 0.065, 1.45), (math.pi / 2, 0, math.pi), mat_image(f'Out{rid}', A('loading-golf-cliffside.jpg'), emission=3.0, rough=0.2))
    pics = [A('loading-bowling-lanes.jpg'), A('loading-golf-magma.jpg'), A('loading-golf-cliffside.jpg')]
    px = tx - side * (tvw / 2 + rng.uniform(0.5, 1.0)); px = max(-3.4, min(3.4, px))
    pw = rng.uniform(0.6, 1.0)
    box('PicFrame', (pw + 0.06, 0.03, pw * 0.5625 + 0.06), (px, 0.015, 1.55), frame)
    plane('Picture', (pw, pw * 0.5625), (px, 0.035, 1.55), (math.pi / 2, 0, math.pi), mat_image(f'Pic{rid}', rng.choice(pics)))
    # side-wall picture and door
    plane('SidePic', (0.9, 0.6), (-3.98, rng.uniform(1.5, 4.5), 1.5), (math.pi / 2, 0, -math.pi / 2), mat_image(f'Side{rid}', rng.choice(pics)))
    box('Door', (0.05, 0.9, 2.05), (3.97, rng.uniform(1.5, 5.0), 1.025), mat_diffuse(f'Door{rid}', (0.85, 0.83, 0.8), 0.4))
    box('Shelf', (0.9, 0.35, 1.8), (-side * 3.0, 0.2, 0.9), wood)
    # light: a ceiling panel and a window sun; the bench scales the room's light level afterwards
    bpy.ops.object.light_add(type='AREA', location=(0, 3.0, 2.6)); l = bpy.context.active_object; l.data.energy = 400; l.data.size = 1.5
    bpy.ops.object.light_add(type='POINT', location=(-side * 3.0, 4.5, 1.6)); l = bpy.context.active_object; l.data.energy = 120
    return {'tvw': tvw, 'tvh': tvh, 'tx': tx, 'tz': tz, 'sy': sy, 'wall_mount': wall_mount, 'window_x': wx, 'picture_x': px}, screen

def look_rotation(forward):
    f = forward.normalized(); up = Vector((0, 0, 1))
    r = f.cross(up)
    if r.length < 1e-4: r = Vector((1, 0, 0))
    r.normalize(); u = r.cross(f)
    # camera local: x right, y up, -z forward
    return Matrix(((r.x, u.x, -f.x), (r.y, u.y, -f.y), (r.z, u.z, -f.z)))

def aim_camera(pos, target, uv, roll):
    tanw = math.tan(HFOV / 2); tanh_ = tanw * H / W
    t_local = Vector(((uv[0] - 0.5) * 2 * tanw, (0.5 - uv[1]) * 2 * tanh_, -1)).normalized()
    q = t_local.rotation_difference(Vector((0, 0, -1))).to_matrix()
    rz = Matrix.Rotation(roll, 3, 'Z')
    R = look_rotation(target - pos) @ rz @ q
    cam.matrix_world = Matrix.Translation(pos) @ R.to_4x4()

def project(p):
    v = world_to_camera_view(scene, cam, Vector(p))
    return [v.x, 1 - v.y, v.z]

def screen_corners(info):
    hw, hh = info['tvw'] / 2, info['tvh'] / 2
    return [(info['tx'] + sx * hw, info['sy'], info['tz'] + sz * hh) for sx, sz in ((-1, 1), (1, 1), (1, -1), (-1, -1))]

def render(path, uv_pass, screen):
    others = [o for o in bpy.data.objects if o.name not in ('Phone', 'Screen')]
    for o in others: o.hide_render = uv_pass
    screen.data.materials[0] = screen_uv if uv_pass else screen_gloss
    scene.world = world_black if uv_pass else world_room
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)

poses = []
for rid in range(ROOMS):
    info, screen = build_room(rid)
    centre = Vector((info['tx'], info['sy'], info['tz']))
    for k in range(POS + NEG):
        negative = k >= POS
        for attempt in range(200):
            d = rng.uniform(1.5, 4.5); px = rng.uniform(-1.6, 1.6)
            if abs(math.atan2(px - info['tx'], d)) > math.radians(48): continue
            h = rng.uniform(0.9, 1.5)
            pos = Vector((px, d, h))
            portrait = rng.random() < 0.7
            roll = (math.pi / 2 if portrait else 0) + rng.uniform(-0.35, 0.35)
            if not negative:
                uv = (rng.uniform(0.12, 0.88), rng.uniform(0.12, 0.88))
                aim_camera(pos, centre, uv, roll)
                c = project(centre)
                if c[2] <= 0: continue
                break
            # negative: look at the window, the picture or a bare stretch of wall, the TV wholly out of view
            target = rng.choice([Vector((info['window_x'], 0.06, 1.45)), Vector((info['picture_x'], 0.03, 1.55)),
                                 Vector((-3.95, rng.uniform(1.5, 4.5), 1.5)), Vector((3.95, rng.uniform(1.5, 5), 1.1))])
            aim_camera(pos, target, (rng.uniform(0.3, 0.7), rng.uniform(0.3, 0.7)), roll)
            sc = screen_corners(info)
            pts = [project(p) for p in sc] + [project(centre)] + [project(((Vector(a) + Vector(b)) / 2)) for a, b in zip(sc, sc[1:] + sc[:1])]
            if not any(p[2] > 0 and -0.05 <= p[0] <= 1.05 and -0.05 <= p[1] <= 1.05 for p in pts):
                break
        name = f'r{rid:02d}_p{k:02d}'
        corners = [project(p) for p in screen_corners(info)]
        c = project(centre)
        dist = (pos - centre).length
        poses.append({'name': name, 'room': rid, 'negative': negative, 'centre': c[:2], 'corners': [cn[:2] for cn in corners],
                      'distance': dist, 'view_angle': math.degrees(math.atan2(abs(px - info['tx']), d)),
                      'roll': math.degrees(roll), 'portrait': portrait, 'tv_width': info['tvw'], 'wall_mount': info['wall_mount'],
                      'hfov': math.degrees(HFOV)})
        render(os.path.join(OUT, name + '_room.exr'), False, screen)
        if not negative: render(os.path.join(OUT, name + '_uv.exr'), True, screen)
        with open(os.path.join(OUT, 'poses.json'), 'w') as fh: json.dump(poses, fh, indent=1)
print('DONE', len(poses))

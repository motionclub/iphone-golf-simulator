"""Micro1h core: plate calibration, MEASURED landmark table, mesh I/O, plate-aligned renders.
Runs inside Blender's python (bpy + numpy).  Every number here was read off ArtDir/hero/base_lock/male_head_detail.jpg
with the labeled-grid zooms in work/male-micro1h/plates/ (plate pixel coords -> metres via the head calibration).

Conventions (mesh): x = right/left (symmetric), y negative = front of the face, z up, metres.
Head-detail plate calibration (same one the chin lock used): K = 1.3043874 mm/px, top row 76 -> z 1.70466.
  z(row)  = TOP - (row-76)*K
  x(col)  = (col - CX)*K      front panel, CX = face centre column (227.6)
  y(col)  = 0.065 - (712-col)*K   profile panels (face looks to image-left); occiput col 711 <-> y 0.0645
"""
import math, json, sys
from pathlib import Path
import numpy as np

ROOT = Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
W = ROOT / 'work/male-micro1h'
K = 0.0013043874429196725
TOP = 1.7046599388122559
CX = 227.6
PLATE = ROOT / 'ArtDir/hero/base_lock/male_head_detail.jpg'


def zrow(r): return TOP - (np.asarray(r, float) - 76.0) * K
def xcol(c): return (np.asarray(c, float) - CX) * K
def ycol(c): return 0.065 - (712.0 - np.asarray(c, float)) * K
def rowz(z): return 76.0 + (TOP - np.asarray(z, float)) / K


# --------------------------------------------------------------------------------------------------------------
# MEASURED landmarks (plate px -> metres).  front panel: (col,row);  profile: (col,row)
# --------------------------------------------------------------------------------------------------------------
LM = dict(
    # eyes (front plate): iris centre, corners, lid margin heights, crease
    eye_x=float(xcol(255.7)),                    # +0.03665  iris centre (mirror -)
    eye_z=float(zrow(167.8)),                    # 1.5849
    eye_out_x=float(xcol(270.6)), eye_out_z=float(zrow(168.7)),
    eye_in_x=float(xcol(243.0)), eye_in_z=float(zrow(169.6)),
    eye_top_z=float(zrow(162.5)), eye_bot_z=float(zrow(173.8)),
    eye_crease_z=float(zrow(158.5)),
    iris_r=0.0075, pupil_r=0.0038,
    cornea_y=float(ycol(566.0)),                 # -0.1254   iris front surface (profile)
    # brows
    brow_in_x=0.0160, brow_tail_x=0.0678, brow_z=float(zrow(148.3)), brow_th=0.0115, brow_tail_z=float(zrow(158.0)),
    # nose
    nose_tip_z=float(zrow(198.0)), nose_tip_y=float(ycol(530.3)),      # 1.5455 / -0.1721
    nose_bulb_z=float(zrow(195.5)), nostril_z=float(zrow(204.3)), nose_base_z=float(zrow(210.0)), nose_base_y=float(ycol(544.0)),
    ala_x=0.0242, nostril_x=0.0135, nasion_z=float(zrow(161.0)), nasion_y=float(ycol(550.0)),
    # mouth
    mouth_corner_x=0.0363, mouth_corner_z=float(zrow(224.0)), seam_z=float(zrow(227.8)),
    lip_top_z=float(zrow(222.8)), lip_bot_z=float(zrow(235.5)), mentolabial_z=float(zrow(239.0)),
    lip_up_y=float(ycol(544.0)), lip_lo_y=float(ycol(545.3)),
    # chin
    chin_front_z=float(zrow(252.0)), chin_bot_z=float(zrow(267.0)), chin_y=float(ycol(548.0)),
    # ears (profile)
    ear_top_z=float(zrow(157.4)), ear_bot_z=float(zrow(212.2)), ear_front_y=float(ycol(637.0)), ear_rear_y=float(ycol(669.7)),
    ear_out_x=0.1026, head_side_x_at_ear=0.081,
    # cranium
    head_w_temple=0.1696, head_w_ear=0.1618,
)

# --------------------------------------------------------------------------------------------------------------
# plate silhouettes -> target extents per z (rows 76..300), from plates/sil.json (see plate_sil.py)
# --------------------------------------------------------------------------------------------------------------
_SIL = None


def sil():
    global _SIL
    if _SIL is None:
        _SIL = json.load(open(W / 'plates/sil.json'))
    return _SIL


def plate_extents():
    """returns dict of arrays over rows 80..270: rows, z, half-width front (outer, incl. ears), front-y, back-y (profile)"""
    s = sil()
    rows = np.arange(80, 271)
    hw = np.full(len(rows), np.nan); yf = np.full(len(rows), np.nan); yb = np.full(len(rows), np.nan)
    for i, r in enumerate(rows):
        f = s['front'].get(str(r)); l = s['left'].get(str(r))
        if f: hw[i] = 0.5 * (f[-1][1] - f[0][0] + 1) * K
        if l:
            yf[i] = ycol(l[0][0]); yb[i] = ycol(l[-1][1] + 1)
    return dict(rows=rows, z=zrow(rows), hw=hw, yf=yf, yb=yb)


# --------------------------------------------------------------------------------------------------------------
# mesh I/O (inside Blender)
# --------------------------------------------------------------------------------------------------------------
def get_body(blend=None):
    import bpy
    if blend:
        bpy.ops.wm.open_mainfile(filepath=str(blend))
    return bpy.data.objects['Body_M']


def mesh_arrays(me):
    n = len(me.vertices)
    V = np.empty(n * 3, np.float64); me.vertices.foreach_get('co', V); V = V.reshape(-1, 3)
    nl = len(me.loops)
    cv = np.empty(nl, np.int64); me.loops.foreach_get('vertex_index', cv)
    ls = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('loop_start', ls)
    lt = np.empty(len(me.polygons), np.int64); me.polygons.foreach_get('loop_total', lt)
    F = [cv[a:a + b] for a, b in zip(ls, lt)]
    return V, F


def set_verts(me, V):
    me.vertices.foreach_set('co', np.asarray(V, np.float32).ravel()); me.update()


def make_mesh_object(name, V, F, mats=None, link=True):
    """new mesh object from numpy verts + list-of-index-arrays faces"""
    import bpy
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V)); me.vertices.foreach_set('co', np.asarray(V, np.float32).ravel())
    lens = np.array([len(f) for f in F], np.int64)
    me.loops.add(int(lens.sum())); me.polygons.add(len(F))
    me.loops.foreach_set('vertex_index', np.concatenate([np.asarray(f, np.int64) for f in F]))
    me.polygons.foreach_set('loop_start', np.concatenate([[0], np.cumsum(lens)[:-1]]))
    me.polygons.foreach_set('loop_total', lens)
    me.update(calc_edges=True)
    me.shade_smooth() if hasattr(me, 'shade_smooth') else None
    o = bpy.data.objects.new(name, me)
    if link:
        bpy.context.scene.collection.objects.link(o)
    return o


def tri_count(F):
    return int(sum(len(f) - 2 for f in F))


# --------------------------------------------------------------------------------------------------------------
# plate-aligned rendering (orthographic).  Verified conventions:
#   az=0   : camera at -Y looking +Y, image right = +X          (front)
#   az=90  : camera at +X looking -X, image right = +Y          (profile with the face to the image LEFT)
#   az=+40 : camera between front and +X
# --------------------------------------------------------------------------------------------------------------
_cam = None


def setup_render(res=(1200, 1200), skin=(0.80, 0.56, 0.42), bg=(0.18, 0.18, 0.19), cavity=True, light='STUDIO'):
    import bpy
    s = bpy.context.scene
    s.render.engine = 'BLENDER_WORKBENCH'
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGB'
    sh = s.display.shading
    sh.light = light; sh.color_type = 'MATERIAL' if False else 'SINGLE'; sh.single_color = skin
    sh.show_cavity = cavity
    try:
        sh.cavity_type = 'BOTH'; sh.cavity_ridge_factor = 0.55; sh.cavity_valley_factor = 0.9
        sh.show_shadows = False
    except Exception:
        pass
    sh.show_specular_highlight = True
    s.view_settings.view_transform = 'Standard'
    s.world = s.world or bpy.data.worlds.new('w')
    s.world.color = bg


def camera():
    global _cam
    import bpy
    if _cam is None or _cam.name not in bpy.data.objects:
        d = bpy.data.cameras.new('h1cam'); d.type = 'ORTHO'; d.clip_start = 0.01; d.clip_end = 50
        _cam = bpy.data.objects.new('h1cam', d); bpy.context.scene.collection.objects.link(_cam)
    return _cam


def shot(path, target, az=0.0, el=0.0, scale=0.3, res=(1000, 1000), dist=3.0):
    import bpy
    from mathutils import Vector
    s = bpy.context.scene; cam = camera(); s.camera = cam
    a = math.radians(az); e = math.radians(el); t = Vector(target)
    cam.location = t + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = scale
    s.render.resolution_x, s.render.resolution_y = res
    s.render.filepath = str(Path(path).resolve())
    bpy.ops.render.render(write_still=True)


# head-detail panel boxes (full-plate coords) and the camera that reproduces each panel at 2 px per plate px
PANELS = {
    '01_front': dict(box=(5, 62, 433, 352), az=0, el=0),
    '02_left': dict(box=(433, 62, 834, 352), az=90, el=0),
    '03_right': dict(box=(834, 62, 1271, 352), az=90, el=0),     # plate 03 also faces image-left (same side view)
}


def panel_cam(name, up=2):
    p = PANELS[name]; x0, y0, x1, y1 = p['box']
    w, h = x1 - x0, y1 - y0
    cxp, cyp = (x0 + x1) / 2, (y0 + y1) / 2
    zc = float(zrow(cyp))
    if name == '01_front':
        target = (float(xcol(cxp)), -0.04, zc)
    elif name == '02_left':
        target = (0.0, float(ycol(cxp)), zc)
    else:   # right panel: also faces image-left in the plate, same anchor logic mirrored (occiput col 1122 <-> y 0.0645)
        target = (0.0, float(0.065 - (1123.0 - cxp) * K), zc)
    return dict(target=target, az=p['az'], el=p['el'], scale=w * K, res=(w * up, h * up))


def head_shot(path, name, up=2):
    c = panel_cam(name, up)
    shot(path, c['target'], c['az'], c['el'], c['scale'], c['res'])


# --------------------------------------------------------------------------------------------------------------
# Eevee studio rig (lights parented to the camera so every view is lit like the plate: key upper-left, soft fill right)
# --------------------------------------------------------------------------------------------------------------
SKIN_SRGB = (0.74, 0.555, 0.435)


def _lin(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def skin_material(name='skin_preview', srgb=SKIN_SRGB, rough=0.55, sss=0.12):
    import bpy
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (_lin(srgb[0]), _lin(srgb[1]), _lin(srgb[2]), 1)
    b.inputs['Roughness'].default_value = rough
    for k, v in (('Subsurface Weight', sss), ('Subsurface Radius', (1.0, 0.45, 0.25)), ('Subsurface Scale', 0.004), ('Specular IOR Level', 0.35)):
        try:
            b.inputs[k].default_value = v
        except Exception:
            pass
    m.diffuse_color = (_lin(srgb[0]), _lin(srgb[1]), _lin(srgb[2]), 1)
    return m


def flat_material(name, srgb, rough=0.5, spec=0.3):
    return skin_material(name, srgb, rough, 0.0)


def setup_eevee(res=(900, 900), key=3.0, fill=0.9, ambient=0.55, bg=(0.17, 0.17, 0.19), transparent=False):
    import bpy
    from mathutils import Vector
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.film_transparent = transparent
    s.render.image_settings.file_format = 'PNG'; s.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    s.view_settings.view_transform = 'Standard'
    try:
        s.eevee.use_shadows = True; s.eevee.taa_render_samples = 24
        s.eevee.use_gtao = True
    except Exception:
        pass
    w = bpy.data.worlds.new('w_h1'); s.world = w; w.use_nodes = True
    n = w.node_tree.nodes['Background']; n.inputs['Color'].default_value = (bg[0], bg[1], bg[2], 1); n.inputs['Strength'].default_value = ambient
    cam = camera()
    for nm in ('h1_key', 'h1_fill', 'h1_rim'):
        if nm in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)

    def sun(nm, direction, energy, color, angle=20):
        d = bpy.data.lights.new(nm, 'SUN'); d.energy = energy; d.color = color; d.angle = math.radians(angle)
        ob = bpy.data.objects.new(nm, d); bpy.context.scene.collection.objects.link(ob)
        ob.parent = cam
        q = Vector(direction).normalized().to_track_quat('-Z', 'Y')
        ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = q
        return ob
    # camera-local frame: +x right, +y up, -z forward (into the scene)
    sun('h1_key', (0.55, -0.6, -0.58), key, (1.0, 0.96, 0.9))
    sun('h1_fill', (-0.7, -0.15, -0.7), fill, (0.85, 0.9, 1.0), 40)
    sun('h1_rim', (0.1, -0.3, 0.95), 0.7, (1.0, 1.0, 1.0), 30)

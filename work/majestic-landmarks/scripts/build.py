"""Build, render, export and gate-measure the Majestic landmark kit. Headless, one Blender process:

  heavy.sh blender /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python work/majestic-landmarks/scripts/build.py -- [AssetName ...] [--norender]

Per asset: LOD0 + LOD1 (rebuilt at Q1) + LOD2 impostor cross-card (rendered atlas), separate animated/FX parts,
FBX at fbx/<Name>.fbx, renders at renders/<Name>/, metrics at proof/metrics/<Name>.json (read by gates.py).
"""
import sys, os, json, math, importlib, time
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import kit
importlib.reload(kit)
from registry import REG
import assets_landmarks, assets_setpieces, assets_shore  # noqa: F401  (register recipes)

FBX_FLAGS = dict(use_selection=True, object_types={'MESH', 'EMPTY'}, global_scale=1.0, apply_unit_scale=True,
                 apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', bake_space_transform=True,
                 use_mesh_modifiers=True, mesh_smooth_type='OFF', use_tspace=False, colors_type='SRGB',
                 add_leaf_bones=False, bake_anim=False, path_mode='RELATIVE', embed_textures=False)

LIGHT = {  # course light for preview renders: sun colour/strength, world colour/strength, background gradient (top, bottom)
    'A': dict(sun=(1.0, .97, .9), sun_e=3.6, world=(.62, .74, .95), world_e=.85, bg=('#8ec5f5', '#e8f4ff')),
    'B': dict(sun=(1.0, .82, .58), sun_e=3.8, world=(.80, .68, .62), world_e=.8, bg=('#f7c27a', '#fde9c8')),
    'C': dict(sun=(1.0, .58, .42), sun_e=1.8, world=(.40, .33, .62), world_e=1.0, bg=('#4a3a8a', '#f08a4a')),
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    for eng in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = eng; break
        except TypeError:
            continue
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 1.0
    return sc


def build_lod(spec, q):
    """One quality pass. FX listed in spec['fx_shared'] are built once (LOD0 pass) with no LOD suffix, so they show
    at every distance (plumes, beams)."""
    out = spec['fn'](q)
    objs = {}
    mat = kit.body_material(spec['name'] + '_Mat')
    sfx = '_LOD0' if q >= 1 else '_LOD1'
    shared = set(spec.get('fx_shared', []))
    if out.get('body') is not None:
        objs['body'] = out['body'].finish(spec['name'] + sfx, mat)
    pv = out.get('pivots', {})
    for k, a in out.get('parts', {}).items():
        objs[k] = a.finish(f"{spec['name']}_{k}{sfx}", mat, origin=pv.get(k))
    for k, c in out.get('fx', {}).items():
        if k in shared and q < 1:
            continue
        nm = f"{spec['name']}_{k}" + ('' if k in shared else sfx)
        objs['fx_' + k] = c.finish(nm, kit.fx_material(spec['name'] + '_FX'), origin=pv.get(k))
    return objs, pv


def bbox(objs):
    pts = []
    for o in objs:
        pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    a = np.array([tuple(p) for p in pts])
    return a.min(0), a.max(0)


# ---------------------------------------------------------------- rendering
def setup_render(sc, course, res=(640, 640)):
    L = LIGHT[course]
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    try:
        sc.view_settings.view_transform = 'Standard'
    except TypeError:
        pass
    try:
        sc.eevee.taa_render_samples = 24
    except AttributeError:
        pass
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (*L['world'], 1); bg.inputs[1].default_value = L['world_e']
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = L['sun_e']; sun.color = L['sun']; sun.angle = math.radians(4)
    so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
    cam = bpy.data.cameras.new('cam'); co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
    return so, co


def aim(ob, eye, target):
    d = Vector(target) - Vector(eye)
    ob.location = eye
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def view_dir(az, el):
    az, el = math.radians(az), math.radians(el)
    return Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))


def render_view(sc, so, co, objs, az, el, path, lens=50):
    lo, hi = bbox(objs)
    c = Vector(((lo + hi) / 2).tolist())
    R = float(np.linalg.norm(hi - lo)) / 2
    cam = co.data; cam.type = 'PERSP'; cam.lens = lens; cam.sensor_width = 36; cam.clip_end = max(1000, R * 20); cam.clip_start = max(.01, R / 500)
    fov = 2 * math.atan(18 / lens)
    d = R / math.sin(fov / 2) * 1.02
    aim(co, c + view_dir(az, el) * d, c)
    aim(so, c + view_dir(az - 45, 50) * 10, c)
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def set_visible(all_objs, show):
    for o in all_objs:
        o.hide_render = o not in show


def render_impostor(sc, so, co, objs, out_png, course):
    """Ortho front (-Y) + side (+X) renders packed side by side -> atlas; returns per-view (w, h, uv rect)."""
    lo, hi = bbox(objs)
    c = (lo + hi) / 2
    views = []
    tmp = []
    for k, (axis, wdim) in enumerate((('front', 0), ('side', 1))):
        w = float(hi[wdim] - lo[wdim]) * 1.03; h = float(hi[2] - lo[2]) * 1.03
        big = max(w, h)
        rx = max(32, int(round(512 * w / big))); ry = max(32, int(round(512 * h / big)))
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
        cam = co.data; cam.type = 'ORTHO'; cam.ortho_scale = big; cam.clip_end = big * 10 + 100
        if axis == 'front':
            aim(co, (c[0], lo[1] - big * 2 - 5, c[2]), (c[0], c[1], c[2]))
        else:
            aim(co, (hi[0] + big * 2 + 5, c[1], c[2]), (c[0], c[1], c[2]))
        aim(so, Vector(co.location) + Vector((-big, 0, big)) * 0 + view_dir(-45 if axis == 'front' else 45, 50) * 10, c)
        p = out_png.parent / f'_imp_{axis}.png'
        sc.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        tmp.append((p, rx, ry, w, h))
    W = tmp[0][1] + tmp[1][1]; H = max(tmp[0][2], tmp[1][2])
    atlas = np.zeros((H, W, 4), np.float32)
    x = 0
    for p, rx, ry, w, h in tmp:
        im = bpy.data.images.load(str(p))
        px = np.array(im.pixels[:], np.float32).reshape(ry, rx, 4)
        atlas[0:ry, x:x + rx] = px
        views.append(dict(w=w, h=h, uv=(x / W, 0.0, (x + rx) / W, ry / H)))
        x += rx
        bpy.data.images.remove(im)
        os.remove(p)
    img = bpy.data.images.new(out_png.stem, W, H, alpha=True)
    img.pixels = atlas.ravel()
    img.filepath_raw = str(out_png); img.file_format = 'PNG'; img.save()
    return views, (lo, hi), img


def impostor_object(name, views, box, img):
    lo, hi = box
    c = (lo + hi) / 2
    me = bpy.data.meshes.new(name)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UV0')
    for k, v in enumerate(views):
        w, h = v['w'], v['h']
        u0, v0, u1, v1 = v['uv']
        z0 = c[2] - h / 2; z1 = c[2] + h / 2
        if k == 0:   # front card in XZ through the centre, faces -Y
            q = [(c[0] - w / 2, c[1], z0), (c[0] + w / 2, c[1], z0), (c[0] + w / 2, c[1], z1), (c[0] - w / 2, c[1], z1)]
        else:        # side card in YZ, faces +X; image left = -Y... camera on +X looking -X: screen right = +Y
            q = [(c[0], c[1] - w / 2, z0), (c[0], c[1] + w / 2, z0), (c[0], c[1] + w / 2, z1), (c[0], c[1] - w / 2, z1)]
        vs = [bm.verts.new(p) for p in q]
        f = bm.faces.new(vs)
        for l, uv in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            l[uvl].uv = uv
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    me.uv_layers.new(name='UV1'); me.uv_layers.new(name='UV2')
    m = bpy.data.materials.new(name.replace('_LOD2', '') + '_Impostor'); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img
    nt.links.new(tx.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(tx.outputs['Alpha'], bsdf.inputs['Alpha'])
    m.use_backface_culling = False
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------- checks
def tile_check(ob, tile):
    """Tileable pieces: the vertex sets on the two cut ends must coincide (straight: (y, z) at x = +-L/2; arc: (rho, z) at
    phi = +-span/2 about the ring centre). Returns counts + worst mismatch in mm."""
    vs = [ob.matrix_world @ v.co for v in ob.data.vertices]
    if tile['kind'] == 'x':
        h = tile['L'] / 2
        A = [(v.y, v.z) for v in vs if abs(v.x + h) < 1e-3]; B = [(v.y, v.z) for v in vs if abs(v.x - h) < 1e-3]
    else:
        cx, cy, s, half = tile['c'][0], tile['c'][1], tile['s'], math.radians(tile['span']) / 2
        pol = [(math.atan2(v.x - cx, s * (v.y - cy)), math.hypot(v.x - cx, v.y - cy), v.z) for v in vs]
        A = [(r, z) for p, r, z in pol if abs(p + half) < 1e-4]; B = [(r, z) for p, r, z in pol if abs(p - half) < 1e-4]
    if not A or len(A) != len(B):
        return dict(ends=(len(A), len(B)), max_err_mm=None)
    from mathutils.kdtree import KDTree
    kd = KDTree(len(B))
    for i, (u, w) in enumerate(B):
        kd.insert((u, w, 0), i)
    kd.balance()
    err = max(kd.find((u, w, 0))[2] for u, w in A)
    return dict(ends=(len(A), len(B)), max_err_mm=round(err * 1000, 3))



def mesh_checks(ob, closed):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    nm = sum(1 for e in bm.edges if len(e.link_faces) != 2) if closed else sum(1 for e in bm.edges if len(e.link_faces) > 2)
    wire = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    loose = sum(1 for v in bm.verts if not v.link_edges)
    degen = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
    flipped = 0
    if closed:
        before = [f.normal.copy() for f in bm.faces]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        flipped = sum(1 for f, n in zip(bm.faces, before) if f.normal.dot(n) < 0)
    bm.free()
    return dict(non_manifold=nm, wire=wire, loose=loose, degenerate=degen, flipped=flipped)


def alpha_bbox(png):
    im = bpy.data.images.load(str(png))
    w, h = im.size
    a = np.array(im.pixels[:], np.float32).reshape(h, w, 4)[..., 3]
    bpy.data.images.remove(im)
    ys, xs = np.nonzero(a > 0.5)
    if len(xs) == 0:
        return None
    return dict(w=int(xs.max() - xs.min() + 1), h=int(ys.max() - ys.min() + 1), aspect=float((ys.max() - ys.min() + 1) / (xs.max() - xs.min() + 1)))


def run(spec, do_render=True):
    name = spec['name']
    t0 = time.time()
    sc = reset()
    lod0, pivots = build_lod(spec, 1.0)
    lod1, _ = build_lod(spec, kit.Q1)
    rdir = ROOT / 'renders' / name; rdir.mkdir(parents=True, exist_ok=True)
    so, co = setup_render(sc, spec['course'])
    all_objs = list(lod0.values()) + list(lod1.values())
    open_names = {o.name for d in (lod0, lod1) for k, o in d.items() if k.startswith('fx_') or k in spec.get('open_parts', [])} | {name + '_LOD2'}
    # LOD2 impostor from LOD0
    set_visible(all_objs, lod0.values())
    fbxdir = ROOT / 'fbx'; fbxdir.mkdir(exist_ok=True)
    dyn = {'fx_' + k for k in spec.get('dynamic', [])}
    frame0 = [o for k, o in lod0.items() if not k.startswith('fx_')] or list(lod0.values())   # framing: solid parts
    imp_src = [o for k, o in lod0.items() if k not in dyn]                    # impostor: everything but moving FX
    set_visible(all_objs, imp_src)
    imp = None
    if not spec.get('no_impostor'):
        views, box, img = render_impostor(sc, so, co, imp_src, fbxdir / f'{name}_Impostor.png', spec['course'])
        imp = impostor_object(name + '_LOD2', views, box, img)
    sc.render.resolution_x = sc.render.resolution_y = 640
    if do_render:
        set_visible(all_objs + ([imp] if imp else []), lod0.values())
        for az in (30, 120, 210, 300):
            render_view(sc, so, co, frame0, az, 18, rdir / f'turn_{az:03d}.png')
        az, el = spec.get('match', (20, 12))
        set_visible(all_objs + ([imp] if imp else []), imp_src)
        render_view(sc, so, co, frame0, az, el, rdir / 'match.png', lens=spec.get('match_lens', 50))
        set_visible(all_objs + ([imp] if imp else []), lod1.values())
        render_view(sc, so, co, frame0, 30, 18, rdir / 'lod1.png')
        if imp:
            set_visible(all_objs + [imp], [imp])
            render_view(sc, so, co, frame0, 30, 18, rdir / 'lod2.png')
    # ---- parent + export
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    pv = []
    for nm_, loc in pivots.items():   # named pivots for animated parts already sit at their pivot (object origin)
        pv.append(nm_)
    for o in all_objs + ([imp] if imp else []):
        o.parent = root
    for o in sc.objects:
        o.select_set(o is root or o.parent is root)
    bpy.context.view_layer.objects.active = root
    fbx = fbxdir / f'{name}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx), **FBX_FLAGS)
    import shutil
    shutil.rmtree(fbxdir / f'{name}.fbm', ignore_errors=True)   # importer side-folder; the FBX points at fbx/<Name>_Impostor.png
    src = {o.name: dict(tris=kit.tris(o), mats=[m.name for m in o.data.materials],
                        loc=list(o.matrix_world.translation)) for o in all_objs + ([imp] if imp else [])}
    lo, hi = bbox(frame0)
    tiles = {}
    if spec.get('tile'):
        for d in (lod0, lod1):
            if 'body' in d:
                tiles[d['body'].name] = tile_check(d['body'], spec['tile'])
    # ---- re-import and measure what Unity will get
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx), axis_forward='-Z', axis_up='Y', bake_space_transform=True)
    shutil.rmtree(fbxdir / f'{name}.fbm', ignore_errors=True)
    imp_objs = {o.name: o for o in bpy.context.scene.objects}
    meshes = {n: o for n, o in imp_objs.items() if o.type == 'MESH'}
    re = {}
    for n, o in meshes.items():
        closed = n not in open_names
        is_fx = False
        mw = o.matrix_world
        re[n] = dict(tris=kit.tris(o), mats=[m.name for m in o.data.materials],
                     scale=list(o.matrix_world.to_scale()), rot_identity=bool(np.allclose(np.array(mw.to_3x3()), np.eye(3) * np.array(mw.to_scale()), atol=1e-4)),
                     loc=list(mw.translation), color_attrs=[a.name for a in o.data.color_attributes], uv=[u.name for u in o.data.uv_layers],
                     check=mesh_checks(o, closed and not is_fx), closed=closed and not is_fx)
    solid = [o for n, o in meshes.items() if n.endswith('_LOD0') and n not in open_names] or [o for n, o in meshes.items() if n.endswith('_LOD0')]
    rlo, rhi = bbox(solid)
    root_o = imp_objs.get(name)
    res = dict(name=name, course=spec['course'], holes=spec['holes'], where=spec['where'], kind=spec['kind'],
               budget=spec['budget'], dims_expect=spec['dims'], pivot=spec.get('pivot', 'base'), minz=spec.get('minz'),
               features=spec.get('features', []), target=spec.get('target'), target_aspect=spec.get('target_aspect'),
               match=spec.get('match'), notes=spec.get('notes', ''), animated=spec.get('animated', []),
               src=src, reimport=re, tile=tiles, tile_spec=spec.get('tile'), bbox_src=[lo.tolist(), hi.tolist()], bbox_fbx=[rlo.tolist(), rhi.tolist()],
               root=dict(found=root_o is not None, loc=list(root_o.matrix_world.translation) if root_o else None,
                         scale=list(root_o.matrix_world.to_scale()) if root_o else None),
               fbx=str(fbx.relative_to(ROOT)), fbx_bytes=fbx.stat().st_size, impostor_png=(f'fbx/{name}_Impostor.png' if imp else None), no_impostor=bool(spec.get('no_impostor')), no_impostor_why=spec.get('no_impostor_why', ''), fx_shared=spec.get('fx_shared', []),
               match_alpha=alpha_bbox(rdir / 'match.png') if (rdir / 'match.png').exists() else None,
               seconds=round(time.time() - t0, 1))
    md = ROOT / 'proof' / 'metrics'; md.mkdir(parents=True, exist_ok=True)
    (md / f'{name}.json').write_text(json.dumps(res, indent=1))
    print(f'[kit] {name}: LOD0 {sum(v["tris"] for k, v in re.items() if k.endswith("_LOD0"))} tris, '
          f'LOD1 {sum(v["tris"] for k, v in re.items() if k.endswith("_LOD1"))}, {res["seconds"]} s', flush=True)


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    do_render = '--norender' not in argv
    names = [a for a in argv if not a.startswith('--')] or list(REG)
    fails = []
    for n in names:
        try:
            run(REG[n], do_render)
        except Exception as e:
            import traceback; traceback.print_exc(); fails.append(n)
    print('[kit] done; failed:', fails, flush=True)

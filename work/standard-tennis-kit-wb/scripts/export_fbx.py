"""Export FBXs (same flags as the HeroBase body FBX: scale 1, -Z forward / Y up) and verify by re-import.
blender -b --factory-startup --python export_fbx.py"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import bpy
from mathutils.kdtree import KDTree
from kitlib import *

FLAGS = dict(use_selection=True, object_types={'MESH'}, global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
             axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF', add_leaf_bones=False, bake_anim=False, path_mode='COPY')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def specs(gender):
    G = 'Male' if gender == 'male' else 'Female'
    out = [(f'StdKit_{G}_White.fbx', ['Kit_White']), (f'StdKit_{G}_Black.fbx', ['Kit_Black'])]
    if gender == 'female':
        out += [('StdKit_Female_White_ArmsCandFit.fbx', ['Kit_White_alt']), ('StdKit_Female_Black_ArmsCandFit.fbx', ['Kit_Black_alt'])]
    return out


def main():
    report = {}
    for gender in ('male', 'female'):
        blend = f'{WORK}/export/StandardKit_{"Male" if gender == "male" else "Female"}.blend'
        for fbx, cols in specs(gender):
            bpy.ops.wm.open_mainfile(filepath=blend)
            objs = []
            for c in cols:
                key = c.replace('_alt', '_FitArmsCand')
                coll = bpy.data.collections[key]
                objs += list(coll.objects)
            if cols[0].endswith('_alt'):
                base = cols[0].replace('_alt', '')
                objs = [o for o in bpy.data.collections[base].objects if o.get('kit_category') in ('Top', 'Bottom')] + objs
            keepset = set(o.name for o in objs)
            for o in list(bpy.data.objects):
                if o.name not in keepset:
                    bpy.data.objects.remove(o, do_unlink=True)
            objs = list(bpy.data.objects)
            for o in objs:
                o.name = o['base_name']                       # clean names in the FBX (no colorway suffix)
                o.data.name = o['base_name']
            for o in bpy.data.objects:
                o.select_set(False)
            for o in objs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objs[0]
            path = f'{WORK}/export/{fbx}'
            def loop_data(o):
                me = o.data
                cn = np.array([c.vector[:] for c in me.corner_normals])
                pos = np.array([(o.matrix_world @ me.vertices[l.vertex_index].co)[:] for l in me.loops])
                return cn, pos
            src = {}
            for o in objs:
                cn, pos = loop_data(o)
                src[o.name] = (np.array([(o.matrix_world @ v.co)[:] for v in o.data.vertices]), tris(o), [m.name if m else None for m in o.data.materials], cn, pos, o.data.has_custom_normals)
            path = f'{WORK}/export/{fbx}'
            bpy.ops.export_scene.fbx(filepath=path, **FLAGS)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            bpy.ops.import_scene.fbx(filepath=path)
            imp = {o.name.split('.')[0]: o for o in bpy.context.scene.objects if o.type == 'MESH'}
            r = dict(fbx_sha256=sha(path), size_mb=round(os.path.getsize(path) / 1e6, 2), objects={}, ok=True)
            tot = 0
            for name, (V, nt, mats, CNsrc, POSsrc, cn_src) in src.items():
                o = imp.get(name)
                if o is None:
                    r['objects'][name] = 'MISSING'
                    r['ok'] = False
                    continue
                M = o.matrix_world
                co = np.array([(M @ v.co)[:] for v in o.data.vertices])
                kd = KDTree(len(co))
                for i, c in enumerate(co):
                    kd.insert(c, i)
                kd.balance()
                err = max(kd.find(tuple(c))[2] for c in V) * 1000.0
                CNimp, POSimp = loop_data(o)
                if len(CNimp) == len(CNsrc):
                    dpos = float(np.linalg.norm(POSsrc - POSimp, axis=1).max()) * 1000.0
                    ang = np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i', CNsrc, CNimp), -1, 1)))
                else:
                    dpos, ang = 1e9, np.full(1, 180.0)
                bmin_src, bmax_src = V.min(0), V.max(0)
                bmin, bmax = co.min(0), co.max(0)
                bb_err = float(max(np.abs(bmin - bmin_src).max(), np.abs(bmax - bmax_src).max()) * 1000.0)
                nt2 = tris(o)
                mats2 = [m.name if m else None for m in o.data.materials]
                r['objects'][name] = dict(tris_src=nt, tris_fbx=nt2, max_vertex_err_mm=round(err, 4), bbox_err_mm=round(bb_err, 4), materials=mats2,
                                          has_uv=len(o.data.uv_layers) > 0, size_m=(bmax - bmin).round(4).tolist(), custom_normals_src=bool(cn_src),
                                          custom_normals_fbx=bool(o.data.has_custom_normals), normal_dev_mean_deg=round(float(ang.mean()), 3),
                                          normal_dev_p99_deg=round(float(np.percentile(ang, 99)), 3), normal_dev_max_deg=round(float(ang.max()), 3), loop_pos_err_mm=round(dpos, 5), loops=int(len(CNimp)))
                tot += nt2
                if nt != nt2 or err > 0.05 or bb_err > 0.05 or len(o.data.uv_layers) == 0 or float(ang.max()) > 1.0 or dpos > 0.05:
                    r['ok'] = False
            r['total_tris'] = tot
            report[fbx] = r
            print(f"{fbx}: {r['size_mb']} MB, {len(src)} objects, tris {tot}, ok={r['ok']}, max err {max(v['max_vertex_err_mm'] for v in r['objects'].values() if isinstance(v, dict)):.4f} mm")
    json.dump(report, open(f'{WORK}/export/fbx_verify.json', 'w'), indent=1)


main()

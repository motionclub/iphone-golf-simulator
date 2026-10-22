"""Read-only inspection of the two locked hero blends (library load, never saves).
blender -b --factory-startup --python inspect_bodies.py -- <out.json>"""
import sys, json
import bpy
import numpy as np

out = sys.argv[sys.argv.index('--') + 1]
HERO = '/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/ArtDir/hero/base_lock/blender/'
res = {}
for tag, fn in (('male', 'HeroBase_Male_Silhouette.blend'), ('female', 'HeroBase_Female.blend')):
    with bpy.data.libraries.load(HERO + fn, link=False) as (src, dst):
        info = dict(objects=list(src.objects), meshes=list(src.meshes), materials=list(src.materials),
                    collections=list(src.collections), images=list(src.images), armatures=list(src.armatures))
        dst.objects = list(src.objects)
    objs = {}
    for o in dst.objects:
        if o is None:
            continue
        d = dict(type=o.type, parent=o.parent.name if o.parent else None,
                 loc=[round(x, 5) for x in o.location], rot=[round(x, 5) for x in o.rotation_euler],
                 scale=[round(x, 5) for x in o.scale], modifiers=[m.type for m in o.modifiers])
        if o.type == 'MESH':
            me = o.data
            co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
            d.update(verts=len(me.vertices), polys=len(me.polygons), tris=int(sum(len(p.vertices) - 2 for p in me.polygons)),
                     bbox_min=[round(float(x), 4) for x in co.min(0)], bbox_max=[round(float(x), 4) for x in co.max(0)],
                     mats=[m.name if m else None for m in me.materials], vgroups=[g.name for g in o.vertex_groups])
        objs[o.name] = d
    res[tag] = dict(info=info, objects=objs)
open(out, 'w').write(json.dumps(res, indent=1))
print('INSPECT_DONE')

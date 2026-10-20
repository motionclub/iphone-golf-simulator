"""blender -b <blend> --python dump_materials.py : print every material's node tree essentials (colors, textures, links)."""
import bpy
def fmt(v):
    try: return tuple(round(x, 4) for x in v)
    except TypeError: return round(v, 4) if isinstance(v, float) else v
for m in sorted(bpy.data.materials, key=lambda m: m.name):
    print(f"MAT {m.name!r:18} users={m.users} use_nodes={m.use_nodes} diffuse_color={fmt(m.diffuse_color)} blend={getattr(m,'blend_method',None)}")
    if not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            ins = {k: fmt(n.inputs[k].default_value) for k in ('Base Color', 'Roughness', 'Metallic', 'Emission Color', 'Emission Strength', 'Alpha', 'Subsurface Weight', 'Specular IOR Level', 'Coat Weight') if k in n.inputs}
            linked = [(sk.name, [l.from_node.name + ':' + l.from_node.type for l in sk.links]) for sk in n.inputs if sk.is_linked]
            print('    PRINCIPLED', ins, 'LINKED', linked)
        elif n.type in ('TEX_IMAGE',): print('    IMAGE', n.image.name if n.image else None, n.interpolation)
        elif n.type not in ('OUTPUT_MATERIAL',): print('    NODE', n.type, n.name)
print('IMAGES', [(i.name, i.size[:], i.colorspace_settings.name) for i in bpy.data.images if i.name not in ('Render Result', 'Viewer Node')])

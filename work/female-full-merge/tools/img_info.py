import bpy
for i in bpy.data.images:
    if i.name in ('Render Result','Viewer Node'): continue
    print('IMG', i.name, 'file=', i.filepath, 'abs=', bpy.path.abspath(i.filepath), 'packed=', bool(i.packed_file), 'size', tuple(i.size), 'cs', i.colorspace_settings.name)

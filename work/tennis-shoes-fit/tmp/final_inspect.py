import bpy, numpy as np, json
print('FILE', bpy.data.filepath.split('/')[-1])
bad = [n for n in [o.name for o in bpy.data.objects] + [m.name for m in bpy.data.meshes] + [c.name for c in bpy.data.collections] + [m.name for m in bpy.data.materials] if 'arms' in n.lower()]
print('  names containing "arms":', bad)
print('  collections:', {c.name: len(c.objects) for c in bpy.data.collections})
print('  armatures:', [o.name for o in bpy.data.objects if o.type == 'ARMATURE'], '| images:', [i.name for i in bpy.data.images], '| materials:', sorted(m.name for m in bpy.data.materials))
for cw in ('White', 'Black'):
    row = []
    for f in 'LR':
        sock = bpy.data.objects[f'Foot_{f}_Shoe_{cw}']
        for kind in ('Shoe', 'Sock'):
            o = bpy.data.objects[f'Kit_{kind}_{f}_{cw}']
            row.append(f'{o.name}->{o.parent.name}[{"idW" if np.allclose(np.array(o.matrix_world), np.eye(4), atol=1e-9) else "NOT-ID"}] tris={sum(len(p.vertices)-2 for p in o.data.polygons)} slots={[m.name for m in o.data.materials]}')
        row.append(f'{sock.name} loc={tuple(round(x,4) for x in sock.location)} rot={tuple(round(x,4) for x in sock.rotation_euler)} scale={tuple(round(x,4) for x in sock.scale)}')
    print('  ' + cw + ':\n    ' + '\n    '.join(row))
fit = [o for o in bpy.data.objects if o.name.startswith('FitRef')]
print('  FitRef:', [(o.name, len(o.data.vertices), o['fit_ref'][:60]) for o in fit])

import bpy, sys
a = sys.argv[sys.argv.index('--') + 1:]; ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]; ob['roles'] = a[1].split(','); bpy.ops.wm.save_as_mainfile(filepath=a[0]); print('ROLES', ob.name, list(ob['roles']))

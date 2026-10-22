import bpy,sys,collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
c=collections.Counter()
for o in bpy.data.objects:
    p=o.name.split('_')[0] if '_' in o.name else o.name
    key=o.name.rstrip('0123456789.').rstrip('_.')
    c[(o.type,o.name.split('.')[0][:22])]+=1
for k,v in sorted(c.items()): print(k,v)
print(len(bpy.data.materials),[m.name for m in bpy.data.materials][:80])

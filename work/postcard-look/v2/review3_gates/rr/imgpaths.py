import bpy,sys
for im in bpy.data.images:
    if im.filepath: print('IMG',im.name,im.filepath)

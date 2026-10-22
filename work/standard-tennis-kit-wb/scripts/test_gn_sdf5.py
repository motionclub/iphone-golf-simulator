import bpy
ex = bpy.context.preferences.experimental
print([a for a in dir(ex) if not a.startswith('_') and a not in ('bl_rna','rna_type')])

import bpy,pathlib
bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path.cwd()/'work/reference-rebuild/original-blink-finish/Male_OriginalSeamBlinkFinish1.blend'));m=bpy.data.objects['Body'].data;print('HAS',m.has_custom_normals,flush=True)
for a in m.attributes:
 print('ATTR',a.name,a.data_type,a.domain,type(a.data[0]),[(p.identifier,p.type) for p in a.data[0].bl_rna.properties],flush=True)

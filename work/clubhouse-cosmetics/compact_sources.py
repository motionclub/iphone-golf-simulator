import bpy,pathlib
P=pathlib.Path(__file__).resolve().parent
for style in ['hockey','slugger','balloon','candy']:
 p=P/(style+'.blend');bpy.ops.wm.read_factory_settings(use_empty=True)
 with bpy.data.libraries.load(str(p),link=False) as (src,dst): dst.objects=[n for n in src.objects if n.startswith('CLUB_')]
 for i,o in enumerate(dst.objects):
  if o:bpy.context.collection.objects.link(o);o.location.x=i*.35
 bpy.context.preferences.filepaths.save_version=0
 temp=P/(style+"_source.blend");bpy.ops.wm.save_as_mainfile(filepath=str(temp),compress=True);temp.replace(p)

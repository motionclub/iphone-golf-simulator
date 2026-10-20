import bpy,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[3]
reports=[]
for relative in ['ArtDir/hero/kit/premium/source/Premium_Female_Studio.blend','ArtDir/hero/kit/golf/tailoring/source/Golf_Female.blend','ArtDir/hero/kit/golf/tailoring/source/Golf_Male.blend','ArtDir/hero/kit/premium/source/Tennis_Female_SleeveFit.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(R/relative))
 entry={'file':relative,'objects':[]}
 for o in bpy.data.objects:
  if o.type=='MESH' and (o.name.startswith(('Body','Kit_','Golf_'))):
   p=[o.matrix_world@v.co for v in o.data.vertices]
   row={'name':o.name,'vertices':len(p),'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'bounds':[[min(v[k] for v in p),max(v[k] for v in p)] for k in range(3)],'materials':[m.name if m else None for m in o.data.materials],'modifiers':[(m.name,m.type,m.show_viewport) for m in o.modifiers],'shapes':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'groups':[g.name for g in o.vertex_groups]}
   entry['objects'].append(row)
 reports.append(entry)
(R/'work/full-visual-overhaul/garment-coverage/source-inventory.json').write_text(json.dumps(reports,indent=2))
print(json.dumps([{ 'file':r['file'],'objects':[{k:v for k,v in o.items() if k not in ('groups','shapes')} for o in r['objects']]} for r in reports],indent=2))

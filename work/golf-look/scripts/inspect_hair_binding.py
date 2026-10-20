import bpy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dcommon import activate_clip,evaluated_co
W=Path(__file__).resolve().parents[1];rig=bpy.data.objects['Rig_Female'];hair=bpy.data.objects['Hair_F'];body=bpy.data.objects['Body_F'];rows=[]
print('HAIR_FLAGS',hair.hide_viewport,hair.hide_get(),[(c.name,c.type,c.mute) for c in hair.constraints],flush=True)
hair.hide_viewport=False;hair.hide_set(False);bpy.context.view_layer.update()
out=dict(parent=hair.parent.name if hair.parent else None,parentType=hair.parent_type,parentBone=hair.parent_bone,modifiers=[dict(name=m.name,type=m.type,object=m.object.name if m.type=='ARMATURE' and m.object else None) for m in hair.modifiers],groups=[dict(name=g.name,vertices=sum(any(x.group==g.index and x.weight>0 for x in v.groups) for v in hair.data.vertices)) for g in hair.vertex_groups])
for a in ['ReadyIdle','GolfProof_RH_Top','GolfProof_RH_Impact','GolfProof_RH_Finish']:
 activate_clip(rig,a);bpy.context.scene.frame_set(0);bpy.context.view_layer.update();h=evaluated_co(hair,bpy.context.evaluated_depsgraph_get());rows.append(dict(action=a,headMatrix=list(map(list,rig.matrix_world@rig.pose.bones['Head'].matrix)),hairMatrix=list(map(list,hair.matrix_world)),hairMin=h.min(axis=0).tolist(),hairMax=h.max(axis=0).tolist()))
out['poses']=rows;(W/'data/hair_binding_Female.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)

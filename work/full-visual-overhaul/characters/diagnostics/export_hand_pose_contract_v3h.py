"""Export bone-axis-independent authored skin deltas and independent evaluated geometry."""
import bpy,pathlib,sys,json
from mathutils import Matrix
R=pathlib.Path(__file__).resolve().parents[4];sex=sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3H.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Body'));bpy.context.view_layer.update()
B=rig.matrix_world.inverted()@body.matrix_world;A=B.inverted()
flat=lambda m:[m[r][c] for c in range(4) for r in range(4)]
bones=[]
for b in rig.data.bones:
 rest=A@b.matrix_local;delta=A@rig.pose.bones[b.name].matrix@b.matrix_local.inverted()@B
 bones.append({'name':b.name,'restHead':list(rest.translation),'delta':flat(delta)})
out=R/'work/full-visual-overhaul/characters/exports/HandsV3H';out.mkdir(parents=True,exist_ok=True)
(out/f'{sex}_Pose.json').write_text(json.dumps({'version':'match-hero-hand-anatomy-v3','sourceCoordinates':'Blender Body local','bones':bones},separators=(',',':')))
eval=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=eval.to_mesh()
base=[x for v in body.data.shape_keys.key_blocks['Basis'].data for x in v.co];posed=[x for v in mesh.vertices for x in v.co]
(out/f'{sex}_FistGolden.json').write_text(json.dumps({'source':str(R/f'ArtDir/hero/kit/premium/source/Premium_{sex}_FistSurfaceV3H.blend'),'basePositions':base,'posedPositions':posed},separators=(',',':')))
full=json.loads((out/f'{sex}_FistGolden.json').read_text());full['stages']=[{'percent':percent,'posedPositions':json.loads((out/f'{sex}_FistGolden_{percent}.json').read_text())['posedPositions']} for percent in (25,50,75)];(out/f'{sex}_FistGolden.json').write_text(json.dumps(full,separators=(',',':')))
print('HAND_POSE_CONTRACT_V3',sex,len(bones),len(base)//3,flush=True)

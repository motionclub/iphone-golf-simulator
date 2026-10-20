"""Transfer only sleeve influence from approved body triangles; geometry/UV/maps/rest stay exact."""
import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(sys.argv[sys.argv.index('--')+1]);sex=sys.argv[sys.argv.index('--')+2];low='--lod' in sys.argv
source=R/(f'ArtDir/hero/kit/premium/source/Tennis_{sex}_MatchDistance.blend' if low else f'work/cloth-overhaul/export/Cloth_{sex}.blend')
bpy.ops.wm.open_mainfile(filepath=str(source));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.data.pose_position='REST'
with bpy.data.libraries.load(str(R/f'work/match-anim-set/export/HeroBase_{sex}_MatchAnims.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('Body_')]
body=next(o for o in b.objects if o and o.type=='MESH');body.data.calc_loop_triangles();M=body.matrix_world
points=[M@v.co for v in body.data.vertices];tri=[tuple(t.vertices) for t in body.data.loop_triangles];bvh=BVHTree.FromPolygons(points,tri,all_triangles=True)
weights=[]
for v in body.data.vertices:weights.append({body.vertex_groups[g.group].name:g.weight for g in v.groups})
top=bpy.data.objects['Kit_Top'];count=0;largest=0;sumchange=0
for v in top.data.vertices:
 original={top.vertex_groups[g.group].name:g.weight for g in v.groups};arms=sum(w for n,w in original.items() if 'Arm' in n or 'Shoulder' in n)
 if arms<.02:continue
 p=top.matrix_world@v.co;nearest,normal,face,distance=bvh.find_nearest(p)
 if distance>.05:continue
 ia,ib,ic=tri[face];a,b,c=[np.array(points[i]) for i in (ia,ib,ic)];p0=np.array(nearest);v0=b-a;v1=c-a;v2=p0-a
 d00=v0@v0;d01=v0@v1;d11=v1@v1;den=d00*d11-d01*d01
 if abs(den)<1e-12:continue
 beta=(d11*(v2@v0)-d01*(v2@v1))/den;gamma=(d00*(v2@v1)-d01*(v2@v0))/den;alpha=1-beta-gamma
 incoming={}
 for i,f in [(ia,alpha),(ib,beta),(ic,gamma)]:
  for n,w in weights[i].items():incoming[n]=incoming.get(n,0)+float(f)*w
 blend=.85;merged={n:(1-blend)*original.get(n,0)+blend*incoming.get(n,0) for n in set(original)|set(incoming)}
 merged=sorted([(n,w) for n,w in merged.items() if w>1e-5],key=lambda x:-x[1])[:4];total=sum(w for n,w in merged);merged={n:w/total for n,w in merged}
 change=sum(abs(original.get(n,0)-merged.get(n,0)) for n in set(original)|set(merged));largest=max(largest,change);sumchange+=change;count+=1
 for g in list(v.groups):top.vertex_groups[g.group].remove([v.index])
 for n,w in merged.items():(top.vertex_groups.get(n) or top.vertex_groups.new(name=n)).add([v.index],w,'REPLACE')
# Remove appended read-only body, keeping cloth rig and all original construction.
bpy.data.objects.remove(body,do_unlink=True)
if low:
 save=R/f'ArtDir/hero/kit/premium/source/Tennis_{sex}_MatchDistance.blend';fbx=R/f'Unity/Assets/Resources/Tennis/KitsLOD/{sex}.fbx';meshes=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.endswith('_High')]
else:
 save=R/f'ArtDir/hero/kit/premium/source/Tennis_{sex}_SleeveFit.blend';fbx=R/f'Unity/Assets/Resources/Tennis/KitsFitted/{sex}.fbx';meshes=[top]
fbx.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(save));bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,path_mode='STRIP')
report={'sex':sex,'mesh':'match-distance' if low else 'full','changed_sleeve_vertices':count,'mean_L1_weight_change':sumchange/max(1,count),'max_L1_weight_change':largest,'geometry_uv_maps_rest':'UNCHANGED','native_bind_import_and_pose_visual':'UNVERIFIED','source':str(save),'asset':str(fbx)}
(R/f'proof/full-visual-overhaul/characters/sleeve-weights-{sex.lower()}{"-lod" if low else ""}.json').write_text(json.dumps(report,indent=2))
print('SLEEVE_FIT '+str(report),flush=True)

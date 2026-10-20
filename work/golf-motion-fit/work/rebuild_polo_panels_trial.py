"""Use the approved tennis polo's connected fabric panels and weight field.
Golf refinements are local to the tuck, with separate pose correctives.
"""
import bpy,sys
from mathutils import Matrix
sex=sys.argv[-1];rig=bpy.data.objects['Rig_'+sex];o=bpy.data.objects['Golf_Polo']
# The source construction already contains collars, plackets, cuffs, hems,
# buttons and seam strips. It must not be replaced by overlapping body surfaces.
for v in o.data.vertices:
 if v.co.z<1.05:
  t=max(0,min(1,(1.05-v.co.z)/.07));t=t*t*(3-2*t);v.co.z-=.025*t
# Cuff construction is a short-sleeve band on the upper arm. It must not
# inherit the torso weights of the neighboring body surface in a resting pose.
from mathutils import Vector
adj=[[] for v in o.data.vertices]
for e in o.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set();groups=[]
for start in range(len(adj)):
 if start in seen:continue
 todo=[start];ids=[];seen.add(start)
 while todo:
  i=todo.pop();ids.append(i)
  for j in adj[i]:
   if j not in seen:seen.add(j);todo.append(j)
 groups.append(ids)
main=max(groups,key=len)
for ids in groups:
 if ids==main:continue
 center=sum((o.data.vertices[i].co for i in ids),Vector())/len(ids)
 if abs(center.x)<.16 or not 1.0<center.z<1.25:continue
 side='Left' if center.x>0 else 'Right'
 for vg in o.vertex_groups:vg.remove(ids)
 group=o.vertex_groups.get(side+'UpperArm') or o.vertex_groups.new(name=side+'UpperArm');group.add(ids,1,'REPLACE')
 print('GOLF_CUFF_WEIGHT',sex,side,len(ids),flush=True)
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[sys.argv.index('--python')+1]).resolve().parent))
from polo_panels import refine_panels
refine_panels(o,main)
for m in o.modifiers:
 if m.type=='ARMATURE':m.object=rig
if not any(m.type=='ARMATURE' for m in o.modifiers):o.modifiers.new('CurrentHero','ARMATURE').object=rig
print('APPROVED_POLO_CONSTRUCTION',sex,len(o.data.vertices),sum(len(p.vertices)-2 for p in o.data.polygons),flush=True)

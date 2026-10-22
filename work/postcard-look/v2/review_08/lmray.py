import bpy, sys, math, collections, numpy as np, json
sys.path.insert(0,'/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/blender/scripts')
import hole08_design as D, postcard_check as PC
from mathutils import Vector
H=PC.Hole(D); YD=0.9144
for b in [(0,0),(19,178),(2.5,24)]: print('lie',b,H.lie_at(b))
sc=bpy.context.scene; dg=bpy.context.evaluated_depsgraph_get()
lm=json.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/hole08/landmarks.json'))['shots'][2]
def L(p): return Vector((p[0]*YD,p[2]*YD,p[1]*YD))
cam=L(lm['pos']); look=L(lm['look'])
masonry=[o for o in bpy.data.objects if o.name.startswith(('DRESS_ARCH','DRESS_BLOCK'))]
def wc(o):
    M=np.array(o.matrix_world); V=np.array([v.co[:] for v in o.data.vertices]).reshape(-1,3); return (np.c_[V,np.ones(len(V))]@M.T)[:,:3]
allV=np.vstack([wc(o) for o in masonry]); print('masonry bbox',allV.min(0),allV.max(0),'cam',cam)
arch=bpy.data.objects['DRESS_ARCH_00']; AV=wc(arch)
print('arch verts z',AV[:,2].min(),AV[:,2].max(),'x',AV[:,0].min()/YD,AV[:,0].max()/YD,'y',AV[:,1].min()/YD,AV[:,1].max()/YD)
# ray test from camera to random arch vertices
rng=np.random.default_rng(3); blocked=0; tot=0; hits=collections.Counter()
for v in AV[rng.choice(len(AV),300)]:
    d=Vector(v)-cam; dist=d.length; d.normalize()
    ok,loc,n,i,ob,mw=sc.ray_cast(dg,cam,d,distance=dist-0.05)
    tot+=1
    if ok and not ob.name.startswith(('PLANT_VINE','DRESS_ARCH','DRESS_BLOCK')):
        blocked+=1; hits[ob.name]+=1
print('rays blocked',blocked,'/',tot,dict(hits))
# is the look direction the arch? angle between look dir and arch centre dir
c=Vector(AV.mean(0)); print('arch centre',c/YD, 'angle look->centre deg', math.degrees((look-cam).angle(c-cam)))
# camera inside any solid? ray up/down
ok,loc,n,i,ob,mw=sc.ray_cast(dg,cam,Vector((0,0,-1)),distance=50); print('below cam',ob.name if ok else None, 'dist', (loc-cam).length if ok else None)
# frame fraction: project arch verts to camera
from bpy_extras.object_utils import world_to_camera_view
cam_o=bpy.data.objects.new('c',bpy.data.cameras.new('c')); sc.collection.objects.link(cam_o); cam_o.location=cam
cam_o.rotation_euler=(look-cam).to_track_quat('-Z','Y').to_euler(); cam_o.data.sensor_fit='VERTICAL'; cam_o.data.angle_y=math.radians(60)
sc.render.resolution_x,sc.render.resolution_y=900,1600; bpy.context.view_layer.update()
co=[world_to_camera_view(sc,cam_o,Vector(v)) for v in AV]
xs=[c.x for c in co]; ys=[c.y for c in co]
print('arch in frame x %.2f..%.2f y %.2f..%.2f'%(min(xs),max(xs),min(ys),max(ys)))

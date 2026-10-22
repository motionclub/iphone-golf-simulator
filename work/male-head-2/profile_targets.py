import bpy,bmesh,numpy as np,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock'
bpy.ops.wm.open_mainfile(filepath=str(W/'baseline/HeroBase_Male_Silhouette.blend'));o=bpy.data.objects['Body_M'];bm=bmesh.new();bm.from_mesh(o.data);tree=BVHTree.FromBMesh(bm);bm.free()
c=np.load(W/'baseline/mesh.npz')['co'];top=float(c[:,2].max());k=(top-1.449)/(272-76)
im=np.load(W/'reference-rgb.npy');crop=im[:,505:730]
skin=(crop[:,:,0]-crop[:,:,1]>12)&(crop[:,:,1]-crop[:,:,2]>7)&(crop[:,:,0]>65)
# Neutral foreground threshold for the grey upper torso below the rear collar.
fg=skin|(np.mean(crop,axis=2)>75)
rows=[]
for py in range(76,326):
 s=np.where(skin[py])[0];a=np.where(fg[py])[0]
 if not len(s) or not len(a):continue
 left=int(s[0]+505);right=int((s[-1] if py<275 else a[-1])+505)
 rows.append([top-(py-76)*k,(left-712)*k+.065,(right-712)*k+.065])
ref=np.array(rows)[::-1];kernel=np.exp(-np.arange(-5,6)**2/(2*1.5**2));kernel/=kernel.sum()
for j in [1,2]:ref[:,j]=np.convolve(np.pad(ref[:,j],(5,5),mode='edge'),kernel,mode='valid')
samples=[]
for z in np.arange(1.375,top-.0001,.0007):
 f=tree.ray_cast(Vector((0,-1,float(z))),Vector((0,1,0)),2)[0];b=tree.ray_cast(Vector((0,1,float(z))),Vector((0,-1,0)),2)[0]
 if f is not None and b is not None:samples.append([z,f.y,b.y])
samples=np.array(samples)
np.savez(W/'profile-targets.npz',reference=ref,current=samples)
(W/'profile-calibration.json').write_text(json.dumps({'use':'Head-detail side-form diagnostic only; no new numeric gate and no change to primary reference masks/cameras.','reference':'male_head_detail.jpg, LEFT PROFILE','top_reference_pixel_y':76,'chin_reference_pixel_y':272,'target_chin_height_metres':1.449,'top_height_metres':top,'metres_per_reference_pixel':k,'posterior_anchor_reference_pixel_x':712,'posterior_anchor_y_metres':.065,'skin_threshold':'R-G>12, G-B>7, R>65; ignore stubble as a color cue; use outer contour only.','reference_row_smoothing_sigma_pixels':1.5},indent=2))
print('Profile calibration',top,k,'curve samples',len(samples))

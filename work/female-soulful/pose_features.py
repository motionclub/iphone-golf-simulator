"""Female garment pose distance includes full joint frames so axial twist is retained."""
import numpy as np
from mathutils import Matrix
SEG=[('Spine','Chest'),('Chest','Neck'),('LeftShoulder','LeftUpperArm'),('LeftUpperArm','LeftLowerArm'),('LeftLowerArm','LeftHand'),('RightShoulder','RightUpperArm'),('RightUpperArm','RightLowerArm'),('RightLowerArm','RightHand')]
def segment_features(hero,bones):
 directions=[]
 for parent,child in SEG:
  v=bones[hero.body.bones.index(child),:3,3]-bones[hero.body.bones.index(parent),:3,3];directions.append(v/(np.linalg.norm(v)+1e-12))
 return np.asarray([directions[i]@directions[j]for i in range(8)for j in range(i+1,8)])
PAIRS=[('Hips','Chest'),('Chest','LeftUpperArm'),('Chest','RightUpperArm'),('LeftUpperArm','LeftLowerArm'),('RightUpperArm','RightLowerArm')]
def features(hero,bones_world):
 f=list(segment_features(hero,bones_world))
 for parent,child in PAIRS:
  pa=Matrix(bones_world[hero.body.bones.index(parent),:3,:3]).to_quaternion()
  ch=Matrix(bones_world[hero.body.bones.index(child),:3,:3]).to_quaternion()
  m=(pa.inverted()@ch).to_matrix();f.extend(float(m[row][col])for col in range(3)for row in range(3))
 return np.asarray(f)

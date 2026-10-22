import sys, numpy as np, bpy
tag=sys.argv[sys.argv.index('--')+1]; clip=sys.argv[sys.argv.index('--')+2]
rig=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
act=bpy.data.actions[clip]; rig.animation_data_create(); rig.animation_data.action=act
try: rig.animation_data.action_slot=act.slots[0]
except Exception: pass
sc=bpy.context.scene
def P(n): return np.array(rig.matrix_world@rig.pose.bones[n].head)
prev=None
for f in range(int(act.frame_end)+1):
    sc.frame_set(f); bpy.context.view_layer.update()
    r=P('RightHand'); l=P('LeftHand'); rs=P('RightUpperArm'); ls=P('LeftUpperArm'); re=P('RightLowerArm')
    # to hero frame: right=-x, fwd=-y
    rel=lambda v,o:(-(v-o)[0], -(v-o)[1], (v-o)[2])
    d=np.linalg.norm(r-prev[0])*30 if prev else 0
    print('f%02d t=%.2f Rhand rel R-shoulder (r,f,u)= %5.2f %5.2f %5.2f speed %.1f m/s | Lhand rel L-shoulder %5.2f %5.2f %5.2f | |shoulder-hand| R %.2f L %.2f'%(f,f/30,*rel(r,rs),d,*rel(l,ls),np.linalg.norm(r-rs),np.linalg.norm(l-ls)))
    prev=(r,)

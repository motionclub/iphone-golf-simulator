import os,sys,json
import bpy,numpy as np
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'))
sys.path.insert(0,os.path.join(repo,'blender/scripts'))
import postcard_look_verify as V
import hole08_design as des
bpy.ops.wm.open_mainfile(filepath=os.path.join(repo,'work/postcard-look/v3/hole08/stage/hole_08.blend'),load_ui=False)
C=V.Ctx(8,des,des.__file__,{})
obs=[o for o in bpy.data.objects if o.name.startswith('DRESS_ARCH') and o.type=='MESH']
rows=[]
for ob in obs:
    old=np.array([v.co[:] for v in ob.data.vertices])
    for ratio in [1.0,1.27/1.30,1.25/1.30]:
        for v,q in zip(ob.data.vertices,old):v.co=(float(q[0]*ratio),float(q[1]),float(q[2]))
        ob.data.update();S=V.Snap('blend',C)
        ok,detail=V.arch_opening(S,{ob.name:ob})
        rows.append({'object':ob.name,'span_ratio':ratio,'opening_pass':ok,'detail':detail,'local_x_span_m':float(np.ptp(old[:,0])*ratio),'world_z_span_m':float(np.ptp(old[:,2]))})
    for v,q in zip(ob.data.vertices,old):v.co=q
json.dump(rows,open(os.path.join(os.path.dirname(__file__),'arch_diagnosis.json'),'w'),indent=2)
print(json.dumps(rows,indent=2))

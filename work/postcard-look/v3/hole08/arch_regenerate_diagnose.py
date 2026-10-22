import os,sys,json
import bpy
repo=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../..'));sys.path.insert(0,os.path.join(repo,'blender/scripts'))
import postcard_look_verify as V
import hole08_design as des
import postcard_props_lib as PL
bpy.ops.wm.open_mainfile(filepath=os.path.join(repo,'work/postcard-look/v3/hole08/stage/hole_08.blend'),load_ui=False)
C=V.Ctx(8,des,des.__file__,{});rows=[]
old=bpy.data.objects.get('DRESS_ARCH_00');center=tuple(old.location);facing=171.2
bpy.data.objects.remove(old,do_unlink=True)
for scale,depth in [(1.25,1.9),(1.25,None)]:
 a=PL.build_masonry_arch(None,center,facing,span_m=8*.9144*scale,height_m=12.2,depth_m=depth,seed=8,base_rock=False,vines=False,name='DRESS_ARCH_00')
 bpy.context.view_layer.update();S=V.Snap('fbx',C);ob=a['arch'];ok,detail=V.arch_opening(S,{ob.name:ob});rows.append({'arch_scale':scale,'depth_m':depth,'opening_pass':ok,'detail':detail,'dims':a['dims']})
 for o in [ob]+a['fallen']:bpy.data.objects.remove(o,do_unlink=True)
json.dump(rows,open(os.path.join(os.path.dirname(__file__),'arch_regenerate_diagnosis.json'),'w'),indent=2);print(json.dumps(rows,indent=2))

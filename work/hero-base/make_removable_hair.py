from pathlib import Path
p=Path('Tools/HeroBase/plate_profiles.py');s=p.read_text();s+='''
# Complete bald cranium beneath the optional hairstyle; facial landmarks remain locked.
MALE['head']=[(173,16,21),(168,27,27),(159,37,35),(149,43,41),(135,47,43),(118,47,43),(98,46,44),(79,47,44),(66,40,37),(58,34,36),(50,25,28),(44,13,15),(41,1,1)]
FEMALE['head']=[(189,8,13),(186,17,19),(178,27,27),(168,34,33),(154,40,35),(137,40,34),(120,37,35),(106,31,30),(95,23,26),(89,16,19),(85,7,8),(84,1,1)]
''';p.write_text(s)
p=Path('Tools/HeroBase/build_static.py');s=p.read_text().replace('step=5.2 if female else 6.40','step=5.35 if female else 6.55').replace('hr=[];N=72;K=34','hr=[];N=72;K=39')
a=s.index("    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);hair.select_set(True);bpy.context.view_layer.objects.active=body\n    bpy.ops.export_scene.fbx(")
b=s.index('    # Neutral studio.',a)
s=s[:a]+'''    export_args=dict(use_selection=True,object_types={'MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False)
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
    bpy.ops.export_scene.fbx(filepath=str(D/'unity_import'/('HeroBase_'+sex.title()+'_Body.fbx')),**export_args)
    # A hairstyle is a separate asset in head-local metres. It never supplies scalp, ears or neck.
    anchor_z=(sole-profile['eye_y'])*scale
    style=hair.copy();style.data=hair.data.copy();style.name='Hair_'+suffix;bpy.context.collection.objects.link(style)
    for v in style.data.vertices:v.co.z-=anchor_z
    bpy.ops.object.select_all(action='DESELECT');style.select_set(True);bpy.context.view_layer.objects.active=style
    bpy.ops.export_scene.fbx(filepath=str(D/'unity_import'/('Hair_Default_'+sex.title()+'.fbx')),**export_args)
    bpy.data.objects.remove(style,do_unlink=True)
    (D/'unity_import'/('HeroBase_'+sex.title()+'_Attachments.json')).write_text(json.dumps({'body_fbx':'HeroBase_'+sex.title()+'_Body.fbx','default_hair_fbx':'Hair_Default_'+sex.title()+'.fbx','hair_anchor_metres':[0,anchor_z,0],'hair_origin':'head-local; Unity Y up','body_contains_hair':False,'bald_height_m':max(v.co.z for v in body.data.vertices)-min(v.co.z for v in body.data.vertices)},indent=2))
'''+s[b:]
a=s.index("    for name,ang in [('front',0),('back',math.pi),('threequarter',math.pi/5)]:")
b=s.index('    cam.location=(0,-5',a)
s=s[:a]+'''    for bald in (False,True):
        hair.hide_render=bald
        for name,ang in [('front',0),('back',math.pi),('threequarter',math.pi/5)]:
            cam.location=(math.sin(ang)*5,-math.cos(ang)*5,(sole-360)*scale);cam.rotation_euler=(Vector((0,0,cam.location.z))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(P/'blender'/(suffix+('_bald' if bald else '')+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
    hair.hide_render=False
'''+s[b:]
p.write_text(s)

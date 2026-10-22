"""Correct only the scratch fixture's missing exportable support ground."""
import os,sys
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
sys.path.insert(0,ROOT+'/blender/scripts')
import bpy
import postcard_lib as P
import postcard_look_lib as L
for cap in (490,3000):
    folder=os.path.dirname(__file__)+f'/faces{cap}'
    D=P.start('hole09_design',out_dir=folder)
    bpy.ops.wm.open_mainfile(filepath=folder+'/fixture.blend',load_ui=False)
    P.link_to(bpy.data.objects['TERRAIN_fixture'],'COURSE')
    bpy.ops.wm.save_as_mainfile(filepath=folder+'/fixture.blend',relative_remap=False)
    L.export_look_fbx(D)

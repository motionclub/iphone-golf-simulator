import pathlib,runpy,sys
R=pathlib.Path(__file__).resolve().parents[3];src=R/'work/full-visual-overhaul/garment-coverage/author-sleeve-geometry-9.py'
for name in ['female_intro','male_intro','female_Ready_1','female_IntroPushups_1']:
 sys.argv=[str(src),'--',name]
 runpy.run_path(str(src),run_name='__main__')

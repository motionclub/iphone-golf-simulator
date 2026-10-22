import pathlib,runpy,sys
R=pathlib.Path(__file__).resolve().parents[3];src=R/'work/full-visual-overhaul/garment-coverage/author-sleeve-geometry-9.py';D=R/'proof/full-visual-overhaul/character-pose-data-1/poses'
for p in sorted(D.glob('*.json')):
 sys.argv=[str(src),'--',p.stem,'--data-only']
 try:runpy.run_path(str(src),run_name='__main__')
 except SystemExit as e:
  if e.code not in [0,None]:raise

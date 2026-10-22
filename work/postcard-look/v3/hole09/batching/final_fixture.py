"""Verify the final source's normal architecture and actual stone batching."""
import os,sys,runpy
sys.dont_write_bytecode=True
for name in ('custom_normals.py','fixture.py'):
    path=os.path.dirname(__file__)+'/'+name
    sys.argv=[path]
    try:
        runpy.run_path(path,run_name='__main__')
    except SystemExit as exc:
        if exc.code:
            raise

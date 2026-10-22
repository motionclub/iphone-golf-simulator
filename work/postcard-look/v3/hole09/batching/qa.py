"""Run unchanged ruin and independent cuboid checkers on batched fixtures."""
import os,sys,runpy,json
sys.dont_write_bytecode=True
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'../../../../..'))
OUT=os.path.dirname(__file__)
tools=[('ruin',ROOT+'/work/postcard-look/v2/hole09/tools/ruin_check.py'),
       ('pieces',ROOT+'/work/postcard-look/v3/lib/masonry/piece_classifier.py')]
rows=[]
for cap in (490,3000):
    for format_ in ('blend','fbx'):
        folder=OUT+f'/faces{cap}'
        source=folder+('/fixture.blend' if format_=='blend' else '/hole_09.fbx')
        for kind,path in tools:
            out=folder+f'/{kind}_{format_}.json'
            sys.argv=[path,'--','--'+format_,source,'--json' if kind=='ruin' else '--out',out]
            try:
                runpy.run_path(path,run_name='__main__')
                code=0
            except SystemExit as exc:
                code=exc.code or 0
            with open(out) as f:result=json.load(f)
            if kind=='ruin':
                gates=result if isinstance(result,list) else result.get('gates',result.get('results',[]))
                okay=bool(gates) and all(g.get('ok',g.get('pass',False)) for g in gates)
            else:okay=result['pass']
            rows.append(dict(cap=cap,format=format_,tool=kind,exit=code,ok=code==0 and okay,output=out))
with open(OUT+'/qa_results.json','w') as f:json.dump(rows,f,indent=2)
print(json.dumps(rows,indent=2),flush=True)
sys.exit(0 if all(r['ok'] for r in rows) else 1)

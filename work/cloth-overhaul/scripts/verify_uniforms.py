from pathlib import Path
import numpy as np,json,sys
W=Path(__file__).resolve().parents[1];D=W/(sys.argv[1] if len(sys.argv)>1 else 'after_final');rows=json.loads((D/'palette_uniforms.json').read_text())['rows'];results=[]
floor=np.array([.035,.035,.0401])
def colour(c):return np.array([c[k] for k in ['r','g','b']])
def tint(p):return np.maximum(.93*p,floor)
for r in rows:
 pick=np.array([int(r['pick'][i:i+2],16)/255 for i in [0,2,4]]);derived=.65*pick if pick@np.array([.2126,.7152,.0722])>=.5 else pick+.35*(1-pick);roles={'shirt':['Kit_Shirt','Kit_ShirtTrim'],'shorts':['Kit_Shorts','Kit_ShortsBand'],'shoes':['Kit_Shoe']}
 if r['role'] not in roles[r['group']]:continue
 main=tint(derived if r['role'].endswith('Trim') or r['role'].endswith('Band') else pick);trim=tint(derived);error=float(max(abs(colour(r['main'])-main).max(),abs(colour(r['trim'])-trim).max()));results.append({**r,'max_rgb_error':error,'pass':error<2e-6})
report={'checked_materials':len(results),'distinct_picks':sorted(set(r['pick'] for r in results)),'max_rgb_error':max(r['max_rgb_error'] for r in results),'pass':all(r['pass'] for r in results),'rows':results};(W/'recolour_uniforms.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='rows'})

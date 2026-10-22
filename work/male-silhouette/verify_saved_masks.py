"""Independently confirm re-opened saved blend renders against frozen masks."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
W=Path(__file__).parent;R=W.parents[1];P=R/'ArtDir/hero/base_lock/proof/male_silhouette'
O=Path('/Users/adnanyonathan/Documents/Codex/2026-09-30/open-3/outputs/Male_Silhouette')
metrics=json.loads((P/'silhouette-metrics.json').read_text());measurements=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in metrics['measurements']:
    assert sha(W/(r['view']+'_target.png'))==r['target_mask_sha256']
    assert sha(P/(r['view']+'.png'))==r['render_sha256']
    if not r['gate_authority']:continue
    target=np.array(Image.open(W/(r['view']+'_target.png')))>127
    delivered=np.array(Image.open(P/(r['view']+'.png')))
    saved=np.array(Image.open(W/'verified-save'/(r['view']+'.png')))
    assert np.array_equal(delivered,saved),'Saved source render differs from proof'
    mask=saved[:,:,3]>127
    difference=int((target^mask).sum());union=int((target|mask).sum())
    assert difference==r['symmetric_difference_pixels'] and union==r['union_pixels']
    assert difference/union<=.05
    measurements.append({'view':r['view'],'difference_pixels':difference,'union_pixels':union,'percent':100*difference/union})
verification=json.loads((P/'saved-blockout-verification.json').read_text())
verification.update({'saved_source_rerender_pixels_match_proof':True,'independently_verified_primary_measurements':measurements})
for dst in [P/'saved-blockout-verification.json',O/'saved-blockout-verification.json']:
    dst.write_text(json.dumps(verification,indent=2))
print(json.dumps({'GATE':'MALE_SIL PASS','measurements':measurements,'saved_source_rerender_pixels_match_proof':True},indent=2))

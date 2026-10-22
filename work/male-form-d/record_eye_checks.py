"""Record the explicit visual review, tied to the actual saved source/captures."""
from pathlib import Path
import hashlib,json
W=Path(__file__).parent;R=W.parents[1];D=R/'ArtDir/hero/base_lock';P=D/'proof';F=P/'male_form_d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={
 'ARMS_SIDE':{'flag':'PASS','note':'Left/right profiles show closed rounded deltoid, upper-arm and forearm depth; wrist narrows continuously. No thin arm cards.'},
 'CHIN':{'flag':'PASS','note':'The old forward-closing cap was retracted and rounded, with a further 8 mm local depth correction. The chin ends in an under-chin surface joining the throat; no separate beard/stubble strap. Upper-face identity remains unpolished.'},
 'FEET_SIDE':{'flag':'PASS','note':'Both profiles show a rounded toe box, sloped instep, ankle and heel; a broad low sole can plant on the ground. No old twisted slab.'},
 'SHOULDERS':{'flag':'PASS','note':'Full rounded deltoid at both arm joins. Folded front/rear deltoid/torso triangles were locally unfolded; the previous horizontal cavity/crease is absent in front, back and three-quarter proof.'},
 'WAIST':{'flag':'PASS','note':'Waist tapers below the chest and widens toward the hips without the former waist shelf/love-handle ridge. Front/back and three-quarter views reviewed.'}
}
views=['front','back','left','right','threequarter','head_side','foot_side']
report={'review':'Manual geometry eye check of native Blender views and actual final Unity captures; no whole-face or hand likeness claim.',
 'source_sha256':sha(D/'blender/HeroBase_Male_Silhouette.blend'),'unity_capture_sha256':{n:sha(F/'unity'/(n+'.png')) for n in views},'checks':checks}
(P/'male-form-d-eye-checks.json').write_text(json.dumps(report,indent=2))
print('EYE_CHECKS_RECORDED')

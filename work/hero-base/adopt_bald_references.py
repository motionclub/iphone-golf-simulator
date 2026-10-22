from pathlib import Path
import shutil,json,hashlib
from PIL import Image
r=Path('.');d=r/'ArtDir/hero/base_lock';a=d/'archive/with_hair_20260930';a.mkdir(parents=True,exist_ok=True)
for name in ['male_body_plain.jpg','female_body_plain.jpg','plate-measurements.json','ACCEPTANCE.md','METRICS.md','SCALE.md']:
 if not (a/name).exists():shutil.copy2(d/name,a/name)
shutil.copy2(r/'work/hero-base/visual-before-v2/plate_profiles.py',a/'plate_profiles.py')
files={'male':Path('/Users/adnanyonathan/Downloads/76c005d722ecfefab530b266606a147486693340a75bc22654c07b950c6bc4a0.jpg'),'female':Path('/Users/adnanyonathan/Downloads/ef62ce52ac6772fa13fac2b4e62727859efebf995c52d78e86e04517eddd5614.jpg')}
measured={}
for sex,src in files.items():
 dst=d/(sex+'_body_plain.jpg');shutil.copy2(src,dst);im=Image.open(dst)
 measured[sex]={'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'image_size':list(im.size),'authority':'User replacement bald reference supplied 2026-09-30','source_filename':src.name,'front_center_x':354 if sex=='male' else 440,'back_center_x':917 if sex=='male' else 847,'sole_y':654 if sex=='male' else 679,'top_y':61 if sex=='male' else 24,'reference_height_px':593 if sex=='male' else 655,'base_has_hair':False}
(d/'plate-measurements.json').write_text(json.dumps(measured,indent=2))
(d/'REFERENCE_CHANGE.md').write_text('# Reference replacement — 2026-09-30\n\nThe user explicitly replaced the earlier hair-on plates with these two bald plates and requested improved head shapes. The current male_body_plain.jpg and female_body_plain.jpg are unchanged copies of those supplied images. Hashes and source filenames are in plate-measurements.json. Earlier authority images and measurements are preserved under archive/with_hair_20260930/.\n\nCurrent acceptance is against the complete bald bodies and heads. Hair remains an independent optional asset and supplies no scalp, face, ears or neck geometry. The main HeroBase prefabs must be bald; optional hairstyles do not participate in the bald silhouette/face comparison.\n')
print(json.dumps(measured,indent=2))

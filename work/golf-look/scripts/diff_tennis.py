from pathlib import Path
import json,numpy as np
from PIL import Image
W=Path(__file__).resolve().parents[1]
B=W/'proof/post_cloth_before/tennis';A=W/'proof/shared_core_after/tennis';D=W/'proof/shared_core_after/tennis_diffs';D.mkdir(exist_ok=True)
rows=[]
for p in sorted(B.glob('*.png')):
    if '_mask' in p.stem or 'noao' in p.stem:continue
    after=A/p.name
    if not after.exists():continue
    b=np.asarray(Image.open(p).convert('RGB')).astype(int);a=np.asarray(Image.open(after).convert('RGB')).astype(int)
    e=np.abs(a-b)
    row={'file':p.name,'whole_image_mean_bytes':float(e.mean()),'whole_image_max_bytes':int(e.max())}
    mask=B/(p.stem+'_mask.png')
    if mask.exists():
        ids=np.asarray(Image.open(mask).convert('RGB'));m=np.max(ids,axis=-1)>20
        # Erode colour-ID foreground to remove MSAA/depth silhouette pixels.
        for dy in [-1,0,1]:
            for dx in [-1,0,1]:m&=np.roll(np.roll(np.max(ids,axis=-1)>20,dy,0),dx,1)
        row.update(kit_pixels=int(m.sum()),kit_mean_bytes=float(e[m].mean()) if m.any() else None,kit_max_bytes=int(e[m].max()) if m.any() else None)
    row['whole_image_pass']=row['whole_image_mean_bytes']<=1 and row['whole_image_max_bytes']<=3
    Image.fromarray(np.minimum(e*16,255).astype('uint8')).save(D/p.name)
    rows.append(row)
(W/'data/tennis_shared_core_diff.json').write_text(json.dumps({'threshold_bytes':{'mean':1,'max':3},'rows':rows,
    'scope':'full images plus available kit masks; whole-image PASS also proves every hero pixel, while a whole-image FAIL requires a complete hero mask to distinguish background motion'},indent=2)+'\n')
print('Tennis comparisons',len(rows),'whole-frame passes',sum(r['whole_image_pass'] for r in rows))
for r in rows:
    if 'match_phone' in r['file'] or 'full_front' in r['file']:print(r)

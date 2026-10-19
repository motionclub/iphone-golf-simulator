"""Actual effect frames with their measured capture timestamps, no retouching.
Usage: RAW_OUTPUT PROOF_OUTPUT. Native encode_frames.swift produces the MP4s.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys, json, shutil

raw,out=map(Path,sys.argv[1:]);out.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[4]
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
records=[]
for after in sorted((raw/'stage6').iterdir()):
    if not after.is_dir():continue
    before=raw/'stage5'/after.name
    def rows(p):return [line.split('\t') for line in (p/'frames.tsv').read_text().splitlines()]
    old,new=rows(before),rows(after)
    # Newly emitted particles reach the renderer on the following frame.
    # Show visible onset, expansion, and the actual captured tail.
    indices=[1,len(new)//2 if after.name=='celebration' else 4,len(new)-1]
    refname='r2' if after.name in ['normal-contact','perfect-contact','net','celebration'] else 'r4' if after.name in ['ice','lava'] else 'r3'
    ref=Image.open(root/'ArtDir/style/refs'/f'{refname}.png').convert('RGB')
    if refname=='r4':
        w,h=ref.size;x=0 if after.name=='ice' else w//2;ref=ref.crop((x,h//2,x+w//2,h))
    w,h=480,270;sheet=Image.new('RGB',(w*3,44+3*(h+42)),'#f2f3f5');draw=ImageDraw.Draw(sheet)
    for col,label in enumerate(['BEFORE — phase 5','AFTER — phase 6','REF — '+refname+' appearance only']):draw.text((col*w+8,12),label,font=font,fill='#19212c')
    for row,i in enumerate(indices):
        y=44+row*(h+42)
        for col,im in enumerate([Image.open(before/f'{i:03}.jpg'),Image.open(after/f'{i:03}.jpg'),ref]):sheet.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(col*w,y))
        draw.text((8,y+h+8),f'{after.name}: before {float(old[i][1]):.3f}s / after {float(new[i][1]):.3f}s | still reference has no event timing',font=font,fill='#19212c')
    sheet.save(out/(after.name+'_before_after_ref.jpg'),quality=94)
    for stage,source in [('stage5',before),('stage6',after)]:
        (out/'clips'/stage/after.name).mkdir(parents=True,exist_ok=True)
        shutil.copy2(source/'frames.tsv',out/'clips'/stage/after.name/'frames.tsv')
    records.append({'event':after.name,'sampledFrames':indices,'beforePeakParticles':max(int(r[2]) for r in old),'afterPeakParticles':max(int(r[2]) for r in new),'afterDurationSeconds':float(new[-1][1]),'reference':refname})
(out/'particle-measurements.json').write_text(json.dumps(records,indent=2)+'\n')
print(len(records),'effect sheets')

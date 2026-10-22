"""Evaluate the requested gates. Capture-test success is not visual acceptance."""
from pathlib import Path
import json,csv,sys,math,xml.etree.ElementTree as ET
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from measure import lab,morph
src=Path(sys.argv[1]);out=Path(sys.argv[2]);native=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
rows=json.loads((src/'metrics.json').read_text());main=[r for r in rows if not r['shot'].startswith('lookdev_')];game=[r for r in main if r['shot'].endswith('__a_gameplay')];lookup={r['shot']:r for r in rows}
# These rectangles select cheek/nose skin in the fixed SceneKit head camera.
# Material-ID masks exclude eyes, cap and background. Save the marked ROIs for inspection.
rois={'MatchHero_Male':[345,530,570,610],'MatchHero_Female':[345,565,570,635],
      'GolfKitHero_Male':[290,520,485,565],'GolfKitHero_Female':[275,545,475,585]}
references={}
(out/'lobby-reference').mkdir(exist_ok=True)
for hero,rect in rois.items():
 p=native/(hero+'_head.png')
 if not p.exists():continue
 a=np.array(Image.open(p).convert('RGB'));m=np.array(Image.open(native/(hero+'_head.mask.png')).convert('RGB'));skin=(m[:,:,0]>240)&(m[:,:,1]<10)&(m[:,:,2]<10);roi=np.zeros(skin.shape,dtype=bool);x0,y0,x1,y1=rect;roi[y0:y1,x0:x1]=True;skin=morph(skin&roi,3,False)
 body=np.array(Image.open(native/(hero+'_body.png')).convert('RGB'));bm=np.array(Image.open(native/(hero+'_body.mask.png')).convert('RGB'));shirt=morph((bm[:,:,1]>240)&(bm[:,:,0]<10)&(bm[:,:,2]<10),3,False)
 if skin.sum()<12 or shirt.sum()<12:raise ValueError('Inspect native reference ROI for '+hero)
 face=np.median(lab(a)[skin],axis=0);cloth=np.median(lab(body)[shirt],axis=0)
 references[hero]={'faceLab':face.round(2).tolist(),'shirtLab':cloth.round(2).tolist(),'facePixels':int(skin.sum()),'shirtPixels':int(shirt.sum()),'faceROI':rect}
 marked=Image.open(p).convert('RGB');ImageDraw.Draw(marked).rectangle(rect,outline='#00ffff',width=3);marked.save(out/'lobby-reference'/(hero+'_face_roi.jpg'),quality=95)
 Image.open(native/(hero+'_body.png')).convert('RGB').save(out/'lobby-reference'/(hero+'_body.jpg'),quality=95)
(out/'lobby-reference/metrics.json').write_text(json.dumps(references,indent=2)+'\n')

def faceok(v):return 45<=v['L']<=65 and 10<=v['a']<=20 and 18<=v['b']<=30
summary={}
for key in ['before','after']:
 visible=[r[key]['face'] for r in main if 'L' in r[key]['face']];shirts=[r[key]['shirt'] for r in main if 'hueError' in r[key]['shirt']]
 summary[key]={'faceMeasured':len(visible),'faceNotVisible':len(main)-len(visible),'facePass':sum(faceok(v) for v in visible),'faceLRange':[min(v['L'] for v in visible),max(v['L'] for v in visible)],'faceARange':[min(v['a'] for v in visible),max(v['a'] for v in visible)],'faceBRange':[min(v['b'] for v in visible),max(v['b'] for v in visible)],'faceBelow35':sum(v['L']<35 for v in visible),'gameplayShots':len(game),'silhouettePass':sum(r[key]['silhouetteDeltaL']>=15 for r in game),'silhouetteMin':min(r[key]['silhouetteDeltaL'] for r in game),'shirtMeasured':len(shirts),'shirtPass':sum(v['L']>=25 and v['hueError']<=12 for v in shirts),'shirtHueMax':max(v['hueError'] for v in shirts),'shirtMinL':min(v['L'] for v in shirts)}
parity={}
for hero,ref in references.items():
 name=hero+'__tennis_resort__b_close' if hero.startswith('Match') else 'lookdev_resort__'+hero+'__b_close'
 r=lookup[name];parity[hero]={}
 for key in ['before','after']:
  v=r[key];parity[hero][key]={'faceDeltaL':round(abs(v['face']['L']-ref['faceLab'][0]),2),'shirtDeltaL':round(abs(v['shirt']['L']-ref['shirtLab'][0]),2)}
summary['lobbyParity']=parity
# Only the supplied baseline cases have independent before light inventories.
def inventory(p):
 return {line.split('\t')[0].replace('.mask.png',''):sorted(item.split(':')[0] for item in line.split('\t')[1].strip().split('|')) for line in p.read_text().splitlines()}
beforeinv=inventory(src.parent/'before/lights.tsv');afterinv=inventory(src/'lights.tsv');common=sorted(beforeinv.keys() & afterinv.keys());diff=[n for n in common if beforeinv[n]!=afterinv[n]]
summary['lights']={'independentBeforeCasesCompared':len(common),'changedInventories':diff,'maxActiveBefore':max(map(len,beforeinv.values())),'maxActiveAfterCommonCases':max(len(afterinv[n]) for n in common)}
xml=ET.parse(src.parent/'after-results.xml').getroot();summary['captureTests']={k:xml.attrib[k] for k in ['result','passed','failed','duration']}
summary['captureCount']=len(rows);summary['expectedCaptureCount']=344
summary['visualGate']='PASS' if len(rows)==344 and summary['after']['facePass']==summary['after']['faceMeasured'] and summary['after']['silhouettePass']==len(game) and summary['after']['shirtPass']==summary['after']['shirtMeasured'] and not diff and all(v['after']['faceDeltaL']<=8 and v['after']['shirtDeltaL']<=8 for v in parity.values()) and len(parity)==4 else 'FAIL'
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
with (out/'measurements.csv').open('w') as f:
 w=csv.writer(f, lineterminator="\n");w.writerow(['shot','before_face_L','after_face_L','before_face_a','after_face_a','before_face_b','after_face_b','before_edge_dL','after_edge_dL','before_shirt_L','after_shirt_L','before_shirt_hue_error','after_shirt_hue_error','face_gate','silhouette_gate','shirt_gate'])
 for r in rows:
  b,a=r['before'],r['after'];v=a['face'];w.writerow([r['shot'],b['face'].get('L'),v.get('L'),b['face'].get('a'),v.get('a'),b['face'].get('b'),v.get('b'),b['silhouetteDeltaL'],a['silhouetteDeltaL'],b['shirt'].get('L'),a['shirt'].get('L'),b['shirt'].get('hueError'),a['shirt'].get('hueError'),'N/A' if 'L' not in v else 'PASS' if faceok(v) else 'FAIL','N/A' if not r['shot'].endswith('__a_gameplay') else 'PASS' if a['silhouetteDeltaL']>=15 else 'FAIL','PASS' if a['shirt'].get('L',0)>=25 and a['shirt'].get('hueError',999)<=12 else 'FAIL'])
print(json.dumps(summary,indent=2))

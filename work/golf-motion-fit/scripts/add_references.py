from pathlib import Path
import json
W=Path(__file__).resolve().parents[1]
refs=[dict(id='rory',url='https://www.youtube.com/watch?v=BmRL2K-rz0Q',observedSeconds=[31,50,65,221,341,346]),dict(id='nelly',url='https://www.youtube.com/watch?v=o7RDyjPy89k',observedSeconds=[0,2,5,6]),dict(id='grip',url='https://www.titleist.com/videos/instruction/golf-grip-fundamentals',playbackURL='https://www.youtube.com/watch?v=FZoZMTbr1VA',observedSeconds=[1,71,90,130,181,230]),dict(id='chip',url='https://www.youtube.com/watch?v=8ZUZChc5S5M',observedSeconds=[110]),dict(id='putt',url='https://www.youtube.com/watch?v=JdVCci1G6oU',observedSeconds=[40,75,115])]
for sex in ['Male','Female']:
 p=W/f'export/golf_manifest_{sex}.json';doc=json.loads(p.read_text());doc['references']=refs;doc['referenceEvidence']='REFERENCE_EVIDENCE.md';doc['correctiveEncoding']={'fbx':'targets','sceneKit':'additive position and normal deltas'}
 for e in doc['clips']:
  family=e['motion'];source=['grip']
  if family in ['Drive','IronSwing','AddressDriver','AddressIron']:source+=['rory','nelly']
  if family in ['Chip','Pitch','AddressWedge']:source+=['chip']
  if family in ['Putt','AddressPutt']:source+=['putt']
  e['referenceIDs']=source;e['authoring']='editable hero-rig keyframes; explicit handedness; references are instruction evidence, not extracted motion capture'
 p.write_text(json.dumps(doc,indent=2)+'\n')
print('REFERENCE_METADATA_COMPLETE')

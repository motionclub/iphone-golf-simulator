from pathlib import Path
W=Path(__file__).resolve().parents[1];p=W/'candidate/GolfArcade/Unity/MatchHeroData.swift';s=p.read_text().replace('struct RigInfo: Decodable {','struct RigInfo: Decodable {\n        let golfWristRH: [[Float]]?, golfWristLH: [[Float]]?')
pos=s.index('    func coefficients(');s=s[:pos]+'''    func golfAnchors(left:Bool)->[SIMD3<Float>]? { guard let rows=left ? info.golfWristLH:info.golfWristRH,rows.count==2,rows.allSatisfy({$0.count==3}) else { return nil };return rows.map{SIMD3($0[0],$0[1],$0[2])} }
'''+s[pos:];p.write_text(s)
p=W/'candidate/GolfArcade/Unity/MatchHeroMotion.swift';s=p.read_text().replace('let target=(handle.simdTransform*SIMD4(anchor,1)).xyz','let point=handle.simdTransform*SIMD4(anchor,1);let target=SIMD3(point.x,point.y,point.z)');p.write_text(s)
p=W/'scripts/export_native.py';s=p.read_text().replace("sys.path.insert(0,str(R/'work/match-anim-set/scripts'));import kin","sys.path.insert(0,str(R/'work/match-anim-set/scripts'));sys.path.insert(0,str(W/'scripts'));import kin,motions")
s=s.replace("parts=rigparts,clips=clips)","parts=rigparts,clips=clips,golfWristRH=anchors['RH'],golfWristLH=anchors['LH'])")
pos=s.index('result=dict(version=3');s=s[:pos]+'''anchors={};grips=json.loads((W/f'data/grip_{sex}.json').read_text());baseClub=C4@np.array(club.matrix_world)@C4.T;reflection=np.diag([-1,1,1])
for hand in ['RH','LH']:
 rows=[]
 for side in ['L','R']:
  src=side if hand=='RH' else ('R' if side=='L' else 'L');anchor=np.array(grips[src]['anchor'])[:3,3]
  if hand=='LH':anchor=reflection@anchor
  world=baseClub@np.r_[C@anchor,1];rows.append(world[:3].tolist())
 anchors[hand]=rows
'''+s[pos:]
s=s.replace("dict(fps=120,names=e['correctiveTracks'],values=coeff.tolist())","dict(fps=120,names=e['correctiveTracks'],values=coeff.tolist(),trailRelease=[float(motions.controls(motions.definition(e['motion']),i/120,k.J['head_top'][2]/1.70465994)['release']) for i in range(e['frames'])])")
p.write_text(s)

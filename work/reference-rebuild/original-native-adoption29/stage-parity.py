from pathlib import Path
import json,difflib,hashlib,re
TASK=Path(__file__).resolve().parent;REPO=TASK.parents[2];shader=REPO/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader';surface=REPO/'GolfArcade/Unity/MatchHeroSurfaces.swift'
old=surface.read_text();needle='''            float3 lip=skinFinish<1.5 ? float3(0.99,0.83,0.80):float3(0.99,0.76,0.74);
            _surface.diffuse.rgb=heroTint.rgb*mix(float3(1.0),lip,masks.x)*mix(float3(1.0),float3(0.80,0.67,0.64),masks.y);'''
new='''            float lipPigment=masks.x, linePigment=masks.y;
            float3 lip=skinFinish<1.5 ? float3(0.99,0.83,0.80):float3(0.99,0.76,0.74);
            float3 line=float3(0.80,0.67,0.64);
            if(skinPigmentUV>1.5){
                // Exact SkinPigmentUV2 relative palette and mouth-only seam gain.
                lip=skinFinish<1.5 ? float3(0.95,0.68,0.69):float3(0.94,0.61,0.64);
                line=float3(0.62,0.44,0.42);
                linePigment=saturate(linePigment*mix(1.0,1.65,saturate(lipPigment*4.0)));
            }
            _surface.diffuse.rgb=heroTint.rgb*mix(float3(1.0),lip,lipPigment)*mix(float3(1.0),line,linePigment);'''
assert old.count(needle)==1,'Current native baseline drift: inspect before regenerating'
u=shader.read_text()
for token in ['half3(.95h,.68h,.69h)','half3(.94h,.61h,.64h)','half3(.62h,.44h,.42h)','linePigment*lerp(1.0h,1.65h,saturate(lipPigment*4.0h))']:
 assert token in u,'Unity palette drift: '+token
candidate=old.replace(needle,new);(TASK/'MatchHeroSurfaces.swift').write_text(candidate)
patch=''.join(difflib.unified_diff(old.splitlines(True),candidate.splitlines(True),fromfile='a/GolfArcade/Unity/MatchHeroSurfaces.swift',tofile='b/GolfArcade/Unity/MatchHeroSurfaces.swift'))
(TASK/'native-lip-palette.patch').write_text(patch)
test=REPO/'GolfArcadeTests/VisualOverhaulNativeTests.swift';before=test.read_text();assert before.count('XCTAssertEqual(look.skinPigmentUV, 1)')==1;after=before.replace('XCTAssertEqual(look.skinPigmentUV, 1)','XCTAssertEqual(look.skinPigmentUV, 2)');(TASK/'VisualOverhaulNativeTests.swift').write_text(after)
(TASK/'xctest-lip-mode2.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/GolfArcadeTests/VisualOverhaulNativeTests.swift',tofile='b/GolfArcadeTests/VisualOverhaulNativeTests.swift')))
test=REPO/'GolfArcadeTests/LockerMirrorTests.swift';before=test.read_text();assert before.count('XCTAssertEqual(sl.skinPigmentUV, 1)')==1;after=before.replace('XCTAssertEqual(sl.skinPigmentUV, 1)','XCTAssertEqual(sl.skinPigmentUV, 2)');(TASK/'LockerMirrorTests.swift').write_text(after)
with (TASK/'xctest-lip-mode2.patch').open('a') as f:f.write(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/GolfArcadeTests/LockerMirrorTests.swift',tofile='b/GolfArcadeTests/LockerMirrorTests.swift')))
contract=json.loads((TASK.parent/'original-native-adoption1/accepted-contract.json').read_text());contract['skinPigmentUV']=2;contract['counts']['Male']['Body']=33694;contract['count_proof']='export-split-proof.json';contract['source_files']={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in contract['source_files']};contract['frozen_face_source']='OriginalFaceFinish29Smooth1';contract['unity_palette_shader_sha256']=hashlib.sha256(shader.read_bytes()).hexdigest();(TASK/'accepted-contract.json').write_text(json.dumps(contract,indent=2)+'\n')
(TASK/'STAGED_GATE.json').write_text(json.dumps({'gate':'STAGED CPU CHECKS PENDING; NO PRODUCTION WRITES','unityPaletteShaderSha256':contract['unity_palette_shader_sha256'],'nativeBaselineSha256':hashlib.sha256(old.encode()).hexdigest(),'nativeCandidateSha256':hashlib.sha256(candidate.encode()).hexdigest(),'skinPigmentUV2Only':True,'mode0and1CoefficientsUnchanged':True,'sourceExportsOrGPUPerformed':False,'mode2Palette':{'male':[.95,.68,.69],'female':[.94,.61,.64],'line':[.62,.44,.42],'lineGain':1.65,'lipGateMultiplier':4},'nativeFillDefault':'Native preview consumers keep established lights; root removes optional fill experiment; Unity owns on-map presentation'},indent=2)+'\n')

from pathlib import Path
import json,difflib
root=Path(__file__).resolve().parents[3];out=Path(__file__).parent
base=json.loads((root/'work/reference-rebuild/face-finish29/actual-queue.json').read_text())[1]
base['env'].update({'VISUAL_CHARACTER_TWO_FRONT_ONLY':'1','VISUAL_CHARACTER_FULL_REVIEW':'0','VISUAL_CHARACTER_BLINK_REVIEW':'0','VISUAL_CHARACTER_BLINK_POSES':'','VISUAL_CHARACTER_NORMALS':'continuous','VISUAL_HERO_FILMIC':'1','VISUAL_CHARACTER_STAGE_LIGHT':'0'})
jobs=[]
for label,flag in [('control','0'),('satin','1')]:
 job=json.loads(json.dumps(base));job['name']='reference-face-material30-'+label
 job['env']['VISUAL_CHARACTER_SKIN_POLISH']=flag;job['env']['VISUAL_CHARACTER_OUT']=str(root/'proof/reference-rebuild'/('face-material30-'+label))
 jobs.append(job)
(out/'tiny-queue.json').write_text(json.dumps(jobs,indent=2))
old=(root/'work/reference-rebuild/original-native-adoption29/NativeParity.swift').read_text()
a='        light(1100,target-r*2+u*3+f*3);light(350,target+r*3+u*1+f*2);light(300,.zero,true)'
b='''        if ProcessInfo.processInfo.environment["NATIVE_PROOF_LOBBY_LIGHT"] == "1" {
            // Exact CharacterModelPreview.Coordinator light recipe, not a new lobby look.
            func stageLight(_ intensity:CGFloat,_ colour:NSColor,_ elevation:Float,_ azimuth:Float,_ shadow:Bool=false) {
                let node=SCNNode(),l=SCNLight();l.type = .directional;l.intensity=intensity;l.color=colour
                if shadow {l.castsShadow=true;l.shadowRadius=6;l.shadowSampleCount=8;l.shadowMode = .deferred;l.shadowColor=NSColor(red:0.12,green:0.14,blue:0.24,alpha:0.35);l.orthographicScale=2.2}
                node.light=l;let e=elevation*Float.pi/180,a=azimuth*Float.pi/180
                node.position=SCNVector3(-sin(a)*cos(e)*6,sin(e)*6,cos(a)*cos(e)*6)
                node.look(at:SCNVector3(0,0.8,0));scene.rootNode.addChildNode(node)
            }
            stageLight(1050,NSColor(red:1,green:0.92,blue:0.82,alpha:1),40,38,true)
            stageLight(370,NSColor(red:0.84,green:0.9,blue:1,alpha:1),18,-55)
            stageLight(520,NSColor(red:1,green:0.96,blue:0.9,alpha:1),35,160)
            let amb=SCNNode();amb.light=SCNLight();amb.light!.type = .ambient;amb.light!.intensity=210
            amb.light!.color=NSColor(red:0.86,green:0.88,blue:0.96,alpha:1);scene.rootNode.addChildNode(amb)
        } else {
            light(1100,target-r*2+u*3+f*3);light(350,target+r*3+u*1+f*2);light(300,.zero,true)
        }'''
assert a in old
new=old.replace(a,b);(out/'NativeParity.swift').write_text(new)
(out/'native-lobby-proof.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='work/reference-rebuild/original-native-adoption29/NativeParity.swift',tofile='work/reference-rebuild/original-native-adoption29/NativeParity.swift')))

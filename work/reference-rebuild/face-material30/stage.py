from pathlib import Path
import difflib,json,hashlib
root=Path(__file__).resolve().parents[3]; out=Path(__file__).parent

def stage(rel, transform):
 old=(root/rel).read_text();new=transform(old)
 assert old!=new,rel
 p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(new)
 patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel,tofile=rel))
 (out/(Path(rel).name+'.patch')).write_text(patch)
 return {'file':rel,'baseSha256':hashlib.sha256(old.encode()).hexdigest(),'candidateSha256':hashlib.sha256(new.encode()).hexdigest()}
files=[]
files.append(stage('Unity/Assets/Resources/Tennis/Shaders/HeroLighting.hlsl',lambda s:s.replace('half _HeroPresentationFill;','half _HeroPresentationFill;\nhalf _HeroSkinPolish;').replace('    half broad = pow(nh, 18 + smoothness * 18) * .075h;','''    half broad = pow(nh, 18 + smoothness * 18) * .075h;
    if (_HeroSkinPolish > .5h) {
        // Satin skin: a wide soft reflection with a restrained central sheen.
        // Diffuse/pigment and geometric normals remain the accepted source.
        broad = pow(nh, 12 + smoothness * 12) * .13h;
        broad += pow(nh, 48 + smoothness * 60) * .018h;
    }''')))
files.append(stage('Unity/Assets/Scripts/Tennis/HeroLightingProfile.cs',lambda s:s.replace('        static void Presentation()\n        {','        static void Presentation()\n        {\n            Shader.SetGlobalFloat("_HeroSkinPolish", System.Environment.GetEnvironmentVariable("VISUAL_CHARACTER_SKIN_POLISH")=="1" ? 1f : 0f);')))
files.append(stage('Unity/Assets/Scripts/Tennis/HeroOriginalSeamAnatomy.cs',lambda s:s.replace('                material.SetFloat("_SpecularStrength", iris ? .70f : .45f);','''                bool polish = Environment.GetEnvironmentVariable("VISUAL_CHARACTER_SKIN_POLISH") == "1";
                material.SetFloat("_SpecularStrength", polish ? (iris ? .85f : .52f) : (iris ? .70f : .45f));''')))
files.append(stage('GolfArcade/Unity/MatchHeroSurfaces.swift',lambda s:s.replace('        mat.name = sub.material   //',"""        if ProcessInfo.processInfo.environment["VISUAL_CHARACTER_SKIN_POLISH"] == "1", let look=sub.look, look.anatomicalFace == true,
           sub.material.contains("Iris") || sub.material.contains("Sclera") {
            let spec:Float=sub.material.contains("Iris") ? 0.85:0.52
            mat.setValue(SCNVector4(look.wrap,look.smoothness,spec,look.saturation),forKey:"athleteSurface")
        }
        mat.name = sub.material   //""").replace('        m.setValue(look.skinFinish ?? 0,forKey:"skinFinish")','        m.setValue(look.skinFinish ?? 0,forKey:"skinFinish")\n        m.setValue(ProcessInfo.processInfo.environment["VISUAL_CHARACTER_SKIN_POLISH"] == "1" ? Float(1):Float(0),forKey:"skinPolish")').replace('    float skinFinish;','    float skinFinish;\n    float skinPolish;').replace('        spec=pow(nh,18.0+smoothness*18.0)*0.075*0.95*smoothstep(-0.06,0.24,nl);',"""        float skinLobe=pow(nh,18.0+smoothness*18.0)*0.075;
        if(skinPolish>0.5) skinLobe=pow(nh,12.0+smoothness*12.0)*0.13+pow(nh,48.0+smoothness*60.0)*0.018;
        spec=skinLobe*0.95*smoothstep(-0.06,0.24,nl);""")))
(out/'source-contract.json').write_text(json.dumps(files,indent=2))
(out/'material.patch').write_text(''.join((out/(Path(x['file']).name+'.patch')).read_text() for x in files))

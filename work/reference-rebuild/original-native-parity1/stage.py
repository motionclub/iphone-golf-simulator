from pathlib import Path
import difflib,json,hashlib
out=Path('work/reference-rebuild/original-native-parity1'); records={}
def save(path,fn):
 old=Path(path).read_text();new=fn(old);assert new!=old,path
 name=Path(path).name;(out/(name+'.baseline')).write_text(old);(out/name).write_text(new)
 (out/(name+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=path,tofile=path)))
 records[path]={'base_sha256':hashlib.sha256(old.encode()).hexdigest(),'candidate_sha256':hashlib.sha256(new.encode()).hexdigest()}
def export(s):
 s=s.replace('public float specularStrength, environmentStrength, metallic, craftedPaint;', 'public float specularStrength, environmentStrength, metallic, craftedPaint, skinFinish, skinPigmentUV;\n            public bool anatomicalFace, baseMapLinear;')
 s=s.replace('look = ReadLook(mat, copiedMaps, golf)', 'look = ReadLook(mat, copiedMaps, golf, p.kind == "face" && p.skinned)')
 s=s.replace('if (p.kind == "kit")\n                    {', 'if (p.kind == "kit" || ((p.kind == "body" || p.kind == "face") && p.mesh.uv.Length == p.pos.Length))\n                    {')
 s=s.replace('else if (p.kind == "body")\n                    {','if (p.kind == "body")\n                    {')
 s=s.replace('static Look ReadLook(Material m, SortedSet<string> maps, bool golf)','static Look ReadLook(Material m, SortedSet<string> maps, bool golf, bool anatomicalFace)')
 s=s.replace('if (string.IsNullOrEmpty(path)) return "";   // a built-in default (the shader\'s "bump" / "white"), nothing to ship', '''if (string.IsNullOrEmpty(path)) {
                    // Eye13 and relative pigment are runtime, linear multiplier LUTs.
                    // Built-in white/bump defaults still have nothing to ship.
                    if (!(tex is Texture2D generated) || !tex.name.StartsWith("Original")) return "";
                    string cache = Path.Combine(OutDir, ".generated-maps"); Directory.CreateDirectory(cache);
                    path = Path.Combine(cache, generated.name + ".png");
                    File.WriteAllBytes(path, generated.EncodeToPNG());
                    if (n == "_BaseMap") look.baseMapLinear = true;
                }''')
 s=s.replace('look.craftedPaint=F("_CraftedPaint");','look.anatomicalFace=anatomicalFace; look.skinFinish=F("_SkinFinish"); look.skinPigmentUV=F("_SkinPigmentUV");\n            look.craftedPaint=F("_CraftedPaint");')
 old='''            var face = root.GetComponentsInChildren<MeshRenderer>(true).First(r => r.name.StartsWith("Face_"));
            list.Add(new PartSource { name = "Face", kind = "face", mesh = face.GetComponent<MeshFilter>().sharedMesh, renderer = face, materials = face.sharedMaterials });'''
 new='''            var face = root.GetComponent<MatchHeroLook>().face;
            if (!face || !face.enabled) throw new InvalidOperationException("Active match face renderer missing");
            var skinnedFace = face as SkinnedMeshRenderer;
            var faceMesh = skinnedFace ? skinnedFace.sharedMesh : face.GetComponent<MeshFilter>()?.sharedMesh;
            if (!faceMesh) throw new InvalidOperationException("Active match face mesh missing");
            list.Add(new PartSource { name = "Face", kind = "face", mesh = faceMesh, renderer = face, skinned = skinnedFace, materials = face.sharedMaterials });'''
 assert old in s;s=s.replace(old,new)
 return s
save('Unity/Assets/Editor/MatchHeroLockerExport.cs',export)
def data(s):
 s=s.replace('let fabricVersion: Float?', 'let fabricVersion: Float?\n        let skinFinish: Float?, skinPigmentUV: Float?\n        let anatomicalFace: Bool?, baseMapLinear: Bool?')
 start=s.index('    static func texcoordSources(');end=s.index('\n    // MARK: the hero node',start)
 s=s[:start]+'''    static func texcoordSources(_ part: Part, bin: Data) -> [SCNGeometrySource]? {
        var result: [SCNGeometrySource] = []
        if let uv = part.uvOffset, uv >= 0, uv + part.vertexCount * 8 <= bin.count {
            result.append(SCNGeometrySource(data: bin.subdata(in: uv ..< uv + part.vertexCount * 8), semantic: .texcoord, vectorCount: part.vertexCount,
                                           usesFloatComponents: true, componentsPerVector: 2, bytesPerComponent: 4, dataOffset: 0, dataStride: 8))
        }
        if let bp = part.bindPositionOffset, bp >= 0, bp + part.vertexCount * 12 <= bin.count {
            // Legacy body: bind xy/z in channels 0/1. OriginalSeam: UV0,
            // then bind xy/z in channels 1/2. Preserve both semantic fields.
            var d = bin.subdata(in: bp ..< bp + part.vertexCount * 12); d.append(contentsOf: [0, 0, 0, 0])
            result += [SCNGeometrySource(data: d, semantic: .texcoord, vectorCount: part.vertexCount, usesFloatComponents: true, componentsPerVector: 2, bytesPerComponent: 4, dataOffset: 0, dataStride: 12),
                       SCNGeometrySource(data: d, semantic: .texcoord, vectorCount: part.vertexCount, usesFloatComponents: true, componentsPerVector: 2, bytesPerComponent: 4, dataOffset: 8, dataStride: 12)]
        }
        return result.isEmpty ? nil : result
    }
''' +s[end:]
 s=s.replace('part.morphTargets[shape].name == "Hero_Blink"', 'part.morphTargets[shape].name?.hasPrefix("Hero_Blink") == true')
 return s
save('GolfArcade/Unity/MatchHeroData.swift',data)
def surface(s):
 s=s.replace('configurePaint(mat, role: sub.material, crafted: sub.look?.craftedPaint ?? 0)', 'if sub.look?.anatomicalFace != true { configurePaint(mat, role: sub.material, crafted: sub.look?.craftedPaint ?? 0) }')
 at='''        // Same broad skin / varnished eye-frame lobes as HeroCharacterShade'''
 pos=s.index(at)
 s=s[:pos]+'''        // Exported relative LUTs multiply the selected tint; never bake a skin preset.
        m.setValue(SCNVector4(srgbToLinear(tint.x),srgbToLinear(tint.y),srgbToLinear(tint.z),1),forKey:"heroTint")
        if !look.baseMap.isEmpty, let map=image(look.baseMap,linear:look.baseMapLinear ?? false) {
            m.diffuse.contents=map; m.diffuse.wrapS = .clamp; m.diffuse.wrapT = .clamp
            m.multiply.contents=flatColour(tint)
        }
        m.setValue(look.skinFinish ?? 0,forKey:"skinFinish")
        m.setValue(look.skinPigmentUV ?? 0,forKey:"skinPigmentUV")
        m.setValue((look.skinPigmentUV ?? 0)>0.5 ? Float(1):Float(0),forKey:"skinBindChannel")
''' +s[pos:]
 s=s.replace('''        m.shaderModifiers = [.lightingModel: athleteLighting]''','''        m.shaderModifiers = [.lightingModel: athleteLighting]''')
 # Replace full-only Body blink with two-stage Body + Face, bypass legacy overlays when face has native morphs.
 start=s.index('        if let body=root.childNode(withName:"Body"');end=s.index('        guard let node=root.childNode(withName:"Face"',start)
 s=s[:start]+'''        let b=max(0,min(1,blink))
        var anatomicalFace=false
        for partName in ["Body","Face"] {
            guard let node=root.childNode(withName:partName,recursively:true),let morpher=node.morpher,
                  let full=morpher.targets.firstIndex(where:{$0.name=="Hero_Blink"}) else { continue }
            let half=morpher.targets.firstIndex(where:{$0.name=="Hero_Blink_Half"})
            if let half { morpher.setWeight(CGFloat(max(0,1-abs(2*b-1))),forTargetAt:half) }
            morpher.setWeight(CGFloat(half == nil ? b:max(0,2*b-1)),forTargetAt:full)
            if partName == "Face" { anatomicalFace=true }
        }
        // OriginalSeam's source targets already close/recess the eyes. Unity
        // also bypasses gaze, brow lift and the legacy fragment closure stack.
        if anatomicalFace { return }
''' +s[end:]
 s=s.replace('''    #pragma varyings
    float3 bindPos;
    #pragma body
    out.bindPos = float3(_geometry.texcoords[0].x, _geometry.texcoords[0].y, _geometry.texcoords[1].x);''','''    #pragma arguments
    float skinBindChannel;
    #pragma varyings
    float3 bindPos;
    #pragma body
    out.bindPos = skinBindChannel>0.5 ? float3(_geometry.texcoords[1].x, _geometry.texcoords[1].y, _geometry.texcoords[2].x) : float3(_geometry.texcoords[0].x, _geometry.texcoords[0].y, _geometry.texcoords[1].x);''')
 # Accepted regional skin response on existing bind frame.
 s=s.replace('''    float4 athleteSurface;
    """\n    static let headSurfaceBody''','''    float4 athleteSurface;
    float4 heroTint;
    float skinFinish,skinPigmentUV;
    """\n    static let headSurfaceBody''')
 old='''    _surface.diffuse.rgb*=float3(1.0+0.025*warmth,1.0-0.060*warmth,1.0-0.025*warmth)*(1.0+0.012*forehead);
    _surface.shininess=saturate(athleteSurface.y+0.08*nose+0.06*forehead-0.025*cheeks);'''
 new='''    if(skinFinish>0.5){
        if(skinPigmentUV>0.5){
            float2 masks=saturate((_surface.diffuseTexcoord*64.0-0.5)/63.0);
            float3 lip=skinFinish<1.5 ? float3(0.99,0.83,0.80):float3(0.99,0.76,0.74);
            _surface.diffuse.rgb=heroTint.rgb*mix(float3(1.0),lip,masks.x)*mix(float3(1.0),float3(0.80,0.67,0.64),masks.y);
        }
        _surface.diffuse.rgb*=mix(float3(1.0),float3(1.012,0.965,0.955),warmth);
        if(skinFinish<1.5){
            q=(hp-float3(0.0,-0.126,-0.010))/float3(0.086,0.048,0.095);float jaw=exp(-2.0*dot(q,q));
            q=(hp-float3(0.0,-0.077,0.016))/float3(0.048,0.016,0.060);float upperLip=exp(-2.0*dot(q,q));
            _surface.diffuse.rgb*=mix(float3(1.0),float3(0.88,0.91,0.94),saturate(jaw*0.42+upperLip*0.20));
        }
        _surface.shininess=mix(0.32,0.40,saturate(nose+forehead*0.55));
        float lum=dot(_surface.diffuse.rgb,float3(0.2126,0.7152,0.0722));
        _surface.diffuse.rgb=mix(float3(lum),_surface.diffuse.rgb,athleteSurface.w);
    }else{
        _surface.diffuse.rgb*=float3(1.0+0.025*warmth,1.0-0.060*warmth,1.0-0.025*warmth)*(1.0+0.012*forehead);
        _surface.shininess=saturate(athleteSurface.y+0.08*nose+0.06*forehead-0.025*cheeks);
    }'''
 assert old in s;s=s.replace(old,new)
 # Preserve generic shader; branch accepted lobe only on marked Body.
 s=s.replace('''    float4 headOrigin;
    #pragma body
    float3 n''','''    float4 headOrigin;
    float skinFinish;
    #pragma body
    float3 n''')
 old='''    _lightingContribution.diffuse += _light.intensity.rgb*(float3(wrapped)+athleteWarmth.rgb*edge);
    _lightingContribution.specular += _light.intensity.rgb*(float3(spec)+rim*(float3(0.35)+0.65*_surface.diffuse.rgb));'''
 new='''    if(skinFinish>0.5){
        wrapped=saturate((nl+0.28)/1.28);
        edge=saturate(wrapped-saturate(nl));
        spec=pow(nh,18.0+smoothness*18.0)*0.075*0.95*smoothstep(-0.06,0.24,nl);
        _lightingContribution.diffuse += _light.intensity.rgb*(float3(wrapped*0.84)+athleteWarmth.rgb*edge);
        _lightingContribution.specular += _light.intensity.rgb*(float3(spec)+rim*0.45*(float3(0.35)+0.65*_surface.diffuse.rgb));
    }else{
        _lightingContribution.diffuse += _light.intensity.rgb*(float3(wrapped)+athleteWarmth.rgb*edge);
        _lightingContribution.specular += _light.intensity.rgb*(float3(spec)+rim*(float3(0.35)+0.65*_surface.diffuse.rgb));
    }'''
 assert old in s;s=s.replace(old,new)
 return s
save('GolfArcade/Unity/MatchHeroSurfaces.swift',surface)
(out/'source-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))

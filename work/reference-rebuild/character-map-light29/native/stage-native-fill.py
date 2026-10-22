import pathlib,difflib,json,hashlib
R=pathlib.Path.cwd();O=R/'work/reference-rebuild/character-map-light29/native';p=R/'GolfArcade/Unity/MatchHeroSurfaces.swift';base=p.read_text()
helper='''    /// Optional camera-side reflector, once per fragment, after authored surface
    /// maps/normals and before the existing native scene lighting/cloth shoulder.
    /// Surface emission carries this computed direct-light contribution exactly once;
    /// never insert it in a lighting modifier, which SceneKit runs per scene light.
    static var presentationFill: Float = ProcessInfo.processInfo.environment["VISUAL_CHARACTER_STAGE_LIGHT"] == "1" ? 0.65 : 0

    private static func configurePresentationFill(_ material: SCNMaterial, look: MatchHeroData.Look) {
        guard presentationFill > 0, look.isCharacter || look.isCloth else { return }
        var modifiers = material.shaderModifiers ?? [:]
        let original = modifiers[.surface] ?? "#pragma arguments\\n#pragma body\\n"
        // Idempotent if the same material is configured again.
        guard !original.contains("heroPresentationFill") else { return }
        material.setValue(min(presentationFill, 0.65), forKey: "heroPresentationFill")
        let arguments = "float heroPresentationFill;\\n"
        modifiers[.surface] = original.replacingOccurrences(of: "#pragma arguments", with: "#pragma arguments\\n" + arguments) + "\\n" + presentationDirection + (look.isCharacter ? presentationCharacter : presentationCloth(look))
        material.shaderModifiers = modifiers
    }
    static let presentationDirection = """
    float3 hpN = normalize(_surface.normal), hpV = normalize(_surface.view);
    float3 hpUp = normalize((scn_frame.viewTransform * float4(0,1,0,0)).xyz);
    float3 hpRight = cross(hpUp,hpV);
    hpRight *= rsqrt(max(dot(hpRight,hpRight),1e-8));
    float3 hpL = normalize(hpV*0.80 + hpUp*0.60 - hpRight*0.30);
    float3 hpColor = float3(1,0.95,0.88)*heroPresentationFill;
    float hpNL = dot(hpN,hpL), hpNH = saturate(dot(hpN,normalize(hpL+hpV)));
    """
    static let presentationCharacter = """
    float hpSmooth = headOrigin.w>0.5 ? _surface.shininess : athleteSurface.y;
    float hpWrap = skinFinish>0.5 ? 0.28 : athleteSurface.x;
    float hpWrapped = saturate((hpNL+hpWrap)/(1.0+hpWrap));
    float hpEdge = saturate(hpWrapped-saturate(hpNL));
    float hpSpec;
    if(skinFinish>0.5){
        hpSpec = pow(hpNH,18.0+hpSmooth*18.0)*0.075*0.95*smoothstep(-0.06,0.24,hpNL);
        _surface.emission.rgb += hpColor*(_surface.diffuse.rgb*(hpWrapped*0.84+athleteWarmth.rgb*hpEdge)+float3(hpSpec));
    }else{
        float hpFresnel = 1.0+pow(1.0-saturate(dot(hpV,normalize(hpL+hpV))),5.0)*1.5;
        hpSpec = (pow(hpNH,10.0+hpSmooth*30.0)*0.045+pow(hpNH,24.0+hpSmooth*hpSmooth*200.0)*hpSmooth*0.25)*athleteSurface.z*hpFresnel*saturate(hpNL*3.0);
        _surface.emission.rgb += hpColor*(_surface.diffuse.rgb*(hpWrapped+athleteWarmth.rgb*hpEdge*1.35)+float3(hpSpec));
    }
    """
    private static func presentationCloth(_ look: MatchHeroData.Look) -> String {
        // Reuse the actual native kit response; only substitute the synthetic
        // direction/intensity and collect the result outside the per-light stage.
        let lighting = (look.useGarmentMaps ?? 0)>0.5 ? ((look.fabricVersion ?? 1)>1.5 ? garmentLightingV2 : garmentLighting) : clothLighting
        let body = String(lighting.components(separatedBy: "#pragma body").last ?? "")
            .replacingOccurrences(of: "_light.direction", with: "hpL")
            .replacingOccurrences(of: "_light.intensity.rgb", with: "hpColor")
            .replacingOccurrences(of: "_lightingContribution.diffuse", with: "hpDiffuse")
            .replacingOccurrences(of: "_lightingContribution.specular", with: "hpSpecular")
        return "{\\nfloat3 hpDiffuse=float3(0),hpSpecular=float3(0);\\n" + body + "\\n_surface.emission.rgb += hpDiffuse*_surface.diffuse.rgb+hpSpecular;\\n}\\n"
    }

'''
needle='        mat.name = sub.material';assert base.count(needle)==1
new=base.replace(needle,'        if let look = sub.look { configurePresentationFill(mat, look: look) }\n'+needle)
needle='    // ---- TennisCharacter: skin, eyes, face decals, racket frame and strings';assert new.count(needle)==1
new=new.replace(needle,helper+needle)
(O/'MatchHeroSurfaces.swift').write_text(new);(O/'MatchHeroSurfaces.swift.baseline').write_text(base)
(O/'native-character-presentation-fill.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),new.splitlines(True),fromfile='a/GolfArcade/Unity/MatchHeroSurfaces.swift',tofile='b/GolfArcade/Unity/MatchHeroSurfaces.swift')))
(O/'SOURCE_GATE.json').write_text(json.dumps({'gate':'STAGED OPTIONAL; SWIFT PARSE AND ACTUAL METAL/ART PENDING','productionSourceSha256':hashlib.sha256(base.encode()).hexdigest(),'candidateSha256':hashlib.sha256(new.encode()).hexdigest(),'enabledBy':'VISUAL_CHARACTER_STAGE_LIGHT=1, sampled when material is created','fillStrength':.65,'fillColorLinear':[1,.95,.88],'sceneLightOrCameraEdits':0,'addedSceneLightSlots':0,'affectedRoles':['TennisCharacter','TennisCloth'],'perLightModifierChanges':0,'surfaceFillAddedOnce':True,'disabledPathExistingStringsExact':True,'nativeActualRequired':['SceneKit generated Metal compile','existing-light vs fill comparison in native locker/course portrait','original eye reflections and white kit headroom','camera tilt and vertical view degeneracy']},indent=2)+'\n')

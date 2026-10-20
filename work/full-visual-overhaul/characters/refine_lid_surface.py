from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
p=r/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader';s=p.read_text().replace('if (_FaceRole > 1.5h) clip(.5h - lid);\n                    else c.rgb = lerp(c.rgb, _FaceSkin.rgb, lid);','c.rgb = lerp(c.rgb, _FaceSkin.rgb, lid);').replace('half surfaceSpecular = lerp(_SpecularStrength, .8h, lid);','half surfaceSpecular = lerp(_SpecularStrength, .8h, lid);\n                half surfaceWrap = lerp(_Wrap, .32h, lid);').replace('c.rgb, _Wrap, surfaceSmoothness','c.rgb, surfaceWrap, surfaceSmoothness')
p.write_text(s)
p=r/'GolfArcade/Unity/MatchHeroSurfaces.swift';s=p.read_text();s=s.replace('modifiers[.surface]=faceSurface;material.shaderModifiers=modifiers','modifiers[.surface]=faceSurface;modifiers[.lightingModel]=faceAthleteLighting;material.shaderModifiers=modifiers')
s=s.replace('''        if(role>1.5){if(lid>0.5)discard_fragment();}
        else {
            _surface.diffuse.rgb=mix(_surface.diffuse.rgb,faceSkin.rgb,lid);
            _surface.specular.rgb*=1.0-lid*0.85;
        }''','''        _surface.diffuse.rgb=mix(_surface.diffuse.rgb,faceSkin.rgb,lid);''')
a=s.index('\n    // ----',s.index('static let faceSurface'))
s=s[:a]+'''
    static var faceAthleteLighting: String {
        athleteLighting.replacingOccurrences(of: "float3 n = normalize", with: """
        float lid=0.0;
        if(in.eyeLidData.y>0.5 && in.eyeLidData.y<2.5 && in.eyeLidData.z>0.001){
            float upper=mix(1.0,-0.12,in.eyeLidData.z),lower=mix(-1.0,-0.12,in.eyeLidData.z);
            lid=max(smoothstep(upper-0.025,upper+0.025,in.eyeLidData.x),1.0-smoothstep(lower-0.025,lower+0.025,in.eyeLidData.x));
            if(in.eyeLidData.z>0.995)lid=1.0;
        }
        float4 lidSurface=athleteSurface;
        lidSurface.x=mix(lidSurface.x,0.32,lid);
        lidSurface.y=mix(lidSurface.y,0.28,lid);
        lidSurface.z=mix(lidSurface.z,0.8,lid);
        float3 n = normalize
        """).replacingOccurrences(of:"athleteSurface.x",with:"lidSurface.x").replacingOccurrences(of:"athleteSurface.y",with:"lidSurface.y").replacingOccurrences(of:"athleteSurface.z",with:"lidSurface.z")
    }
''' + s[a:]
p.write_text(s)

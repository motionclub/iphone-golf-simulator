from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
p=r/'GolfArcade/Unity/MatchHeroSurfaces.swift';s=p.read_text()
s=s.replace('modifiers[.geometry]=faceGeometry;material.shaderModifiers=modifiers','modifiers[.geometry]=faceGeometry;modifiers[.surface]=faceSurface;material.shaderModifiers=modifiers')
s=s.replace('let left=(lo[0]+hi[0])*0.5,right=(lo[1]+hi[1])*0.5','let left=(lo[0]+hi[0])*0.5,right=(lo[1]+hi[1])*0.5\n        let skin=root.childNode(withName:"Body",recursively:true)?.geometry?.materials.first.flatMap { made($0)?.colour } ?? SIMD3<Float>(0.76,0.48,0.3)\n        let skinLinear=SIMD3(srgbToLinear(skin.x),srgbToLinear(skin.y),srgbToLinear(skin.z))')
s=s.replace('SCNVector4(left.x,left.y,left.z,0)', 'SCNVector4(left.x,left.y,left.z,(hi[0].y-lo[0].y)*0.5)').replace('SCNVector4(right.x,right.y,right.z,0)', 'SCNVector4(right.x,right.y,right.z,(hi[1].y-lo[1].y)*0.5)')
s=s.replace('forKey:"faceEyeR")\n        }','forKey:"faceEyeR")\n            material.setValue(SCNVector4(skinLinear.x,skinLinear.y,skinLinear.z,1),forKey:"faceSkin")\n        }')
a=s.index('    static let faceGeometry = """');b=s.index('\n    // ----',a)
s=s[:a]+'''    static let faceGeometry = """
    #pragma arguments
    float4 faceEyeL;
    float4 faceEyeR;
    float4 faceUp;
    float4 faceRight;
    float4 facePaint;
    float4 facePerformance;
    #pragma varyings
    float3 eyeLidData;
    #pragma body
    float3 facePos=_geometry.position.xyz;
    out.eyeLidData=float3(0.0,facePaint.x,facePaint.z);
    if(facePaint.x>0.5){
        float4 eye=dot(facePos-(faceEyeL.xyz+faceEyeR.xyz)*0.5,faceRight.xyz)<0.0 ? faceEyeL:faceEyeR;
        if(facePaint.x<3.5){
            if(facePaint.x>1.5 && facePaint.x<2.5)facePos+=(faceRight.xyz*facePerformance.x+faceUp.xyz*facePerformance.y)*(1.0-facePaint.z);
            float height=dot(facePos-eye.xyz,faceUp.xyz);
            out.eyeLidData.x=height/max(eye.w,0.0001);
            if(facePaint.x>2.5)facePos-=faceUp.xyz*(height+0.12*eye.w)*facePaint.z;
        }else facePos+=faceUp.xyz*facePaint.w;
    }
    facePos+=_geometry.normal.xyz*facePaint.y;
    _geometry.position.xyz=facePos;
    """
    static let faceSurface = """
    #pragma arguments
    float4 faceSkin;
    #pragma body
    float role=in.eyeLidData.y, blink=in.eyeLidData.z;
    if(role>0.5 && role<2.5 && blink>0.001){
        float upper=mix(1.0,-0.12,blink),lower=mix(-1.0,-0.12,blink);
        float lid=max(smoothstep(upper-0.025,upper+0.025,in.eyeLidData.x),1.0-smoothstep(lower-0.025,lower+0.025,in.eyeLidData.x));
        if(blink>0.995)lid=1.0;
        if(role>1.5){if(lid>0.5)discard_fragment();}
        else {
            _surface.diffuse.rgb=mix(_surface.diffuse.rgb,faceSkin.rgb,lid);
            _surface.specular.rgb*=1.0-lid*0.85;
        }
    }
    """
''' + s[b:]
p.write_text(s)

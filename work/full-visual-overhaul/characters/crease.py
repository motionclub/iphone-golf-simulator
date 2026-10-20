from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
p=r/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader';s=p.read_text().replace('[HideInInspector] _FaceSkin', '[HideInInspector] _EyeNL ("Left closure normal and width", Vector) = (0,0,1,.03)\n        [HideInInspector] _EyeNR ("Right closure normal and width", Vector) = (0,0,1,.03)\n        [HideInInspector] _FaceSkin')
s=s.replace('_Gaze, _FaceSkin;', '_Gaze, _FaceSkin, _EyeNL, _EyeNR;').replace('float eyeHeight : TEXCOORD7;', 'float2 eyeCoord : TEXCOORD7;')
s=s.replace('o.eyeHeight = 0;', 'o.eyeCoord = 0;\n                float3 faceNormal = i.normalOS;')
s=s.replace('if (_FaceRole < 3.5h) {','if (_FaceRole < 3.5h) {\n                        float4 closeNormal = dot(facePos - (_EyeL.xyz + _EyeR.xyz) * .5, _FaceRight.xyz) < 0 ? _EyeNL : _EyeNR;')
s=s.replace('o.eyeHeight = h / max(eye.w, .0001);\n                        if (_FaceRole > 2.5h) facePos -= _FaceUp.xyz * (h + .12 * eye.w) * _Blink;','o.eyeCoord = float2(dot(facePos - eye.xyz, _FaceRight.xyz) / max(closeNormal.w,.0001), h / max(eye.w, .0001));\n                        faceNormal = normalize(lerp(i.normalOS, closeNormal.xyz, _Blink));')
s=s.replace('GetVertexNormalInputs(i.normalOS, i.tangentOS)', 'GetVertexNormalInputs(faceNormal, i.tangentOS)')
s=s.replace('i.eyeHeight', 'i.eyeCoord.y').replace('_FaceRole < 2.5h && _Blink', '_FaceRole < 3.5h && _Blink')
s=s.replace('c.rgb = lerp(c.rgb, _FaceSkin.rgb, lid);', '''if (_FaceRole > 2.5h) lid = _Blink;
                    c.rgb = lerp(c.rgb, _FaceSkin.rgb, lid);
                    if (_FaceRole < 2.5h) {
                        half creaseY = -.12h + .35h * i.eyeCoord.x * i.eyeCoord.x;
                        half crease = (1 - smoothstep(.018h,.045h,abs(i.eyeCoord.y - creaseY))) * (1 - smoothstep(.78h,.98h,abs(i.eyeCoord.x))) * smoothstep(.72h,1,_Blink);
                        c.rgb *= 1 - crease * .45h;
                    }''')
p.write_text(s)
p=r/'Unity/Assets/Scripts/Tennis/MatchHeroLook.cs';s=p.read_text().replace('name.Contains("LidLine")', '(name.Contains("LidLine") || name.Contains("LidLower"))')
s=s.replace('var mesh = filter.sharedMesh; var vertices = mesh.vertices;', 'var mesh = filter.sharedMesh; var vertices = mesh.vertices; var normals = mesh.normals; var eyeNormals = new Vector3[2]; var eyeCounts = new int[2];')
s=s.replace('int side = Vector3.Dot(vertices[i] - mid, right) < 0 ? 0 : 1;', 'int side = Vector3.Dot(vertices[i] - mid, right) < 0 ? 0 : 1;\n                    eyeNormals[side] += normals[i]; eyeCounts[side]++;')
s=s.replace('m.SetVector("_FaceUp", up);', 'm.SetVector("_EyeNL", new Vector4(eyeNormals[0].normalized.x,eyeNormals[0].normalized.y,eyeNormals[0].normalized.z,bounds[0].size.x*.5f));\n                m.SetVector("_EyeNR", new Vector4(eyeNormals[1].normalized.x,eyeNormals[1].normalized.y,eyeNormals[1].normalized.z,bounds[1].size.x*.5f));\n                m.SetVector("_FaceUp", up);')
p.write_text(s)
p=r/'GolfArcade/Unity/MatchHeroSurfaces.swift';s=p.read_text().replace('role.contains("LidLine")', '(role.contains("LidLine") || role.contains("LidLower"))')
s=s.replace('let vertices=geometry.sources(for:.vertex).first else{return}', 'let vertices=geometry.sources(for:.vertex).first,let normals=geometry.sources(for:.normal).first else{return}')
s=s.replace('var hi=lo.map {-$0};var found=[false,false]', 'var hi=lo.map {-$0};var found=[false,false];var eyeNormals=[SIMD3<Float>.zero,SIMD3<Float>.zero]')
s=s.replace('let v=vertex(i),side=v.x<0 ? 0:1;lo[side]', '''let v=vertex(i),side=v.x<0 ? 0:1
                    normals.data.withUnsafeBytes { nraw in let at=normals.dataOffset+i*normals.dataStride;eyeNormals[side]+=SIMD3(nraw.loadUnaligned(fromByteOffset:at,as:Float.self),nraw.loadUnaligned(fromByteOffset:at+4,as:Float.self),nraw.loadUnaligned(fromByteOffset:at+8,as:Float.self)) }
                    lo[side]''')
s=s.replace('let left=(lo[0]+hi[0])*0.5,right=(lo[1]+hi[1])*0.5', 'let left=(lo[0]+hi[0])*0.5,right=(lo[1]+hi[1])*0.5\n        let nl=simd_normalize(eyeNormals[0]),nr=simd_normalize(eyeNormals[1])')
s=s.replace('material.setValue(SCNVector4(skinLinear.x', 'material.setValue(SCNVector4(nl.x,nl.y,nl.z,(hi[0].x-lo[0].x)*0.5),forKey:"faceNormalL")\n            material.setValue(SCNVector4(nr.x,nr.y,nr.z,(hi[1].x-lo[1].x)*0.5),forKey:"faceNormalR")\n            material.setValue(SCNVector4(skinLinear.x')
s=s.replace('float4 facePerformance;\n    #pragma varyings\n    float3 eyeLidData;', 'float4 facePerformance;\n    float4 faceNormalL;\n    float4 faceNormalR;\n    #pragma varyings\n    float4 eyeLidData;')
s=s.replace('out.eyeLidData=float3(0.0,facePaint.x,facePaint.z);','out.eyeLidData=float4(0.0,facePaint.x,facePaint.z,0.0);')
s=s.replace('if(facePaint.x<3.5){', 'if(facePaint.x<3.5){\n            float4 closeNormal=dot(facePos-(faceEyeL.xyz+faceEyeR.xyz)*0.5,faceRight.xyz)<0.0 ? faceNormalL:faceNormalR;')
s=s.replace('if(facePaint.x>2.5)facePos-=faceUp.xyz*(height+0.12*eye.w)*facePaint.z;', 'out.eyeLidData.w=dot(facePos-eye.xyz,faceRight.xyz)/max(closeNormal.w,0.0001);\n            _geometry.normal=normalize(mix(_geometry.normal,closeNormal.xyz,facePaint.z));')
s=s.replace('role<2.5 && blink>0.001', 'role<3.5 && blink>0.001')
s=s.replace('_surface.diffuse.rgb=mix(_surface.diffuse.rgb,faceSkin.rgb,lid);','''if(role>2.5)lid=blink;
        _surface.diffuse.rgb=mix(_surface.diffuse.rgb,faceSkin.rgb,lid);
        if(role<2.5){
            float creaseY=-0.12+0.35*in.eyeLidData.w*in.eyeLidData.w;
            float crease=(1.0-smoothstep(0.018,0.045,abs(in.eyeLidData.x-creaseY)))*(1.0-smoothstep(0.78,0.98,abs(in.eyeLidData.w)))*smoothstep(0.72,1.0,blink);
            _surface.diffuse.rgb*=1.0-crease*0.45;
        }''')
s=s.replace('in.eyeLidData.y<2.5', 'in.eyeLidData.y<3.5').replace('if(in.eyeLidData.z>0.995)lid=1.0;', 'if(in.eyeLidData.z>0.995)lid=1.0;\n            if(in.eyeLidData.y>2.5)lid=in.eyeLidData.z;')
p.write_text(s)

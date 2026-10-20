from pathlib import Path
r=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator')
p=r/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader'
s=p.read_text().replace('[HideInInspector] _Blink ("Blink", Range(0,1)) = 0','[HideInInspector] _Blink ("Blink", Range(0,1)) = 0\n        [HideInInspector] _FaceSkin ("Fitted lid skin", Color) = (1,1,1,1)')
s=s.replace('float4 _EyeL, _EyeR, _FaceUp, _FaceRight, _Gaze;', 'float4 _EyeL, _EyeR, _FaceUp, _FaceRight, _Gaze, _FaceSkin;')
s=s.replace('float3 normalOS : TEXCOORD6; };','float3 normalOS : TEXCOORD6; float eyeHeight : TEXCOORD7; };')
a=s.index('                if (_FaceRole > .5h) {');b=s.index('                facePos += i.normalOS',a)
s=s[:a]+'''                o.eyeHeight = 0;
                if (_FaceRole > .5h) {
                    float4 eye = dot(facePos - (_EyeL.xyz + _EyeR.xyz) * .5, _FaceRight.xyz) < 0 ? _EyeL : _EyeR;
                    if (_FaceRole < 3.5h) {
                        // The sclera is the fitted surface over a real eye cavity. Keep it
                        // intact: eyelid color sweeps over it rather than opening a hole.
                        if (_FaceRole > 1.5h && _FaceRole < 2.5h) facePos += (_FaceRight.xyz * _Gaze.x + _FaceUp.xyz * _Gaze.y) * (1 - _Blink);
                        float h = dot(facePos - eye.xyz, _FaceUp.xyz);
                        o.eyeHeight = h / max(eye.w, .0001);
                        if (_FaceRole > 2.5h) facePos -= _FaceUp.xyz * (h + .12 * eye.w) * _Blink;
                    } else facePos += _FaceUp.xyz * _BrowLift;
                }
''' + s[b:]
s=s.replace('                // The generated textures', '''                half lid = 0;
                if (_FaceRole > .5h && _FaceRole < 2.5h && _Blink > .001h) {
                    half upper = lerp(1, -.12h, _Blink), lower = lerp(-1, -.12h, _Blink);
                    lid = max(smoothstep(upper - .025h, upper + .025h, i.eyeHeight), 1 - smoothstep(lower - .025h, lower + .025h, i.eyeHeight));
                    if (_Blink > .995h) lid = 1;
                    if (_FaceRole > 1.5h) clip(.5h - lid);
                    else c.rgb = lerp(c.rgb, _FaceSkin.rgb, lid);
                }
                half surfaceSmoothness = lerp(_Smoothness, .28h, lid);
                half surfaceSpecular = lerp(_SpecularStrength, .8h, lid);
                // The generated textures''')
s=s.replace('c.rgb, _Wrap, _Smoothness, _Subsurface.rgb, _SpecularStrength,','c.rgb, _Wrap, surfaceSmoothness, _Subsurface.rgb, surfaceSpecular,')
s=s.replace('1 - _Smoothness, .08h','1 - surfaceSmoothness, .08h').replace('* _EnvironmentStrength;', '* lerp(_EnvironmentStrength, .12h, lid);')
p.write_text(s)
p=r/'Unity/Assets/Scripts/Tennis/MatchHeroLook.cs';s=p.read_text();s=s.replace('m.SetVector("_EyeL", bounds[0].center); m.SetVector("_EyeR", bounds[1].center);','var l = bounds[0].center; var r = bounds[1].center;\n                m.SetVector("_EyeL", new Vector4(l.x,l.y,l.z,bounds[0].size.y * .5f)); m.SetVector("_EyeR", new Vector4(r.x,r.y,r.z,bounds[1].size.y * .5f));')
s=s.replace('foreach (var m in skinMaterials) if (m) {', 'foreach (var m in faceMaterials ?? System.Array.Empty<Material>()) if (m) m.SetColor("_FaceSkin", tone);\n            foreach (var m in skinMaterials) if (m) {')
p.write_text(s)

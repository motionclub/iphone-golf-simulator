from pathlib import Path
R=Path(__file__).resolve().parents[3]
p=R/'Unity/Assets/Resources/Tennis/Shaders/TennisCloth.shader'
s=p.read_text()
s=s[s.index('Shader "'):]
s=s.replace('_Smoothness ("Smoothness",', '_TrimColor ("Trim colour", Color) = (0.035,0.035,0.0401,1)\n        _NormalMap ("Garment normal (kit UV)", 2D) = "bump" {}\n        _MaskMap ("AO / cavity / trim / fabric ID", 2D) = "white" {}\n        _UseGarmentMaps ("Use garment construction", Float) = 0\n        _NormalStrength ("Garment normal strength", Range(0,2)) = 1\n        _Smoothness ("Smoothness",')
s=s.replace('float4 _BaseColor; half4 _RimColor;', 'float4 _BaseColor, _TrimColor; half4 _RimColor;')
s=s.replace('half _WeaveNormal, _WeaveThread, _SheenStrength, _SheenPower;', 'half _WeaveNormal, _WeaveThread, _SheenStrength, _SheenPower;\n                half _UseGarmentMaps, _NormalStrength;')
s=s.replace('TEXTURE2D(_BaseMap);', 'TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);\n            TEXTURE2D(_MaskMap); SAMPLER(sampler_MaskMap);\n            TEXTURE2D(_BaseMap);')
a=s.index('            // Direct light on');b=s.index('            // Roll the brightest',a)
s=s[:a]+'''            // Charlie distribution with Ashikhmin visibility. Knit fibres have a broad grazing lobe,
            // while rubber/foam have zero sheen. Numbers are shared with GARMENT_SPEC.md.
            half3 Shade(Light light, half3 n, half3 v, half3 albedo, half smoothness, half sheenStrength, half ao)
            {
                half ndl = dot(n, light.direction), nl = saturate(ndl), nv = saturate(dot(n, v));
                half wrapped = saturate((ndl + _Wrap) / (1 + _Wrap));
                half3 h = SafeNormalize(light.direction + v);
                half nh = saturate(dot(n, h));
                half invR = rcp(max(1 - smoothness, .25h));
                half charlie = (2 + invR) * pow(max(1 - nh * nh, .0001h), invR * .5h) * .15915494h;
                half visibility = rcp(max(4 * (nl + nv - nl * nv), .08h));
                half3 sheen = albedo * (charlie * visibility * nl * sheenStrength);
                half spec = pow(nh, smoothness * 28 + 2) * smoothness * .22h * nl * ao;
                return (albedo * wrapped * ao + spec + sheen * ao) * light.color * light.distanceAttenuation * light.shadowAttenuation;
            }
            void Fabric(half id, out half smoothness, out half sheen, out half knit, out float2 quadrant, out half frequency)
            {
                smoothness = .10h; sheen = .55h; knit = 1; quadrant = float2(0,0); frequency = 8;
                if (id > .5h && id < 1.5h) { smoothness = .13h; sheen = .38h; quadrant = float2(1,0); frequency = 12; }
                else if (id < 2.5h && id > 1.5h) { smoothness = .16h; sheen = .24h; knit = 0; quadrant = float2(0,1); }
                else if (id < 3.5h && id > 2.5h) { smoothness = .04h; sheen = 0; knit = 0; quadrant = float2(1,1); }
                else if (id < 4.5h && id > 3.5h) { smoothness = .08h; sheen = 0; knit = 0; quadrant = float2(1,1); }
                else if (id > 4.5h) { smoothness = .10h; sheen = .18h; knit = 0; quadrant = float2(1,0); }
            }

'''+s[b:]
a=s.index('                // weave:');b=s.index('                Light main',a)
s=s[:a]+'''                half4 mask = half4(1, 1, 0, 0);
                half3 garment = half3(0, 0, 1);
                if (_UseGarmentMaps > .5h) {
                    mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_MaskMap, i.uv);
                    garment = UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, i.uv));
                    garment.xy *= _NormalStrength;
                }
                half id = floor(mask.a * 5 + .5h), smoothness, sheen, knit, frequency;
                float2 quadrant;
                Fabric(id, smoothness, sheen, knit, quadrant, frequency);
                if (_UseGarmentMaps < .5h) { smoothness = _Smoothness; sheen = _SheenStrength; }
                float ang = radians(_WeaveAngle); float sn, cs; sincos(ang, sn, cs);
                float2 wuv = float2(cs * i.uv.x - sn * i.uv.y, sn * i.uv.x + cs * i.uv.y) * _WeaveTile;
                // Fade individual threads before their Nyquist limit; UV derivatives are evaluated before frac.
                float2 dx = ddx(wuv), dy = ddy(wuv);
                half fade = 1 - smoothstep(.32h, .72h, max(max(abs(dx.x), abs(dx.y)), max(abs(dy.x), abs(dy.y))) * frequency);
                float2 atlasUV = (quadrant + .03125 + frac(wuv) * .9375) * .5;
                half4 weave = SAMPLE_TEXTURE2D_GRAD(_WeaveMap, sampler_WeaveMap, atlasUV, dx * .46875, dy * .46875);
                half2 slope = (weave.rg * 2 - 1) * _WeaveNormal * fade;
                if (id > 2.5h && id < 4.5h) slope = 0;
                // Rotate slopes back from the grain coordinate system (the previous male 41-degree correction).
                slope = half2(cs * slope.x + sn * slope.y, -sn * slope.x + cs * slope.y);
                half3 ts = normalize(half3(garment.xy + slope, garment.z));
                float3 tw = i.tangentWS.xyz;
                if (dot(tw, tw) > 1e-8) {
                    half3 t = normalize(tw), b = cross(n, t) * i.tangentWS.w;
                    n = normalize(TransformTangentToWorld(ts, half3x3(t, b, n)));
                }
                half threadBreak = lerp(1, weave.b * 1.28h, _WeaveThread * fade);
                if (id > 2.5h && id < 4.5h) threadBreak = 1;
                half3 albedo = lerp(_BaseColor.rgb, _TrimColor.rgb, mask.b) * threadBreak;
                if (_UseGarmentMaps < .5h) albedo *= SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv * _BaseMap_ST.xy + _BaseMap_ST.zw).rgb * 1.07h;
                half ao = max(mask.r, .70h);
                albedo *= lerp(.94h, 1, mask.g);
                half ndv = saturate(dot(n, v));

'''+s[b:]
s=s.replace('Shade(main, n, v, albedo, sheenTint, ndv)','Shade(main, n, v, albedo, smoothness, sheen, ao)').replace('Shade(extra, n, v, albedo, sheenTint, ndv)','Shade(extra, n, v, albedo, smoothness, sheen, ao)')
s=s.replace('SampleSH(n) * albedo;', 'SampleSH(n) * albedo * ao;')
s=s.replace('colour += ambient +', 'colour += albedo * knit * pow(1 - ndv, 5) * .045h * saturate(dot(n, main.direction)) * main.shadowAttenuation * main.color;\n                colour += ambient +')
s='// CLOTH_OVERHAUL: colour-neutral garment normal/masks, six fabric IDs, derivative-filtered detail atlas.\n// Same shader name and seven-role runtime API. No new keywords or pipeline settings.\n'+s
p.write_text(s)
print('Wrote',p)

// CLOTH_OVERHAUL: colour-neutral garment normal/masks, six fabric IDs, derivative-filtered detail atlas.
// Same shader name and seven-role runtime API. No new keywords or pipeline settings.
Shader "GolfArcade/TennisCloth"
{
    Properties
    {
        [MainColor] _BaseColor ("Color", Color) = (1,1,1,1)
        _TrimColor ("Trim colour", Color) = (0.035,0.035,0.0401,1)
        _NormalMap ("Garment normal (kit UV)", 2D) = "bump" {}
        _MaskMap ("AO / cavity / trim / fabric ID", 2D) = "white" {}
        _UseGarmentMaps ("Use garment construction", Float) = 0
        _AOStrength ("Garment AO strength", Range(0,1)) = 1
        _NormalStrength ("Garment normal strength", Range(0,2)) = 1
        _Smoothness ("Smoothness", Range(0,1)) = 0.1
        _Wrap ("Wrap", Range(0,1)) = 0.5
        _RimColor ("Rim colour", Color) = (1,0.96,0.88,1)
        _RimPower ("Rim power", Range(0.5,8)) = 3.5
        _RimStrength ("Rim strength", Range(0,1)) = 0.2
        _Exposure ("Cloth exposure", Range(0.2,1.5)) = 0.7
        _Knee ("Highlight knee", Range(0.3,0.95)) = 0.7
        _WeaveMap ("Weave: normal xy, thread break", 2D) = "gray" {}
        _WeaveTile ("Weave tiles per UV unit", Float) = 120
        _WeaveAngle ("Weave grain angle (deg)", Float) = 0
        _WeaveNormal ("Weave normal strength", Range(0,2)) = 1
        _WeaveThread ("Thread break strength", Range(0,1)) = 0.5
        _SheenStrength ("Sheen strength", Range(0,2)) = 0.55
        _SheenPower ("Sheen power", Range(1,8)) = 3
    }
    HLSLINCLUDE
    #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseColor, _TrimColor; half4 _RimColor; float4 _WeaveMap_ST; float4 _NormalMap_ST, _MaskMap_ST;
                half _Smoothness, _Wrap, _RimPower, _RimStrength, _Exposure, _Knee;
                float _WeaveTile, _WeaveAngle;
                half _WeaveNormal, _WeaveThread, _SheenStrength, _SheenPower;
                half _UseGarmentMaps, _NormalStrength, _AOStrength;
            CBUFFER_END
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            TEXTURE2D(_MaskMap); SAMPLER(sampler_MaskMap);
            TEXTURE2D(_WeaveMap); SAMPLER(sampler_WeaveMap);

    ENDHLSL
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile _ _LIGHT_LAYERS
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float3 positionWS : TEXCOORD1; float3 normalWS : TEXCOORD2;
                float4 tangentWS : TEXCOORD3; half fog : TEXCOORD4;
            };

            Varyings vert (Attributes i)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS;
                VertexNormalInputs nrm = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.normalWS = nrm.normalWS;
                o.tangentWS = float4(nrm.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.uv = i.uv;
                o.fog = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            // Two symmetric comparison taps keep cloth shadow sampling within the six-fetch phone budget.
            // Court/pipeline shadow settings stay unchanged; this receiver alone uses two taps.
            half ClothShadow(float3 world)
            {
                #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
                return MainLightRealtimeShadow(ComputeScreenPos(TransformWorldToHClip(world)));
                #elif defined(MAIN_LIGHT_CALCULATE_SHADOWS)
                float4 sc = TransformWorldToShadowCoord(world);
                ShadowSamplingData data = GetMainLightShadowSamplingData();
                float2 stepUV = data.shadowmapSize.xy * .45;
                half a = SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, sc.xyz + float3(stepUV,0));
                half b = SAMPLE_TEXTURE2D_SHADOW(_MainLightShadowmapTexture, sampler_LinearClampCompare, sc.xyz - float3(stepUV,0));
                half attenuation = LerpWhiteTo((a+b)*.5h, GetMainLightShadowParams().x);
                if (BEYOND_SHADOW_FAR(sc)) attenuation=1;
                return lerp(attenuation, 1, GetMainLightShadowFade(world));
                #else
                return 1;
                #endif
            }

            // Charlie distribution with Ashikhmin visibility. Knit fibres have a broad grazing lobe,
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

            // Roll the brightest channel off above the knee (hue kept): a lit white keeps a gradient instead of clipping.
            half3 SoftShoulder (half3 c)
            {
                half peak = max(max(c.r, c.g), max(c.b, 1e-4));
                half k = _Knee;
                half rolled = peak <= k ? peak : k + (1 - k) * (1 - exp(-(peak - k) / (1 - k)));
                return c * (rolled / peak);
            }

            half4 frag (Varyings i) : SV_Target
            {
                half3 n = normalize(i.normalWS);
                half3 v = normalize(GetWorldSpaceViewDir(i.positionWS));

                half4 mask = half4(1, 1, 0, 0);
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
                if (_UseGarmentMaps < .5h) atlasUV = wuv;
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
                half aoVisibility = lerp(1, max(mask.r, .70h), _AOStrength);
                half ao = lerp(1, aoVisibility, .5h);
                albedo *= lerp(.40h, 1, mask.g);
                half ndv = saturate(dot(n, v));

                Light main = GetMainLight();
                main.shadowAttenuation = ClothShadow(i.positionWS);
                half3 colour = Shade(main, n, v, albedo, smoothness, sheen, ao);
                #if defined(_ADDITIONAL_LIGHTS)
                uint count = GetAdditionalLightsCount();
                #if defined(_LIGHT_LAYERS)
                uint meshLayers = GetMeshRenderingLayer();
                #endif
                for (uint li = 0; li < count; li++)
                {
                    Light extra = GetAdditionalLight(li, i.positionWS);
                    #if defined(_LIGHT_LAYERS)
                    if (!IsMatchingLightLayer(extra.layerMask, meshLayers)) continue;
                    #endif
                    colour += Shade(extra, n, v, albedo, smoothness, sheen, ao);
                }
                #endif
                half3 ambient = SampleSH(n) * albedo * ao;
                #if defined(_SCREEN_SPACE_OCCLUSION)
                AmbientOcclusionFactor screenAO = GetScreenSpaceAmbientOcclusion(GetNormalizedScreenSpaceUV(i.positionCS));
                ambient *= screenAO.indirectAmbientOcclusion; colour *= screenAO.directAmbientOcclusion;
                #endif
                half rim = pow(1 - ndv, _RimPower) * _RimStrength;
                colour += albedo * knit * pow(1 - ndv, 5) * .045h * saturate(dot(n, main.direction)) * main.shadowAttenuation * main.color;
                colour += ambient + _RimColor.rgb * rim * (0.35 + 0.65 * albedo) * main.color;
                // Preserve moderate AO contrast through the bright-white highlight shoulder.
                colour = SoftShoulder(colour * _Exposure) * lerp(.68h, 1, aoVisibility);
                return half4(MixFog(colour, i.fog), 1);
            }
            ENDHLSL
        }
        // Own depth/shadow passes share the exact UnityPerMaterial layout: SRP Batcher compatible.
        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0
            HLSLPROGRAM
            #pragma vertex shadowVert
            #pragma fragment shadowFrag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            struct ShadowInput { float4 positionOS : POSITION; float3 normalOS : NORMAL; };
            float4 shadowVert(ShadowInput i) : SV_POSITION {
                float3 p = TransformObjectToWorld(i.positionOS.xyz), n = TransformObjectToWorldNormal(i.normalOS);
                float4 clip = TransformWorldToHClip(ApplyShadowBias(p,n,_LightDirection));
                #if UNITY_REVERSED_Z
                clip.z = min(clip.z, UNITY_NEAR_CLIP_VALUE * clip.w);
                #else
                clip.z = max(clip.z, UNITY_NEAR_CLIP_VALUE * clip.w);
                #endif
                return clip;
            }
            half4 shadowFrag() : SV_Target { return 0; }
            ENDHLSL
        }
        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma vertex depthVert
            #pragma fragment depthFrag
            float4 depthVert(float4 p : POSITION) : SV_POSITION { return TransformObjectToHClip(p.xyz); }
            half4 depthFrag() : SV_Target { return 0; }
            ENDHLSL
        }
        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode"="DepthNormals" }
            ZWrite On
            HLSLPROGRAM
            #pragma vertex normalVert
            #pragma fragment normalFrag
            struct NInput { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; };
            struct NOutput { float4 positionCS : SV_POSITION; float3 normalWS : TEXCOORD0; float4 tangentWS : TEXCOORD1; float2 uv : TEXCOORD2; };
            NOutput normalVert(NInput i) {
                NOutput o; o.positionCS=TransformObjectToHClip(i.positionOS.xyz);
                VertexNormalInputs n=GetVertexNormalInputs(i.normalOS,i.tangentOS);o.normalWS=n.normalWS;
                o.tangentWS=float4(n.tangentWS,i.tangentOS.w*GetOddNegativeScale());o.uv=i.uv;return o;
            }
            half4 normalFrag(NOutput i) : SV_Target {
                half3 n=normalize(i.normalWS);
                if(_UseGarmentMaps>.5h) {
                    half3 ts=UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap,sampler_NormalMap,i.uv));ts.xy*=_NormalStrength;
                    half3 t=normalize(i.tangentWS.xyz),b=cross(n,t)*i.tangentWS.w;
                    n=normalize(TransformTangentToWorld(ts,half3x3(t,b,n)));
                }
                return half4(n,0);
            }
            ENDHLSL
        }
    }
    FallBack "Universal Render Pipeline/Lit"
}

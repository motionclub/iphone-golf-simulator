// The Plaza's built surfaces (cream stone, slate roofs, planks, paving): URP's own PBR lighting (the same response as the
// URP Lit materials they replace) plus the detail those lacked: a normal map and a cavity map baked from each painted texture
// (HubClub.Relief), sampled with the mesh's metre UVs; tangents come from screen derivatives, so batched procedural meshes need
// none. A soft weathering band darkens the foot of every wall and a large world noise breaks up repeats. No keywords of its own
// (runtime-created materials never lose a stripped variant): one variant set, SRP-batcher compatible.
Shader "GolfArcade/HubFacade"
{
    Properties
    {
        [MainTexture] _BaseMap ("Base map", 2D) = "white" {}
        [MainColor] _BaseColor ("Colour", Color) = (1, 1, 1, 1)
        [NoScaleOffset] _ReliefMap ("Relief (rg normal xy, b cavity)", 2D) = "grey" {}
        _Relief ("Normal strength", Range(0, 2)) = 1
        _Cavity ("Cavity occlusion", Range(0, 1)) = .6
        _Smoothness ("Smoothness", Range(0, 1)) = .25
        _Weather ("Weathering at the foot", Range(0, 1)) = .25
        _Macro ("Large-scale variation", Range(0, 1)) = .3
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
#include "../Environment/Shaders/EnvironmentSurface.hlsl"
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
        TEXTURE2D(_ReliefMap); SAMPLER(sampler_ReliefMap);
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST; half4 _BaseColor;
            half _Relief, _Cavity, _Smoothness, _Weather, _Macro;
        CBUFFER_END
        struct A { float4 p : POSITION; float3 n : NORMAL; float2 uv : TEXCOORD0; };
        struct V { float4 p : SV_POSITION; float3 w : TEXCOORD0; half3 n : TEXCOORD1; float2 uv : TEXCOORD2; };
        V vert(A a)
        {
            V o; o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w);
            o.n = TransformObjectToWorldNormal(a.n); o.uv = TRANSFORM_TEX(a.uv, _BaseMap); return o;
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit" Tags { "LightMode" = "UniversalForward" }
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _LIGHT_LAYERS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            float Hash(float3 p) { p = frac(p * .3183099 + .1); p *= 17.0; return frac(p.x * p.y * p.z * (p.x + p.y + p.z)); }
            float Noise(float3 x)
            {
                float3 i = floor(x), f = frac(x); f = f * f * (3 - 2 * f);
                return lerp(lerp(lerp(Hash(i), Hash(i + float3(1, 0, 0)), f.x), lerp(Hash(i + float3(0, 1, 0)), Hash(i + float3(1, 1, 0)), f.x), f.y),
                            lerp(lerp(Hash(i + float3(0, 0, 1)), Hash(i + float3(1, 0, 1)), f.x), lerp(Hash(i + float3(0, 1, 1)), Hash(i + float3(1, 1, 1)), f.x), f.y), f.z);
            }
            half4 frag(V i) : SV_Target
            {
                half3 n0 = normalize(i.n);
                half4 tex = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv);
                half3 rel = SAMPLE_TEXTURE2D(_ReliefMap, sampler_ReliefMap, i.uv).rgb;
                // tangent frame from screen derivatives of the world position and the UVs (no mesh tangents needed)
                float3 dp1 = ddx(i.w), dp2 = ddy(i.w); float2 du1 = ddx(i.uv), du2 = ddy(i.uv);
                float3 c1 = cross(dp2, n0), c2 = cross(n0, dp1);
                float3 T = c1 * du1.x + c2 * du2.x, B = c1 * du1.y + c2 * du2.y;
                float inv = rsqrt(max(max(dot(T, T), dot(B, B)), 1e-12));
                half2 nxy = (rel.rg * 2 - 1) * _Relief;
                half3 n = normalize(n0 + (T * nxy.x + B * nxy.y) * inv);
                half cavity = lerp(1, rel.b, _Cavity);
                // large soft variation (a wall is never one flat colour) and a weathered foot (rain splash, soil)
                half macro = Noise(i.w * .35) * .6 + Noise(i.w * 1.3 + 7.1) * .4;
                half3 albedo = tex.rgb * _BaseColor.rgb * (1 + (macro - .5) * .14 * _Macro) * lerp(1, cavity, .55);
                half foot = (1 - smoothstep(0, .55, i.w.y)) * saturate(1 - abs(n0.y) * 2);
                albedo *= 1 - foot * .22 * _Weather;
                albedo = lerp(albedo, albedo * half3(.92, .9, .86), foot * _Weather);

                InputData input = (InputData)0;
                input.positionWS = i.w; input.normalWS = n; input.viewDirectionWS = SafeNormalize(GetWorldSpaceViewDir(i.w));
                input.shadowCoord = TransformWorldToShadowCoord(i.w);
                input.bakedGI = SampleSH(n); input.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.p);
                input.shadowMask = half4(1, 1, 1, 1);
                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo; s.alpha = 1; s.metallic = 0; s.specular = 0;
                s.smoothness = _Smoothness * lerp(.55, 1, rel.b); s.occlusion = cavity; s.normalTS = half3(0, 0, 1);
                half4 c = UniversalFragmentPBR(input, s);
                return half4(EnvironmentBackdrop(c.rgb, i.w), 1);
            }
            ENDHLSL
        }
        Pass
        {
            Name "ShadowCaster" Tags { "LightMode" = "ShadowCaster" }
            ZWrite On ZTest LEqual ColorMask 0
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex shadow
            #pragma fragment zero
            float3 _LightDirection;
            float4 shadow(A a) : SV_POSITION
            {
                float3 w = TransformObjectToWorld(a.p.xyz), n = TransformObjectToWorldNormal(a.n);
                float4 p = TransformWorldToHClip(ApplyShadowBias(w, n, _LightDirection));
                #if UNITY_REVERSED_Z
                    p.z = min(p.z, UNITY_NEAR_CLIP_VALUE * p.w);
                #else
                    p.z = max(p.z, UNITY_NEAR_CLIP_VALUE * p.w);
                #endif
                return p;
            }
            half4 zero() : SV_Target { return 0; }
            ENDHLSL
        }
        Pass
        {
            Name "DepthOnly" Tags { "LightMode" = "DepthOnly" }
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment depth
            half depth(V i) : SV_Target { return i.p.z; }
            ENDHLSL
        }
        Pass
        {
            Name "DepthNormals" Tags { "LightMode" = "DepthNormals" }
            ZWrite On
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment normals
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            half4 normals(V i) : SV_Target
            {
                float3 n = normalize(i.n);
                #if defined(_GBUFFER_NORMALS_OCT)
                    float2 oct = saturate(PackNormalOctQuadEncode(n) * .5 + .5);
                    return half4(PackFloat2To888(oct), 0);
                #else
                    return half4(n, 0);
                #endif
            }
            ENDHLSL
        }
    }
    Fallback Off
}

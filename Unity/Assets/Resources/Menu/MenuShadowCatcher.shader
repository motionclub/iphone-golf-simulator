// MENU BACKDROP: the floor under the line-up when the plaza is swapped for a venue plate. Invisible except where the heroes' shadows
// fall (the main light's shadow map) plus a soft contact darkening round each hero's feet (_Feet: up to 4 xz centres, w = on), so the
// heroes stand on the plate's floor instead of floating over it.
Shader "GolfArcade/MenuShadowCatcher"
{
    Properties
    {
        _Strength ("Shadow strength", Range(0, 1)) = .6
        _Contact ("Contact darkening", Range(0, 1)) = .35
        _ContactRadius ("Contact radius (m)", Float) = .42
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent-100" }
        Pass
        {
            Name "ForwardLit" Tags { "LightMode" = "UniversalForward" }
            ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fragment _ _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            CBUFFER_START(UnityPerMaterial)
                half _Strength, _Contact; float _ContactRadius;
            CBUFFER_END
            float4 _Feet[4];
            struct A { float4 p : POSITION; };
            struct V { float4 p : SV_POSITION; float3 w : TEXCOORD0; };
            V vert(A i) { V o; o.w = TransformObjectToWorld(i.p.xyz); o.p = TransformWorldToHClip(o.w); return o; }
            half4 frag(V i) : SV_Target
            {
                Light sun = GetMainLight(TransformWorldToShadowCoord(i.w));
                half shade = (1 - sun.shadowAttenuation) * _Strength;
                half contact = 0;
                [unroll] for (int k = 0; k < 4; k++)
                {
                    float d = distance(i.w.xz, _Feet[k].xy) / max(_ContactRadius, .01);
                    contact = max(contact, _Feet[k].w * saturate(1 - d) * saturate(1 - d));
                }
                return half4(0, 0, 0, saturate(max(shade, contact * _Contact)));
            }
            ENDHLSL
        }
    }
}

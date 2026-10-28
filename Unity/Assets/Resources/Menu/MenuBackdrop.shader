// MENU BACKDROP (Adnan 10-28): the venue plate behind the menu line-up, a camera-locked quad drawn first. The plate was rendered from
// the venue with the menu camera's pose and no post (MenuVenueStand), so the menu camera's own grade runs once over plate and heroes
// alike. Unlit, no depth write: the heroes and the shadow catcher draw over it. No keywords (a runtime material never loses a variant).
Shader "GolfArcade/MenuBackdrop"
{
    Properties
    {
        [MainTexture] _BaseMap ("Plate", 2D) = "black" {}
        _Exposure ("Exposure", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Background" }
        Pass
        {
            Name "Plate" Tags { "LightMode" = "UniversalForward" }
            ZWrite Off Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST; half _Exposure;
            CBUFFER_END
            struct A { float4 p : POSITION; float2 uv : TEXCOORD0; };
            struct V { float4 p : SV_POSITION; float2 uv : TEXCOORD0; };
            // full screen whatever the quad's size or the camera's aspect (the quad only keeps the renderer in the frustum)
            V vert(A i)
            {
                V o; o.uv = i.uv;
                o.p = float4(i.uv * 2 - 1, UNITY_RAW_FAR_CLIP_VALUE, 1);
                o.p.y *= _ProjectionParams.x;   // render-texture targets flip y
                return o;
            }
            half4 frag(V i) : SV_Target { return half4(SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb * _Exposure, 1); }
            ENDHLSL
        }
    }
}

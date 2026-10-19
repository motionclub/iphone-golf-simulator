// Chat 10: far impostor cards of the landmark kit (LOD2): the atlas texture, alpha-clipped, lit flat, fogged.
Shader "GolfArcade/MajesticImpostor"
{
    Properties { _BaseMap("Atlas", 2D) = "white" {} _Cutoff("Cutoff", Range(0,1)) = .5 }
    SubShader
    {
        Tags { "RenderType"="TransparentCutout" "Queue"="AlphaTest" "RenderPipeline"="UniversalPipeline" }
        Cull Off
        Pass
        {
            Name "ForwardLit" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            CBUFFER_START(UnityPerMaterial) float4 _BaseMap_ST; half _Cutoff; CBUFFER_END
            struct A { float4 p:POSITION; float2 uv:TEXCOORD0; };
            struct V { float4 p:SV_POSITION; float2 uv:TEXCOORD0; half fog:TEXCOORD1; };
            V vert(A a) { V o; o.p = TransformObjectToHClip(a.p.xyz); o.uv = a.uv; o.fog = ComputeFogFactor(o.p.z); return o; }
            half4 frag(V i) : SV_Target
            {
                half4 c = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv);
                clip(c.a - _Cutoff);
                Light sun = GetMainLight();
                half3 col = c.rgb * (sun.color * .55 + SampleSH(half3(0, 1, 0)) * .75);
                return half4(MixFog(col, i.fog), 1);
            }
            ENDHLSL
        }
    }
}

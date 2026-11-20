// ClothAudit (work/cloth-rip-1120): flat vertex colour, no lighting. Editor films only.
Shader "Hidden/ClothAuditVCol"
{
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }
        Pass
        {
            Name "Unlit"
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct A { float4 positionOS : POSITION; float4 color : COLOR; };
            struct V { float4 positionCS : SV_POSITION; nointerpolation float4 color : COLOR; };
            V vert (A i) { V o; o.positionCS = TransformObjectToHClip(i.positionOS.xyz); o.color = i.color; return o; }
            half4 frag (V i) : SV_Target { return half4(i.color.rgb, 1); }
            ENDHLSL
        }
    }
}

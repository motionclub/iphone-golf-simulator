// Animation audit vertex-id pass: the provoking vertex index of the visible triangle, R + G*256 + B*65536 (flat, unlit). Pairs with
// Hidden/AAId rendered from the same camera to find which garment vertices show their inside in the reference pose.
Shader "Hidden/AAVid"
{
    Properties { _Cull ("Cull", Float) = 2 }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Pass
        {
            Tags { "LightMode" = "UniversalForward" }
            Cull [_Cull] ZWrite On ZTest LEqual
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct A { float4 pos : POSITION; uint vid : SV_VertexID; };
            struct V { float4 pos : SV_POSITION; nointerpolation uint vid : TEXCOORD0; };
            V vert(A a) { V o; o.pos = TransformObjectToHClip(a.pos.xyz); o.vid = a.vid; return o; }
            half4 frag(V i) : SV_Target
            {
                uint v = i.vid;
                return half4((v & 255) / 255.0, ((v >> 8) & 255) / 255.0, ((v >> 16) & 255) / 255.0, 1);
            }
            ENDHLSL
        }
    }
}

// Animation audit ID pass: flat colours, no lighting, drawn on the REAL renderers (so every runtime deformation is in it).
// R = object id * 20, G = 255 front face / 128 back face, B = per-vertex code from _Code (indexed by SV_VertexID):
// garments 1 = inner wall (the lining side); body 1 = head, .5 = skin a garment covers at rest. Culling follows the real material (_Cull).
Shader "Hidden/AAId"
{
    Properties { _Id ("Id", Float) = 0 _Cull ("Cull", Float) = 2 _HasCode ("Has code", Float) = 0 }
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
            float _Id, _HasCode;
            StructuredBuffer<float> _Code;
            struct A { float4 pos : POSITION; uint vid : SV_VertexID; };
            struct V { float4 pos : SV_POSITION; float code : TEXCOORD0; };
            V vert(A a) { V o; o.pos = TransformObjectToHClip(a.pos.xyz); o.code = _HasCode > .5 ? _Code[a.vid] : 0; return o; }
            half4 frag(V i, bool front : SV_IsFrontFace) : SV_Target
            {
                return half4(_Id * 20.0 / 255.0, front ? 1.0 : 128.0 / 255.0, i.code > .75 ? 1.0 : i.code > .25 ? 128.0 / 255.0 : 0.0, 1);
            }
            ENDHLSL
        }
    }
}

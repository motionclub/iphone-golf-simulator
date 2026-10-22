// Majestic weather (chat W): readability glow. A soft additive shell on the ball (and the flag) that keeps them reading
// against wet, dark, ashy or foggy ground: brightest facing the camera, so the ball looks self-lit rather than outlined
// (soft-plastic house style). Shares the object's own mesh, drawn on top of it (depth-equal), off in clear weather.
Shader "GolfArcade/MajesticWeatherGlow"
{
    Properties { _Color("Glow colour", Color) = (1,1,1,1) _Amount("Amount", Range(0,2)) = 0 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent+40" "IgnoreProjector"="True" }
        Blend One One ZWrite Off ZTest LEqual Cull Back Offset -1, -1
        Pass
        {
            Name "Glow" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial) half4 _Color; float _Amount; CBUFFER_END
            struct A { float4 p : POSITION; float3 n : NORMAL; };
            struct V { float4 p : SV_POSITION; float3 n : TEXCOORD0; float3 w : TEXCOORD1; };
            V vert(A a) { V o; o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w); o.n = TransformObjectToWorldNormal(a.n); return o; }
            half4 frag(V i) : SV_Target
            {
                float3 v = normalize(_WorldSpaceCameraPos - i.w);
                float facing = saturate(dot(normalize(i.n), v));
                return half4(_Color.rgb * _Amount * (.45 + .55 * facing), 0);
            }
            ENDHLSL
        }
    }
}

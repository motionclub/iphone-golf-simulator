// Chat 9 majestic: additive light shafts (searchlights, sun shafts). Cheap: no texture, alpha from the
// mesh (uv0.x = 0 at the source .. 1 at the far end, uv0.y = -1..1 across), fogged, below the HUD queue.
Shader "GolfArcade/MajesticBeam"
{
    Properties { _Color("Beam colour", Color) = (.8,.85,1,1) _Intensity("Intensity", Float) = .35 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent-120" "IgnoreProjector"="True" }
        Blend One One ZWrite Off Cull Off
        Pass
        {
            Name "Beam" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/ShaderVariablesFunctions.hlsl"
            CBUFFER_START(UnityPerMaterial) half4 _Color; half _Intensity; CBUFFER_END
            struct A { float4 p:POSITION; half4 c:COLOR; float2 uv:TEXCOORD0; };
            struct V { float4 p:SV_POSITION; half4 c:COLOR; float2 uv:TEXCOORD0; half fog:TEXCOORD1; };
            V vert(A a) { V o; o.p = TransformObjectToHClip(a.p.xyz); o.c = a.c; o.uv = a.uv; o.fog = ComputeFogFactor(o.p.z); return o; }
            half4 frag(V i) : SV_Target
            {
                half along = 1 - saturate(i.uv.x); half across = 1 - i.uv.y * i.uv.y;
                half a = along * along * across * across * _Intensity * i.c.a;
                half3 col = _Color.rgb * i.c.rgb * a;
                col = MixFogColor(col, half3(0,0,0), i.fog);   // additive: fog fades the beam out
                return half4(col, 0);
            }
            ENDHLSL
        }
    }
}

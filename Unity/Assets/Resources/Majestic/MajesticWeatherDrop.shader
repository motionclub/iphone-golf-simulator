// Majestic weather (chat W): the near drops (<= 400 particles, spawned outside the ball corridor). Procedural shapes,
// no texture: a rain streak (stretched billboard, uv.y along the fall) or a soft flake; vertex colour, premultiplied.
Shader "GolfArcade/MajesticWeatherDrop"
{
    Properties { _Kind("1 rain, 2 snow, 3 ash, 4 petals, 5 wind wisp", Float) = 1 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent+55" "IgnoreProjector"="True" }
        Blend One OneMinusSrcAlpha ZWrite Off Cull Off
        Pass
        {
            Name "Drops" Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial) float _Kind; CBUFFER_END
            struct A { float4 p : POSITION; half4 c : COLOR; float2 uv : TEXCOORD0; };
            struct V { float4 p : SV_POSITION; half4 c : COLOR; float2 uv : TEXCOORD0; };
            V vert(A a) { V o; o.p = TransformObjectToHClip(a.p.xyz); o.c = a.c; o.uv = a.uv; return o; }
            half4 frag(V i) : SV_Target
            {
                float a;
                if (_Kind < 1.5) { float x = (i.uv.y - .5) / .2; a = exp(-x * x) * sin(3.14159 * saturate(i.uv.x)); }
                else if (_Kind > 4.5) { float x = (i.uv.y - .5) * 2; a = saturate(1 - x * x); a *= a; }   // wind wisp: a soft ribbon along the trail
                else if (_Kind > 3.5) { float2 q = (i.uv - .5) * float2(2.2, 4.2); a = saturate(1 - dot(q, q)) * 1.2; }   // petal / leaf
                else { a = pow(saturate(1 - length(i.uv - .5) * 2), 1.4); }
                a *= i.c.a;
                return half4(i.c.rgb * a, a * .8);
            }
            ENDHLSL
        }
    }
}

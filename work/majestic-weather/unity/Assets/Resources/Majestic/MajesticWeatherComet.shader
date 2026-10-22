// Majestic weather (chat W): the ball's "comet" outline (Adnan 10-18: "an extremely subtle, happy outlining ... like a
// heat seeking missile / asteroid outline, like flames"). Never dark: additive warm light only.
// _Mode 0  rim: a camera-facing shell a little larger than the ball. Each pixel knows how far its view ray passes from
//          the ball's centre (rho, in ball radii): a hair-thin hot line hugging the silhouette (rho ~ 1) and a soft warm
//          falloff outside it, its width licked by flame tongues that flicker and stream away from the motion (up at rest).
//          Inside the silhouette (the shell is in front of the ball) nothing but the inner edge of that line.
// _Mode 1  trail: a ribbon from the ball's centre back along its motion, hot at the head, tapering and cooling to orange,
//          flickering; shown only while the ball moves fast.
Shader "GolfArcade/MajesticWeatherComet"
{
    Properties
    {
        _Mode("Mode", Float) = 0
        _Amount("Amount", Range(0,2)) = 0
        _Hot("Hot colour", Color) = (1,.93,.72,1)
        _Warm("Flame colour", Color) = (1,.5,.14,1)
        _Width("Glow width (radii)", Float) = .12
        _Flame("Flame tongues", Range(0,2)) = .5
        _Speed("Flicker speed", Float) = 3
        _Inner("Outline starts at (radii, inside the ball)", Float) = .88
        _Center("Ball centre (world) + radius", Vector) = (0,0,0,1)
        _Bias("Flame direction (world, unit) + strength", Vector) = (0,1,0,0)
        [Enum(UnityEngine.Rendering.CullMode)] _Cull("Cull", Float) = 2
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "Queue"="Transparent-50" "IgnoreProjector"="True" }
        Blend One One ZWrite Off ZTest LEqual
        Pass
        {
            Name "Comet" Tags { "LightMode"="UniversalForward" }
            Cull [_Cull]
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            CBUFFER_START(UnityPerMaterial) half4 _Hot, _Warm; float4 _Center, _Bias; float _Mode, _Amount, _Width, _Flame, _Speed, _Cull, _Inner; CBUFFER_END
            struct A { float4 p : POSITION; float2 uv : TEXCOORD0; };
            struct V { float4 p : SV_POSITION; float3 w : TEXCOORD0; float2 uv : TEXCOORD1; };
            V vert(A a) { V o; o.w = TransformObjectToWorld(a.p.xyz); o.p = TransformWorldToHClip(o.w); o.uv = a.uv; return o; }

            float H(float2 p) { p = frac(p * float2(127.1, 311.7)); p += dot(p, p + 19.19); return frac(p.x * p.y); }
            float N(float2 p) { float2 i = floor(p), f = frac(p); f = f * f * (3 - 2 * f);
                return lerp(lerp(H(i), H(i + float2(1, 0)), f.x), lerp(H(i + float2(0, 1)), H(i + 1), f.x), f.y); }

            half4 frag(V i) : SV_Target
            {
                float t = _Time.y * _Speed;
                if (_Mode < .5)
                {
                    float3 cam = _WorldSpaceCameraPos, C = _Center.xyz; float r = _Center.w;
                    float3 D = normalize(i.w - cam);
                    float3 O = cam + D * dot(C - cam, D) - C;          // closest point of the view ray to the centre
                    float rho = length(O) / r;
                    // where around the ball (screen angle) and how much that side faces the flame direction
                    float3 right = UNITY_MATRIX_V[0].xyz, up = UNITY_MATRIX_V[1].xyz;
                    float2 o2 = float2(dot(O, right), dot(O, up));
                    float2 b2 = float2(dot(_Bias.xyz, right), dot(_Bias.xyz, up));
                    float ang = atan2(o2.y, o2.x);
                    float facing = length(b2) > 1e-3 ? saturate(dot(normalize(o2 + 1e-5), normalize(b2))) : 0;
                    float tongue = N(float2(ang * 2.2 + 7, t)) * .65 + N(float2(ang * 5.1, t * 1.7 + 3)) * .35;
                    float w = _Width * (1 + _Flame * (tongue - .35) * 1.4 + _Flame * _Bias.w * facing * facing * 1.6);
                    w = max(w, .02);
                    float outer = rho >= 1 ? exp(-(rho - 1) / w) : 0;
                    float edgeLine = smoothstep(_Inner, 1, rho) * (rho < 1 ? 1 : exp(-(rho - 1) / .05));    // the hair-thin hot outline
                    float g = outer * .35 + edgeLine * 1.6;
                    half3 c = lerp(_Warm.rgb, _Hot.rgb, saturate(edgeLine + exp(-(rho - 1) / (w * .45)) * .6));
                    return half4(c * g * _Amount, 0);
                }
                // trail ribbon: uv.x 0 at the ball .. 1 at the tip, uv.y -1..1 across
                float u = i.uv.x, v = i.uv.y;
                float width = lerp(1, .15, u);
                float across = saturate(1 - abs(v) / width);
                float flick = .75 + .5 * N(float2(u * 6 - t * 2.5, v * 2 + t));
                float a = pow(saturate(1 - u), 1.6) * across * across * flick * smoothstep(0, .12, u);
                half3 c = lerp(_Hot.rgb, _Warm.rgb, saturate(u * 1.4 + abs(v) * .5));
                return half4(c * a * _Amount, 0);
            }
            ENDHLSL
        }
    }
}

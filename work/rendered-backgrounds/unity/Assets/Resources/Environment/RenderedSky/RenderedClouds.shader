Shader "GolfArcade/RenderedClouds"
{
    // Cumulus impostors rendered in Cycles from our own volumes as six-way lightmaps
    // (work/rendered-backgrounds/blender/clouds). Relit every frame from the real light: any time of
    // day, sunset colour, moonlight, overcast. Cards sit at true 3D positions (true parallax) and use
    // the far-field projection so they never need the camera's far clip.
    Properties
    {
        _SixWayA("Six-way A (+X, +Y, back, alpha)",2D)="black"{}
        _SixWayB("Six-way B (-X, -Y, front, ambient)",2D)="black"{}
        _SunScale("Direct light scale",Float)=1.6
        _AmbientScale("Sky light scale",Float)=1.1
        _Opacity("Opacity",Range(0,1))=1
        _Grey("Overcast grey",Color)=(.55,.58,.63,1)
        _Tint("Tint (ash, dusk)",Color)=(1,1,1,1)
    }
    SubShader
    {
        Tags { "Queue"="Transparent-400" "RenderType"="Transparent" "IgnoreProjector"="True" "RenderPipeline"="UniversalPipeline" }
        ZWrite Off ZTest LEqual Cull Off
        Blend SrcAlpha OneMinusSrcAlpha
        Pass
        {
            Name "Clouds"
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "RenderedSkyCommon.hlsl"
            TEXTURE2D(_SixWayA); SAMPLER(sampler_SixWayA);
            TEXTURE2D(_SixWayB); SAMPLER(sampler_SixWayB);
            CBUFFER_START(UnityPerMaterial)
            float _SunScale,_AmbientScale,_Opacity; half4 _Grey,_Tint;
            CBUFFER_END
            float4 _RSkyWind;   // xy = drift (m/s), z = wrap half-size (m)
            struct A
            {
                float4 corner : POSITION;      // xy = card corner, x in [-.5,.5], y in [0,1] (y 0 = card bottom)
                float2 uv : TEXCOORD0;         // atlas uv
                float4 centre : TEXCOORD1;     // xyz = card bottom centre in world (m), w = width (m)
                float4 extra : TEXCOORD2;      // x = height (m), y = brightness jitter, z = drift phase, w = opacity
            };
            struct V
            {
                float4 p : SV_POSITION; float2 uv : TEXCOORD0;
                float3 right : TEXCOORD1; float3 fwd : TEXCOORD2; float3 view : TEXCOORD3;
                float4 info : TEXCOORD4;       // x = haze amount, y = jitter, z = opacity
                half3 haze : TEXCOORD5;        // aerial-perspective colour, per vertex (cards are small in angle)
            };
            V vert(A a)
            {
                V o;
                float3 c = a.centre.xyz;
                // drift with the wind, wrapped in a square around the venue; faded near the wrap
                float half_ = max(_RSkyWind.z, 1000);
                c.xz = fmod(fmod(c.xz + _RSkyWind.xy * _RSkyParams.w + half_, 2 * half_) + 2 * half_, 2 * half_) - half_;
                float edge = 1 - smoothstep(.82 * half_, .97 * half_, max(abs(c.x), abs(c.z)));
                float3 toC = c - _WorldSpaceCameraPos; toC.y = 0;
                float3 fwd = normalize(toC + float3(1e-4, 0, 0));
                float3 right = normalize(cross(float3(0, 1, 0), fwd));
                float3 wp = c + right * (a.corner.x * a.centre.w) + float3(0, 1, 0) * (a.corner.y * a.extra.x);
                float dist;
                float3 fp = RS_FarField(wp, dist);
                o.p = TransformWorldToHClip(fp);
                o.uv = a.uv; o.right = right; o.fwd = fwd; o.view = normalize(wp - _WorldSpaceCameraPos);
                // aerial perspective per vertex: the fragment only blends (cheap on the phone)
                half3 white = half3(1, 1, 1);
                half3 hazed = RS_Aerial(white, o.view, dist);
                o.haze = RS_Aerial(half3(0, 0, 0), o.view, dist);           // = haze colour x amount
                float amount = 1 - saturate(dot(hazed - o.haze, half3(.333, .333, .334)));
                o.info = float4(amount, a.extra.y, a.extra.w * edge, 0);
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half4 ta = SAMPLE_TEXTURE2D(_SixWayA, sampler_SixWayA, i.uv);
                half4 tb = SAMPLE_TEXTURE2D(_SixWayB, sampler_SixWayB, i.uv);
                float3 L = _RSkySunDir.xyz;
                float x = dot(L, i.right), y = L.y, z = dot(L, i.fwd);   // z > 0: light from behind the cloud
                float3 p = max(float3(x, y, z), 0), n = max(-float3(x, y, z), 0);
                p *= p; n *= n;   // squared: the six weights sum to one
                half direct = ta.r * p.x + tb.r * n.x + ta.g * p.y + tb.g * n.y + ta.b * p.z + tb.b * n.z;
                float night = _RSkyParams.y, overcast = _RSkyParams.z;
                half3 sun = _RSkySunColor.rgb * (1 - night * .82) * (1 - overcast * .65);
                half3 amb = lerp(_RSkyAmbientUp.rgb, _RSkyAmbientHorizon.rgb, .35);
                half ambient = tb.a * tb.a;   // packed sRGB in alpha (alpha is never linearised by the sampler)
                half3 col = sun * direct * _SunScale + amb * ambient * _AmbientScale;
                col *= i.info.y * _Tint.rgb;
                half lum = dot(col, half3(.3, .55, .15));
                col = lerp(col, _Grey.rgb * lum * 1.1, overcast * .7);
                col = col * (1 - i.info.x) + i.haze;
                return half4(col, saturate(ta.a * _Opacity * i.info.z));
            }
            ENDHLSL
        }
    }
    Fallback Off
}

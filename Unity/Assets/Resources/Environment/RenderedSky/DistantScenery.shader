Shader "GolfArcade/DistantScenery"
{
    // Real 3D distant scenery (islands, ranges, skylines) built and baked by us in Blender
    // (work/rendered-backgrounds/blender). Lit by the scene's real light, sky ambient from the rendered
    // sky, aerial perspective toward the rendered sky in the view direction (so silhouettes melt into
    // exactly the sky behind them). Far-field projection: true direction (true parallax), depth
    // compressed into the camera's far clip, so no far-clip change is needed.
    Properties
    {
        _BaseMap("Albedo (A = ambient occlusion)",2D)="white"{}
        _NormalMap("Normal",2D)="bump"{}
        _NormalStrength("Normal strength",Range(0,2))=1
        _Tint("Tint",Color)=(1,1,1,1)
        _SunScale("Direct light scale",Float)=1
        _AmbientScale("Sky light scale",Float)=1
        _Streaks("World-space streak detail",Range(0,1))=.35
        _SeaLevelFade("Waterline fade (m)",Float)=2
    }
    SubShader
    {
        Tags { "Queue"="Geometry+40" "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        Pass
        {
            Name "Scenery"
            Tags { "LightMode"="UniversalForward" }
            ZWrite On ZTest LEqual Cull Back
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "RenderedSkyCommon.hlsl"
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_NormalMap); SAMPLER(sampler_NormalMap);
            CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST; half4 _Tint; float _NormalStrength,_SunScale,_AmbientScale,_Streaks,_SeaLevelFade;
            CBUFFER_END
            struct A { float4 p : POSITION; float3 n : NORMAL; float4 t : TANGENT; float2 uv : TEXCOORD0; };
            struct V
            {
                float4 p : SV_POSITION; float2 uv : TEXCOORD0; float3 n : TEXCOORD1; float4 t : TEXCOORD2;
                float3 wp : TEXCOORD3; half4 haze : TEXCOORD4;   // rgb = haze colour x amount, a = 1 - amount (per vertex: cheap)
            };
            V vert(A a)
            {
                V o;
                float3 wp = TransformObjectToWorld(a.p.xyz);
                float dist; float3 fp = RS_FarField(wp, dist);
                o.p = TransformWorldToHClip(fp);
                o.uv = a.uv; o.n = TransformObjectToWorldNormal(a.n);
                o.t = float4(TransformObjectToWorldDir(a.t.xyz), a.t.w * GetOddNegativeScale());
                o.wp = wp;
                half3 h0 = RS_Aerial(half3(0, 0, 0), normalize(wp - _WorldSpaceCameraPos), dist);
                half3 h1 = RS_Aerial(half3(1, 1, 1), normalize(wp - _WorldSpaceCameraPos), dist);
                o.haze = half4(h0, saturate(dot(h1 - h0, half3(.333, .333, .334))));
                return o;
            }
            half4 frag(V i) : SV_Target
            {
                half4 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv);
                half3 nt = UnpackNormalScale(SAMPLE_TEXTURE2D(_NormalMap, sampler_NormalMap, i.uv), _NormalStrength);
                float3 n = normalize(i.n), t = normalize(i.t.xyz), b = cross(n, t) * i.t.w;
                n = normalize(nt.x * t + nt.y * b + nt.z * n);
                // world-space vertical streak detail so a long lens never shows a smooth blow-up
                float2 sp = float2(dot(i.wp.xz, float2(.7071, .7071)) / 9.0, i.wp.y / 140.0);
                half streak = SAMPLE_TEXTURE2D(_RSkyNoise, sampler_RSkyNoise, sp).r;
                half3 col = albedo.rgb * _Tint.rgb * lerp(1, .78 + .44 * streak, _Streaks * saturate(1 - n.y * 1.4));
                float3 L = _RSkySunDir.xyz;
                float night = _RSkyParams.y, overcast = _RSkyParams.z;
                half ndl = saturate(dot(n, L));
                half3 sun = _RSkySunColor.rgb * (1 - night * .8) * (1 - overcast * .6);
                half3 amb = lerp(_RSkyAmbientHorizon.rgb * .55, _RSkyAmbientUp.rgb, saturate(n.y * .5 + .5));
                half3 lit = col * (sun * ndl * _SunScale + amb * _AmbientScale * albedo.a);
                // wet dark waterline, then the same haze as the sky behind it
                lit *= lerp(.72, 1, saturate((i.wp.y - _RSkyAerial.y) / max(_SeaLevelFade, .01)));
                lit = lit * i.haze.a + i.haze.rgb;
                return half4(lit, 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}

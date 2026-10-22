Shader "GolfArcade/RenderedCloudSea"
{
    // The cloud sea under the skyscraper deck: the venue's own 3D cloud-sea mesh (large domes) surfaced with
    // a tileable stratocumulus field rendered in Cycles from our own volume as six-way lightmaps
    // (work/rendered-backgrounds/blender/cloudsea), relit every frame from the real light. Replaces the
    // painted CloudTops texture.
    Properties
    {
        _SeaA("Six-way A (+X, -X, +Z, -Z)",2D)="black"{}
        _SeaB("Six-way B (top, ambient)",2D)="black"{}
        _TileMetres("Tile size (m)",Float)=3000
        _SunScale("Direct light scale",Float)=.56
        _AmbientScale("Sky light scale",Float)=.42
        _ShapeShade("Mesh dome shading",Range(0,1))=.45
    }
    SubShader
    {
        Tags { "Queue"="Geometry" "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        Pass
        {
            Name "CloudSea"
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "RenderedSkyCommon.hlsl"
            TEXTURE2D(_SeaA); SAMPLER(sampler_SeaA);
            TEXTURE2D(_SeaB); SAMPLER(sampler_SeaB);
            CBUFFER_START(UnityPerMaterial)
            float _TileMetres,_SunScale,_AmbientScale,_ShapeShade;
            CBUFFER_END
            struct A { float4 p : POSITION; float3 n : NORMAL; };
            struct V { float4 p : SV_POSITION; float3 wp : TEXCOORD0; float3 n : TEXCOORD1; };
            V vert(A a)
            {
                V o; o.wp = TransformObjectToWorld(a.p.xyz); o.n = TransformObjectToWorldNormal(a.n);
                o.p = TransformWorldToHClip(o.wp); return o;
            }
            half Lit(half4 ta, half4 tb, float3 L)
            {
                // the side maps were lit from 20 deg; blend toward the overhead map as the light rises
                float2 h = L.xz; float hl2 = max(dot(h, h), 1e-4);
                float2 p = max(h, 0), n = max(-h, 0); p *= p; n *= n;
                half side = (ta.r * p.x + ta.g * n.x + ta.b * p.y + ta.a * n.y) / hl2;
                float el = degrees(asin(saturate(L.y)));
                // keep the side-lit relief even with a high sun: the overhead map alone is flat
                return lerp(side, tb.r, smoothstep(30, 90, el) * .35) * smoothstep(-4, 6, el);
            }
            half4 frag(V i) : SV_Target
            {
                float2 uv = i.wp.xz / _TileMetres;
                // two scales/orientations so the 3 km tile never reads as a repeat
                float2 uv2 = float2(uv.y, -uv.x) * .43 + float2(.39, .18);
                half4 ta = SAMPLE_TEXTURE2D(_SeaA, sampler_SeaA, uv), tb = SAMPLE_TEXTURE2D(_SeaB, sampler_SeaB, uv);
                half4 ta2 = SAMPLE_TEXTURE2D(_SeaA, sampler_SeaA, uv2), tb2 = SAMPLE_TEXTURE2D(_SeaB, sampler_SeaB, uv2);
                ta.a *= ta.a; ta2.a *= ta2.a;   // alpha is stored sRGB, the sampler leaves it encoded
                float3 L = _RSkySunDir.xyz;
                // second sample is rotated 90 deg: rotate the light into its frame
                float3 L2 = float3(L.z, L.y, -L.x);   // texture +u = world +z, texture +v = world -x
                half direct = lerp(Lit(ta, tb, L), Lit(ta2, tb2, L2), .3);
                half amb = lerp(tb.g, tb2.g, .3);
                float night = _RSkyParams.y, overcast = _RSkyParams.z;
                half3 sun = _RSkySunColor.rgb * (1 - night * .82) * (1 - overcast * .6);
                half3 col = sun * direct * _SunScale + lerp(_RSkyAmbientUp.rgb, _RSkyAmbientHorizon.rgb, .4) * amb * _AmbientScale;
                float3 n = normalize(i.n);
                col *= lerp(1, .75 + .5 * saturate(dot(n, L) * .5 + .5), _ShapeShade);
                col = col < .78 ? col : .78 + .22 * (1 - exp(-(col - .78) / .22));   // soft shoulder: bright tops, never flat white
                float3 v = i.wp - _WorldSpaceCameraPos;
                col = RS_Aerial(col, normalize(v), length(v));
                return half4(col, 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}

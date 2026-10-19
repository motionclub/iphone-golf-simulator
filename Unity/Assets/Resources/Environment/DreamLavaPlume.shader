Shader "GolfArcade/DreamLavaPlume"
{
    SubShader
    {
        Tags {"RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent"}
        Pass
        {
            Blend SrcAlpha One
            ZWrite Off
            Cull Off
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            struct A {float4 p:POSITION;float2 uv:TEXCOORD0;};
            struct V {float4 p:SV_POSITION;float2 uv:TEXCOORD0;half fog:TEXCOORD1;};
            float Hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
            float Noise(float2 p){float2 cell=floor(p),q=frac(p);q=q*q*(3-2*q);return lerp(lerp(Hash(cell),Hash(cell+float2(1,0)),q.x),lerp(Hash(cell+float2(0,1)),Hash(cell+1),q.x),q.y);}
            V Vert(A a)
            {
                V o;float height=saturate(a.p.y*.5+.5);
                float flutter=sin(a.p.y*5+_Time.y*9+a.p.x*12)*.07;
                a.p.xz*=lerp(.95,.45,height)+flutter*height;
                o.p=TransformObjectToHClip(a.p.xyz);o.uv=a.uv;o.fog=ComputeFogFactor(o.p.z);return o;
            }
            half4 Frag(V i):SV_Target
            {
                float2 flow=float2(i.uv.x*18,i.uv.y*7-_Time.y*3.2);
                float turbulence=Noise(flow)*.7+Noise(flow*2.1+5)*.3;
                float tongues=saturate(turbulence*1.8-.3-i.uv.y*.35);
                float fade=saturate((1-i.uv.y)*3);
                half3 colour=lerp(half3(1,.075,.005),half3(1,.83,.22),smoothstep(.35,.85,turbulence));
                colour*=1.5;colour=MixFogColor(colour,half3(0,0,0),i.fog);
                return half4(colour,tongues*fade*.78);
            }
            ENDHLSL
        }
    }
}

// A rounded-rectangle glass panel drawn as a signed-distance box: radius, an inside stroke and a
// three-stop vertical gradient, anti-aliased at any scale. No background blur (too costly on iPhone).
// Driven per panel by GlassGraphic; the UI stencil and clip rect work like UI/Default.
Shader "GolfArcade/UI/Glass"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite Texture", 2D) = "white" {}
        _Top ("Top", Color) = (1,1,1,1)
        _Mid ("Middle", Color) = (1,1,1,1)
        _Bottom ("Bottom", Color) = (1,1,1,1)
        _Stroke ("Stroke", Color) = (1,1,1,1)
        _Size ("Size (w, h)", Vector) = (100, 100, 0, 0)
        _Radius ("Radius", Float) = 24
        _StrokeWidth ("Stroke width", Float) = 2

        _StencilComp ("Stencil Comparison", Float) = 8
        _Stencil ("Stencil ID", Float) = 0
        _StencilOp ("Stencil Operation", Float) = 0
        _StencilWriteMask ("Stencil Write Mask", Float) = 255
        _StencilReadMask ("Stencil Read Mask", Float) = 255
        _ColorMask ("Color Mask", Float) = 15
        [Toggle(UNITY_UI_ALPHACLIP)] _UseUIAlphaClip ("Use Alpha Clip", Float) = 0
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "IgnoreProjector"="True" "RenderType"="Transparent" "PreviewType"="Plane" "CanUseSpriteAtlas"="True" }
        Stencil { Ref [_Stencil] Comp [_StencilComp] Pass [_StencilOp] ReadMask [_StencilReadMask] WriteMask [_StencilWriteMask] }
        Cull Off Lighting Off ZWrite Off ZTest [unity_GUIZTestMode]
        Blend SrcAlpha OneMinusSrcAlpha
        ColorMask [_ColorMask]

        Pass
        {
            Name "Default"
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma target 2.0
            #include "UnityCG.cginc"
            #include "UnityUI.cginc"
            #pragma multi_compile_local _ UNITY_UI_CLIP_RECT
            #pragma multi_compile_local _ UNITY_UI_ALPHACLIP

            struct appdata { float4 vertex : POSITION; float4 color : COLOR; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct v2f { float4 vertex : SV_POSITION; fixed4 color : COLOR; float2 uv : TEXCOORD0; float4 worldPosition : TEXCOORD1; UNITY_VERTEX_OUTPUT_STEREO };

            fixed4 _Top, _Mid, _Bottom, _Stroke;
            float4 _Size;
            float _Radius, _StrokeWidth;
            float4 _ClipRect;

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.worldPosition = v.vertex;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                o.color = v.color;
                return o;
            }

            float RoundBox(float2 p, float2 hs, float r)
            {
                float2 q = abs(p) - (hs - r);
                return length(max(q, 0)) + min(max(q.x, q.y), 0) - r;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float2 hs = _Size.xy * 0.5;
                float r = min(_Radius, min(hs.x, hs.y));
                float2 p = (i.uv - 0.5) * _Size.xy;
                float d = RoundBox(p, hs, r);
                float aa = max(fwidth(d), 1e-4);
                float shape = saturate(0.5 - d / aa);
                float t = i.uv.y;   // 1 at the top
                fixed4 fill = t > 0.5 ? lerp(_Mid, _Top, (t - 0.5) * 2) : lerp(_Bottom, _Mid, t * 2);
                float ring = _StrokeWidth > 0 ? saturate(0.5 + (d + _StrokeWidth) / aa) : 0;
                fixed4 c = lerp(fill, _Stroke, ring);
                c.a *= shape * i.color.a;
                c.rgb *= i.color.rgb;
                #ifdef UNITY_UI_CLIP_RECT
                c.a *= UnityGet2DClipping(i.worldPosition.xy, _ClipRect);
                #endif
                #ifdef UNITY_UI_ALPHACLIP
                clip(c.a - 0.001);
                #endif
                return c;
            }
            ENDCG
        }
    }
}

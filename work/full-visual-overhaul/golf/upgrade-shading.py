from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets')
for filename in ['GolfGround.shader','GolfRock.shader']:
 p=root/'Resources/Course/Shaders'/filename;s=p.read_text()
 s=s.replace(' _RockMipBias("Rock mip bias",Float)=1.5',' _RockMipBias("Rock mip bias",Float)=1.5\n _PaletteMode("Quiet colour palette",Float)=0\n _LowColor("Low palette",Color)=(.25,.45,.19,1)\n _HighColor("High palette",Color)=(.46,.66,.29,1)\n _DetailContrast("Texture contrast",Float)=1')
 if filename=='GolfGround.shader':
  s=s.replace('  // Keep texel density', '''  if(_PaletteMode>.5h) {
   // Preserve authored blade detail with a controlled green hue and quiet contrast.
   half value=dot(base.rgb,half3(.2126h,.7152h,.0722h));
   half blend=saturate(.5h+(value-.25h)*_DetailContrast);
   base.rgb=lerp(_LowColor.rgb,_HighColor.rgb,blend);
   half macro=sin(i.w.x*.047h+sin(i.w.z*.028h))*sin(i.w.z*.039h);
   base.rgb*=1+macro*.025h;
  }
  // Keep texel density''')
  s=s.replace('   base=lerp(base,SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,sideUV),side);','''   half4 sideBase=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,sideUV);
   if(_PaletteMode>.5h) sideBase.rgb=lerp(_LowColor.rgb,_HighColor.rgb,saturate(.5h+(dot(sideBase.rgb,half3(.2126h,.7152h,.0722h))-.25h)*_DetailContrast));
   base=lerp(base,sideBase,side);''')
 else:
  s=s.replace('  half strata=GolfBand', '''  if(_PaletteMode>.5h) {
   half value=dot(base.rgb,half3(.2126h,.7152h,.0722h));
   base.rgb=lerp(_LowColor.rgb,_HighColor.rgb,saturate(.5h+(value-.22h)*_DetailContrast));
  }
  half strata=GolfBand''')
 # Specular distinguishes stone and waxy leaves while ground stays soft and broad.
 s=s.replace(' half edge=1-saturate(dot(n,v));edge*=edge;edge*=edge;',''' half3 h=SafeNormalize(main.direction+v);
 half spec=pow(saturate(dot(n,h)),lerp(24h,90h,saturate(gloss)));
 colour+=main.color*main.shadowAttenuation*spec*(.008h+gloss*.025h);
 half edge=1-saturate(dot(n,v));edge*=edge;edge*=edge;''')
 p.write_text(s)
p=root/'Resources/Course/Shaders/GolfSurface.hlsl';s=p.read_text().replace('float4 _MowingBounds;','float4 _MowingBounds;\nhalf4 _LowColor,_HighColor;\nhalf _PaletteMode,_DetailContrast;');p.write_text(s)
p=root/'Scripts/Course/GolfLook.cs';s=p.read_text().replace('water = Resources.Load<Shader>("Tennis/Shaders/TennisWater")','water = Resources.Load<Shader>("Course/Shaders/GolfOcean")')
# Shader assignment checks must track the new ocean, retaining backwards compatible old water.
s=s.replace('m.shader.name == "GolfArcade/TennisWater"','(m.shader.name == "GolfArcade/TennisWater" || m.shader.name == "GolfArcade/GolfOcean")')
s=s.replace('            m.SetFloat("_DeepDistance", spec.DeepDistance);','            if (HoleView.Current) { var h = HoleView.Current.Hole; m.SetVector("_WaterOrigin",new Vector4((float)((h.Tee.X+h.Pin.X)*.5),0,(float)((h.Tee.D+h.Pin.D)*.5),0)); }\n            m.SetFloat("_DeepDistance", spec.DeepDistance);')
# Postcard fairway/rough share the quiet premium palette too.
s=s.replace('            return m;\n        }\n        static void SurfaceDirection','''            ResortPalette(m,name.Contains("GREEN")?GolfCourseLook.Surface.Green:name.Contains("FAIRWAY")?GolfCourseLook.Surface.Fairway:name.Contains("ROUGH")?GolfCourseLook.Surface.Rough:name.Contains("SAND")?GolfCourseLook.Surface.Sand:GolfCourseLook.Surface.Rock);
            return m;
        }
        public static void ResortPalette(Material m,GolfCourseLook.Surface role,bool volcanic=false,bool jungle=false)
        {
            if(!m.HasProperty("_PaletteMode"))return;
            Color low,high;
            switch(role)
            {
                case GolfCourseLook.Surface.Fairway: low=new Color(.31f,.49f,.17f);high=new Color(.50f,.65f,.28f);break;
                case GolfCourseLook.Surface.Green: case GolfCourseLook.Surface.Tee: low=new Color(.41f,.59f,.23f);high=new Color(.57f,.73f,.34f);break;
                case GolfCourseLook.Surface.Fringe: low=new Color(.25f,.43f,.16f);high=new Color(.38f,.55f,.21f);break;
                case GolfCourseLook.Surface.Rough: low=new Color(.23f,.40f,.17f);high=new Color(.37f,.51f,.24f);break;
                case GolfCourseLook.Surface.Sand: low=new Color(.78f,.69f,.48f);high=new Color(.95f,.87f,.65f);break;
                default:return;
            }
            if(jungle&&role!=GolfCourseLook.Surface.Sand){low.b+=.015f;high.b+=.01f;}
            m.SetFloat("_PaletteMode",1);m.SetColor("_LowColor",low);m.SetColor("_HighColor",high);
            m.SetFloat("_DetailContrast",role==GolfCourseLook.Surface.Sand?.35f:.45f);m.SetColor("_BaseColor",Color.white);
            m.SetFloat("_Bands",role==GolfCourseLook.Surface.Fairway?.045f:role==GolfCourseLook.Surface.Green?.008f:0);
            m.SetFloat("_StripeWidth",role==GolfCourseLook.Surface.Fairway?7.5f:3f);
            m.SetFloat("_BumpScale",role==GolfCourseLook.Surface.Sand?.20f:.25f);
            m.SetFloat("_Smoothness",role==GolfCourseLook.Surface.Green?.22f:.12f);
        }
        static void SurfaceDirection''')
p.write_text(s)

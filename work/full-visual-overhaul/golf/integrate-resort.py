from pathlib import Path
root=Path('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/Unity/Assets/Scripts/Course')
p=root/'GolfCourseLook.cs';s=p.read_text()
s=s.replace('number == 7 || number is >= 12 and <= 23','number is >= 7 and <= 10 || number is >= 12 and <= 23')
s=s.replace('                m.SetFloat("_Sparkle",role == Surface.Shallow ? 1.5f : 2.5f);','''                if(hole.Number!=17){ m.SetColor("_Shallow",new Color(.055f,.59f,.62f));m.SetColor("_Deep",new Color(.025f,.29f,.45f));m.SetColor("_Sky",new Color(.28f,.53f,.70f)); }
                if(role==Surface.Shallow)m.SetColor("_Deep",m.GetColor("_Shallow"));
                m.SetVector("_WaterOrigin",new Vector4((float)((hole.Tee.X+hole.Pin.X)*.5),0,(float)((hole.Tee.D+hole.Pin.D)*.5),0));
                m.SetFloat("_Sparkle",role == Surface.Shallow ? .7f : 1.35f);''')
s=s.replace('            if (role is Surface.Rock or Surface.Cliff or Surface.Masonry) m.SetColor("_BaseColor",new Color(.80f,.82f,.84f));','''            if (role is Surface.Rock or Surface.Cliff or Surface.Masonry) {
                m.SetFloat("_PaletteMode",1);m.SetFloat("_DetailContrast",.80f);m.SetColor("_BaseColor",Color.white);
                bool temple=hole.Number==19&&role==Surface.Masonry;
                m.SetColor("_LowColor",temple?new Color(.49f,.43f,.29f):new Color(.38f,.41f,.38f));
                m.SetColor("_HighColor",temple?new Color(.78f,.70f,.48f):new Color(.70f,.70f,.60f));
                m.SetFloat("_RockScale",.09f);m.SetFloat("_StrataStrength",.035f);m.SetFloat("_RockMipBias",.5f);m.SetFloat("_BumpScale",.75f);
            }
            if(role==Surface.Basalt&&!Volcanic){
                m.SetFloat("_PaletteMode",1);m.SetFloat("_DetailContrast",.7f);m.SetColor("_BaseColor",Color.white);
                m.SetColor("_LowColor",new Color(.37f,.40f,.39f));m.SetColor("_HighColor",new Color(.70f,.70f,.60f));m.SetFloat("_Basalt",.15f);
            }''')
s=s.replace('            return m;\n        }\n\n        static Texture2D Texture','''            GolfLook.ResortPalette(m,role,Volcanic,hole.Number==19);
            if(role==Surface.Sand&&original=="MAT_SAND_BLACK") {m.SetFloat("_PaletteMode",0);m.SetColor("_BaseColor",new Color(.25f,.27f,.30f));}
            return m;
        }

        static Texture2D Texture''')
s=s.replace('            var palms = model.GetComponent<GolfCoursePalms>();\n            if (palms) palms.Rebuild();','''            var resort = GolfResortDress.Apply(model,hole);
            var palms = model.GetComponent<GolfCoursePalms>();
            if (palms && (!resort || !resort.ReplacedAuthoredPlants)) palms.Rebuild();''')
p.write_text(s)

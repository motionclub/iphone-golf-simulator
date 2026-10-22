"""Route the frozen GolfLook material table through the P3 switch in work only."""
from pathlib import Path
W=Path(__file__).resolve().parents[1];C=W/'candidate/Unity';B=W/'inputs/post_cloth/Unity'
rel='Assets/Scripts/Course/GolfLook.cs';s=(B/rel).read_text()
s=s.replace('public const string Prefix = "LK_";', '''public const string Prefix = "LK_";
        // One-line rollback. No pipeline or scoring changes.
        public static bool UseSurfaceShaders = true;
        static Material BuildSurface(string name, Spec spec)
        {
            bool rock=name.Contains("CLIFF")||name.Contains("ROCK")||name.Contains("BASALT")||name.Contains("MASONRY");
            var shader=Resources.Load<Shader>("Course/Shaders/"+(rock?"GolfRock":"GolfGround"));
            if(!shader||!shader.isSupported)throw new System.InvalidOperationException("Golf surface shader unavailable: "+name);
            var m=new Material(shader){name=name,enableInstancing=true};
            var albedo=rock?Resources.Load<Texture2D>("Course/Surface/"+spec.Tex+"_CE"):Load(spec.Tex,"_C",true);var normal=spec.Normal?Load(spec.Tex,"_N",true):null;
            m.SetColor("_BaseColor",albedo?spec.Tint:spec.Fallback);if(albedo)m.SetTexture("_BaseMap",albedo);
            if(normal)m.SetTexture("_BumpMap",normal);m.SetFloat("_NormalEnabled",normal?1:0);
            m.SetFloat("_BumpScale",spec.BumpScale);m.SetFloat("_Smoothness",spec.Smoothness);
            m.SetFloat("_SheenFromAlpha",spec.SmoothnessFromAlbedoAlpha?1:0);
            m.SetFloat("_Rock",rock?1:0);m.SetFloat("_Basalt",name.Contains("BASALT")?1:0);
            m.SetFloat("_Cap",name.Contains("WET")||name.Contains("BASALT")||name.Contains("MASONRY")?0:.3f);
            float surface=name=="LK_FAIRWAY"?1:name=="LK_GREEN"?2:name=="LK_SAND"?5:0;
            if(surface==5)m.EnableKeyword("_GOLF_SAND");\n            m.SetFloat("_Surface",surface);m.SetFloat("_Bands",surface==1?.025f:surface==2?.018f:0);
            m.SetFloat("_StripeWidth",surface==1?5:2.2f);
            if(spec.Emissive) {var e=Load(spec.Tex,"_E",true);if(e)m.SetTexture("_EmissionMap",e);
                m.SetFloat("_EmissionEnabled",e?1:0);m.SetVector("_EmissionColor",(Vector4)spec.Emission);}
            return m;
        }
        static void SurfaceDirection(Material m,int hole)
        {
            if(!m||!m.HasProperty("_StripeDirection"))return;
            var view=HoleView.Current;Vector3 along=Vector3.forward;
            if(view&&view.Hole.Number==hole){along=new Vector3((float)(view.Hole.Pin.X-view.Hole.Tee.X),0,(float)(view.Hole.Pin.D-view.Hole.Tee.D)).normalized;}
            m.SetVector("_StripeDirection",new Vector4(along.z,0,-along.x,0));
        }
        public static void DressLegacy(GameObject model,int hole)
        {
            if(!UseSurfaceShaders)return;
            var cache=new Dictionary<string,Material>();
            foreach(var r in model.GetComponentsInChildren<MeshRenderer>(true))
            {
                var mats=r.sharedMaterials;
                for(int i=0;i<mats.Length;i++)
                {
                    var src=mats[i];if(!src)continue;
                    string n=r.name;string key=n.StartsWith("GREEN")?"LK_GREEN":n.StartsWith("FAIRWAY")?"LK_FAIRWAY":n.StartsWith("TEE_BOX")?"LK_GREEN":n.StartsWith("BUNKER")?"LK_SAND":n.StartsWith("TERRAIN")?"LK_ROUGH":null;
                    if(key==null)continue;
                    string cacheKey=key+src.color.ToString();
                    if(!cache.TryGetValue(cacheKey,out var m)){
                        m=BuildSurface(key,Table[key]);m.SetColor("_BaseColor",src.color);SurfaceDirection(m,hole);cache.Add(cacheKey,m);
                    }
                    mats[i]=m;
                }
                r.sharedMaterials=mats;
            }
            GolfSurfaceEdges.Apply(model);
            GolfSurfaceBatching.Apply(model);
        }''')
s=s.replace('var shader = LitShader;\n            if (!shader)', 'if (UseSurfaceShaders) return BuildSurface(name,spec);\n            var shader = LitShader;\n            if (!shader)')
s=s.replace('var shared = Get(name);','var shared = Get(name);\n            SurfaceDirection(shared,holeNumber);')
s=s.replace('cache[key] = m;\n            return m;','SurfaceDirection(m,holeNumber);\n            cache[key] = m;\n            return m;')
s=s.replace('int swapped = 0, lights = 0, densified = 0;', 'if(UseSurfaceShaders)GolfSurfaceEdges.Apply(model);\n            int swapped = 0, lights = 0, densified = 0;')
s=s.replace('if (swapped > 0 || lights > 0 || densified > 0)', 'if(UseSurfaceShaders){GolfSurfaceBatching.Apply(model);GolfPlantInstances.Apply(model);}\n            if (swapped > 0 || lights > 0 || densified > 0)')
p=C/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
rel='Assets/Scripts/Course/HoleView.cs';s=(B/rel).read_text()
s=s.replace('if (postcard) GolfLook.DressModel(model, Hole.Number);', 'if(!postcard) GolfLook.DressLegacy(model,Hole.Number);\n            if (postcard) GolfLook.DressModel(model, Hole.Number);')
(C/rel).write_text(s)
print('Surface routing prepared in candidate only')

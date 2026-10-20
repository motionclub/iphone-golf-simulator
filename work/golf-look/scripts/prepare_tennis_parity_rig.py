from pathlib import Path
W=Path(__file__).resolve().parents[1];B=W/'inputs/post_cloth/Unity/Assets/Editor/ClothProofRig.cs';s=B.read_text()
fn='''        static void FullHeroMask(Camera cam,MatchHeroLook look,string name,int w,int h)
        {
            var saved=look.GetComponentsInChildren<Renderer>(true).Select(r=>(r,r.gameObject.layer,r.sharedMaterials)).ToArray();
            int cull=cam.cullingMask;var flags=cam.clearFlags;var bg=cam.backgroundColor;bool fog=RenderSettings.fog;
            var temporary=new System.Collections.Generic.List<Material>();
            try {
                foreach(var row in saved){row.r.gameObject.layer=31;row.r.sharedMaterials=row.Item3.Select(src=>{
                    var m=new Material(Shader.Find("Hidden/ClothProofMask"));m.SetColor("_ClassColour",Color.white);temporary.Add(m);return m;
                }).ToArray();}
                cam.cullingMask=unchecked((int)0x80000000);cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.black;RenderSettings.fog=false;
                Save(cam,name+"_hero_mask",w,h);
            } finally {foreach(var row in saved){row.r.gameObject.layer=row.Item2;row.r.sharedMaterials=row.Item3;}
                cam.cullingMask=cull;cam.clearFlags=flags;cam.backgroundColor=bg;RenderSettings.fog=fog;foreach(var m in temporary)Object.DestroyImmediate(m);}
        }
'''
s=s.replace('        static void Mask(Camera cam,',fn+'        static void Mask(Camera cam,')
s=s.replace('Save(cam, sex + "_match_behind", 1280, 720); Save(cam, sex + "_match_phone", 1170, 2532);', '''Save(cam, sex + "_match_behind", 1280, 720); FullHeroMask(cam,look,sex+"_match_behind",1280,720);
                Save(cam, sex + "_match_phone", 1170, 2532);FullHeroMask(cam,look,sex+"_match_phone",1170,2532);''')
s=s.replace('var m = r is SkinnedMeshRenderer s ? s.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh;', 'var mf=r.GetComponent<MeshFilter>();var m = r is SkinnedMeshRenderer s ? s.sharedMesh : mf?mf.sharedMesh:null;')
(W/'proof-tools/ClothProofRig.cs').write_text(s)
print('Full-hero tennis parity masks prepared; production rig unchanged')

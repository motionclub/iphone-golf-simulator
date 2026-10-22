        static IEnumerator FilmWorld(Camera cam,int hole) {
            string dir=Out+"/film_hole"+hole.ToString("00");Directory.CreateDirectory(dir);
            var start=cam.transform.position;var rotation=cam.transform.rotation;var right=cam.transform.right;var frames=new List<FilmFrame>();
            var saved=new Dictionary<Renderer,Material[]>();var temporary=new List<Material>();var shader=Shader.Find("Hidden/GolfWorldProof");
            if(!shader)throw new InvalidOperationException("World proof shader missing");
            var rt=RenderTexture.GetTemporary(Width,Height,24,RenderTextureFormat.ARGBFloat,RenderTextureReadWrite.Linear,1);
            var target=cam.targetTexture;var active=RenderTexture.active;var tex=new Texture2D(Width,Height,TextureFormat.RGBAFloat,false,true);
            var flags=cam.clearFlags;var background=cam.backgroundColor;bool fog=RenderSettings.fog;
            try{
                foreach(var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r=>r.enabled&&r.gameObject.activeInHierarchy)){
                    var old=r.sharedMaterials;saved[r]=old;r.sharedMaterials=old.Select(src=>{
                        string n=src?src.name.ToUpperInvariant():"";
                        float cl=new[]{"FAIRWAY","ROUGH","GREEN","FRINGE","TEE","TERRAIN","SCRUB","GRASS"}.Any(k=>n.Contains(k))?1f:new[]{"CLIFF","BASALT","ROCK","RUIN","STONE","MASON"}.Any(k=>n.Contains(k))?2f:3f;
                        var m=new Material(shader){hideFlags=HideFlags.HideAndDontSave};m.SetFloat("_SurfaceClass",cl);temporary.Add(m);return m;
                    }).ToArray();
                }
                cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.clear;RenderSettings.fog=false;cam.targetTexture=rt;
                for(int f=0;f<90;f++){
                    float time=f/30f;cam.transform.SetPositionAndRotation(start+right*(time/3f*8f),rotation);GolfWindSway.FreezeTime=time;GolfWindSway.Push();yield return Frames(2);
                    cam.Render();RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,Width,Height),0,0);tex.Apply();
                    File.WriteAllBytes(dir+"/w_"+f.ToString("D3")+".exr",tex.EncodeToEXR(Texture2D.EXRFlags.OutputAsFloat|Texture2D.EXRFlags.CompressZIP));
                    frames.Add(new FilmFrame{frame=f,seconds=time,position=cam.transform.position,euler=cam.transform.eulerAngles,view=cam.worldToCameraMatrix,projection=cam.projectionMatrix});
                    if(f%30==0)Debug.Log("GOLF_WORLD "+hole+" "+f+"/90");
                }
                File.WriteAllText(dir+"/manifest.json",JsonUtility.ToJson(new Film{hole=hole,frames=frames.ToArray()},true));
            }finally{
                foreach(var pair in saved)if(pair.Key)pair.Key.sharedMaterials=pair.Value;foreach(var m in temporary)Object.DestroyImmediate(m);
                cam.clearFlags=flags;cam.backgroundColor=background;RenderSettings.fog=fog;cam.targetTexture=target;RenderTexture.active=active;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);cam.transform.SetPositionAndRotation(start,rotation);GolfWindSway.FreezeTime=0;GolfWindSway.Push();
            }
        }

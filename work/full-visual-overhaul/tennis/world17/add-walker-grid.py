from pathlib import Path
p=Path(__file__).parent/'TennisPromenadeFilm.cs';s=p.read_text();at=s.index('        static IEnumerator Go(')
s=s[:at]+'''        static void Grid(Camera camera,string path,Transform[] actors)
        {
            const int width=320,height=480;
            var position=camera.transform.position;var rotation=camera.transform.rotation;float fov=camera.fieldOfView,aspect=camera.aspect;
            var rt=RenderTexture.GetTemporary(width,height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.Default,4);var target=camera.targetTexture;var active=RenderTexture.active;
            var image=new Texture2D(width*3,height*2,TextureFormat.RGB24,false);
            camera.targetTexture=rt;camera.fieldOfView=37;camera.aspect=(float)width/height;
            for(int i=0;i<actors.Length;i++)
            {
                var from=actors[i].TransformPoint(2.4f,1.35f,3f);var at=actors[i].TransformPoint(0,.88f,0);
                camera.transform.SetPositionAndRotation(from,Quaternion.LookRotation(at-from));camera.Render();RenderTexture.active=rt;
                image.ReadPixels(new Rect(0,0,width,height),(i%3)*width,(1-i/3)*height,false);
            }
            image.Apply(false);File.WriteAllBytes(path,image.EncodeToPNG());Object.DestroyImmediate(image);
            camera.targetTexture=target;RenderTexture.active=active;RenderTexture.ReleaseTemporary(rt);camera.transform.SetPositionAndRotation(position,rotation);camera.fieldOfView=fov;camera.aspect=aspect;
        }
'''+s[at:]
s=s.replace('Shot(game.GameplayCamera,Path.Combine(output,"visitor_"+id+".png"),actors[2]);','Grid(game.GameplayCamera,Path.Combine(output,"visitors_"+id+".png"),actors);')
s=s.replace('Actual six independent fitted rigid visitors; natural path,60fps evaluated and30fps captured.', 'Actual six independent fitted rigid visitors; natural path,60fps evaluated and30fps captured. Grid row1 variants0/1/2, row2 variants3/4/5; allsix moving joints are filmed concurrently. Gameplay capture retains the ordinary world and HUD.')
p.write_text(s)

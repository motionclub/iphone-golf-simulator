using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using GolfArcade.Game;
using GolfArcade.Shot;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    public static class PartyCosmeticsProof
    {
        public static void Run()
        {
            string output = Environment.GetEnvironmentVariable("PARTY_PROOF_OUT");
            if (string.IsNullOrEmpty(output)) throw new Exception("PARTY_PROOF_OUT required");
            bool previouslyWorn = GolferStyle.Worn;
            var previousLook = GolferStyle.Current.Clone();
            string previousPrefs = PlayerPrefs.GetString("golfer.look.v1", "");
            string previousClub = PartyCosmetics.ClubSkin, previousBall = PartyCosmetics.BallSkin, previousExtra = PartyCosmetics.AccessorySkin;
            try {
            GolferStyle.Wear(previousLook); // preview edits must never call SaveDevice
            Directory.CreateDirectory(output);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = new Color(.55f,.57f,.62f);
            var key = new GameObject("Proof key").AddComponent<Light>(); key.type = LightType.Directional; key.intensity = 1.3f; key.transform.rotation = Quaternion.Euler(35,-35,0);
            var fill = new GameObject("Proof fill").AddComponent<Light>(); fill.type = LightType.Directional; fill.intensity = .5f; fill.transform.rotation = Quaternion.Euler(15,150,0);
            var cam = new GameObject("Proof camera").AddComponent<Camera>();cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=new Color(.78f,.81f,.83f);
            cam.orthographic=true;cam.orthographicSize=1.05f;cam.nearClipPlane=.01f;cam.farClipPlane=30;
            var reports = new List<string>();
            foreach (string style in PartyCosmetics.Clubs)
            foreach (bool female in new[]{false,true})
            {
                PartyCosmetics.ClubSkin = style;
                GolferStyle.Body = female ? GolferStyle.BodyKind.Female : GolferStyle.BodyKind.Male;
                var root = new GameObject("Proof golfer");
                var golfer = GolferView.Create(root.transform);
                if (!golfer.IsHero) throw new Exception("Hero missing");
                golfer.SetClub(GolfClub.Iron, false);
                golfer.Stand(Vector3.zero, Vector3.forward);
                golfer.ShowLoad(0);
                var rs = golfer.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r=>r.name.StartsWith("CLUB_")).ToArray();
                if(rs.Length != 4) throw new Exception("Expected four club families, got "+rs.Length);
                foreach(var r in rs) {
                    if(!r.sharedMaterials.All(m=>m && m.name.StartsWith("Party_"))) throw new Exception("Material not installed: "+r.name);
                    if(r.bones.Any(b=>!b)) throw new Exception("Missing bound bone "+r.name);
                    reports.Add(style+" "+female+" "+r.name+" vertices="+r.sharedMesh.vertexCount+" triangles="+r.sharedMesh.triangles.Length/3);
                }
                var bounds = new Bounds(golfer.transform.position+Vector3.up,.01f*Vector3.one);
                foreach(var r in golfer.GetComponentsInChildren<Renderer>().Where(r=>r.enabled && r.gameObject.activeInHierarchy))bounds.Encapsulate(r.bounds);
                var target=bounds.center;
                cam.transform.position=target+new Vector3(2,1.1f,-4);cam.transform.LookAt(target);cam.orthographicSize=Mathf.Max(1.05f,bounds.extents.y*1.12f);
                Capture(cam,Path.Combine(output,style.Replace('.','_')+(female?"_female":"_male")+".png"));
                var active = rs.First(r=>r.gameObject.activeInHierarchy);
                var close = new Mesh();active.BakeMesh(close);
                var points = close.vertices.Select(v=>active.transform.TransformPoint(v)).ToArray();
                var cb = new Bounds(points[0],Vector3.zero);foreach(var point in points)cb.Encapsulate(point);
                var face = ProductFace(active, female);
                var shaft = (active.bones.First(b=>b.name=="Club").position-cb.center).normalized;
                var side = Vector3.Cross(shaft,face).normalized;
                cam.transform.position=cb.center+face*3+side*.65f+shaft*.15f;cam.transform.LookAt(cb.center,shaft);cam.orthographicSize=.67f;
                var hidden = golfer.GetComponentsInChildren<Renderer>(true).Where(r=>!r.name.StartsWith("CLUB_") && r.enabled).ToArray();
                foreach(var renderer in hidden)renderer.enabled=false;
                Capture(cam,Path.Combine(output,style.Replace('.','_')+(female?"_female":"_male")+"_club.png"));
                var grip = active.bones.First(b=>b.name=="Club").position;
                float detailCutoff = style=="party.slugger" ? .62f : .87f;
                var headPoints = points.Where(v=>Vector3.Distance(v,grip)>detailCutoff).ToArray();
                var hb = new Bounds(headPoints[0],Vector3.zero);foreach(var point in headPoints)hb.Encapsulate(point);
                cam.transform.position=hb.center+face*3+side*.5f+shaft*.1f;cam.transform.LookAt(hb.center,shaft);cam.orthographicSize=style=="party.slugger" ? .21f : .12f;
                Capture(cam,Path.Combine(output,style.Replace('.','_')+(female?"_female":"_male")+"_detail.png"));
                foreach(var renderer in hidden)renderer.enabled=true;
                Object.DestroyImmediate(close);
                cam.transform.position=target+new Vector3(2,1.1f,-4);cam.transform.LookAt(target);cam.orthographicSize=Mathf.Max(1.05f,bounds.extents.y*1.12f);
                // Full load / contact pose: changes no gameplay or animation data.
                var flags = System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance;
                float impact = (float)typeof(GolferView).GetField("ImpactTime", flags).GetValue(golfer);
                typeof(GolferView).GetMethod("Show", flags).Invoke(golfer, new object[]{impact});
                Capture(cam,Path.Combine(output,style.Replace('.','_')+(female?"_female":"_male")+"_impact.png"));
                Object.DestroyImmediate(root);
            }
            PartyCosmetics.ClubSkin="standard";
            foreach (var id in PartyCosmetics.Balls) {
                var sphere=GameObject.CreatePrimitive(PrimitiveType.Sphere);
                Object.DestroyImmediate(sphere.GetComponent<Collider>());
                sphere.transform.localScale=Vector3.one*.44f;
                var getBall=typeof(GolfGame).GetMethod("DimpledBall",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);
                var material=new Material((Material)getBall.Invoke(null,null));
                material.SetTexture("_MainTex",PartyCosmetics.BallTexture(id));material.color=Color.white;
                sphere.GetComponent<Renderer>().sharedMaterial=material;
                cam.orthographicSize=.28f;cam.transform.position=new Vector3(0,.04f,-2);cam.transform.LookAt(Vector3.zero);
                Capture(cam,Path.Combine(output,id.Replace('.','_')+".png"));
                Object.DestroyImmediate(sphere);Object.DestroyImmediate(material);
            }
            foreach(var set in new[]{new[]{"coastal","36BDB0","183248","FFF4DC","extra.mint"},new[]{"arcade","8048D6","252343","FF73AA","extra.neon"},new[]{"citrus","FF8B36","234C44","F6F0D8","extra.caramel"}}) {
                PartyCosmetics.AccessorySkin=set[4];
                GolferStyle.Edit(look=>{look.Shirt=set[1];look.Shorts=set[2];look.Shoes=set[3];});
                var root=new GameObject("Skin proof");var view=GolferView.Create(root.transform);view.Stand(Vector3.zero,Vector3.forward);
                cam.orthographicSize=1.1f;cam.transform.position=view.transform.position+new Vector3(2,1.5f,-4);cam.transform.LookAt(view.transform.position+Vector3.up*.9f);
                Capture(cam,Path.Combine(output,"skin_"+set[0]+".png"));Object.DestroyImmediate(root);
            }
            PartyCosmetics.AccessorySkin="standard";
            File.WriteAllLines(Path.Combine(output,"runtime-geometry.txt"),reports);
            AssetDatabase.SaveAssets();
            } finally {
                if (previouslyWorn) GolferStyle.Wear(previousLook); else GolferStyle.Unwear();
                PartyCosmetics.ClubSkin=previousClub;PartyCosmetics.BallSkin=previousBall;PartyCosmetics.AccessorySkin=previousExtra;
                if (PlayerPrefs.GetString("golfer.look.v1", "") != previousPrefs) throw new Exception("Capture changed the saved editor look");
            }
        }
        static Vector3 ProductFace(SkinnedMeshRenderer active, bool female) {
            // The sculpted candy sector is an open surface, so its area-weighted normal
            // gives the authored striking-face direction in the common mesh/bind frame.
            var asset=Resources.Load<GameObject>("Golf/Equipment/Party/candy/"+(female?"Female":"Male"));
            var source=asset.GetComponentsInChildren<SkinnedMeshRenderer>(true).First(r=>r.name==active.name);
            var mesh=source.sharedMesh;var vertices=mesh.vertices;Vector3 normal=Vector3.zero;
            for(int i=0;i<source.sharedMaterials.Length;i++) {
                if(source.sharedMaterials[i].name.Split('.')[0] != "Party_pink")continue;
                var triangles=mesh.GetTriangles(i);
                for(int t=0;t<triangles.Length;t+=3)normal+=Vector3.Cross(vertices[triangles[t+1]]-vertices[triangles[t]],vertices[triangles[t+2]]-vertices[triangles[t]]);
            }
            int club=Array.FindIndex(source.bones,b=>b.name=="Club");
            var live=active.bones.First(b=>b.name=="Club");
            return live.TransformDirection(source.sharedMesh.bindposes[club].MultiplyVector(normal)).normalized;
        }
        static void Capture(Camera cam,string path) {
            var rt=new RenderTexture(800,900,24){antiAliasing=4};cam.targetTexture=rt;cam.Render();
            var old=RenderTexture.active;RenderTexture.active=rt;var tex=new Texture2D(rt.width,rt.height,TextureFormat.RGB24,false);
            tex.ReadPixels(new Rect(0,0,rt.width,rt.height),0,0);tex.Apply();File.WriteAllBytes(path,tex.EncodeToPNG());
            RenderTexture.active=old;cam.targetTexture=null;rt.Release();Object.DestroyImmediate(rt);Object.DestroyImmediate(tex);
        }
    }
}

// P0/P7 proof tool draft. Copy to Assets/Editor ONLY in an isolated Unity copy.
// G0 released by explicit user override; runs in the isolated post-cloth project.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Course;
using GolfArcade.Game;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class GolfLookProofRig
    {
        const string Flag = "GolfLookProofRig";
        const int Width = 1170, Height = 2532;
        static IEnumerator run;
        static int warm;
        static readonly Stack<IEnumerator> stack=new();
        static readonly List<Shot> shots = new();
        static string Out => Path.GetFullPath(Environment.GetEnvironmentVariable("GOLF_LOOK_OUT") ?? "../work/golf-look/proof/before");
        [Serializable] sealed class Shot
        {
            public string file, specimen, angle;
            public int hole, width, height, rendererSlots, submittedMeshTrianglesUpperBound;
            public Vector3 cameraPosition, cameraEuler, keyDirection;
            public Color keyColor;
            public float keyStrength,fieldOfView,aspect;
            public string maskFile;
            public int drawCallsBefore, drawCallsAfter, trianglesBefore, trianglesAfter;
        }
        [Serializable] sealed class Manifest { public Shot[] shots; public string[] unmeasured; }

        static GolfLookProofRig() { EditorApplication.update += Tick; }
        public static void Run()
        {
            shots.Clear(); warm = 0; run = null;stack.Clear();
            Directory.CreateDirectory(Out);
            EditorSceneManager.OpenScene("Assets/Scenes/Golf.unity");
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static bool ticking;
        static void Tick() {if(ticking)return;ticking=true;try{TickOnce();}finally{ticking=false;}}
        static void TickOnce()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying) return;
            // Only the initial warmup needs a current view. Between holes the
            // coroutine destroys that view and must still advance to build the next.
            if (run == null && (!HoleView.Current || ++warm < 90)) return;
            if(run==null){run=Capture();stack.Push(run);}
            try {
                while(stack.Count>0){var current=stack.Peek();if(!current.MoveNext()){stack.Pop();continue;}
                    if(current.Current is IEnumerator nested){stack.Push(nested);continue;}return;}
                Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); Finish(1); }
        }
        static void Finish(int exit)
        {
            File.WriteAllText(Out + "/capture_manifest.json", JsonUtility.ToJson(new Manifest
            {
                shots = shots.ToArray(),
                unmeasured = new[] { "GPU draw calls", "visible triangles", "iPhone frame time", "Metal ALU/fetches", "clipping/L* until semantic masks are reviewed" }
            }, true));
            var results=new List<string>();
            foreach(var name in new[]{"GolfArcade/GolfGround","GolfArcade/GolfRock","GolfArcade/TennisCloth","GolfArcade/GolfPlants","Universal Render Pipeline/Lit"}){
                var shader=Shader.Find(name);if(!shader)continue;
                var flags=System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.NonPublic;
                var code=typeof(ShaderUtil).GetMethod("GetSRPBatcherCompatibilityCode",flags);var reason=typeof(ShaderUtil).GetMethod("GetSRPBatcherCompatibilityIssueReason",flags);
                int c=(int)code.Invoke(null,new object[]{shader,0});results.Add(name+" "+c+" "+reason.Invoke(null,new object[]{shader,0,c}));
                if(ShaderUtil.ShaderHasError(shader)){results.Add(name+" ERROR");exit=1;}
            }
            File.WriteAllLines(Out+"/srp_batcher.txt",results);GolfWindSway.FreezeTime=null;
            SessionState.SetBool(Flag, false);
            if (Application.isBatchMode) EditorApplication.Exit(exit); else EditorApplication.isPlaying = false;
        }
        static IEnumerator Frames(int n) { while (n-- > 0) yield return null; }
        static void PlantMask(bool value) {
            var t=AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType("GolfArcade.Course.GolfPlantInstances")).FirstOrDefault(t=>t!=null);
            t?.GetField("ProofMask",System.Reflection.BindingFlags.Public|System.Reflection.BindingFlags.Static)?.SetValue(null,value);
        }
        static int Tris(Renderer r)
        {
            var mf=r.GetComponent<MeshFilter>();
            Mesh mesh = r is SkinnedMeshRenderer s ? s.sharedMesh : mf ? mf.sharedMesh : null;
            if (!mesh) return 0;
            int count = 0; for (int i = 0; i < mesh.subMeshCount; i++) count += (int)mesh.GetIndexCount(i) / 3;
            return count;
        }
        static IEnumerator Grab(Camera cam, int hole, string specimen, string angle, Light sun)
        {
            var rt = RenderTexture.GetTemporary(Width, Height, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB, 4);
            var oldTarget = cam.targetTexture; var oldActive = RenderTexture.active;
            var tex = new Texture2D(Width, Height, TextureFormat.RGB24, false);
            try
            {
                cam.targetTexture = rt;
                int dcBefore=UnityStats.drawCalls, triBefore=UnityStats.triangles;
                cam.Render(); RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, Width, Height), 0, 0); tex.Apply();
                string file = $"hole{hole:00}_{specimen}_{angle}.png";
                File.WriteAllBytes(Out + "/" + file, tex.EncodeToPNG());
                var renderers = Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r => r.enabled && r.gameObject.activeInHierarchy).ToArray();
                shots.Add(new Shot { file = file, hole = hole, specimen = specimen, angle = angle,
                    width = Width, height = Height, cameraPosition = cam.transform.position, cameraEuler = cam.transform.eulerAngles,
                    rendererSlots = renderers.Sum(r => r.sharedMaterials.Length), submittedMeshTrianglesUpperBound = renderers.Sum(Tris),
                    keyDirection = sun ? -sun.transform.forward : Vector3.zero, keyColor = sun ? sun.color : Color.black, keyStrength = sun ? sun.intensity : 0,fieldOfView=cam.fieldOfView,aspect=cam.aspect,
                    drawCallsBefore=dcBefore,drawCallsAfter=UnityStats.drawCalls,trianglesBefore=triBefore,trianglesAfter=UnityStats.triangles });
                if (specimen != "v4")
                {
                    string mask=file.Replace(".png","_semantic.png");
                    PlantMask(true);yield return Frames(2);
                    Semantic(cam,rt,tex,Out+"/"+mask); shots[shots.Count-1].maskFile=mask;
                    PlantMask(false);yield return Frames(2);
                }
                File.WriteAllText(Out+"/capture_progress.json",JsonUtility.ToJson(new Manifest {shots=shots.ToArray(),unmeasured=new[]{"capture in progress; not a completed baseline"}},true));
            }
            finally { PlantMask(false);cam.targetTexture = oldTarget; RenderTexture.active = oldActive; RenderTexture.ReleaseTemporary(rt); Object.DestroyImmediate(tex); }
        }
        // Material identities supply masks; never select skin/white pixels by their brightness.
        // RGB: skin, polo main, dark trim. Yellow: eyes. Magenta: other hero surfaces.
        static void Semantic(Camera cam,RenderTexture rt,Texture2D tex,string path)
        {
            var saved=new Dictionary<Renderer,Material[]>(); var temporary=new List<Material>();
            var flags=cam.clearFlags;var bg=cam.backgroundColor;bool fog=RenderSettings.fog;
            var shader=Shader.Find("Hidden/ClothProofMask");
            if(!shader)throw new InvalidOperationException("Semantic proof shader missing");
            try
            {
                foreach(var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None).Where(r=>r.enabled&&r.gameObject.activeInHierarchy))
                {
                    var old=r.sharedMaterials;saved[r]=old;var look=r.GetComponentInParent<MatchHeroLook>();
                    r.sharedMaterials=old.Select(src=>{
                        Color c=Color.black;string role=src?src.name.Replace(" (hero)",""):"";
                        if(look)
                        {
                            c=Color.magenta;
                            if(r==look.body)c=Color.red;
                            if(role==MatchHeroLook.RoleShirt)c=Color.green;
                            if(role==MatchHeroLook.RoleShirtTrim||role==MatchHeroLook.RoleShortsBand||role==MatchHeroLook.RoleGolfHead)c=Color.blue;
                            if(r.name.Contains("Sclera")||role.Contains("Sclera"))c=new Color(1,1,0,1);
                        }
                        var m=new Material(shader){hideFlags=HideFlags.HideAndDontSave};
                        m.SetColor("_ClassColour",c);
                        if(role==MatchHeroLook.RoleShirt&&src&&src.HasProperty("_MaskMap")&&src.GetTexture("_MaskMap"))
                        {
                            m.SetTexture("_MaskMap",src.GetTexture("_MaskMap"));m.SetFloat("_UseMaps",1);
                        }
                        temporary.Add(m);return m;
                    }).ToArray();
                }
                cam.clearFlags=CameraClearFlags.SolidColor;cam.backgroundColor=Color.black;RenderSettings.fog=false;
                cam.Render();RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,Width,Height),0,0);tex.Apply();
                File.WriteAllBytes(path,tex.EncodeToPNG());
            }
            finally
            {
                foreach(var pair in saved)if(pair.Key)pair.Key.sharedMaterials=pair.Value;
                foreach(var m in temporary)Object.DestroyImmediate(m);
                cam.clearFlags=flags;cam.backgroundColor=bg;RenderSettings.fog=fog;
            }
        }
        static void CameraAt(Camera cam, Vector3 from, Vector3 target, float fov)
        { cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(target - from)); cam.fieldOfView = fov; }

        [Serializable] sealed class FilmFrame {public int frame;public float seconds;public Vector3 position,euler;public Matrix4x4 view,projection;public int drawCalls,triangles;}
        [Serializable] sealed class Film {public int hole,width=Width,height=Height,fps=30;public float seconds=3;public FilmFrame[] frames;}
        static IEnumerator FilmMove(Camera cam,int hole) {
            string dir=Out+"/film_hole"+hole.ToString("00");Directory.CreateDirectory(dir);
            var start=cam.transform.position;var rotation=cam.transform.rotation;var right=cam.transform.right;var frames=new List<FilmFrame>();
            var rt=RenderTexture.GetTemporary(Width,Height,24,RenderTextureFormat.ARGB32,RenderTextureReadWrite.sRGB,4);
            var target=cam.targetTexture;var active=RenderTexture.active;var tex=new Texture2D(Width,Height,TextureFormat.RGB24,false);
            try{
                cam.targetTexture=rt;
                for(int f=0;f<90;f++){
                    float time=f/30f;cam.transform.SetPositionAndRotation(start+right*(time/3f*8f),rotation);
                    GolfWindSway.FreezeTime=time;GolfWindSway.Push();yield return Frames(2);
                    cam.Render();RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,Width,Height),0,0);tex.Apply();
                    File.WriteAllBytes(dir+"/f_"+f.ToString("D3")+".png",tex.EncodeToPNG());
                    frames.Add(new FilmFrame{frame=f,seconds=time,position=cam.transform.position,euler=cam.transform.eulerAngles,view=cam.worldToCameraMatrix,projection=cam.projectionMatrix,drawCalls=UnityStats.drawCalls,triangles=UnityStats.triangles});
                    if(f%30==0)Debug.Log("GOLF_FILM "+hole+" "+f+"/90");
                }
                File.WriteAllText(dir+"/manifest.json",JsonUtility.ToJson(new Film{hole=hole,frames=frames.ToArray()},true));
            }finally{cam.targetTexture=target;RenderTexture.active=active;RenderTexture.ReleaseTemporary(rt);Object.DestroyImmediate(tex);cam.transform.SetPositionAndRotation(start,rotation);GolfWindSway.FreezeTime=0;GolfWindSway.Push();}
        }
        static IEnumerator Capture()
        {
            var game = Object.FindFirstObjectByType<GolfGame>();
            var cameraRig = Object.FindFirstObjectByType<CameraRig>();
            var cam = game.GameplayCamera;
            if (!cam || !cameraRig) throw new InvalidOperationException("Gameplay camera is missing");
            foreach (var c in Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None)) c.enabled = false;
            game.StopAllCoroutines();game.CancelInvoke();game.enabled = false; cameraRig.enabled = false;GolfWindSway.FreezeTime=0;GolfWindSway.Push();
            var oldView = HoleView.Current; if (oldView) Object.DestroyImmediate(oldView.gameObject);
            // StartHole hides the golfer during its Intro state. Include inactive objects.
            var v4 = Object.FindObjectsByType<GolferView>(FindObjectsInactive.Include,FindObjectsSortMode.None).FirstOrDefault();
            if (!v4) throw new InvalidOperationException("V4 GolferView is missing");
            var sun = RenderSettings.sun;
            if (!sun) sun = Object.FindObjectsByType<Light>(FindObjectsSortMode.None).First(l => l.type == LightType.Directional);
            var root = new GameObject("GolfLook proof only");
            var holes = new[] { Course.Course.Cliffside().Holes.First(h => h.Number == 7) }.Concat(Course.Course.Postcards().Holes).ToArray();
            yield return Frames(3);
            foreach (var hole in holes)
            {
                var view = HoleView.Build(hole, root.transform);
                GolfAtmosphere.Apply(sun, cam, hole.Number);
                Physics.SyncTransforms();
                if(Object.FindObjectsByType<HoleView>(FindObjectsSortMode.None).Length!=1)throw new InvalidOperationException("Proof has overlapping hole colliders");
                var ball = HoleView.ToWorld(hole.Tee, .06);
                var heading = HoleView.ToWorld(hole.Pin) - HoleView.ToWorld(hole.Tee); heading.y = 0; heading.Normalize();
                v4.gameObject.SetActive(true); v4.Stand(ball, heading); v4.ShowLoad(0);
                yield return Frames(10);
                cameraRig.FrameAddress(ball, heading, false); cameraRig.SnapNext(); cameraRig.ApplyFrame();
                if(Environment.GetEnvironmentVariable("GOLF_FILMS_ONLY")=="1") {
                    yield return FilmMove(cam,hole.Number);Object.DestroyImmediate(view.gameObject);yield return Frames(3);continue;
                }
                yield return Grab(cam, hole.Number, "v4", "gameplay", sun);
                var centre = (HoleView.ToWorld(hole.Tee) + HoleView.ToWorld(hole.Pin)) * .5f;
                // Exact delivered postcard camera transforms (p7 round1 capture_configs/aerial_cfg_3.json).
                if (hole.Number == 8) CameraAt(cam, new Vector3(100,135,-55),new Vector3(2,6,185),57);
                else if (hole.Number == 9) CameraAt(cam, new Vector3(120,185,-65),new Vector3(-22,6,230),57);
                else if (hole.Number == 10) CameraAt(cam, new Vector3(-95,175,-105),new Vector3(145,6,125),58);
                else CameraAt(cam, centre + Vector3.up * 180 - heading * 210 + Vector3.right * 90, centre, 48);
                yield return Grab(cam, hole.Number, "v4", hole.Number == 7 ? "aerial_legacy" : "aerial", sun);
                foreach (string sex in new[] { "Male", "Female" })
                {
                    v4.gameObject.SetActive(false);
                    var prefab = Resources.Load<GameObject>("Tennis/Customization/Player" + sex + "GolfKit");
                    if (!prefab) throw new InvalidOperationException("Missing match hero " + sex);
                    var hero = Object.Instantiate(prefab, root.transform);
                    var heroLook=hero.GetComponentInChildren<MatchHeroLook>();
                    if(heroLook)
                    {
                        heroLook.SetKit(null,null,null);
                        heroLook.SetSkin(HeroKit.Hex("C47A4C"));
                        if(heroLook.racketGrip)heroLook.racketGrip.gameObject.SetActive(false);
                    }
                    foreach (var b in hero.GetComponentsInChildren<MonoBehaviour>()) if (!(b is MatchHeroLook)) b.enabled = false;
                    var animator = hero.GetComponentInChildren<Animator>(); if (animator) animator.enabled = false;
                    var clip = AssetDatabase.LoadAllAssetsAtPath($"Assets/Characters/MatchHeroes/{sex}/{sex}_ReadyIdle.fbx").OfType<AnimationClip>().First(c => !c.name.StartsWith("__"));
                    clip.SampleAnimation(hero, 0);
                    hero.GetComponent<GolfGarmentCorrectives>()?.Apply();
                    hero.transform.position = ball - Vector3.up * .06f - heading * .35f;
                    hero.transform.rotation = Quaternion.LookRotation(heading);
                    hero.transform.localScale = Vector3.one * 1.0936f;
                    yield return Frames(3);
                    cameraRig.FrameAddress(ball, heading, false); cameraRig.SnapNext(); cameraRig.ApplyFrame();
                    yield return Grab(cam, hole.Number, sex.ToLowerInvariant(), "gameplay", sun);
                    var at = hero.transform.position;
                    CameraAt(cam, at + hero.transform.forward * 3.8f + hero.transform.right * .7f + Vector3.up * 1.0f, at + Vector3.up * .98f, 34);
                    yield return Grab(cam, hole.Number, sex.ToLowerInvariant(), "fullbody", sun);
                    var casting=hero.GetComponentsInChildren<Renderer>().ToDictionary(r=>r,r=>r.shadowCastingMode);
                    foreach(var r in casting.Keys)r.shadowCastingMode=ShadowCastingMode.Off;
                    yield return Frames(3);
                    yield return Grab(cam,hole.Number,sex.ToLowerInvariant(),"fullbody_nocast",sun);
                    foreach(var pair in casting)pair.Key.shadowCastingMode=pair.Value;
                    yield return Frames(3);
                    CameraAt(cam, at + hero.transform.forward * 2.1f + hero.transform.right * .3f + Vector3.up * 1.5f, at + Vector3.up * 1.46f, 30);
                    yield return Grab(cam, hole.Number, sex.ToLowerInvariant(), "chest", sun);
                    Object.DestroyImmediate(hero); yield return Frames(2);
                }
                Object.DestroyImmediate(view.gameObject); yield return Frames(3);
            }
            Object.DestroyImmediate(root);
        }
    }
}

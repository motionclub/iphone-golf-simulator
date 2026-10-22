// DRAFT: generic Unity Game-camera fixture / staged aerial, no HoleView dependency.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using GolfArcade.Course;

namespace GolfArcade.EditorTools
{
    public static class PostcardV3FixtureCapture
    {
        [Serializable] sealed class Config {public Shot[] shots;}
        [Serializable] sealed class Shot {public string name,model,splitCfg;public int hole;public float[] pos,look;public float fov=60;public bool requireBands,buildCourseModel;}
        [Serializable] sealed class BandResult {public string status,fairwayCapStatus,greenCapStatus,reason;}
        [Serializable] sealed class FrameResult {public BandResult bands;}
        [Serializable] sealed class Summary {public string unityProject;public string tool="PostcardV3FixtureCapture",status="FAIL",reason;public int rendered,requiredBandFrames,failedBandFrames;public string[] files;}
        [Serializable] sealed class StageProvenance
        {
            public string status="FAIL",reason,asset,sha256,alignment="Unchanged HoleView.BuildFromModel, baseline Course model removed before reflection call";
            public int hole,holeViews,courseModels,sourceMeshes,staleInstalledMeshes;public string[] meshAssetPaths;
            public float[] tee,pin,up,rootPosition,rootScale;public float teeResidualXZ,pinResidualXZ,upTiltDegrees;
        }
        const int W=900,H=1600;
        static Vector3 V(float[] a) {if(a==null||a.Length!=3)throw new InvalidOperationException("Camera pos/look must contain 3 Unity world coordinates");return new Vector3(a[0],a[1],a[2]);}
        static float[] A(Vector3 v) => new[]{v.x,v.y,v.z};
        static GameObject BuildCourse(Shot shot,GameObject prefab,out GameObject owner,out StageProvenance provenance)
        {
            var hole=GolfArcade.Course.Course.Postcards().Holes.SingleOrDefault(h=>h.Number==shot.hole);
            if(hole==null)throw new InvalidOperationException("Postcard hole definition missing: "+shot.hole);
            foreach(var marker in new[]{"MARKER_TEE","MARKER_PIN","MARKER_UP"})
                if(!prefab.GetComponentsInChildren<Transform>(true).Any(t=>t.name==marker))throw new InvalidOperationException("Staged model lacks required "+marker+"; primitive fallback is not proof");
            var build=typeof(HoleView).GetMethod("BuildFromModel",BindingFlags.Instance|BindingFlags.NonPublic,null,new[]{typeof(GameObject)},null);
            if(build==null||build.ReturnType!=typeof(void))throw new InvalidOperationException("Unchanged HoleView.BuildFromModel API missing/version mismatch");
            owner=new GameObject("Staged postcard proof root");
            var view=HoleView.Build(hole,owner.transform); // actual Hole, ground, and pin setup
            var baseline=view.transform.Find("Course model");if(!baseline)throw new InvalidOperationException("Original HoleView Course model missing before staged replacement");
            UnityEngine.Object.DestroyImmediate(baseline.gameObject); // only the original model, not HoleView or its gameplay pin/cup
            try {build.Invoke(view,new object[]{prefab});}catch(TargetInvocationException e){throw e.InnerException??e;}
            var model=view.transform.Find("Course model");if(!model)throw new InvalidOperationException("Staged BuildFromModel did not produce Course model");
            var transforms=model.GetComponentsInChildren<Transform>(true);Vector3 Marker(string name)=>transforms.Single(t=>t.name==name).position;
            Vector3 tee=Marker("MARKER_TEE"),pin=Marker("MARKER_PIN"),up=Marker("MARKER_UP");
            var meshes=model.GetComponentsInChildren<MeshFilter>(true).Where(m=>m.sharedMesh).ToArray();
            provenance=new StageProvenance {asset=shot.model,hole=shot.hole,holeViews=UnityEngine.Object.FindObjectsByType<HoleView>(FindObjectsInactive.Include,FindObjectsSortMode.None).Length,
                courseModels=view.transform.Cast<Transform>().Count(t=>t.name=="Course model"),sourceMeshes=meshes.Count(m=>AssetDatabase.GetAssetPath(m.sharedMesh)==shot.model),
                staleInstalledMeshes=UnityEngine.Object.FindObjectsByType<MeshFilter>(FindObjectsInactive.Include,FindObjectsSortMode.None).Count(m=>m.sharedMesh&&AssetDatabase.GetAssetPath(m.sharedMesh).StartsWith("Assets/Resources/Course/hole_",StringComparison.Ordinal)),
                meshAssetPaths=meshes.Select(m=>AssetDatabase.GetAssetPath(m.sharedMesh)).Distinct().OrderBy(p=>p).ToArray(),tee=A(tee),pin=A(pin),up=A(up),rootPosition=A(model.position),rootScale=A(model.lossyScale),
                teeResidualXZ=Vector2.Distance(new Vector2(tee.x,tee.z),new Vector2((float)hole.Tee.X,(float)hole.Tee.D)),
                pinResidualXZ=Vector2.Distance(new Vector2(pin.x,pin.z),new Vector2((float)hole.Pin.X,(float)hole.Pin.D)),upTiltDegrees=Vector3.Angle(up-tee,Vector3.up)};
            using(var sha=SHA256.Create())provenance.sha256=BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(Path.Combine(Directory.GetParent(Application.dataPath).FullName,shot.model)))).Replace("-","").ToLowerInvariant();
            bool valid=provenance.holeViews==1&&provenance.courseModels==1&&provenance.sourceMeshes>0&&provenance.staleInstalledMeshes==0;
            provenance.status=valid?"PASS":"FAIL";provenance.reason="Pipeline/provenance gate only: one actual HoleView/model, staged source meshes, no installed baseline meshes. Alignment residuals retained, not a substitute for the separate exact scoring/marker gate.";
            if(!valid)throw new InvalidOperationException("Staged model provenance/isolation FAIL");return model.gameObject;
        }
        static Color32[] Render(Camera cam,RenderTexture rt,Texture2D tex)
        {
            var target=cam.targetTexture;var active=RenderTexture.active;
            try {cam.targetTexture=rt;cam.Render();RenderTexture.active=rt;tex.ReadPixels(new Rect(0,0,W,H),0,0);tex.Apply(false);return tex.GetPixels32();}
            finally {cam.targetTexture=target;RenderTexture.active=active;}
        }
        public static void Run()
        {
            string cfgPath=Environment.GetEnvironmentVariable("GOLF_V3_FIXTURE_CFG"),outDir=Environment.GetEnvironmentVariable("GOLF_V3_FIXTURE_OUT");
            var summary=new Summary{unityProject=Directory.GetParent(Application.dataPath).FullName};var files=new List<string>();int exitCode=1;bool outputValidated=false;
            try {
                if(!File.Exists(cfgPath)||string.IsNullOrEmpty(outDir))throw new InvalidOperationException("GOLF_V3_FIXTURE_CFG and GOLF_V3_FIXTURE_OUT required");
                outDir=Path.GetFullPath(outDir);string v3=Path.Combine((System.Environment.GetEnvironmentVariable("GOLF_PROOF_REPO_ROOT") ?? Directory.GetParent(Application.dataPath).Parent.FullName),"work/postcard-look/v3")+Path.DirectorySeparatorChar;
                if(!outDir.StartsWith(v3,StringComparison.Ordinal))throw new InvalidOperationException("Fixture output must be beneath project v3");
                outputValidated=true;
                Directory.CreateDirectory(outDir);var cfg=JsonUtility.FromJson<Config>(File.ReadAllText(cfgPath));
                if(cfg?.shots==null||cfg.shots.Length==0)throw new InvalidOperationException("Fixture config has no shots");
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
                var cameraGO=new GameObject("P1 proof Game camera");var cam=cameraGO.AddComponent<Camera>();cam.cameraType=CameraType.Game;cam.enabled=false;cam.nearClipPlane=.05f;cam.farClipPlane=2000;cam.aspect=(float)W/H;
                var sun=new GameObject("P1 actual golf atmosphere sun").AddComponent<Light>();sun.type=LightType.Directional;
                var rt=new RenderTexture(W,H,24,RenderTextureFormat.ARGB32) {antiAliasing=4};var tex=new Texture2D(W,H,TextureFormat.RGB24,false);
                try {
                    foreach(var s in cfg.shots) {
                        if(string.IsNullOrEmpty(s.name)||Path.GetFileName(s.name)!=s.name)throw new InvalidOperationException("Shot requires a simple filename name");
                        if(!s.model.StartsWith("Assets/Editor/PostcardV3Scratch/",StringComparison.Ordinal))throw new InvalidOperationException("Fixture/staged model must be in the approved scratch import namespace");
                        AssetDatabase.ImportAsset(s.model,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);
                        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(s.model);if(!prefab)throw new InvalidOperationException("Scratch model import/load failed: "+s.model);
                        GameObject owner=null,model=null;
                        try {
                            if(s.buildCourseModel) {model=BuildCourse(s,prefab,out owner,out var provenance);string sourcePath=Path.Combine(outDir,s.name+".stage_provenance.json");File.WriteAllText(sourcePath,JsonUtility.ToJson(provenance,true)+"\n");files.Add(sourcePath);}
                            else {model=UnityEngine.Object.Instantiate(prefab);model.name="Course model";owner=model;GolfLook.DressModel(model,s.hole);}
                            GolfAtmosphere.Apply(sun,cam,s.hole);
                            cam.transform.position=V(s.pos);cam.transform.rotation=Quaternion.LookRotation(V(s.look)-V(s.pos),Vector3.up);cam.fieldOfView=s.fov>1?s.fov:60;
                            Render(cam,rt,tex);Render(cam,rt,tex);var full=Render(cam,rt,tex);
                            string fullPath=Path.Combine(outDir,s.name+".full.png");File.WriteAllBytes(fullPath,tex.EncodeToPNG());files.Add(fullPath);
                            var renderers=model.GetComponentsInChildren<Renderer>(false).Where(r=>r.enabled&&r.gameObject.activeInHierarchy).ToArray();
                            PostcardV3FrameProof.Capture(s.name,s.hole,cam,rt,tex,full,model.transform,renderers,outDir);
                            if(!string.IsNullOrEmpty(s.splitCfg)){var type=typeof(PostcardV3FixtureCapture).Assembly.GetType("GolfArcade.EditorTools.PostcardV3SplitOutline");var capture=type?.GetMethod("Capture",BindingFlags.Public|BindingFlags.Static);if(capture==null)throw new InvalidOperationException("Split outline proof helper missing/version mismatch");capture.Invoke(null,new object[]{s.name,cam,rt,tex,full,model.transform,renderers,outDir,s.splitCfg});}
                            string proofPath=Path.Combine(outDir,s.name+".v3_frame_proof.json");files.Add(proofPath);summary.rendered++;
                            if(s.requireBands) {summary.requiredBandFrames++;var proof=JsonUtility.FromJson<FrameResult>(File.ReadAllText(proofPath));
                                if(proof?.bands?.status!="PASS")summary.failedBandFrames++;}
                        } finally {if(owner)UnityEngine.Object.DestroyImmediate(owner);}
                    }
                } finally {UnityEngine.Object.DestroyImmediate(tex);rt.Release();UnityEngine.Object.DestroyImmediate(rt);}
                summary.status=summary.failedBandFrames==0?"PASS":"FAIL";
                summary.reason="Rendering/import and explicitly required authored-band measurements only. BASALT_JOINTS is a separate frozen-threshold image measurement, not implied by this runner status.";
                if(summary.status=="PASS")exitCode=0;
            } catch(Exception e) {summary.reason=e.ToString();Debug.LogException(e);}
            finally {summary.files=files.ToArray();if(outputValidated&&Directory.Exists(outDir))File.WriteAllText(Path.Combine(outDir,"fixture_capture.json"),JsonUtility.ToJson(summary,true)+"\n");
                Debug.Log("[PostcardV3FixtureCapture] "+summary.status+": "+summary.reason);if(Application.isBatchMode)EditorApplication.Exit(exitCode);}
        }
    }
}

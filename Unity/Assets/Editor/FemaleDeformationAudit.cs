using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    public static class FemaleDeformationAudit
    {
        public static void Run()
        {
            try { Execute(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }
        static void Execute()
        {
            string dir = Environment.GetEnvironmentVariable("ANIMATION_PROOF") ?? "/private/tmp/female-deformation";
            Directory.CreateDirectory(dir);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            QualitySettings.skinWeights = SkinWeights.FourBones;
            RenderSettings.ambientLight = new Color(.65f, .65f, .65f);
            var light = new GameObject("Diagnostic key").AddComponent<Light>(); light.type = LightType.Directional;
            light.intensity = 1.3f; light.transform.rotation = Quaternion.Euler(35, -30, 0);
            var camera = new GameObject("Diagnostic camera").AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.23f, .26f, .29f);
            camera.transform.position = new Vector3(0, 1.1f, 3.5f);
            camera.transform.LookAt(new Vector3(0, .95f, 0)); camera.fieldOfView = 36;
            var go = Object.Instantiate(TennisCustomization.HeroBase(true));
            var look = go.GetComponent<MatchHeroLook>(); look.SetSkin(look.skinTone);
            var driver = go.GetComponent<HeroTennisDriver>(); driver.ResolvePerformanceClips();
            var covered = look.body.sharedMesh;
            var full = (Mesh)typeof(MatchHeroLook).GetField("kitV2CoverSource", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(look);
            var log = new StringBuilder();
            log.AppendLine($"coveredTriangles={covered.triangles.Length / 3} fullTriangles={full.triangles.Length / 3}");
            for (int k=0; k<look.kit.Length; k++) {
                var r=look.kit[k]; if(!r)continue;
                var expected=look.kitV2Bones[k].names; var bones=r.bones;
                log.AppendLine($"{r.name} bones={bones.Length} mesh={r.sharedMesh.name}");
                for(int i=0;i<expected.Length;i++) if(!bones[i] || bones[i].name!=expected[i]) log.AppendLine($"MISMATCH {i} expected={expected[i]} actual={(bones[i]?bones[i].name:"NULL")}");
            }
            camera.transform.position = new Vector3(0,1.1f,3.5f);camera.transform.LookAt(new Vector3(0,.95f,0));
            foreach (var pose in new[] { (HeroTennisDriver.Clip.Ready, .1f), (HeroTennisDriver.Clip.IntroWave, 1f), (HeroTennisDriver.Clip.Backhand, .6f), (HeroTennisDriver.Clip.Serve, 2.267f), (HeroTennisDriver.Clip.IntroPushups, 1.5f), (HeroTennisDriver.Clip.EmoteDefeat, 2.5f) }) {
                var clip=driver.slots.First(s=>s.id==pose.Item1).clip;
                clip.SampleAnimation(go,pose.Item2);
                new HeroPoseSafety(look).Apply(!HeroTennisDriver.IsEmote(pose.Item1),pose.Item1==HeroTennisDriver.Clip.Serve);look.body.GetComponent<HeroArmSkinning>()?.Apply(); look.GetComponent<HeroShoulderDeformation>()?.Apply();
                look.GetComponent<HeroShoulderDeformation>()?.Apply();
                foreach(var boneName in new[]{"LeftUpperArm","LeftLowerArm","LeftHand","RightUpperArm","RightLowerArm","RightHand","LeftIndexProximal","LeftMiddleProximal","LeftLittleProximal"}){var bone=go.GetComponentsInChildren<Transform>().First(t=>t.name==boneName);log.AppendLine($"{pose.Item1} {boneName} position={bone.position:F5} scale={bone.lossyScale:F3}");}
                look.body.sharedMesh=covered; look.GetComponent<HeroShoulderDeformation>()?.Apply();
                AnimationSafetyAudit.Save(camera,$"{dir}/{pose.Item1}_covered.png");
                look.body.sharedMesh=full; look.GetComponent<HeroShoulderDeformation>()?.Apply();
                AnimationSafetyAudit.Save(camera,$"{dir}/{pose.Item1}_full.png");
                foreach(var r in look.kit)if(r)r.enabled=false;
                AnimationSafetyAudit.Save(camera,$"{dir}/{pose.Item1}_body.png");
                foreach(var r in look.kit)if(r)r.enabled=true;
                look.body.enabled=false;
                AnimationSafetyAudit.Save(camera,$"{dir}/{pose.Item1}_cloth.png");
                look.body.enabled=true;
                Dump(look.body,$"{dir}/{pose.Item1}_body");
                foreach(var r in look.kit)if(r&&(r.name=="Kit_Top"||r.name=="Kit_Bottom")) Dump(r,$"{dir}/{pose.Item1}_{r.name}");
            }
            File.WriteAllText(dir+"/bindings.txt",log.ToString());
        }
        internal static void Dump(SkinnedMeshRenderer r,string path) {
            var m=r.sharedMesh;var baked=new Mesh();r.BakeMesh(baked);
            if(baked.vertexCount!=m.vertexCount)throw new InvalidOperationException("Mesh bake failed: "+r.name);
            using(var w=new BinaryWriter(File.Create(path+".bin"))) {
                w.Write(m.vertexCount);w.Write(m.triangles.Length);w.Write(r.bones.Length);
                foreach(var p in m.vertices){w.Write(p.x);w.Write(p.y);w.Write(p.z);}
                foreach(var p in baked.vertices){var q=r.transform.TransformPoint(p);w.Write(q.x);w.Write(q.y);w.Write(q.z);}
                foreach(var v in m.triangles)w.Write(v);
                foreach(var b in m.boneWeights){w.Write(b.boneIndex0);w.Write(b.boneIndex1);w.Write(b.boneIndex2);w.Write(b.boneIndex3);w.Write(b.weight0);w.Write(b.weight1);w.Write(b.weight2);w.Write(b.weight3);}
            }
            File.WriteAllLines(path+"-joints.tsv",r.bones.Select(b=>$"{b.name}\t{b.position.x:R}\t{b.position.y:R}\t{b.position.z:R}"));
            File.WriteAllLines(path+"-bones.txt",r.bones.Select((b,i)=>$"{i} {(b?b.name:"NULL")}"));
            using(var w=new BinaryWriter(File.Create(path+"-matrices.bin"))) {foreach(var matrix in r.bones.Select((b,i)=>b.localToWorldMatrix*r.sharedMesh.bindposes[i]))for(int i=0;i<16;i++)w.Write(matrix[i]);}
            Object.DestroyImmediate(baked);
        }
    }
}

using System;
using System.IO;
using System.Linq;
using System.Text;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    public static partial class AnimationSafetyAudit
    {
        public static void Run()
        {
            try { Execute(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }
        static void Execute()
        {
            string dir = Environment.GetEnvironmentVariable("ANIMATION_PROOF") ?? "/private/tmp/animation-safety-proof";
            Directory.CreateDirectory(dir);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            RenderSettings.ambientLight = new Color(.55f, .55f, .55f);
            var light = new GameObject("Key").AddComponent<Light>(); light.type = LightType.Directional;
            light.intensity = 1.3f; light.transform.rotation = Quaternion.Euler(35, -30, 0);
            var camera = new GameObject("Proof camera").AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor; camera.backgroundColor = new Color(.23f, .26f, .29f);
            camera.transform.position = new Vector3(0, 1.1f, 3.5f);
            camera.transform.LookAt(new Vector3(0, .95f, 0)); camera.fieldOfView = 36;
            var csv = new StringBuilder("sex,clip,time,volumes,before,after,wristShift,segmentError,solveMs,garmentMs,leftWristShift,gripSeparationError,waveFlex,wavePalmFront\n");
            foreach (bool female in new[] { false, true })
            {
                if (Environment.GetEnvironmentVariable("ANIMATION_FEMALE_ONLY") == "1" && !female) continue;
                var go = Object.Instantiate(TennisCustomization.HeroBase(female));
                var look = go.GetComponent<MatchHeroLook>(); look.SetSkin(look.skinTone);
                bool noCorrectives = Environment.GetEnvironmentVariable("ANIMATION_NO_CLOTH_CORRECTIVES") == "1";
                if (noCorrectives && look.kit != null) foreach (var kit in look.kit)
                    if (kit && kit.sharedMesh) for (int i = 0; i < kit.sharedMesh.blendShapeCount; i++) kit.SetBlendShapeWeight(i, 0);
                var driver = go.GetComponent<HeroTennisDriver>(); driver.ResolvePerformanceClips();
                var safety = new HeroPoseSafety(look);
                Debug.Log($"[AnimationSafetyAudit] female={female} volumes={safety.VolumeCount}");
                foreach (var slot in driver.slots.Where(s => s.clip && (HeroTennisDriver.IsEmote(s.id) || s.id == HeroTennisDriver.Clip.Backhand || s.id == HeroTennisDriver.Clip.BackhandWide || s.id == HeroTennisDriver.Clip.Serve || s.id == HeroTennisDriver.Clip.Ready)))
                {
                    string only = Environment.GetEnvironmentVariable("ANIMATION_ONLY");
                    if (!string.IsNullOrEmpty(only) && !only.Split(',').Contains(slot.id.ToString())) continue;
                    int count = Mathf.CeilToInt(slot.clip.length * 30);
                    for (int frame = 0; frame <= count; frame++)
                    {
                        bool capture = frame == count / 2 || frame == count / 4 || frame == 3 * count / 4;
                        if (Environment.GetEnvironmentVariable("ANIMATION_SNAPSHOTS_ONLY") == "1" && !capture) continue;
                        float time = Mathf.Min(slot.clip.length, frame / 30f);
                        slot.clip.SampleAnimation(go, time);
                        look.body.GetComponent<HeroArmSkinning>()?.Apply();
                        look.GetComponent<HeroShoulderDeformation>()?.Apply();
                        var upper = look.Bone(HumanBodyBones.RightUpperArm); var lower = look.Bone(HumanBodyBones.RightLowerArm); var hand = look.Bone(HumanBodyBones.RightHand);
                        var wrist = hand.position; var leftHand=look.Bone(HumanBodyBones.LeftHand);var leftWrist=leftHand.position;float separation=Vector3.Distance(wrist,leftWrist);float a = Vector3.Distance(upper.position, lower.position), b = Vector3.Distance(lower.position, hand.position);
                        float before = safety.MeasureArmDepth();
                        string name = (female ? "female" : "male") + "_" + slot.id + "_" + frame;
                        if (capture) Save(camera, dir + "/" + name + "_before.png");
                        if (slot.id == HeroTennisDriver.Clip.IntroWave) safety.RelaxWaveWrist();
                        var timer = System.Diagnostics.Stopwatch.StartNew();
                        safety.Apply(!HeroTennisDriver.IsEmote(slot.id), slot.id == HeroTennisDriver.Clip.Serve, Mathf.SmoothStep(0,1,Mathf.InverseLerp(.12f,.28f,Mathf.Abs(time-slot.contact))), slot.id == HeroTennisDriver.Clip.Backhand || slot.id == HeroTennisDriver.Clip.BackhandWide);
                        if(slot.id==HeroTennisDriver.Clip.IntroWave)safety.LimitWaveWristFlexion();
                        timer.Stop();
                        var garmentTimer=System.Diagnostics.Stopwatch.StartNew();
                        look.body.GetComponent<HeroArmSkinning>()?.Apply();
                        look.GetComponent<HeroShoulderDeformation>()?.Apply();
                        if (!noCorrectives) look.GetComponent<KitV2PoseCorrectives>()?.Apply();
                        garmentTimer.Stop();

                        var index=look.Bone(HumanBodyBones.LeftIndexProximal);var little=look.Bone(HumanBodyBones.LeftLittleProximal);var middle=look.Bone(HumanBodyBones.LeftMiddleProximal);var forearm=leftHand.position-look.Bone(HumanBodyBones.LeftLowerArm).position;
                        float flex=Vector3.Angle(middle.position-leftHand.position,forearm);float facing=Vector3.Dot(Vector3.Cross(index.position-little.position,middle.position-leftHand.position).normalized,go.transform.forward);
                        float error = Mathf.Max(Mathf.Abs(a - Vector3.Distance(upper.position, lower.position)), Mathf.Abs(b - Vector3.Distance(lower.position, hand.position)));
                        csv.AppendLine($"{female},{slot.id},{time:R},{safety.VolumeCount},{before:R},{safety.ResidualDepth:R},{Vector3.Distance(wrist,hand.position):R},{error:R},{timer.Elapsed.TotalMilliseconds:R},{garmentTimer.Elapsed.TotalMilliseconds:R},{Vector3.Distance(leftWrist,leftHand.position):R},{Mathf.Abs(separation-Vector3.Distance(hand.position,leftHand.position)):R},{flex:R},{facing:R}");
                        if (capture) Save(camera, dir + "/" + name + "_after.png");
                        if (error > .0001f) throw new Exception("Bone length changed: " + name);
                    }
                }
                Object.DestroyImmediate(go);
            }
            File.WriteAllText(dir + "/pose-sweep.csv", csv.ToString());
            Debug.Log("[AnimationSafetyAudit] completed " + dir);
        }
        internal static void Save(Camera camera, string path)
        {
            // Batch edit-mode rendering can reuse a GPU skinning buffer within
            // one editor frame. Bake each evaluated pose for truthful snapshots.
            var skins = Object.FindObjectsByType<SkinnedMeshRenderer>(FindObjectsSortMode.None).Where(s => s.enabled).ToArray();
            var copies = new GameObject[skins.Length]; var meshes = new Mesh[skins.Length];
            for (int i = 0; i < skins.Length; i++)
            {
                var skin = skins[i]; var mesh = new Mesh(); skin.BakeMesh(mesh); meshes[i] = mesh;
                var copy = new GameObject("Baked proof"); copies[i] = copy; copy.transform.SetParent(skin.transform, false);
                copy.AddComponent<MeshFilter>().sharedMesh = mesh;
                copy.AddComponent<MeshRenderer>().sharedMaterials = skin.sharedMaterials; skin.enabled = false;
            }
            var rt = RenderTexture.GetTemporary(512, 640, 24);
            camera.targetTexture = rt; camera.Render(); var previous = RenderTexture.active; RenderTexture.active = rt;
            var tex = new Texture2D(512, 640, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, 512, 640), 0, 0); tex.Apply();
            File.WriteAllBytes(path, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
            RenderTexture.active = previous; camera.targetTexture = null; RenderTexture.ReleaseTemporary(rt);
            for (int i = 0; i < skins.Length; i++) { skins[i].enabled = true; Object.DestroyImmediate(copies[i]); Object.DestroyImmediate(meshes[i]); }
        }
    }
}

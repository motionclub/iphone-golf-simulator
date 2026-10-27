using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Game;
using GolfArcade.Hub;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// Menu heroes proof (work/menu-tv/heroes): boots the plaza in menu mode through the phone's start message, then films the
    /// menu hero close up: whole body front, both hands, the shirt front / side / back (see-through checks), while idling and
    /// during an emote; and logs which renderers are drawn (racket in the hand, racket on the back) each second.
    /// HC_OUT = output folder, HC_FEMALE=1 for the female hero, HC_BACK = back carry (racket_back | golf_bag), HC_EMOTE = clip id.
    public class MenuHeroCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("HC_OUT");
        GameObject host;
        [TearDown] public void Clean() { Time.captureFramerate = 0; HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        const int W = 1280, H = 1280;
        static RenderTexture rt; static Texture2D tex;
        static void Save(Camera cam, string path)
        {
            if (!rt)
            {
                var a = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
                rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = a ? Mathf.Max(1, a.msaaSampleCount) : 1 };
                tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            }
            var prevA = cam.aspect; cam.aspect = 1; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = prevA;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(path, tex.EncodeToJPG(90));
        }
        /// The distance from a point to the nearest body vertex that is not the arm's (no arm bone carries more than 10 % of it).
        static float BodyGap(GolfArcade.Tennis.MatchHeroLook look, Vector3 point)
        {
            var body = look.body; if (!body || !body.sharedMesh || !body.sharedMesh.isReadable) return -1;
            var baked = new Mesh(); body.BakeMesh(baked);   // (without the renderer's scale: TransformPoint below applies it once)
            var v = baked.vertices; var w = body.sharedMesh.boneWeights; var bones = body.bones;
            var arm = new HashSet<int>();
            foreach (var hb in new[] { HumanBodyBones.LeftUpperArm, HumanBodyBones.RightUpperArm })
            {
                var t = look.Bone(hb); if (!t) continue;
                foreach (var c in t.GetComponentsInChildren<Transform>(true)) { int k = Array.IndexOf(bones, c); if (k >= 0) arm.Add(k); }
            }
            float ArmShare(BoneWeight bw) => (arm.Contains(bw.boneIndex0) ? bw.weight0 : 0) + (arm.Contains(bw.boneIndex1) ? bw.weight1 : 0) + (arm.Contains(bw.boneIndex2) ? bw.weight2 : 0) + (arm.Contains(bw.boneIndex3) ? bw.weight3 : 0);
            float best = float.MaxValue; var tr = body.transform;
            for (int i = 0; i < v.Length; i++)
            {
                if (i < w.Length && ArmShare(w[i]) > .1f) continue;
                float d = (tr.TransformPoint(v[i]) - point).sqrMagnitude; if (d < best) best = d;
            }
            Object.DestroyImmediate(baked);
            return Mathf.Sqrt(best);
        }
        /// The distance from a point to the nearest vertex of the clothes (the Kit_ garment renderers): a palm resting on them is ~1-2.5 cm.
        static float ClothGap(GolfArcade.Tennis.MatchHeroLook look, Vector3 point)
        {
            float best = float.MaxValue;
            foreach (var r in look.GetComponentsInChildren<SkinnedMeshRenderer>(false))
            {
                if (!r.name.StartsWith("Kit_") || !r.enabled || !r.sharedMesh) continue;
                var baked = new Mesh(); r.BakeMesh(baked);
                foreach (var v in baked.vertices) { float d = (r.transform.TransformPoint(v) - point).sqrMagnitude; if (d < best) best = d; }
                Object.DestroyImmediate(baked);
            }
            return best == float.MaxValue ? -1 : Mathf.Sqrt(best);
        }
        static void Aim(Camera cam, Vector3 at, Vector3 from, float fov)
        {
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(at - from, Vector3.up)); cam.fieldOfView = fov; cam.nearClipPlane = .02f;
        }

        [UnityTest, Timeout(900000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("HC_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;
            bool female = Environment.GetEnvironmentVariable("HC_FEMALE") == "1";
            HubHeroAnimator.LogStances = Environment.GetEnvironmentVariable("HC_STANCES") == "1";
            string back = Environment.GetEnvironmentVariable("HC_BACK") ?? "racket_back";
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "menu-hero", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan", female = female, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = back }));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Menu, "menu mode");
            hub.StartArrival();
            for (float t = 0; t < 2.5f; t += Time.unscaledDeltaTime) yield return null;
            foreach (var tr in hub.GetComponentsInChildren<Transform>(true))
                if (tr.name.StartsWith("Name tag") || tr.name == "Hub prompt") tr.gameObject.SetActive(false);
            if (hub.Hud) hub.Hud.Canvas.enabled = false;

            var player = hub.Player; var look = player.look; Assert.IsNotNull(look, "hero look");
            var cam = new GameObject("Hero cam").AddComponent<Camera>();
            cam.CopyFrom(hub.Camera); cam.enabled = false;
            var log = new List<string>();
            void Inventory(string when)
            {
                foreach (var r in look.GetComponentsInChildren<Renderer>(true))
                {
                    bool drawn = r.enabled && r.gameObject.activeInHierarchy && !r.forceRenderingOff;
                    if (!drawn) continue;
                    string path = r.name; for (var p = r.transform.parent; p && p != look.transform; p = p.parent) path = p.name + "/" + path;
                    if (path.Contains("Racket") || path.Contains("racket") || path.Contains("Back")) log.Add($"{when}\tDRAWN\t{path}\t{r.GetType().Name}");
                }
            }
            Transform B(HumanBodyBones b) => look.Bone(b);
            var root = player.transform; Vector3 fwd = root.forward, right = root.right, up = Vector3.up;

            void Shots(string tag)
            {
                var hips = B(HumanBodyBones.Hips).position; var chest = (B(HumanBodyBones.UpperChest) ?? B(HumanBodyBones.Chest)).position;
                var lh = B(HumanBodyBones.LeftHand).position; var rh = B(HumanBodyBones.RightHand).position;
                var mid = root.position + up * .9f;
                Aim(cam, mid, mid + fwd * 4.2f, 30); Save(cam, Path.Combine(Dir, $"{tag}_body_front.jpg"));
                Aim(cam, mid, mid - fwd * 4.2f, 30); Save(cam, Path.Combine(Dir, $"{tag}_body_back.jpg"));
                Aim(cam, chest, chest + fwd * 1.3f + up * .05f, 32); Save(cam, Path.Combine(Dir, $"{tag}_shirt_front.jpg"));
                Aim(cam, chest, chest + right * 1.3f, 32); Save(cam, Path.Combine(Dir, $"{tag}_shirt_side_r.jpg"));
                Aim(cam, chest, chest - right * 1.3f, 32); Save(cam, Path.Combine(Dir, $"{tag}_shirt_side_l.jpg"));
                Aim(cam, chest, chest - fwd * 1.3f, 32); Save(cam, Path.Combine(Dir, $"{tag}_shirt_back.jpg"));
                Aim(cam, chest + up * .1f, chest + fwd * .5f + right * .5f + up * .55f, 40); Save(cam, Path.Combine(Dir, $"{tag}_shirt_collar_down.jpg"));
                Aim(cam, rh, rh + fwd * .45f + right * .15f, 30); Save(cam, Path.Combine(Dir, $"{tag}_hand_r_front.jpg"));
                Aim(cam, rh, rh + right * .45f, 30); Save(cam, Path.Combine(Dir, $"{tag}_hand_r_out.jpg"));
                Aim(cam, lh, lh + fwd * .45f - right * .15f, 30); Save(cam, Path.Combine(Dir, $"{tag}_hand_l_front.jpg"));
                Aim(cam, lh, lh - right * .45f, 30); Save(cam, Path.Combine(Dir, $"{tag}_hand_l_out.jpg"));
                Inventory(tag);
            }

            if (Environment.GetEnvironmentVariable("HC_PALMSWEEP") == "1")
            {
                // the female hands-on-hips: wrist height / out / forward combinations, each palm's gap to the body after the clearance pass
                hub.Menu.enabled = false;
                var sdir = Path.Combine(Dir, "sweep"); Directory.CreateDirectory(sdir);
                var lines = new List<string> { "up\tout\tfwd\tleft_cm\tright_cm" };
                foreach (var pu in new[] { .12f, .16f })
                foreach (var po in new[] { 1.7f, 1.9f, 2.1f })
                foreach (var pf in new[] { .0f, .04f })
                {
                    HubHeroAnimator.PalmHipUp = pu; HubHeroAnimator.PalmHipOut = po; HubHeroAnimator.PalmHipFwd = pf;
                    player.hero.RebuildStances(); player.hero.SetStance(4);
                    for (float t = 0; t < 1.0f; t += Time.unscaledDeltaTime) yield return null;
                    float[] gaps = new float[2]; int k = 0;
                    foreach (bool left in new[] { true, false })
                    {
                        var hand = B(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand); var mid = B(left ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
                        gaps[k++] = BodyGap(look, Vector3.Lerp(hand.position, mid.position, .55f)) * 100;
                    }
                    lines.Add($"{pu:0.00}\t{po:0.0}\t{pf:0.00}\t{gaps[0]:0.0}\t{gaps[1]:0.0}");
                    var m2 = root.position + up * .95f;
                    string tag = $"u{pu:0.00}_o{po:0.0}_f{pf:0.00}";
                    Aim(cam, m2, m2 - fwd * 4.0f, 32); Save(cam, Path.Combine(sdir, tag + "_front.jpg"));
                    var c2 = B(HumanBodyBones.Hips).position + up * .1f;
                    Aim(cam, c2, c2 + right * 1.4f - fwd * .3f, 36); Save(cam, Path.Combine(sdir, tag + "_side.jpg"));
                }
                File.WriteAllLines(Path.Combine(Dir, "sweep.tsv"), lines);
                yield break;
            }
            if (Environment.GetEnvironmentVariable("HC_STANCES") == "1")
            {
                // the menu stances (HubHeroAnimator.StanceNames), each held: front, three-quarter, side and back
                var sdir = Path.Combine(Dir, "stances"); Directory.CreateDirectory(sdir);
                for (int i = 0; i < HubHeroAnimator.StanceNames.Length; i++)
                {
                    hub.Menu.enabled = false;   // the stage would put slot 0's own stance back
                    player.hero.SetStance(i);
                    for (float t = 0; t < 1.6f; t += Time.unscaledDeltaTime) yield return null;
                    string n = HubHeroAnimator.StanceNames[i];
                    var m2 = root.position + up * .95f; var c2 = (B(HumanBodyBones.UpperChest) ?? B(HumanBodyBones.Chest)).position;
                    Aim(cam, m2, m2 - fwd * 4.0f, 32); Save(cam, Path.Combine(sdir, $"{n}_front.jpg"));
                    Aim(cam, m2, m2 - fwd * 3.0f + right * 2.6f, 32); Save(cam, Path.Combine(sdir, $"{n}_threequarter.jpg"));
                    Aim(cam, c2, c2 + right * 1.6f, 34); Save(cam, Path.Combine(sdir, $"{n}_side_r.jpg"));
                    Aim(cam, c2, c2 - right * 1.6f, 34); Save(cam, Path.Combine(sdir, $"{n}_side_l.jpg"));
                    Aim(cam, c2, c2 - fwd * 1.4f, 36); Save(cam, Path.Combine(sdir, $"{n}_chest.jpg"));
                    Aim(cam, m2, m2 + fwd * 4.0f, 32); Save(cam, Path.Combine(sdir, $"{n}_back.jpg"));
                    // each hand close up: from the front, the side and behind (contact you can see)
                    foreach (bool left in new[] { true, false })
                    {
                        var h = B(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand).position; float sd = left ? -1 : 1;
                        string hs = left ? "L" : "R";
                        Aim(cam, h, h - fwd * .7f, 40); Save(cam, Path.Combine(sdir, $"{n}_hand{hs}_front.jpg"));
                        Aim(cam, h, h + right * sd * .7f, 40); Save(cam, Path.Combine(sdir, $"{n}_hand{hs}_side.jpg"));
                        Aim(cam, h, h + fwd * .7f, 40); Save(cam, Path.Combine(sdir, $"{n}_hand{hs}_back.jpg"));
                        Aim(cam, h, h + up * .6f + right * sd * .25f - fwd * .1f, 45); Save(cam, Path.Combine(sdir, $"{n}_hand{hs}_top.jpg"));
                    }
                    // CONTACT: each palm's gap to the body surface (the body mesh baked now, the arms' own vertices left out)
                    foreach (bool left in new[] { true, false })
                    {
                        var hand = B(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand); var mid = B(left ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
                        if (!hand || !mid) continue;
                        var palm = Vector3.Lerp(hand.position, mid.position, .55f);
                        // the palm's skin to the REAL clothes / body surface, straight in from the side (palm centre gap minus its half thickness)
                        float err = player.hero.PalmHipError(left);
                        File.AppendAllText(Path.Combine(Dir, "contact.tsv"), $"{n}\t{(left ? "L" : "R")}\tpalm to its spot on the side of the hip {err * 100:0.0} cm\t{(err >= 0 && err <= .01f ? "ON THE HIP" : "OFF")}\n");
                    }
                }
                yield break;
            }
            if (Environment.GetEnvironmentVariable("HC_SURVEY") == "1")
            {
                // candidate held poses: five moments of every clip, front (the hero faces -forward) and the shirt's side
                var sdir = Path.Combine(Dir, "survey"); Directory.CreateDirectory(sdir);
                float[] at = { .25f, .4f, .55f, .7f, .85f };
                foreach (var id in player.hero.Emotes.ToList())
                {
                    float len = player.hero.ClipLength(id);
                    foreach (var f in at)
                    {
                        player.hero.Hold(id, f * len);
                        for (int i = 0; i < 12; i++) yield return null;   // the fade in (.15 s) and the solvers settle
                        var c2 = (B(HumanBodyBones.UpperChest) ?? B(HumanBodyBones.Chest)).position;
                        var m2 = root.position + up * .95f;
                        Aim(cam, m2, m2 - fwd * 4.0f, 32); Save(cam, Path.Combine(sdir, $"{id}_{f:0.00}_front.jpg"));
                        Aim(cam, c2, c2 + right * 1.5f - fwd * .4f, 36); Save(cam, Path.Combine(sdir, $"{id}_{f:0.00}_side.jpg"));
                    }
                }
                player.hero.Stop();
                yield break;
            }
            // idle: three moments of the stand's breathing / weight shift
            for (int k = 0; k < 3; k++)
            {
                for (float t = 0; t < 1.3f; t += Time.unscaledDeltaTime) yield return null;
                Shots($"idle{k}");
            }
            // an emote, three moments
            string emote = Environment.GetEnvironmentVariable("HC_EMOTE");
            if (string.IsNullOrEmpty(emote)) emote = player.hero ? player.hero.Emotes.FirstOrDefault(e => e.StartsWith("Emote")) : null;
            log.Add("emotes\t" + (player.hero ? string.Join(",", player.hero.Emotes) : "-"));
            if (!string.IsNullOrEmpty(emote) && player.PlayEmote(emote))
                for (int k = 0; k < 3; k++)
                {
                    for (float t = 0; t < .6f; t += Time.unscaledDeltaTime) yield return null;
                    Shots($"emote{k}");
                }
            File.WriteAllLines(Path.Combine(Dir, "renderers.tsv"), log);
            Object.DestroyImmediate(cam.gameObject);
        }
    }
}

using System;
using System.Collections;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// MENU HERO (work/menu-hero, chat G): plaza stills of the local hero standing still: front, 3/4 back, back, each sex, with the back pick
    /// MH_BACK (golf_bag | racket_back), through the real NativeSportsSession hub start. Only runs with MH_OUT set (installed into the chat's clone only).
    public class MenuHeroPlazaProof
    {
        const int W = 1080, H = 1350;
        static string Dir => Environment.GetEnvironmentVariable("MH_OUT");
        GameObject host;
        [TearDown] public void Clean() { HubWorld.EditorDriven = false; if (host) Object.DestroyImmediate(host); }

        [UnityTest, Timeout(600000)] public IEnumerator Plaza([Values(false, true)] bool female, [Values("golf_bag", "racket_back")] string pick)
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("MH_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0;
            LogAssert.ignoreFailingMessages = true;   // the male face fit logs a pre-existing invariant error (chat F's neck relax, reported separately)
            string back = Environment.GetEnvironmentVariable("MH_BACK") ?? pick, tag = (Environment.GetEnvironmentVariable("MH_TAG") ?? "after") + "_" + back;
            if (Environment.GetEnvironmentVariable("MH_BACK") != null && pick != "golf_bag") { Assert.Ignore("single pick run"); yield break; }
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "hub-test", action = "start", sport = "hub", female = female, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = back }));
            for (int i = 0; i < 900 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); var p = hub.Player; var cam = hub.Camera;
            if (hub.Arriving) { hub.HurryArrival(); for (int i = 0; i < 300 && hub.Arriving; i++) yield return null; }
            p.Teleport(HubLayout.Spawn, 0); yield return new WaitForSeconds(2.5f);
            var hero = p.look.transform; var acc = HeroAccessories.For(p.look);
            File.AppendAllText(Path.Combine(Dir, "report.txt"), $"{(female ? "female" : "male")} {tag}: back item {acc.Item(AccessorySlot.BackCarry)} visible {acc.IsVisible(AccessorySlot.BackCarry)}\n");
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            float fov = cam.fieldOfView; cam.fieldOfView = 30;
            void Shot(string name, float yawDeg)
            {
                var c = hero.position + Vector3.up * .95f;
                var dir = Quaternion.AngleAxis(yawDeg, Vector3.up) * hero.forward;
                cam.transform.SetPositionAndRotation(c + dir * 4.2f + Vector3.up * .25f, Quaternion.LookRotation(-dir * 4.2f - Vector3.up * .25f));
                var prevA = cam.aspect; cam.aspect = W / (float)H; cam.targetTexture = rt; cam.Render(); cam.Render(); cam.targetTexture = null; cam.aspect = prevA;
                RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
                File.WriteAllBytes(Path.Combine(Dir, $"plaza_{tag}_{(female ? "female" : "male")}_{name}.png"), tex.EncodeToPNG());
            }
            Shot("front", 0); Shot("back34", 145); Shot("back", 180);
            cam.fieldOfView = fov; rt.Release(); Object.DestroyImmediate(rt); Object.DestroyImmediate(tex);
        }
    }
}

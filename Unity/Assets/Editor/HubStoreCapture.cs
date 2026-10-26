#if UNITY_EDITOR
using System;
using System.Collections;
using System.IO;
using GolfArcade.Hub;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// App Store landscape shots (2868x1320) of the real plaza and Locker Room, no phone panels (those live on the phone).
    /// -executeMethod GolfArcade.EditorTools.HubStoreCapture.Run, APPSTORE_OUT=<dir>.
    [InitializeOnLoad]
    public static class HubStoreCapture
    {
        const string Key = "HubStoreCapture"; const int W = 2868, H = 1320;
        static IEnumerator script; static int last = -1; static RenderTexture rt;
        static string Out => SessionState.GetString(Key + "out", ".");

        static HubStoreCapture() { EditorApplication.update += Tick; }
        public static void Run()
        {
            var o = Environment.GetEnvironmentVariable("APPSTORE_OUT") ?? Path.GetFullPath("../work/appstore-shots/hub");
            Directory.CreateDirectory(o); SessionState.SetString(Key + "out", o); SessionState.SetBool(Key, true);
            SessionState.SetBool(Key + "female", Environment.GetEnvironmentVariable("HUB_MALE") != "1");
            EditorSceneManager.OpenScene("Assets/Scenes/Hub.unity"); EditorApplication.isPlaying = true;
        }

        static void Tick()
        {
            if (!SessionState.GetBool(Key, false) || !EditorApplication.isPlaying || last == Time.frameCount) return;
            last = Time.frameCount;
            try
            {
                HubWorld.StartFemale = SessionState.GetBool(Key + "female", true);
                if (script == null) { var h = HubWorld.Find(); if (!h || !h.Initialized || !h.Camera) return; script = Shots(h); }
                if (!script.MoveNext()) Finish(0);
            }
            catch (Exception e) { Debug.LogException(e); File.WriteAllText(Path.Combine(Out, "hub_error.txt"), e.ToString()); Finish(1); }
        }
        static void Finish(int code) { SessionState.SetBool(Key, false); Time.captureFramerate = 0; EditorApplication.Exit(code); }

        static void Shot(Camera cam, string name)
        {
            if (!rt) { rt = new RenderTexture(W, H, 24) { antiAliasing = 4 }; rt.Create(); }
            var keep = cam.targetTexture; cam.targetTexture = rt; cam.aspect = (float)W / H; cam.Render(); cam.targetTexture = keep; cam.ResetAspect();
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false); var a = RenderTexture.active;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = a;
            File.WriteAllBytes(Path.Combine(Out, name + ".png"), tex.EncodeToPNG()); Object.DestroyImmediate(tex);
            Debug.Log("[HubStoreCapture] wrote " + name);
        }
        static IEnumerator Wait(int n) { for (int i = 0; i < n; i++) yield return null; }

        static readonly RemoteState[] Friends =
        {
            new RemoteState { id = "f1", name = "Milo", female = false, colour = 1, skinHex = "C47A4C", shirt = "FF5B4A", shorts = "F6F3EB", accent = "F6F3EB", place = HubLayout.Plaza },
            new RemoteState { id = "f2", name = "Ava", female = true, colour = 2, skinHex = "F3C9A6", shirt = "38C6FF", shorts = "1F2C5C", accent = "F6F3EB", place = HubLayout.Plaza },
            new RemoteState { id = "f3", name = "Leo", female = false, colour = 3, skinHex = "965835", shirt = "1FBF75", shorts = "16204A", accent = "F6F3EB", place = HubLayout.Plaza },
        };

        static IEnumerator Shots(HubWorld hub)
        {
            Time.captureFramerate = 30; HubWorld.EditorDriven = true;
            bool female = SessionState.GetBool(Key + "female", true);
            hub.ApplyLook(female, "EEBB8F", 1, "1F2C5C", "F6F3EB", "F6F3EB", "", "golf_bag");
            var cam = hub.Camera; var p = hub.Player;
            var remotes = HubRemotes.For(hub);
            // friends walking about the plaza, relayed the way the phones relay them (x, z, facing yaw, speed)
            Vector3[] from = { new Vector3(-3.0f, 0, -4.5f), new Vector3(2.6f, 0, -5.2f), new Vector3(-1.4f, 0, 1.0f) };
            Vector3[] dir = { new Vector3(.15f, 0, 1).normalized, new Vector3(-.1f, 0, 1).normalized, new Vector3(.6f, 0, -.8f).normalized };
            float[] speed = { .55f, .5f, 0f };
            float clock = 0;
            void Relay()
            {
                for (int i = 0; i < Friends.Length; i++)
                {
                    var f = Friends[i]; var at = from[i] + dir[i] * speed[i] * clock;
                    var s = new RemoteState { id = f.id, name = f.name, female = f.female, colour = f.colour, skinHex = f.skinHex, shirt = f.shirt, shorts = f.shorts, accent = f.accent, place = f.place,
                        x = at.x, y = 0, z = at.z, yaw = Mathf.Atan2(dir[i].x, dir[i].z) * Mathf.Rad2Deg, speed = speed[i] };
                    remotes.Receive(s);
                }
            }
            // 1) the real opening shot: the camera circles down over the plaza to behind the hero
            hub.PrepareArrival();
            for (int i = 0; i < 30; i++) { Relay(); clock += 1 / 30f; yield return null; }
            Shot(cam, "plaza_arrival_00");
            hub.StartArrival();
            for (int k = 1; k <= 4; k++) { for (int i = 0; i < 16; i++) { Relay(); clock += 1 / 30f; yield return null; } Shot(cam, "plaza_arrival_" + k.ToString("00")); }
            for (int i = 0; i < 40; i++) { Relay(); clock += 1 / 30f; yield return null; }
            // 2) the hero walking north toward the PLAY hall, friends around
            for (int k = 0; k < 6; k++)
            {
                for (int i = 0; i < 14; i++) { p.SetStick(k < 3 ? .12f : -.1f, 1, .62f); Relay(); clock += 1 / 30f; yield return null; }
                Shot(cam, "plaza_walk_" + k.ToString("00"));
            }
            p.SetStick(0, 0, 0); remotes.Roster(new string[0]);
            yield return Wait(10);
            // 3) the Locker Room: each outfit at the mirror (the TV frames the hero; the phone shows the panel)
            string[][] looks =
            {
                new[] { "EEBB8F", "1F2C5C", "F6F3EB", "F6F3EB", "", "golf_bag" },
                new[] { "EEBB8F", "FF5B4A", "F6F3EB", "F6F3EB", "", "racket_back" },
                new[] { "EEBB8F", "E6B94E", "16204A", "F6F3EB", "", "golf_bag" },
                new[] { "EEBB8F", "38C6FF", "F6F3EB", "1F2C5C", "", "racket_back" },
            };
            (string spot, int look)[] plan = { ("look-mirror", 0), ("look-mirror", 1), ("look-mirror", 2), ("look-mirror", 3), ("rack-club", 2), ("rack-club", 0), ("rack-racket", 1), ("rack-racket", 3), ("rack-shirt", 1) };
            string at = null;
            foreach (var (spot, look) in plan)
            {
                var l = looks[look];
                if (at != spot)
                {
                    hub.LeaveStation(); yield return Wait(2);
                    Debug.Log($"[HubStoreCapture] pre {spot}: trans={hub.Transitioning} arriving={hub.Arriving} place={hub.Place} zone={hub.ZoneId} fade={hub.FadeAlpha} dt={Time.unscaledDeltaTime}");
                    for (int t = 0; t < 120 && !hub.GoTo(spot, true); t++) yield return null;
                    at = spot; yield return Wait(2);
                    for (int t = 0; t < 400 && hub.Transitioning; t++) yield return null;
                    yield return Wait(5);
                    if (hub.Station == null) { var sp = HubLayout.SpotById(spot); p.Teleport(sp.position - sp.facing * .2f, Mathf.Atan2(sp.facing.x, sp.facing.z) * Mathf.Rad2Deg); yield return Wait(3); bool ok = hub.Interact(); Debug.Log($"[HubStoreCapture] interact {spot}: {ok} trans={hub.Transitioning} arriving={hub.Arriving} place={hub.Place} zone={hub.ZoneId} pos={p.transform.position}"); }
                    yield return Wait(30);
                    Debug.Log($"[HubStoreCapture] {spot}: place={hub.Place} station={hub.Station?.id}");
                }
                hub.ApplyLook(female, l[0], 1, l[1], l[2], l[3], l[4], l[5]);
                yield return Wait(30);
                Shot(cam, $"locker_{spot}_{look}");
            }
            // 4) the Locker Room from the walking view (no station)
            hub.LeaveStation(); yield return Wait(2); for (int t = 0; t < 120 && !hub.GoTo(HubLayout.Locker); t++) yield return null; yield return Wait(2); for (int t = 0; t < 400 && hub.Transitioning; t++) yield return null; yield return Wait(20);
            hub.ApplyLook(female, "EEBB8F", 1, "1F2C5C", "F6F3EB", "F6F3EB", "", "golf_bag");
            for (int i = 0; i < 20; i++) { p.SetStick(0, 1, .5f); yield return null; }
            p.SetStick(0, 0, 0); yield return Wait(20);
            Shot(cam, "locker_room_walk");
        }
    }
}
#endif

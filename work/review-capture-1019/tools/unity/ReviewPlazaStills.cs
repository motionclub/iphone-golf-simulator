#if UNITY_EDITOR
// Review capture 10-19 (work/review-capture-1019): the TV plaza (Hub) through the real NativeSportsSession hub start, as chat G's
// MenuHeroPlazaProof does: the plaza camera's own view, then the seven-angle still set of the local hero, male then female.
using System;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Hub;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.EditorTools
{
    [InitializeOnLoad]
    public static class ReviewPlazaStills
    {
        const string Flag = "ReviewPlazaStills.Active";
        static ReviewPlazaStills() { EditorApplication.update += Boot; }
        public static void Run()
        {
            EditorUtility.audioMasterMute = true;
            EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<ReviewPlazaDriver>()) return;
            AudioListener.volume = 0; EditorUtility.audioMasterMute = true;
            var go = new GameObject("Review plaza driver"); Object.DontDestroyOnLoad(go); go.AddComponent<ReviewPlazaDriver>();
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    public sealed class ReviewPlazaDriver : MonoBehaviour
    {
        System.Collections.IEnumerator Start()
        {
            string dir = Path.Combine(Path.GetFullPath(ReviewShared.Env("REVIEW_OUT", Path.Combine(Environment.GetEnvironmentVariable("HOME"), "review-1019-frames/plaza"))), "stills");
            Directory.CreateDirectory(dir);
            var log = new StreamWriter(Path.Combine(dir, "..", "events.txt"));
            Time.captureFramerate = 30;
            int code = 0;
            foreach (bool female in new[] { false, true })
            {
                HubWorld.EditorDriven = true;
                var host = new GameObject("NativeSportsSession"); DontDestroyOnLoad(host);
                var bridge = host.AddComponent<NativeSportsSession>();
                bridge.Receive(JsonUtility.ToJson(new NativeSportsSession.Message { version = 1, session = "hub-review", action = "start", sport = "hub", female = female, touch = true, shirt = "E8505B", shorts = "24345E", accent = "FFFFFF", back = "golf_bag" }));
                for (int i = 0; i < 900 && !bridge.Ready; i++) yield return null;
                var hub = HubWorld.Find();
                if (!hub) { log.WriteLine("no hub, female " + female); code = 1; break; }
                if (hub.Arriving) { hub.HurryArrival(); for (int i = 0; i < 300 && hub.Arriving; i++) yield return null; }
                var p = hub.Player; p.Teleport(HubLayout.Spawn, 0);
                for (int i = 0; i < 90; i++) yield return null;
                string sex = female ? "female" : "male";
                // the plaza camera's own view, as on the TV
                var cam = hub.Camera;
                var view = new ReviewAngle("plaza_view", null, 1920, 1080);
                view.Aim(cam.transform.position, cam.transform.position + cam.transform.forward * 10); view.Fov = cam.fieldOfView;
                view.Render(cam, Path.Combine(dir, $"plaza_{sex}_0_tv_camera.jpg"));
                Destroy(view.Cam.gameObject);
                ReviewShared.Stills(cam, p.look, dir, "plaza_" + sex);
                log.WriteLine($"{sex}: stills done, hero at {p.look.transform.position}"); log.Flush();
                Destroy(host); HubWorld.EditorDriven = false;
                for (int i = 0; i < 30; i++) yield return null;
            }
            log.Dispose();
            ReviewPlazaStills.End(code);
        }
    }
}
#endif

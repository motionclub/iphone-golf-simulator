using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using GolfArcade.Tennis;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    [DefaultExecutionOrder(32000)]
    public sealed class TaiRecorder : MonoBehaviour
    {
        static TaiRecorder live; public static void Stop() { if (live) live.Close(); }
        public bool Done;
        TennisGame game; string dir; int maxTicks, tick; bool video;
        StreamWriter frames, events; BinaryWriter bones; Process ff, ffG; Stream ffIn, ffGIn; RenderTexture rtFull; Texture2D full;
        HeroTennisDriver[] drivers = new HeroTennisDriver[2]; MatchHeroLook[] looks = new MatchHeroLook[2]; TennisActor[] actors = new TennisActor[2];
        Camera[] side = new Camera[2]; Camera handCam; RenderTexture rtGame, rtSide, rtHand; Texture2D comp; readonly Vector3[] handAt = new Vector3[4]; Vector3[] sideAt = new Vector3[2];
        static readonly FieldInfo paceField = typeof(TennisActor).GetField("swingPace", BindingFlags.NonPublic | BindingFlags.Instance);
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static string F(float f) => f.ToString("0.#####", Inv);
        const int W = 1920, H = 1080, GW = 1280, GH = 720, SW = 640, SH = 360, HW = 480, HH = 360;
        public void Begin(TennisGame g, string outDir, bool withVideo, string ffmpeg, int ticks)
        {
            live = this; gameObject.AddComponent<TaiPrePolish>().recorder = this; game = g; dir = outDir; maxTicks = ticks; video = withVideo;
            frames = new StreamWriter(Path.Combine(dir, "frames.csv"));
            frames.WriteLine("tick,hero,role,flow,rallyShots,state,clip,clipTime,weights,upperW,actionW,swinging,kind,backhand,ttc,swingPace,prepare,prepareServe,speed,fwdSpeed,guiding,finalSink,groundLift,sinkBefore,footSkate,steps,hits,score,soleBefore,soleAfter,blends,swingStarts");
            events = new StreamWriter(Path.Combine(dir, "events.csv"));
            events.WriteLine("tick,event,who,grade,gap,stringsToBall,clip,clipTime");
            bones = new BinaryWriter(File.Create(Path.Combine(dir, "bones.f32")));
            TennisGame.ContactMade += OnContact; TennisGame.OpponentStruck += OnRival; TennisGame.Whiffed += OnWhiff;
            if (video)
            {
                rtGame = new RenderTexture(GW, GH, 24); rtSide = new RenderTexture(SW, SH, 24); rtHand = new RenderTexture(HW, HH, 24); comp = new Texture2D(W, H, TextureFormat.RGB24, false);
                for (int i = 0; i < 2; i++) { side[i] = new GameObject("TAI side " + i).AddComponent<Camera>(); side[i].enabled = false; side[i].fieldOfView = 26; side[i].nearClipPlane = .1f; side[i].targetTexture = rtSide; }
                handCam = new GameObject("TAI hand").AddComponent<Camera>(); handCam.enabled = false; handCam.fieldOfView = 30; handCam.nearClipPlane = .03f; handCam.targetTexture = rtHand;
                if (string.IsNullOrEmpty(ffmpeg) || !File.Exists(ffmpeg)) throw new FileNotFoundException("TAI_FFMPEG");
                ff = Process.Start(new ProcessStartInfo {
                    FileName = ffmpeg,
                    Arguments = $"-y -hide_banner -loglevel error -f rawvideo -pix_fmt rgb24 -s {W}x{H} -framerate 60 -i pipe:0 -vf vflip -an -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -movflags +faststart \"{Path.Combine(dir, "film.mp4")}\"",
                    UseShellExecute = false, RedirectStandardInput = true, CreateNoWindow = true });
                ffIn = ff.StandardInput.BaseStream;
                // the gameplay camera alone at 1920x1080 / 60 fps (Adnan's 1080p60 target): stepping and pops show at full size
                rtFull = new RenderTexture(1920, 1080, 24); full = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
                ffG = Process.Start(new ProcessStartInfo {
                    FileName = ffmpeg,
                    Arguments = $"-y -hide_banner -loglevel error -f rawvideo -pix_fmt rgb24 -s 1920x1080 -framerate 60 -i pipe:0 -vf vflip -an -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -movflags +faststart \"{Path.Combine(dir, "film_game_1080p60.mp4")}\"",
                    UseShellExecute = false, RedirectStandardInput = true, CreateNoWindow = true });
                ffGIn = ffG.StandardInput.BaseStream;
            }
            var meta = new StringBuilder("{\"bones\":[");
            for (int b = 0; b < (int)HumanBodyBones.LastBone; b++) meta.Append((b > 0 ? "," : "") + "\"" + (HumanBodyBones)b + "\"");
            meta.Append("],\"layout\":\"per frame per hero (player then rival): tick, heroIndex, root pos3 rot4, actor pos3, ball pos3, strings pos3, grip pos3 rot4, grip lossyScale1, pre-polish finger joints (both hands, 5 fingers x 3 joints) pos3 x30, then for each bone pos3 rot4 (NaN when missing)\",");
            meta.Append($"\"head\":116,\"fps\":60,\"gameSpeed\":{F(TennisGame.GameSpeed)},\"jitter\":{F(TennisGame.AutoPlayTimingJitter)}");
            meta.Append("}");
            File.WriteAllText(Path.Combine(dir, "meta.json"), meta.ToString());
        }
        void Resolve()
        {
            actors[0] = game.Player; actors[1] = game.Opponent;
            for (int i = 0; i < 2; i++) { drivers[i] = actors[i] ? actors[i].GetComponentInChildren<HeroTennisDriver>() : null; looks[i] = drivers[i] ? drivers[i].matchLook : null; }
        }
        string Who(int i) => looks[i] ? (looks[i].female ? "female" : "male") : "?";
        void OnContact(Vector2 face, Timing grade, bool super) { Event("contact", 0, grade.ToString()); }
        void OnRival() { Event("contact", 1, ""); }
        void OnWhiff() { Event("whiff", 0, ""); }
        void Event(string what, int i, string grade)
        {
            if (frames == null) return; Resolve(); var d = drivers[i];
            float gap = d ? Vector3.Distance(d.StringCentre, game.BallPosition) : -1;
            events.WriteLine(string.Join(",", tick, what, Who(i), grade, F(game.LastContactGap), F(gap), d ? d.PlayingClip : "", d ? F(d.PlayingClipTime) : ""));
        }
        void LateUpdate()
        {
            if (Done || frames == null) return;
            Resolve();
            for (int i = 0; i < 2; i++) Row(i);
            if (video) Film();
            if (game.Match.Complete && game.Flow == TennisGame.Phase.MatchOver && matchOverTicks++ > 240)
            { matchOverTicks = 0; matchesPlayed++; events.WriteLine($"{tick},rematch,,,,,,"); game.ConfigureMatch(TennisGame.Mode.Exhibition, game.OpponentKey, null, "INTEGRITY"); game.Refeed(); }
            if (++tick >= maxTicks) Close();
            if (tick % 1800 == 0) UnityEngine.Debug.Log($"[TAI] t={tick / 60}s score={game.Match.Scoreboard} hits={game.Hits}");
        }
        int matchOverTicks, matchesPlayed;
        void Row(int i)
        {
            var d = drivers[i]; var a = actors[i]; var l = looks[i]; if (!d || !a || !l) return;
            float pace = paceField != null ? (float)paceField.GetValue(a) : -1;
            frames.WriteLine(string.Join(",", tick, Who(i), i == 0 ? "player" : "rival", game.Flow, game.RallyShots, "\"" + d.State + "\"", d.PlayingClip, F(d.PlayingClipTime),
                "\"" + d.WeightReport().Trim() + "\"", F(d.UpperLayerWeight), F(d.ActionWeight), a.Swinging, a.Kind, a.Backhand, F(a.SignedTimeToContact), F(pace),
                F(a.PrepareAmount), a.PrepareServe, F(a.Speed), F(a.ForwardSpeed), a.Guiding, F(d.FinalSink), F(d.LastGroundLift), F(d.SinkBeforeGround), F(d.FootSkate), d.StepsTaken,
                game.Hits, "\"" + game.Match.Scoreboard + "\"", F(P(d, "SoleDipBefore")), F(P(d, "SoleDipAfter")), (int)P(d, "TransitionsBlended"), (int)P(d, "SwingStarts")));
            bones.Write((float)tick); bones.Write((float)i);
            W3(d.transform.position); W4(d.transform.rotation); W3(a.transform.position); W3(game.BallPosition); W3(d.StringCentre);
            var g = l.racketGrip; W3(g ? g.position : Vector3.positiveInfinity); W4(g ? g.rotation : Quaternion.identity);
            bones.Write(g ? g.lossyScale.x : 0f);
            var pre = TaiPrePolish.Fingers(l); for (int k = 0; k < 30; k++) { var v = pre != null ? pre[k] : Vector3.positiveInfinity; W3(v); }
            for (int b = 0; b < (int)HumanBodyBones.LastBone; b++)
            {
                var t = l.Bone((HumanBodyBones)b);
                if (t) { W3(t.position); W4(t.rotation); } else for (int k = 0; k < 7; k++) bones.Write(float.NaN);
            }
        }
        static float P(object o, string name)
        {
            var p = o.GetType().GetProperty(name); if (p == null) return -1;
            var v = p.GetValue(o); return v is float f ? f : v is int i ? i : -1;
        }
        void W3(Vector3 v) { bones.Write(v.x); bones.Write(v.y); bones.Write(v.z); }
        void W4(Quaternion q) { bones.Write(q.x); bones.Write(q.y); bones.Write(q.z); bones.Write(q.w); }
        void Film()
        {
            var cam = game.GameplayCamera; var prev = cam.targetTexture;
            float aspect = cam.aspect;
            try { cam.targetTexture = rtFull; cam.aspect = 16f / 9f; cam.Render(); } finally { cam.targetTexture = prev; cam.aspect = aspect; }
            var active = RenderTexture.active;
            RenderTexture.active = rtFull; full.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            { var fb = full.GetRawTextureData<byte>().ToArray(); ffGIn.Write(fb, 0, fb.Length); }
            Graphics.Blit(rtFull, rtGame);
            RenderTexture.active = rtGame; comp.ReadPixels(new Rect(0, 0, GW, GH), 0, H - GH);
            // bottom row: right and left hand close-ups of the player, then of the rival (0.5 m off the hand, from the hero's outside and front)
            for (int k = 0; k < 4; k++)
            {
                var l = looks[k / 2]; if (!l) continue; bool right = k % 2 == 0;
                var hand = l.Bone(right ? HumanBodyBones.RightHand : HumanBodyBones.LeftHand); var mid = l.Bone(right ? HumanBodyBones.RightMiddleProximal : HumanBodyBones.LeftMiddleProximal); if (!hand) continue;
                var focus = mid ? Vector3.Lerp(hand.position, mid.position, .6f) : hand.position;
                handAt[k] = handAt[k] == Vector3.zero ? focus : Vector3.Lerp(handAt[k], focus, .5f);
                var root = l.transform; var dir = (root.forward * .8f + root.right * (right ? .7f : -.7f) + Vector3.up * .25f).normalized;
                handCam.transform.position = handAt[k] + dir * .5f; handCam.transform.LookAt(handAt[k]);
                handCam.Render(); RenderTexture.active = rtHand; comp.ReadPixels(new Rect(0, 0, HW, HH), k * HW, 0);
            }
            for (int i = 0; i < 2; i++)
            {
                var l = looks[i]; if (!l) continue; var hips = l.Bone(HumanBodyBones.Hips); if (!hips) continue;
                // side view from the court's +x side (the player's forehand side; the rival's backhand side), 4.2 m out, chest height
                var focus = new Vector3(hips.position.x, .95f, hips.position.z);
                if (sideAt[i] == Vector3.zero) sideAt[i] = focus; else sideAt[i] = Vector3.Lerp(sideAt[i], focus, .25f);
                side[i].transform.position = sideAt[i] + new Vector3(4.6f, .25f, 0); side[i].transform.LookAt(sideAt[i] + Vector3.up * .05f);
                side[i].Render();
                RenderTexture.active = rtSide; comp.ReadPixels(new Rect(0, 0, SW, SH), GW, i == 0 ? H - SH : H - 2 * SH);
            }
            RenderTexture.active = active;
            var raw = comp.GetRawTextureData<byte>();
            var buf = raw.ToArray(); ffIn.Write(buf, 0, buf.Length);
        }
        void Close()
        {
            if (Done) return; Done = true;
            TennisGame.ContactMade -= OnContact; TennisGame.OpponentStruck -= OnRival; TennisGame.Whiffed -= OnWhiff;
            frames?.Close(); events?.Close(); bones?.Close(); frames = null;
            if (ff != null) { ffIn.Close(); ff.WaitForExit(60000); }
            if (ffG != null) { ffGIn.Close(); ffG.WaitForExit(60000); }
            File.WriteAllText(Path.Combine(dir, "done.txt"), $"ticks={tick} score={game.Match.Scoreboard} hits={game.Hits} complete={game.Match.Complete}\n");
        }
        void OnDestroy() => Close();
    }

    /// Runs after the driver (1000) and HeroPoseSafety, before HeroGripPolish (1160): the finger joints as the driver left them.
    [DefaultExecutionOrder(1100)]
    public sealed class TaiPrePolish : MonoBehaviour
    {
        public TaiRecorder recorder;
        static readonly System.Collections.Generic.Dictionary<MatchHeroLook, Vector3[]> store = new System.Collections.Generic.Dictionary<MatchHeroLook, Vector3[]>();
        public static Vector3[] Fingers(MatchHeroLook l) => l && store.TryGetValue(l, out var v) ? v : null;
        static readonly HumanBodyBones[] Joints = MakeJoints();
        static HumanBodyBones[] MakeJoints()
        {
            var list = new System.Collections.Generic.List<HumanBodyBones>();
            foreach (var side in new[] { "Left", "Right" }) foreach (var f in new[] { "Thumb", "Index", "Middle", "Ring", "Little" }) foreach (var j in new[] { "Proximal", "Intermediate", "Distal" })
                        list.Add((HumanBodyBones)Enum.Parse(typeof(HumanBodyBones), side + f + j));
            return list.ToArray();
        }
        void LateUpdate()
        {
            foreach (var l in FindObjectsByType<MatchHeroLook>(FindObjectsSortMode.None))
            {
                if (!store.TryGetValue(l, out var v)) store[l] = v = new Vector3[30];
                for (int k = 0; k < 30; k++) { var t = l.Bone(Joints[k]); v[k] = t ? t.position : Vector3.positiveInfinity; }
            }
        }
    }
}

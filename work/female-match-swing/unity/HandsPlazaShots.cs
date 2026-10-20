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
    public static class HandsPlazaShots
    {
        const string Flag = "HandsPlazaShots.Active";
        static HandsPlazaShots() { EditorApplication.update += Boot; }
        public static void Run()
        {
            EditorUtility.audioMasterMute = true;
            EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Boot()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || Object.FindFirstObjectByType<HandsPlazaDriver>()) return;
            AudioListener.volume = 0; EditorUtility.audioMasterMute = true;
            var go = new GameObject("Hands plaza driver"); Object.DontDestroyOnLoad(go); go.AddComponent<HandsPlazaDriver>();
        }
        public static void End(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
    }

    public sealed class HandsPlazaDriver : MonoBehaviour
    {
        System.Collections.IEnumerator Start()
        {
            string dir = Path.Combine(Path.GetFullPath(ReviewShared.Env("REVIEW_OUT", Path.Combine(Environment.GetEnvironmentVariable("HOME"), "female-swing-frames/hands"))), "stills");
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
                for (int i = 0; i < 60; i++) yield return null;
                var look = p.look; var cam = hub.Camera; var an = look.animator;
                Transform B(HumanBodyBones bb) => look.Bone(bb);
                var lh = B(HumanBodyBones.LeftHand); var rh = B(HumanBodyBones.RightHand);
                var mid = (lh.position + rh.position) * .5f; var fwd = look.transform.forward; var right = look.transform.right;
                var ang = new ReviewAngle("hands", null, 900, 900);
                void Shot(string name, Vector3 pos, Vector3 look_, float fov) { ang.Aim(pos, look_); ang.Fov = fov; var path = Path.Combine(dir, $"hands_{sex}_{name}.jpg"); ang.Render(cam, path); ang.Render(cam, path); }
                // the hand reference sheet's angles on the RIGHT hand: everything but the body skin is hidden, so a view from inside the thigh / skirt still sees the hand
                { var names = new System.Collections.Generic.List<string>(); foreach (var r in look.GetComponentsInChildren<Renderer>(true)) { names.Add(r.name); bool skin = look.body && r == look.body; if (!skin) r.enabled = false; } log.WriteLine("renderers: " + string.Join(", ", names)); }
                {   // keep only the right hand + forearm skin triangles so no thigh / skirt skin gets between the camera and the hand
                    var mesh = look.body.sharedMesh; var pal = look.body.bones; var wts = mesh.boneWeights; var keepV = new bool[wts.Length];
                    for (int v = 0; v < wts.Length; v++)
                    {
                        float sum = 0; var bw = wts[v]; int[] ii = { bw.boneIndex0, bw.boneIndex1, bw.boneIndex2, bw.boneIndex3 }; float[] ww = { bw.weight0, bw.weight1, bw.weight2, bw.weight3 };
                        for (int k = 0; k < 4; k++) { if (ww[k] <= 0 || ii[k] < 0 || ii[k] >= pal.Length || !pal[ii[k]]) continue; var nm = pal[ii[k]].name; if (nm.StartsWith("Right") && (nm.Contains("Hand") || nm.Contains("Thumb") || nm.Contains("Index") || nm.Contains("Middle") || nm.Contains("Ring") || nm.Contains("Little") || nm.Contains("LowerArm")) || nm.StartsWith("ArmBlend_")) sum += ww[k]; }
                        keepV[v] = sum >= .5f;
                    }
                    var only = Object.Instantiate(mesh); only.name = mesh.name + " (hand only)";
                    for (int sub = 0; sub < mesh.subMeshCount; sub++) { var t = mesh.GetTriangles(sub); var keep = new System.Collections.Generic.List<int>(); for (int i = 0; i + 2 < t.Length; i += 3) if (keepV[t[i]] && keepV[t[i + 1]] && keepV[t[i + 2]]) { keep.Add(t[i]); keep.Add(t[i + 1]); keep.Add(t[i + 2]); } only.SetTriangles(keep, sub, false); }
                    look.body.sharedMesh = only; look.body.updateWhenOffscreen = true;
                }
                var backdrop = GameObject.CreatePrimitive(PrimitiveType.Quad); Object.Destroy(backdrop.GetComponent<Collider>());
                backdrop.GetComponent<Renderer>().sharedMaterial = new Material(Shader.Find("Unlit/Color")) { color = new Color(.86f, .86f, .85f) }; backdrop.transform.localScale = Vector3.one * 3;
                {   // joint angles of the relaxed right hand (deg): wrist = forearm vs hand axis; per finger MCP / PIP / DIP bend
                    var sb = new System.Text.StringBuilder(); string sd = "Right";
                    Transform J(string n) => B((HumanBodyBones)System.Enum.Parse(typeof(HumanBodyBones), sd + n));
                    var fa = J("LowerArm"); var ha = J("Hand"); var mp = J("MiddleProximal");
                    float wrist = Vector3.Angle(ha.position - fa.position, mp.position - ha.position);
                    sb.Append($"{sex} wrist {wrist:F0}; ");
                    foreach (var f in new[] { "Index", "Middle", "Ring", "Little", "Thumb" })
                    {
                        var p0 = J(f + "Proximal"); var p1 = J(f + "Intermediate"); var p2 = J(f + "Distal");
                        var tip = p2.childCount > 0 ? p2.GetChild(0).position : p2.position + (p2.position - p1.position) * .8f;
                        float mcp = Vector3.Angle(p0.position - ha.position, p1.position - p0.position), pip = Vector3.Angle(p1.position - p0.position, p2.position - p1.position), dip = Vector3.Angle(p2.position - p1.position, tip - p2.position);
                        sb.Append($"{f} {mcp:F0}/{pip:F0}/{dip:F0}  ");
                    }
                    log.WriteLine(sb.ToString()); log.Flush();
                }
                var hb = B(HumanBodyBones.RightHand); var mi = B(HumanBodyBones.RightMiddleIntermediate); var ip = B(HumanBodyBones.RightIndexProximal); var lp = B(HumanBodyBones.RightLittleProximal);
                var along = (mi.position - hb.position).normalized; var lat = (ip.position - lp.position).normalized; var nrm = Vector3.Cross(along, lat).normalized; lat = Vector3.Cross(nrm, along).normalized;
                var ctr = (hb.position + mi.position) * .5f; float dist = .8f;
                // which way is the palm: toward the thumb-side thigh; pick the sign so "palm" looks at the inside of the hand (the side the fingers curl toward)
                var hipsB = B(HumanBodyBones.Hips); var inward = Vector3.ProjectOnPlane(hipsB.position - hb.position, Vector3.up).normalized; var curl = inward; // the relaxed stand: palm toward the thigh
                var palmDir = curl; var dorsalDir = -curl;
                log.WriteLine($"{sex} ctr {ctr} along {along} lat {lat} nrm {nrm} curl {curl} hero {look.transform.position}"); log.Flush();
                void V(string name, Vector3 dir) { var dn = dir.normalized; backdrop.transform.position = ctr - dn * .45f; backdrop.transform.rotation = Quaternion.LookRotation(-dn); Shot(name, ctr + dn * dist, ctr, 17); }
                V("1_dorsal", dorsalDir); V("2_palm", palmDir); V("3_thumb", lat); V("4_pinky", -lat);
                V("5_front", along); V("6_rear", -along); V("7_q_dorsal", dorsalDir + along * .6f); V("8_q_palm", palmDir + along * .6f);
                V("9_q_thumb_back", lat - along * .6f); V("10_q_pinky_back", -lat - along * .6f);
                var full = look.transform.position + Vector3.up * .95f;
                
                Destroy(backdrop); Destroy(ang.Cam.gameObject);
                log.WriteLine($"{sex}: hand shots done, hero at {p.look.transform.position}"); log.Flush();
                Destroy(host); HubWorld.EditorDriven = false;
                for (int i = 0; i < 30; i++) yield return null;
            }
            log.Dispose();
            HandsPlazaShots.End(code);
        }
    }
}
#endif

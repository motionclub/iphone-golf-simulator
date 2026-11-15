using System;
using System.Collections;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Tennis;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

namespace GolfArcade.Tests
{
    /// Hero look before/after (work/hero-look-1111): the menu hero in the menu's own light — the menu camera's view, a full body,
    /// the face and the torso. HL_OUT = folder, HL_FEMALE=1, HL_SHIRT / HL_SHORTS / HL_ACCENT / HL_SKIN = hex picks, HL_TAG = file prefix.
    public class HeroLookCapture
    {
        static string Dir => Environment.GetEnvironmentVariable("HL_OUT");
        static string E(string k, string d) { var v = Environment.GetEnvironmentVariable(k); return string.IsNullOrEmpty(v) ? d : v; }
        GameObject host;
        [TearDown] public void Clean() { Time.captureFramerate = 0; HubWorld.EditorDriven = false; HubWorld.MenuMode = false; if (host) Object.DestroyImmediate(host); }

        static void Save(Camera cam, string path, int W, int H)
        {
            var a = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            var rt = new RenderTexture(W, H, 24, RenderTextureFormat.ARGB32) { antiAliasing = a ? Mathf.Max(1, a.msaaSampleCount) : 1 };
            var tex = new Texture2D(W, H, TextureFormat.RGB24, false);
            var prevA = cam.aspect; cam.aspect = (float)W / H; cam.targetTexture = rt; cam.Render(); cam.targetTexture = null; cam.aspect = prevA;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, W, H), 0, 0); tex.Apply(); RenderTexture.active = null;
            File.WriteAllBytes(path, tex.EncodeToJPG(92)); Object.DestroyImmediate(tex); rt.Release();
        }
        static void Aim(Camera cam, Vector3 at, Vector3 from, float fov)
        { cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(at - from, Vector3.up)); cam.fieldOfView = fov; cam.nearClipPlane = .02f; }

        [UnityTest, Timeout(900000)] public IEnumerator Capture()
        {
            if (string.IsNullOrEmpty(Dir)) { Assert.Ignore("HL_OUT not set"); yield break; }
            Directory.CreateDirectory(Dir); AudioListener.volume = 0; LogAssert.ignoreFailingMessages = true;
            string tag = E("HL_TAG", "hero");
            HubWorld.EditorDriven = true;
            host = new GameObject("NativeSportsSession"); Object.DontDestroyOnLoad(host);
            var bridge = host.AddComponent<NativeSportsSession>();
            var msg = new NativeSportsSession.Message { version = 1, session = "hero-look", action = "start", sport = "hub", menu = true, leader = true, playerName = "Adnan",
                female = E("HL_FEMALE", "0") == "1", touch = true, shirt = E("HL_SHIRT", "E8505B"), shorts = E("HL_SHORTS", "24345E"), accent = E("HL_ACCENT", "FFFFFF"), back = "racket_back" };
            var skin = E("HL_SKIN", ""); if (skin != "") msg.skinHex = skin;
            bridge.Receive(JsonUtility.ToJson(msg));
            for (int i = 0; i < 1500 && !bridge.Ready; i++) yield return null;
            var hub = HubWorld.Find(); Assert.IsNotNull(hub?.Menu, "menu mode");
            hub.StartArrival();
            for (float t = 0; t < 3f; t += Time.unscaledDeltaTime) yield return null;
            foreach (var tr in hub.GetComponentsInChildren<Transform>(true))
                if (tr.name.StartsWith("Name tag") || tr.name == "Hub prompt") tr.gameObject.SetActive(false);
            if (hub.Hud) hub.Hud.Canvas.enabled = false;
            var player = hub.Player; var look = player.look; Assert.IsNotNull(look, "hero look");
            // ---- prototype options (test side only; none of this is game code) ----
            Color Hex(string h) { ColorUtility.TryParseHtmlString("#" + h, out var c); return c; }
            var acc = HeroAccessories.For(look);
            if (E("HL_NOCAP", "0") == "1") acc.SetVisible(AccessorySlot.Headwear, false);
            var capPick = E("HL_CAP", ""); if (capPick != "") { var c = capPick.Split(','); acc.SetColours(AccessorySlot.Headwear, Hex(c[0]), c.Length > 1 ? Hex(c[1]) : (Color?)null); }
            if (E("HL_FINISH", "") == "matte")
                foreach (var r in look.GetComponentsInChildren<Renderer>(true)) if (r.name == "Kit_Top") foreach (var m in r.sharedMaterials)
                    if (m && m.HasProperty("_StyleSmooth")) { m.SetFloat("_StyleSmooth", .30f); m.SetFloat("_StyleSpec", .25f); m.SetFloat("_StyleEnv", .10f); }
#if UNITY_EDITOR
            if (E("HL_HAIR", "0") == "1")
            {
                bool f = E("HL_FEMALE", "0") == "1";
                var prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Characters/HeroBase/Hair/Hair_Default_{(f ? "Female" : "Male")}.prefab");
                var headBone = look.Bone(HumanBodyBones.Head); int hi = Array.IndexOf(look.body.bones, headBone);
                if (prefab && hi >= 0)
                {
                    // hair is authored in model space; the body mesh's space is the skinned node's: head-local = bindpose * (model -> mesh)
                    var hair = Object.Instantiate(prefab, headBone, false);
                    var modelToMesh = (look.transform.worldToLocalMatrix * look.body.transform.localToWorldMatrix).inverse;
                    var bp = look.body.sharedMesh.bindposes[hi] * modelToMesh;
                    hair.transform.localPosition = bp.GetColumn(3); hair.transform.localRotation = bp.rotation; hair.transform.localScale = bp.lossyScale;
                    Debug.Log($"[HeroLook] hair local pos {hair.transform.localPosition} rot {hair.transform.localEulerAngles} scale {hair.transform.localScale} world {hair.transform.position} head {headBone.position} bodyNode pos {look.body.transform.localPosition} rot {look.body.transform.localEulerAngles} scale {look.body.transform.lossyScale}");
                    foreach (var t in hair.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = look.body.gameObject.layer;
                    var hc = E("HL_HAIRHEX", ""); if (hc != "") foreach (var r in hair.GetComponentsInChildren<Renderer>(true)) foreach (var m in r.materials) if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", Hex(hc));
                }
            }
#endif
            { var hs = float.Parse(E("HL_HEADSCALE", "1"), System.Globalization.CultureInfo.InvariantCulture); if (hs != 1) look.Bone(HumanBodyBones.Head).localScale = Vector3.one * hs;
              var ks = float.Parse(E("HL_HANDSCALE", "1"), System.Globalization.CultureInfo.InvariantCulture); if (ks != 1) { look.Bone(HumanBodyBones.LeftHand).localScale = Vector3.one * ks; look.Bone(HumanBodyBones.RightHand).localScale = Vector3.one * ks; } }
            if (E("HL_LOOKAT", "0") == "1")
            {
                // head towards the menu camera: the idle looks over the viewer's head
                var hb = look.Bone(HumanBodyBones.Head); var la = look.Bone(HumanBodyBones.LeftUpperArm).position; var ra = look.Bone(HumanBodyBones.RightUpperArm).position;
                var toCam = hub.Camera.transform.position - hb.position; var flat = toCam; flat.y = 0; flat.Normalize();
                Vector3 best = hb.forward; float bd = -2;
                foreach (var ax in new[] { hb.forward, -hb.forward, hb.up, -hb.up, hb.right, -hb.right }) { float d = Vector3.Dot(new Vector3(ax.x, 0, ax.z).normalized, flat); if (Mathf.Abs(ax.y) < .75f && d > bd) { bd = d; best = ax; } }
                var want = Quaternion.FromToRotation(best, toCam.normalized); want.ToAngleAxis(out float ang, out var axis); if (ang > 180) ang -= 360;
                hb.rotation = Quaternion.AngleAxis(Mathf.Clamp(ang * .85f, -35, 35), axis) * hb.rotation;
            }
            Save(hub.Camera, Path.Combine(Dir, tag + "_menu_view.jpg"), 1920, 1080);
            var cam = new GameObject("Hero cam").AddComponent<Camera>(); cam.CopyFrom(hub.Camera); cam.enabled = false;
            // what the player sees: the menu camera's post-processing (CopyFrom leaves the URP camera data behind)
            { var d = cam.GetUniversalAdditionalCameraData(); var s = hub.Camera.GetUniversalAdditionalCameraData(); d.renderPostProcessing = E("HL_POST", "1") == "1" && s.renderPostProcessing; d.volumeLayerMask = s.volumeLayerMask; d.antialiasing = s.antialiasing; d.renderShadows = s.renderShadows; }
            var head = look.Bone(HumanBodyBones.Head).position; var chest = (look.Bone(HumanBodyBones.UpperChest) ?? look.Bone(HumanBodyBones.Chest)).position;
            var root = player.transform.position; var up = Vector3.up;
            var fwd = hub.Camera.transform.position - root; fwd.y = 0; fwd.Normalize(); var right = Vector3.Cross(up, fwd);
            var mid = root + up * .92f;
            Aim(cam, mid, mid + fwd * 4.0f + right * 1.1f, 30); Save(cam, Path.Combine(Dir, tag + "_body.jpg"), 1080, 1440);
            Aim(cam, mid, mid - fwd * 4.0f + right * 1.1f, 30); Save(cam, Path.Combine(Dir, tag + "_body_back.jpg"), 1080, 1440);
            Aim(cam, head + up * .06f, head + up * .08f + fwd * 1.15f + right * .28f, 26); Save(cam, Path.Combine(Dir, tag + "_face.jpg"), 1080, 1080);
            Aim(cam, chest, chest + fwd * 1.5f + right * .3f + up * .05f, 34); Save(cam, Path.Combine(Dir, tag + "_torso.jpg"), 1080, 1080);
            var info = "sun"; foreach (var l in Object.FindObjectsByType<Light>(FindObjectsSortMode.None)) if (l.enabled && l.gameObject.activeInHierarchy) info += $"\n{l.name} {l.type} col={l.color} int={l.intensity} dir={l.transform.forward}";
            info += $"\nambientMode={RenderSettings.ambientMode} sky={RenderSettings.ambientSkyColor} eq={RenderSettings.ambientEquatorColor} gnd={RenderSettings.ambientGroundColor} amb={RenderSettings.ambientLight} int={RenderSettings.ambientIntensity}";
            foreach (var v in Object.FindObjectsByType<Volume>(FindObjectsSortMode.None)) { info += $"\nVOLUME {v.name} w={v.weight} global={v.isGlobal} prio={v.priority}"; if (v.profile) foreach (var c in v.profile.components) if (c.active) info += $"\n   {c.GetType().Name}"; }
            foreach (var r in look.GetComponentsInChildren<Renderer>(true)) if (r.enabled && r.gameObject.activeInHierarchy) foreach (var m in r.sharedMaterials) if (m) info += $"\nREND {r.name} mat={m.name} shader={m.shader.name}";
            int total = 0; foreach (var r in look.GetComponentsInChildren<Renderer>(true)) { if (!r.enabled || !r.gameObject.activeInHierarchy) continue; Mesh me = r is SkinnedMeshRenderer sk ? sk.sharedMesh : r.GetComponent<MeshFilter>() ? r.GetComponent<MeshFilter>().sharedMesh : null; if (!me) continue; int t = 0; for (int i = 0; i < me.subMeshCount; i++) t += (int)(me.GetIndexCount(i) / 3); total += t; info += $"\nTRIS {r.name} {t} verts={me.vertexCount} submeshes={me.subMeshCount} blendshapes={me.blendShapeCount}"; }
            info += $"\nTRIS_TOTAL {total}  bones={look.body.bones.Length}";
            { var hb2 = look.Bone(HumanBodyBones.Head); float top = look.body.bounds.max.y, ground = player.transform.position.y; info += $"\nHEIGHT {top - ground:F3} headBoneY {hb2.position.y - ground:F3}"; }
            File.WriteAllText(Path.Combine(Dir, tag + "_scene.txt"), info);
        }
    }
}

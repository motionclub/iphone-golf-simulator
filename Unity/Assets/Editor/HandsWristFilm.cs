#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using GolfArcade.Game;
using GolfArcade.Hub;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace GolfArcade.EditorTools
{
    /// 10-27 hands/wrist proof (Adnan: "the female character has fucked up wrists/hands, super obvious when she walks ... make sure this
    /// looks right for all sports"). Every hero kit (tennis match hero, bowling kit, golf kit) of both sexes walks in place on the plaza's
    /// own animator (HubHeroAnimator), and each frame renders the whole hero plus a close-up of each hand from BakeMesh copies (offscreen
    /// renders do not re-skin, see BowlingFix1027.SaveBaked).
    ///   HWF_OUT=<dir> [HWF_FRAMES=48] [FEMALE_WRIST_SHAPE=0 for the old wrist] Unity -batchmode -projectPath <clone> -executeMethod GolfArcade.EditorTools.HandsWristFilm.Run
    /// Writes <dir>/<sex>_<kit>_<view>_NNN.png (view = body, handL, handR).
    [InitializeOnLoad]
    public static class HandsWristFilm
    {
        const string Flag = "HandsWristFilm"; static IEnumerator script; static int lastFrame = -1;
        static HandsWristFilm() { EditorApplication.update += Tick; }
        public static void Run()
        {
            script = null; lastFrame = -1;
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene);
            EditorUtility.audioMasterMute = true;
            SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return;
            lastFrame = Time.frameCount;
            try { if (script == null) script = Go(); if (!script.MoveNext()) Done(0); }
            catch (Exception e) { Debug.LogException(e); Done(1); }
        }
        static void Done(int c) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(c); else EditorApplication.isPlaying = false; }

        static IEnumerator Go()
        {
            string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("HWF_OUT") ?? "../work/hands-ball-20261027/hwf"); Directory.CreateDirectory(dir);
            int frames = int.Parse(Environment.GetEnvironmentVariable("HWF_FRAMES") ?? "48");
            Time.captureFramerate = 30;
            var cam = new GameObject("HWF camera").AddComponent<Camera>(); cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(.62f, .70f, .78f); cam.nearClipPlane = .02f;
            var key = new GameObject("Key").AddComponent<Light>(); key.type = LightType.Directional; key.intensity = 1.3f; key.transform.rotation = Quaternion.Euler(35, -40, 0);
            var fill = new GameObject("Fill").AddComponent<Light>(); fill.type = LightType.Directional; fill.intensity = .45f; fill.transform.rotation = Quaternion.Euler(20, 140, 0);
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat; RenderSettings.ambientLight = new Color(.42f, .42f, .45f);
            var heroes = new List<(string name, GameObject go, MatchHeroLook look, HubHeroAnimator anim)>();
            int slot = 0;
            foreach (bool female in new[] { false, true })
                foreach (var (kit, path) in new[] { ("tennis", HeroAssets.Match(female)), ("bowling", HeroAssets.Bowling(female)), ("golf", HeroAssets.GolfKitPrefab(female)) })
                {
                    var prefab = Resources.Load<GameObject>(path); if (!prefab) { Debug.Log("[HandsWristFilm] missing " + path); continue; }
                    GameObject go = null;
                    try
                    {
                        go = Object.Instantiate(prefab, new Vector3(slot * 3f, 0, 0), Quaternion.identity); slot++;
                        foreach (var d in go.GetComponentsInChildren<HeroTennisDriver>(true)) d.enabled = false;
                        var look = go.GetComponentInChildren<MatchHeroLook>();
                        if (look && look.racketGrip) foreach (var r in look.racketGrip.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
                        var anim = HubHeroAnimator.Attach(go);
                        if (!look || !anim) { Debug.Log("[HandsWristFilm] no look/animator on " + path); Object.Destroy(go); continue; }
                        heroes.Add(((female ? "female" : "male") + "_" + kit, go, look, anim));
                    }
                    catch (Exception e) { Debug.Log("[HandsWristFilm] skip " + path + ": " + e.Message); if (go) Object.Destroy(go); }
                }
            for (int i = 0; i < 45; i++) { foreach (var h in heroes) h.anim.Tick(1.25f, Time.deltaTime); yield return null; }
            // wrist angles per frame: the hand's axis (wrist -> middle knuckle) against the forearm's, split into flexion (toward the palm +)
            // and deviation (toward the thumb +), in the hand's own frame
            var csv = new System.Text.StringBuilder("frame,hero,side,flex,dev,total\n");
            for (int f = 0; f < frames; f++)
            {
                foreach (var h in heroes) h.anim.Tick(1.25f, Time.deltaTime);
                yield return null;
                foreach (var h in heroes)
                {
                    var t = h.go.transform; var look = h.look;
                    // only this hero is drawn
                    foreach (bool left in new[] { true, false })
                    {
                        var g = HeroBallGrip.Find(look.Bone, left); var la = look.Bone(left ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
                        if (!HeroBallGrip.Valid(g) || !la) continue;
                        HeroBallGrip.Palm(g, out _, out var pn, out var ax, out var ac);
                        var fore = (g.hand.position - la.position).normalized;
                        float flex = -Mathf.Atan2(Vector3.Dot(fore, pn), Vector3.Dot(fore, ax)) * Mathf.Rad2Deg;   // >0: hand bent toward the palm
                        float dev = -Mathf.Atan2(Vector3.Dot(fore, ac), Vector3.Dot(fore, ax)) * Mathf.Rad2Deg;    // >0: hand bent toward the thumb
                        csv.Append($"{f},{h.name},{(left ? "L" : "R")},{flex:0.0},{dev:0.0},{Vector3.Angle(fore, ax):0.0}\n");
                    }
                    var made = Bake(h.go);
                    try
                    {
                        var hip = look.Bone(HumanBodyBones.Hips); var c = hip ? hip.position : t.position + Vector3.up;
                        Shot(cam, $"{dir}/{h.name}_body_{f:000}.png", c + t.forward * 2.6f + t.right * 1.2f + Vector3.up * .25f, c + Vector3.up * .05f, 38, 480, 640);
                        foreach (bool left in new[] { true, false })
                        {
                            var hand = look.Bone(left ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
                            var mid = look.Bone(left ? HumanBodyBones.LeftMiddleProximal : HumanBodyBones.RightMiddleProximal);
                            if (!hand) continue;
                            var at = mid ? Vector3.Lerp(hand.position, mid.position, .25f) : hand.position;
                            var side = left ? -t.right : t.right;
                            Shot(cam, $"{dir}/{h.name}_hand{(left ? "L" : "R")}_{f:000}.png", at + side * .38f + t.forward * .30f + Vector3.up * .06f, at, 35, 480, 640);
                        }
                    }
                    finally { Unbake(made); }
                }
            }
            File.WriteAllText(Path.Combine(dir, "wrist.csv"), csv.ToString());
            Debug.Log($"[HandsWristFilm] heroes={heroes.Count} frames={frames} out={dir}");
        }

        static readonly List<Renderer> hidden = new List<Renderer>();
        static List<(SkinnedMeshRenderer smr, GameObject copy)> Bake(GameObject root)
        {
            var made = new List<(SkinnedMeshRenderer, GameObject)>(); hidden.Clear();
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None)) if (!r.forceRenderingOff && (!r.transform.IsChildOf(root.transform) || r is SkinnedMeshRenderer)) { r.forceRenderingOff = true; hidden.Add(r); }
            foreach (var smr in root.GetComponentsInChildren<SkinnedMeshRenderer>())
            {
                if (!smr.enabled || !smr.sharedMesh || !hidden.Contains(smr)) continue;   // (already forced off: a LOD proxy or a hidden garment)
                var mesh = new Mesh(); smr.BakeMesh(mesh, true);
                var go = new GameObject(smr.name + " (baked)");
                go.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                go.AddComponent<MeshFilter>().sharedMesh = mesh;
                go.AddComponent<MeshRenderer>().sharedMaterials = smr.sharedMaterials;
                made.Add((smr, go));
            }
            return made;
        }
        static void Unbake(List<(SkinnedMeshRenderer smr, GameObject copy)> made)
        {
            foreach (var (smr, go) in made) { Object.DestroyImmediate(go.GetComponent<MeshFilter>().sharedMesh); Object.DestroyImmediate(go); }
            foreach (var r in hidden) if (r) r.forceRenderingOff = false;
            hidden.Clear();
        }
        static void Shot(Camera cam, string path, Vector3 from, Vector3 look, float fov, int w, int h)
        {
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(look - from)); cam.fieldOfView = fov;
            var rt = RenderTexture.GetTemporary(w, h, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4);
            cam.targetTexture = rt; cam.Render(); cam.targetTexture = null;
            var tex = new Texture2D(w, h, TextureFormat.RGB24, false); var act = RenderTexture.active;
            RenderTexture.active = rt; tex.ReadPixels(new Rect(0, 0, w, h), 0, 0); tex.Apply(); RenderTexture.active = act; RenderTexture.ReleaseTemporary(rt);
            File.WriteAllBytes(path, tex.EncodeToPNG()); Object.DestroyImmediate(tex);
        }
    }
}
#endif

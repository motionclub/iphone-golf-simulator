#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Globalization;
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
    /// Chat 4: samples every tennis clip of both match heroes at 120 Hz on the real prefab (racket at the game's 1.3x),
    /// raw and after HeroGripPolish.ApplyGrip, plus the lowest shoe/sole vertex per foot.
    /// TAI_DUMP_OUT=<dir>. Extra clips to compare: every AnimationClip under Assets/TAI_Extra/<Male|Female>/<tag>/ (FBX or .anim).
    /// Output per hero: <Sex>_clips.json (name, slot, length, contact, leftRelease, frameRate, key spacing) and <Sex>_<tag>_<clip>.f32
    /// (per sample: t, strings3, grip pos3 rot4, 55 bones pos3 rot4 raw, 55 bones pos3 rot4 polished, soleMinY L/R).
    public static class TennisAnimClipDump
    {
        const float Rate = 120;
        static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
        static string F(float f) => f.ToString("0.#####", Inv);
        public static void Run()
        {
            EditorUtility.audioMasterMute = true; AudioListener.volume = 0;   // Adnan: every Unity run muted
            string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("TAI_DUMP_OUT") ?? "../work/tennis-anim-integrity/clipdump");
            Directory.CreateDirectory(dir);
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            foreach (bool female in new[] { false, true }) Dump(female, dir);
            if (Application.isBatchMode) EditorApplication.Exit(0);
        }
        static void Dump(bool female, string dir)
        {
            string sex = female ? "Female" : "Male";
            var prefab = TennisCustomization.HeroBase(female);
            var go = (GameObject)Object.Instantiate(prefab); go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            var driver = go.GetComponentInChildren<HeroTennisDriver>(true); var look = driver.matchLook;
            driver.ResolvePerformanceClips();
            var root = look.animator.gameObject;
            look.racketGrip.localScale *= TennisRules.HeroRacketScale;
            var shoes = go.GetComponentsInChildren<SkinnedMeshRenderer>(true).Where(r => r.sharedMesh && (r.name.Contains("Shoe") || r.name.Contains("Sole") || r.sharedMesh.name.Contains("Shoe") || r.sharedMesh.name.Contains("Sole"))).ToArray();
            var list = new List<(string tag, string slot, AnimationClip clip, float contact, float release)>();
            foreach (var s in driver.slots) if (s.clip) list.Add(("live", s.id.ToString(), s.clip, s.contact, s.leftRelease));
            string extra = "Assets/TAI_Extra/" + sex;
            if (AssetDatabase.IsValidFolder(extra))
                foreach (var g in AssetDatabase.FindAssets("t:AnimationClip", new[] { extra }))
                {
                    var p = AssetDatabase.GUIDToAssetPath(g); string tag = Path.GetFileName(Path.GetDirectoryName(p));
                    foreach (var c in AssetDatabase.LoadAllAssetsAtPath(p).OfType<AnimationClip>()) if (!c.name.StartsWith("__preview")) list.Add((tag, "", c, -1, -1));
                }
            var json = new StringBuilder("[\n"); bool first = true;
            var done = new HashSet<string>();
            foreach (var (tag, slot, clip, contact, release) in list)
            {
                string key = tag + "_" + clip.name; string file = sex + "_" + key + ".f32";
                if (!done.Add(key)) { Append(json, ref first, tag, slot, clip, contact, release, file, true); continue; }
                using (var w = new BinaryWriter(File.Create(Path.Combine(dir, file))))
                {
                    int n = Mathf.CeilToInt(clip.length * Rate) + 1;
                    var baked = new Mesh();
                    for (int f = 0; f < n; f++)
                    {
                        float t = Mathf.Min(f / Rate, clip.length);
                        clip.SampleAnimation(root, t);
                        w.Write(t); W3(w, look.racketGrip.TransformPoint(look.stringCentreLocal)); W3(w, look.racketGrip.position); W4(w, look.racketGrip.rotation);
                        Bones(w, look);
                        HeroGripPolish.ApplyGrip(look);
                        Bones(w, look);
                        float l = 9, r = 9; var lf = look.Bone(HumanBodyBones.LeftFoot).position; var rf = look.Bone(HumanBodyBones.RightFoot).position;
                        foreach (var s in shoes)
                        {
                            s.BakeMesh(baked, true); var m = s.transform.localToWorldMatrix; var v = baked.vertices;
                            for (int i = 0; i < v.Length; i++) { var p = m.MultiplyPoint3x4(v[i]); if ((p - lf).sqrMagnitude < (p - rf).sqrMagnitude) l = Mathf.Min(l, p.y); else r = Mathf.Min(r, p.y); }
                        }
                        w.Write(l); w.Write(r);
                    }
                    Object.DestroyImmediate(baked);
                }
                Append(json, ref first, tag, slot, clip, contact, release, file, false);
            }
            json.Append("\n]\n");
            File.WriteAllText(Path.Combine(dir, sex + "_clips.json"), json.ToString());
            Object.DestroyImmediate(go);
        }
        static void Append(StringBuilder json, ref bool first, string tag, string slot, AnimationClip clip, float contact, float release, string file, bool dup)
        {
            float minDt = float.MaxValue, maxDt = 0; int curves = 0;
            foreach (var b in AnimationUtility.GetCurveBindings(clip))
            {
                var c = AnimationUtility.GetEditorCurve(clip, b); if (c == null || c.length < 2) continue; curves++;
                for (int k = 1; k < c.length; k++) { float dt = c.keys[k].time - c.keys[k - 1].time; if (dt > 1e-5f) { minDt = Mathf.Min(minDt, dt); maxDt = Mathf.Max(maxDt, dt); } }
            }
            if (!first) json.Append(",\n"); first = false;
            json.Append($"{{\"tag\":\"{tag}\",\"slot\":\"{slot}\",\"clip\":\"{clip.name}\",\"path\":\"{AssetDatabase.GetAssetPath(clip)}\",\"length\":{F(clip.length)},\"contact\":{F(contact)},\"leftRelease\":{F(release)},\"frameRate\":{F(clip.frameRate)},\"minKeyDt\":{F(minDt == float.MaxValue ? 0 : minDt)},\"maxKeyDt\":{F(maxDt)},\"curves\":{curves},\"file\":\"{file}\",\"dup\":{(dup ? "true" : "false")}}}");
        }
        static void Bones(BinaryWriter w, MatchHeroLook look)
        {
            for (int b = 0; b < (int)HumanBodyBones.LastBone; b++)
            {
                var t = look.Bone((HumanBodyBones)b);
                if (t) { W3(w, t.position); W4(w, t.rotation); } else for (int k = 0; k < 7; k++) w.Write(float.NaN);
            }
        }
        static void W3(BinaryWriter w, Vector3 v) { w.Write(v.x); w.Write(v.y); w.Write(v.z); }
        static void W4(BinaryWriter w, Quaternion q) { w.Write(q.x); w.Write(q.y); w.Write(q.z); w.Write(q.w); }
    }
}
#endif

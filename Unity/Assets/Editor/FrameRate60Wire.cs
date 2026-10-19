using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using GolfArcade.Tennis;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// FRAME_RATE_60: installs the match clips that work/frame-rate-60 re-baked on a 60 Hz grid (the solver ran at 1/60 s steps, so the fast
    /// phases of a swing are sampled twice as finely instead of being joined by straight lines between 30 Hz poses).
    ///   Unity -batchmode -nographics -quit -projectPath Unity -executeMethod GolfArcade.EditorTools.FrameRate60Wire.Run      (env FR60_REPO = repo root, default "..")
    /// It copies the FBXs over the installed ones (same .meta, same clip names, same lengths), then moves each prefab slot's contact / leftRelease
    /// to the 60 Hz table (a clip's contact is rounded to the grid, so a few move by one 1/60 s frame). ReadyIdle (the base model) and the
    /// clips another job owns (Serve, Walk, Run*, emotes) are not touched here. Rollback: Run with FR60_SOURCE=work/match-anim-set/export/fbx and
    /// FR60_TABLE pointing at a table of the 30 Hz values (see work/frame-rate-60/README.md).
    public static class FrameRate60Wire
    {
        [Serializable] public class Row { public string name, sex, fbxSha256; public float length, contact, leftRelease; public int frames; }
        [Serializable] public class Table { public int fps; public Row[] clips; }
        const string Dir = "Assets/Characters/MatchHeroes/", PrefabDir = "Assets/Resources/Tennis/Customization/";
        public static string Repo => Path.GetFullPath(Environment.GetEnvironmentVariable("FR60_REPO") ?? "..");
        public static string Source => Environment.GetEnvironmentVariable("FR60_SOURCE") ?? Repo + "/work/frame-rate-60/match-anim-set/fbx/";
        public static string TablePath => Environment.GetEnvironmentVariable("FR60_TABLE") ?? Repo + "/work/frame-rate-60/match-anim-set/clip_table_60.json";
        static bool Wired(Row r) => r.name != MatchHeroPostprocessor.BaseClip && !ServeAndFeetWire.Owns(r.name);
        static string FbxPath(string sex, string clip) => Dir + sex + "/" + sex + "_" + clip + ".fbx";

        public static void Run()
        {
            int code = 0;
            try
            {
                var table = JsonUtility.FromJson<Table>(File.ReadAllText(TablePath));
                var log = new System.Text.StringBuilder();
                foreach (var r in table.clips.Where(Wired))
                {
                    string src = Source + r.sex + "_" + r.name + ".fbx", dst = FbxPath(r.sex, r.name);
                    if (!File.Exists(src)) throw new FileNotFoundException(src);
                    File.Copy(src, dst, true);
                    log.AppendLine($"copied {r.sex}_{r.name}");
                }
                AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
                foreach (var r in table.clips.Where(Wired)) AssetDatabase.ImportAsset(FbxPath(r.sex, r.name), ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
                foreach (var sex in new[] { "Male", "Female" })
                    foreach (var file in Directory.GetFiles(PrefabDir, "Player" + sex + "*.prefab")) log.Append(WirePrefab(file.Replace('\\', '/'), sex, table));
                AssetDatabase.SaveAssets();
                Debug.Log("FR60 DONE\n" + log);
            }
            catch (Exception e) { Debug.LogError("FR60 FAILED " + e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }

        /// After install_fbx.sh (or its rollback): re-import every hero clip FBX the job touched so Unity's cache matches the files on disk.
        public static void Reimport()
        {
            int code = 0;
            try
            {
                int n = 0;
                foreach (var root in new[] { "Assets/Characters/MatchHeroes", "Assets/Resources/HeroMoves" })
                    foreach (var f in Directory.GetFiles(root, "*.fbx", SearchOption.AllDirectories)) { AssetDatabase.ImportAsset(f.Replace('\\', '/'), ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate); n++; }
                AssetDatabase.SaveAssets();
                Debug.Log("FR60 REIMPORTED " + n);
            }
            catch (Exception e) { Debug.LogError("FR60 FAILED " + e); code = 1; }
            if (Application.isBatchMode) EditorApplication.Exit(code);
        }

        static string WirePrefab(string path, string sex, Table table)
        {
            var sb = new System.Text.StringBuilder("== " + path + "\n");
            var root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var driver = root.GetComponentInChildren<HeroTennisDriver>(true);
                if (!driver) { sb.AppendLine("  no driver"); return sb.ToString(); }
                var slots = driver.slots; int changed = 0;
                for (int i = 0; i < slots.Length; i++)
                {
                    if (!slots[i].clip) continue;
                    string name = slots[i].clip.name;
                    var row = table.clips.FirstOrDefault(c => c.sex == sex && Wired(c) && sex + "_" + c.name == name);
                    if (row == null) continue;
                    var clip = AssetDatabase.LoadAllAssetsAtPath(FbxPath(sex, row.name)).OfType<AnimationClip>().FirstOrDefault(c => c.name == name);
                    if (!clip) throw new InvalidOperationException("clip missing after import: " + name);
                    if (Mathf.Abs(clip.length - row.length) > .003f) throw new InvalidOperationException($"{name}: imported length {clip.length} != table {row.length}");
                    if (!Mathf.Approximately(slots[i].contact, row.contact) || !Mathf.Approximately(slots[i].leftRelease, row.leftRelease)) changed++;
                    sb.AppendLine($"  {slots[i].id,-16} {name,-24} len={clip.length:0.000} contact {slots[i].contact:0.0000} -> {row.contact:0.0000}  leftRelease {slots[i].leftRelease:0.0000} -> {row.leftRelease:0.0000}");
                    slots[i].clip = clip; slots[i].contact = row.contact; slots[i].leftRelease = row.leftRelease;
                }
                driver.slots = slots;
                PrefabUtility.SaveAsPrefabAsset(root, path);
                sb.AppendLine($"  slots with a moved time: {changed}");
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            return sb.ToString();
        }
    }
}

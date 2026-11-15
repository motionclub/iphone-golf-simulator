#if UNITY_EDITOR
using System; using System.Collections; using System.IO;
using UnityEditor; using UnityEditor.SceneManagement; using UnityEngine;
using Object = UnityEngine.Object;
namespace GolfArcade.Tennis
{
    /// CLOTH JIGGLE A/B film (clothing-mm clone): a real autoplay rally with the male hero, 60 fps game time; every 2nd frame the close
    /// hero camera renders TWICE, wobble off (_ClothJiggleGlobal 0) then on (1), so both films have identical motion.
    ///   Unity -batchmode (graphics on) -executeMethod GolfArcade.Tennis.ClothJiggleFilm.Run   env CJF_OUT=<dir> CJF_FRAMES=<game frames>
    [InitializeOnLoad] public static class ClothJiggleFilm
    {
        const string Flag = "ClothJiggleFilm"; static IEnumerator script; static int lastFrame = -1;
        static ClothJiggleFilm() { EditorApplication.update += Tick; }
        public static void Run()
        {
            var ti = (TextureImporter)AssetImporter.GetAtPath("Assets/Resources/Tennis/KitsV2/Male/KitV2_Tennis_Male_Top_J.png");
            if (ti && (ti.sRGBTexture || ti.mipmapEnabled || ti.textureCompression != TextureImporterCompression.Uncompressed))
            { ti.sRGBTexture = false; ti.mipmapEnabled = false; ti.textureCompression = TextureImporterCompression.Uncompressed; ti.wrapMode = TextureWrapMode.Clamp; ti.SaveAndReimport(); }
            script = null; lastFrame = -1; EditorSceneManager.OpenScene("Assets/Scenes/Tennis.unity"); SessionState.SetBool(Flag, true); EditorApplication.isPlaying = true;
        }
        static void Tick()
        {
            if (!SessionState.GetBool(Flag, false) || !EditorApplication.isPlaying || lastFrame == Time.frameCount) return; lastFrame = Time.frameCount;
            var game = Object.FindFirstObjectByType<TennisGame>(); if (!game || !game.Initialized) return;
            if (script == null) script = Go(game);
            try { if (!script.MoveNext()) Done(0); } catch (Exception e) { Debug.LogException(e); Done(1); }
        }
        static void Done(int code) { SessionState.SetBool(Flag, false); Time.captureFramerate = 0; if (Application.isBatchMode) EditorApplication.Exit(code); else EditorApplication.isPlaying = false; }
        static void Shot(Camera cam, Transform root, string file)
        {
            var p = cam.transform.position; var q = cam.transform.rotation; float fov = cam.fieldOfView;
            var from = root.TransformPoint(2.3f, 1.35f, 2.1f); var at = root.TransformPoint(0, 1.0f, .05f);
            cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(at - from)); cam.fieldOfView = 40;
            var rt = RenderTexture.GetTemporary(720, 720, 24, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default, 4); var target = cam.targetTexture; var active = RenderTexture.active;
            cam.targetTexture = rt; cam.Render(); cam.targetTexture = target; RenderTexture.active = rt;
            var image = new Texture2D(720, 720, TextureFormat.RGB24, false); image.ReadPixels(new Rect(0, 0, 720, 720), 0, 0); image.Apply();
            File.WriteAllBytes(file, image.EncodeToPNG()); Object.DestroyImmediate(image); RenderTexture.active = active; RenderTexture.ReleaseTemporary(rt);
            cam.transform.SetPositionAndRotation(p, q); cam.fieldOfView = fov;
        }
        static IEnumerator Go(TennisGame game)
        {
            string dir = Path.GetFullPath(Environment.GetEnvironmentVariable("CJF_OUT") ?? "../work/clothing-mm/polo/film");
            int frames = int.Parse(Environment.GetEnvironmentVariable("CJF_FRAMES") ?? "900");
            Directory.CreateDirectory(Path.Combine(dir, "off")); Directory.CreateDirectory(Path.Combine(dir, "on")); Directory.CreateDirectory(Path.Combine(dir, "game"));
            Time.captureFramerate = 60;
            var presentation = game.GetComponent<TennisPresentation>(); if (presentation) presentation.Finish();
            game.SelectCharacter(false); game.ConfigureMatch(TennisGame.Mode.Campaign, "Nadia", "Nadia", "ROUND"); if (presentation) presentation.Finish();
            for (int n = 0; n < 30; n++) yield return null;
            var driver = game.Player.GetComponentInChildren<HeroTennisDriver>();
            foreach (var skin in driver.GetComponentsInChildren<SkinnedMeshRenderer>(true)) skin.updateWhenOffscreen = true;
            // CJF_KIT=shirt,shorts,shoes (hex): film in a given kit (e.g. the studio turnaround look 2F6FD6,F4F0E6,FFFFFF)
            var kit = Environment.GetEnvironmentVariable("CJF_KIT");
            if (!string.IsNullOrEmpty(kit)) { var k = kit.Split(','); var look = game.Player.GetComponentInChildren<MatchHeroLook>(true); if (look) look.SetKit(k[0], k[1], k[2]); Debug.Log("[ClothJiggleFilm] kit " + kit + (look ? "" : " (no MatchHeroLook)")); }
            var jig = game.Player.GetComponentInChildren<ClothJiggle>(true);
            Debug.Log("[ClothJiggleFilm] jiggle component " + (jig ? "found on " + jig.name : "MISSING"));
            game.AutoPlay = true; game.AutoPlayLean = true; bool dived = false;
            var cam = game.GameplayCamera ? game.GameplayCamera : Camera.main;
            var log = new System.Collections.Generic.List<string> { "frame,hem,sleeveL,sleeveR,collar,accHem,accSL,accSR,accCollar" };
            for (int n = 0; n < frames; n++)
            {
                yield return null;
                if (n % 2 != 0) continue;
                string id = (n / 2).ToString("00000");
                Shader.SetGlobalFloat("_ClothJiggleGlobal", 0); Shot(cam, game.Player.transform, Path.Combine(dir, "off", id + ".png"));
                Shader.SetGlobalFloat("_ClothJiggleGlobal", 1); Shot(cam, game.Player.transform, Path.Combine(dir, "on", id + ".png"));
                GolfArcade.Game.GameCapture.Save(Path.Combine(dir, "game", id + ".png"), 1280, 720);   // the gameplay camera, as the player sees it
                if (jig && jig.material) log.Add($"{n},{jig.material.GetVector("_JigHem").magnitude * 1000:F1},{jig.material.GetVector("_JigSleeveL").magnitude * 1000:F1},{jig.material.GetVector("_JigSleeveR").magnitude * 1000:F1},{jig.material.GetVector("_JigCollar").magnitude * 1000:F1},{jig.DebugAcc.x:F1},{jig.DebugAcc.y:F1},{jig.DebugAcc.z:F1},{jig.DebugAcc.w:F1}");
            }
            File.WriteAllLines(Path.Combine(dir, "offsets_mm.csv"), log);
            Debug.Log("[ClothJiggleFilm] complete " + dir + " dived=" + dived);
        }
    }
}
#endif

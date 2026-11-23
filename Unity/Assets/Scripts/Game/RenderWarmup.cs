using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Game
{
    /// A global shader keyword switched on mid-play (the Majestic weather, MAJESTIC_WEATHER_ON) makes every world shader that carries it
    /// build its pipeline state on the first frame it draws: a visible hitch on Metal. This draws the gameplay camera's view once with the
    /// keyword the other way round, into a small offscreen target with the same MSAA, while the loading cover is still up (TennisWarmup does
    /// the same for tennis's effects).
    public static class RenderWarmup
    {
        public static void Keyword(Camera source, string keyword)
        {
            if (!source) return;
            var kw = GlobalKeyword.Create(keyword);
            bool was = Shader.IsKeywordEnabled(kw);
            var go = new GameObject("Keyword warm-up camera");
            var cam = go.AddComponent<Camera>();
            cam.CopyFrom(source);
            cam.enabled = false;
            var target = new RenderTexture(256, 144, 24, source.allowHDR ? RenderTextureFormat.DefaultHDR : RenderTextureFormat.Default)
            { antiAliasing = Mathf.Max(1, QualitySettings.antiAliasing), name = "Keyword warm-up target" };
            cam.targetTexture = target;
            try { Shader.SetKeyword(kw, !was); cam.Render(); }
            catch (System.Exception e) { Debug.LogWarning("[RenderWarmup] " + keyword + ": " + e.Message); }
            finally
            {
                Shader.SetKeyword(kw, was);
                cam.targetTexture = null; target.Release(); Object.Destroy(target); Object.Destroy(go);
            }
        }
    }
}

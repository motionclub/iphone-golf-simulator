using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Holds the frame rate when a phone cannot (tennis and bowling; golf's Luminous Coast has its own, the same logic: FramePace). If
    /// frames run late -- a slower phone, or one that has heated up -- a ProMotion phone at 120 drops to 60 first, then rendering quality
    /// steps down one notch at a time. It never steps back up within a session: oscillating between two levels would itself read as a hitch.
    public sealed class TennisFrameGovernor : MonoBehaviour
    {
        /// Seconds of grace after loading and after each change, when frame times are not representative.
        public const float Settle = 4f;
        readonly GolfArcade.Game.FrameWindow window = new GolfArcade.Game.FrameWindow(Settle);
        readonly GolfArcade.Game.PacePolicy policy = new GolfArcade.Game.PacePolicy();
        float calm; int inputRate = -1;

        void Update()
        {
            if (Application.isEditor || GolfArcade.EnvironmentArt.LuminousCoastPilot.Active) return;
            GolfArcade.Game.FramePace.Govern(this, window, policy, ref calm, ref inputRate, "governor");
        }
    }

    /// First use of a shader or particle material compiles its pipeline state, which on
    /// Metal is a visible hitch -- traditionally on the first serve or the first contact.
    /// This renders everything that will appear during play once, into an offscreen target
    /// with the same format and sample count as the real one, while the scene is loading.
    public static class TennisWarmup
    {
        public static void Run(Camera gameplay, TennisFx fx)
        {
            if (!gameplay) return;
            var go = new GameObject("Shader warm-up camera");
            var cam = go.AddComponent<Camera>();
            cam.CopyFrom(gameplay);
            cam.enabled = false;
            var target = new RenderTexture(64, 64, 24, gameplay.allowHDR ? RenderTextureFormat.DefaultHDR : RenderTextureFormat.Default)
            { antiAliasing = Mathf.Max(1, QualitySettings.antiAliasing), name = "Warm-up target" };
            cam.targetTexture = target;
            // Fire each effect once in front of the warm-up camera, then render.
            Vector3 at = cam.transform.position + cam.transform.forward * 3;
            if (fx)
            {
                fx.Contact(at, Timing.Perfect, true);
                fx.Bounce(at, Vector3.forward * 10, Color.gray);
            }
            cam.Render();
            if (fx) fx.Clear();
            cam.targetTexture = null;
            target.Release(); Object.Destroy(target); Object.Destroy(go);
        }
    }
}

using System.Collections.Generic;
using GolfArcade.Course;
using GolfArcade.Game;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Majestic
{
    /// Readability under weather (PLAN gate: ball / flag contrast >= 3:1). When the weather darkens, greys or fogs the
    /// ground, the ball (golf and tennis) and the flag get a soft self-light: an additive shell on their own meshes,
    /// scaled by how much the weather costs them (its Readability amount x how far the light has dropped). Clear weather:
    /// nothing. Shells are children of the object they light, so they move, hide and scale with it.
    public sealed class MajesticWeatherGlow
    {
        readonly Material ballMat, flagMat;
        readonly MajesticWeatherComet comet = new();
        readonly List<(Renderer source, MeshRenderer shell)> shells = new();
        Transform ballRoot, flagRoot;

        public MajesticWeatherGlow()
        {
            var s = Resources.Load<Shader>("Majestic/MajesticWeatherGlow");
            ballMat = new Material(s) { name = "Majestic weather ball glow" };
            flagMat = new Material(s) { name = "Majestic weather flag glow" };
        }

        /// How much light the weather has taken from the ball, 0..1 (sun dim, cloud deck, fog, darker sky).
        public static float Darkness(in WeatherLook k) =>
            Mathf.Clamp01(.35f * k.Cloud + .5f * Mathf.Clamp01(k.FogDensity / .012f) + .4f * (1 - k.SkyExposure) + .25f * k.Precip + .2f * k.Cover);

        public void Update(MajesticWeather w)
        {
            Find(w);
            float d = w.Active ? Darkness(w.Now) : 0;
            // a floor whenever weather is up (rain / snow / ash / fog all flatten the ball against wet, lit turf), more as it darkens
            float ball = d > .01f ? Mathf.Min(1.2f, .7f + .5f * d) : 0;
            ballMat.SetFloat("_Amount", ball);
            ballMat.SetColor("_Color", new Color(1f, .98f, .93f));
            flagMat.SetFloat("_Amount", d > .01f ? Mathf.Min(.6f, .15f + .5f * d) : 0);
            comet.Update(w, ballRoot, d, w.Tennis ? 1f : .9144f);
            for (int i = shells.Count - 1; i >= 0; i--)
            {
                var (src, shell) = shells[i];
                if (!src || !shell) { if (shell) Object.Destroy(shell.gameObject); shells.RemoveAt(i); continue; }
                shell.enabled = d > .01f && src.enabled && src.gameObject.activeInHierarchy && !src.forceRenderingOff;
            }
        }

        public void Hide() { foreach (var (_, shell) in shells) if (shell) shell.enabled = false; comet.Hide(); }

        // (10-18: the dark rim disc + contact shade behind/under the ball were removed: on the phone they read as
        //  "a weird shadow around the ball". Replaced by Adnan's pick: a warm comet outline, MajesticWeatherComet.)

        void Find(MajesticWeather w)
        {
            Transform ball = null, flag = null;
            if (!w.Tennis)
            {
                var golf = Object.FindFirstObjectByType<GolfGame>();
                if (golf) ball = golf.transform.Find("Ball");
                if (HoleView.Current) flag = HoleView.Current.Flag ? HoleView.Current.Flag.parent : null;
            }
            else { var t = GameObject.Find("Tennis ball"); if (t) ball = t.transform; }
            if (ball != ballRoot) { ballRoot = ball; Dress(ball, ballMat, null); }
            if (flag != flagRoot) { flagRoot = flag; Dress(flag, flagMat, "FLAG"); }
        }

        void Dress(Transform root, Material m, string nameFilter)
        {
            if (!root) return;
            foreach (var r in root.GetComponentsInChildren<MeshRenderer>(true))
            {
                if (r.name.StartsWith("Majestic weather glow")) continue;
                if (nameFilter != null && r.name.ToUpperInvariant().IndexOf(nameFilter) < 0) continue;
                var mf = r.GetComponent<MeshFilter>(); if (!mf || !mf.sharedMesh) continue;
                var go = new GameObject("Majestic weather glow") { layer = r.gameObject.layer };
                go.transform.SetParent(r.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = mf.sharedMesh;
                var shell = go.AddComponent<MeshRenderer>();
                string up = r.name.ToUpperInvariant();
                if (m == flagMat && up.IndexOf("POLE") < 0 && up.IndexOf("STICK") < 0 && r.sharedMaterial && r.sharedMaterial.HasProperty("_BaseColor"))
                    m.SetColor("_Color", r.sharedMaterial.GetColor("_BaseColor"));
                shell.sharedMaterial = m; shell.shadowCastingMode = ShadowCastingMode.Off; shell.receiveShadows = false;
                shell.lightProbeUsage = LightProbeUsage.Off; shell.reflectionProbeUsage = ReflectionProbeUsage.Off; shell.enabled = false;
                shells.Add((r, shell));
            }
        }

        public void Destroy() { foreach (var (_, shell) in shells) if (shell) Object.Destroy(shell.gameObject); shells.Clear(); comet.Destroy(); }
    }
}

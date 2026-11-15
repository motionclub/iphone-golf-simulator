using UnityEngine;

namespace GolfArcade.Tennis
{
    /// CLOTH JIGGLE (2026-10-30 pilot, clothing-mm clone): secondary motion for a loose garment without a cloth sim or extra bones.
    /// Four damped springs per hero (hem on the hips, each sleeve on its upper arm, collar on the neck) are pushed by their anchor's
    /// acceleration (the cloth lags, overshoots and settles) and trail a little behind steady motion (air drag). Their world offsets go
    /// to the garment material; TennisCloth's vertex stage moves each vertex by offset x its looseness (the _JiggleMap). Cost: 4 springs
    /// per hero on the CPU, one texture fetch per vertex. Off = CLOTH_JIGGLE=0, or the global _ClothJiggleGlobal = 0 (A/B films).
    public sealed class ClothJiggle : MonoBehaviour
    {
        public Material material;
        public static bool GlobalOn = true;
        public Vector4 DebugAcc;            // filtered anchor acceleration per spring (m/s^2), for the A/B film log

        sealed class Spring
        {
            public string prop; public Transform a, b; public float t, freq, zeta, max, gain, drag;
            public Vector3 x, v, pPrev, velPrev, velF, accF; public bool init;
            public Spring(string prop, Transform a, Transform b, float t, float freq, float zeta, float max, float gain, float drag)
            { this.prop = prop; this.a = a; this.b = b; this.t = t; this.freq = freq; this.zeta = zeta; this.max = max; this.gain = gain; this.drag = drag; }
        }
        Spring[] springs;
        static readonly int GlobalId = Shader.PropertyToID("_ClothJiggleGlobal");

        static Transform Find(Transform root, string name)
        {
            foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t;
            return null;
        }

        void Bind()
        {
            Transform hips = Find(transform, "Hips"), neck = Find(transform, "Neck"), chest = Find(transform, "UpperChest");
            Transform lu = Find(transform, "LeftUpperArm"), ll = Find(transform, "LeftLowerArm"), ru = Find(transform, "RightUpperArm"), rl = Find(transform, "RightLowerArm");
            if (!hips || !lu || !ll || !ru || !rl) { enabled = false; return; }
            springs = new[]
            {
                //            property      anchor a  b    t    Hz   zeta  max   gain  drag
                new Spring("_JigHem",      hips, hips, 0, 2.3f, .16f, .050f, .85f, .0050f),
                new Spring("_JigSleeveL",  lu,   ll,  .45f, 2.9f, .18f, .032f, .70f, .0035f),
                new Spring("_JigSleeveR",  ru,   rl,  .45f, 2.9f, .18f, .032f, .70f, .0035f),
                new Spring("_JigCollar",   neck ? neck : chest, neck ? neck : chest, 0, 3.6f, .24f, .015f, .55f, .0018f),
            };
        }

        void OnEnable() { if (GlobalOn) Shader.SetGlobalFloat(GlobalId, 1); }

        void LateUpdate()
        {
            if (!material) return;
            if (springs == null) Bind();
            if (springs == null) return;
            float dt = Mathf.Clamp(Time.deltaTime, 1e-3f, .05f);
            foreach (var s in springs)
            {
                if (!s.a) continue;
                Vector3 p = Vector3.Lerp(s.a.position, s.b.position, s.t);
                if (!s.init) { s.pPrev = p; s.velPrev = Vector3.zero; s.init = true; continue; }
                Vector3 vel = (p - s.pPrev) / dt;
                if (vel.sqrMagnitude > 15f * 15f) { s.pPrev = p; s.velPrev = s.velF = s.accF = Vector3.zero; s.x = s.v = Vector3.zero; continue; }   // teleport (new point, respawn)
                // the anchors carry per-frame pose jitter (IK / catch-up corrections); a second difference amplifies it, so velocity and
                // acceleration are low-passed (50 ms, far shorter than a real step, swing or stop)
                float lp = 1 - Mathf.Exp(-dt / .05f);
                s.velF = Vector3.Lerp(s.velF, vel, lp);
                s.accF = Vector3.Lerp(s.accF, (s.velF - s.velPrev) / dt, lp);
                s.pPrev = p; s.velPrev = s.velF; vel = s.velF;
                // dead zone: everyday micro-moves (< 3 m/s^2) leave the cloth at rest; real steps, swings and stops drive it
                Vector3 acc = Vector3.ClampMagnitude(s.accF, 40f); float am = acc.magnitude;
                acc = am > 3f ? acc * ((am - 3f) / am) : Vector3.zero;
                DebugAcc[System.Array.IndexOf(springs, s)] = acc.magnitude;
                float w = 2 * Mathf.PI * s.freq, k = w * w, c = 2 * s.zeta * w;
                Vector3 rest = Vector3.ClampMagnitude(-vel * s.drag, s.max * .6f);          // steady motion: trails behind a little
                float h = dt / 4;
                for (int i = 0; i < 4; i++)
                {
                    Vector3 a = -k * (s.x - rest) - c * s.v - acc * s.gain;
                    s.v += a * h; s.x += s.v * h;
                }
                if (s.x.magnitude > s.max) { s.x = s.x.normalized * s.max; s.v *= .5f; }
                material.SetVector(s.prop, s.x);
            }
        }
    }
}

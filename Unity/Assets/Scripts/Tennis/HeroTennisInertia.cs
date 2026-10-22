using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Pose inertialization for the match heroes (chat 4, 2026-10-17). When the driver switches what it plays -- a swing starting from a
    /// different prepared clip, a stroke handing back to the base layer, an emote starting or ending, a point reset -- the animation output
    /// can jump between two frames. At such a switch the jump is captured as a per-bone offset (the previous output carried one frame on at
    /// its own velocity, relative to the new output) and faded to zero, so the skeleton never pops and the new clip is reached exactly.
    /// Runs on the animation output only (right after the graph is evaluated), before the driver's foot lock, contact assist and safety layers.
    public sealed class HeroTennisInertia
    {
        readonly Transform[] bones;
        readonly Quaternion[] prev, prev2, off;
        readonly Vector3[] prevP, prev2P, offP;
        // what the offset last wrote: a bone the graph did not re-evaluate since (a physics sub-step without that bone, a helper bone)
        // still carries it and must not get it again, or it compounds every sub-step
        readonly Quaternion[] outR; readonly Vector3[] outP; readonly bool[] wrote;
        int frames; float age, duration, pending;
        /// Largest rotation (deg) the last switch had to absorb, and how many switches were blended.
        public float LastJump { get; private set; }
        public int Blends { get; private set; }
        public bool Active => duration > 0 && age < duration;

        /// `skeleton`: the animated skeleton's root bone (Hips), included. Only its hierarchy is blended: the runtime helpers outside it
        /// (HeroArmSkinning's ArmVolumePalette/ArmBlend_*, written by their own code, never by the clips) must stay out.
        public HeroTennisInertia(Transform skeleton)
        {
            var list = new System.Collections.Generic.List<Transform>();
            foreach (var t in skeleton.GetComponentsInChildren<Transform>(true))
                if (!t.GetComponent<Renderer>() && !t.name.Contains("ArmBlend_")) list.Add(t);
            bones = list.ToArray();
            int n = bones.Length;
            prev = new Quaternion[n]; prev2 = new Quaternion[n]; off = new Quaternion[n];
            prevP = new Vector3[n]; prev2P = new Vector3[n]; offP = new Vector3[n];
            outR = new Quaternion[n]; outP = new Vector3[n]; wrote = new bool[n];
        }

        void Offset(float w)
        {
            for (int i = 0; i < bones.Length; i++)
            {
                var b = bones[i]; if (!b) continue;
                if (wrote[i] && b.localRotation == outR[i] && b.localPosition == outP[i]) continue;   // not re-evaluated: offset already on
                b.localRotation = Quaternion.Slerp(Quaternion.identity, off[i], w) * b.localRotation;
                b.localPosition += offP[i] * w;
                outR[i] = b.localRotation; outP[i] = b.localPosition; wrote[i] = true;
            }
        }

        /// Blend the next evaluated pose in from the one on screen over `seconds`.
        public void Request(float seconds) => pending = Mathf.Max(pending, seconds);
        /// Drop the history (a new hero build, a replay): the next frame is shown as evaluated.
        public void Clear() { frames = 0; duration = 0; pending = 0; }

        /// Displayed frame: call right after the graph is evaluated. Starts a requested blend, applies the live offset, records the result.
        public void Apply(float dt)
        {
            int n = bones.Length;
            if (pending > 0 && frames >= 2 && dt > 0)
            {
                float worst = 0;
                for (int i = 0; i < n; i++)
                {
                    var b = bones[i]; if (!b) continue;
                    // where the shown pose was heading: one more frame at its own (bounded) angular / linear velocity
                    var step = prev[i] * Quaternion.Inverse(prev2[i]);
                    step.ToAngleAxis(out float a, out Vector3 ax); if (a > 180) a -= 360;
                    if (!float.IsFinite(ax.x)) step = Quaternion.identity; else if (Mathf.Abs(a) > 20) step = Quaternion.AngleAxis(Mathf.Sign(a) * 20, ax);
                    var expect = step * prev[i];
                    var expectP = prevP[i] + Vector3.ClampMagnitude(prevP[i] - prev2P[i], .05f);
                    off[i] = expect * Quaternion.Inverse(b.localRotation);
                    offP[i] = expectP - b.localPosition;
                    worst = Mathf.Max(worst, Quaternion.Angle(expect, b.localRotation));
                }
                LastJump = worst; Blends++;
                age = 0; duration = pending;
                System.Array.Clear(wrote, 0, n);
            }
            pending = 0;
            if (Active)
            {
                float x = Mathf.Clamp01(age / duration), w = 1 - x * x * x * (x * (6 * x - 15) + 10);   // quintic: no kick at either end
                Offset(w);
                age += dt;
            }
            for (int i = 0; i < n; i++)
            {
                var b = bones[i]; if (!b) continue;
                prev2[i] = prev[i]; prev2P[i] = prevP[i];
                prev[i] = b.localRotation; prevP[i] = b.localPosition;
            }
            if (frames == 0) for (int i = 0; i < n; i++) { prev2[i] = prev[i]; prev2P[i] = prevP[i]; }
            frames++;
        }

        /// A physics sub-step pose: the live offset, without advancing or recording anything. `sinceFrame`: game time the sub-steps have
        /// covered since the last displayed frame -- a blend must not stay frozen at its frame-start weight while many sub-steps run in one
        /// frame (a test stepping a whole rally per frame saw the previous point's pose on the racket the hit test uses).
        public void ApplyHeld(float sinceFrame = 0)
        {
            if (!Active || age + sinceFrame >= duration) return;
            float x = Mathf.Clamp01((age + sinceFrame) / duration), w = 1 - x * x * x * (x * (6 * x - 15) + 10);
            Offset(w);
        }
    }
}

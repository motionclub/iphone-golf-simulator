using UnityEngine;
namespace GolfArcade.Tennis
{
    /// A hand that holds a ball (Adnan 10-27: "for tennis and bowling the ball just takes over their hand, needs actual rigidness").
    /// Everything here is world space on the final pose, so it does not depend on any hero's curl-sign or hinge conventions:
    ///   Palm(..)  the palm frame (centre on the palm skin, normal out of the palm, axis wrist -> middle knuckle)
    ///   Seat(..)  where a ball of radius r rests on that palm (the ball follows the hand rigidly, every frame, after the hand's last correction)
    ///   Wrap(..)  each finger joint, knuckle to tip, turns about its knuckle line until the next joint (the tip for the last bone) lies on the
    ///             ball's surface plus the finger's half-thickness: a finger that would sink into the ball opens, one short of it closes on it.
    ///             The thumb turns toward the ball the same way, about its own bend axis.
    public static class HeroBallGrip
    {
        public struct Hand { public Transform hand, index, middle, ring, little, thumb; public bool left; }

        public static Hand Find(System.Func<HumanBodyBones, Transform> bone, bool left)
        {
            Transform B(string n) => System.Enum.TryParse<HumanBodyBones>((left ? "Left" : "Right") + n, out var id) ? bone(id) : null;
            return new Hand { hand = B("Hand"), index = B("IndexProximal"), middle = B("MiddleProximal"), ring = B("RingProximal"), little = B("LittleProximal"), thumb = B("ThumbProximal"), left = left };
        }
        public static bool Valid(in Hand h) => h.hand && h.index && h.middle && h.little;

        /// The palm frame. `normal` is the side the fingers curl to (handedness as HubHeroAnimator / BowlingHero build it).
        public static void Palm(in Hand h, out Vector3 centre, out Vector3 normal, out Vector3 axis, out Vector3 across)
        {
            axis = (h.middle.position - h.hand.position).normalized;
            across = Vector3.ProjectOnPlane(h.index.position - h.little.position, axis).normalized;   // toward the thumb side
            normal = h.left ? Vector3.Cross(across, axis) : Vector3.Cross(axis, across);
            // the curled middle finger tells which side the palm really is on (bind conventions differ per hero)
            var mi = Child(h.middle); var md = mi ? Child(mi) : null;
            if (md && Vector3.Dot(md.position - h.middle.position, normal) < -.004f) normal = -normal;
            float len = (h.middle.position - h.hand.position).magnitude;
            centre = h.hand.position + axis * (len * .62f);
        }

        /// Centre of a ball of radius `r` resting in the palm, `skin` = palm thickness from the bone line to the palm skin.
        public static Vector3 Seat(in Hand h, float r, float skin, float along = 0)
        {
            Palm(h, out var c, out var n, out var ax, out _);
            return c + ax * along + n * (skin + r);
        }

        static Transform Child(Transform t)
        {
            if (!t) return null;
            for (int i = 0; i < t.childCount; i++) { var c = t.GetChild(i); if (c.name.Contains("Intermediate") || c.name.Contains("Distal") || c.childCount > 0) return c; }
            return t.childCount > 0 ? t.GetChild(0) : null;
        }

        /// Wraps the fingers (and thumb) on a ball at `centre`, radius `r`; `pad` = finger half-thickness; `w` blends from the current pose.
        /// `thumbToo` false leaves the thumb alone (bowling: the thumb is in its hole and the clip owns it).
        /// `holes` (bowling): the middle and ring fingers and the thumb are in the ball's holes (the clip owns them); only the index and
        /// little fingers are laid on the surface.
        public static void Wrap(in Hand h, Vector3 centre, float r, float pad, float w, bool thumbToo = true, float maxCurl = 95, bool holes = false)
        {
            if (!Valid(h) || w <= .001f) return;
            Palm(h, out _, out _, out _, out var across);
            foreach (var p in holes ? new[] { h.index, h.little } : new[] { h.index, h.middle, h.ring, h.little }) Finger(p, centre, r + pad, w, across, false, maxCurl);
            if (thumbToo && !holes && h.thumb) Finger(h.thumb, centre, r + pad, w, across, true, maxCurl * .8f);
        }

        static void Finger(Transform proximal, Vector3 c, float R, float w, Vector3 across, bool thumb, float maxCurl)
        {
            if (!proximal) return;
            var j0 = proximal; var j1 = Child(j0); var j2 = j1 ? Child(j1) : null;
            if (!j1 || !j2) return;
            var joints = new[] { j0, j1, j2 };
            float tipLen = (j2.position - j1.position).magnitude * .95f;
            for (int k = 0; k < 3; k++)
            {
                var o = joints[k].position;
                // the point this bone carries: the next joint, or the fingertip for the last bone
                Vector3 P() => k < 2 ? joints[k + 1].position : j2.position + (j2.position - j1.position).normalized * tipLen;
                var d = P() - o; if (d.sqrMagnitude < 1e-10f) continue;
                var toBall = Vector3.ProjectOnPlane(c - o, d.normalized);
                if (toBall.sqrMagnitude < 1e-10f) continue;
                // the bend axis: the knuckle line for fingers (signed so a positive turn moves the bone toward the ball), free for the thumb
                Vector3 axis = Vector3.Cross(d.normalized, toBall.normalized);
                if (!thumb) { float s = Vector3.Dot(axis, across); axis = (s >= 0 ? across : -across); }
                axis.Normalize();
                var p0 = P() - o;
                float G(float deg) => (o + Quaternion.AngleAxis(deg, axis) * p0 - c).magnitude - R;
                float lo = -35, hi = maxCurl * (k == 0 ? .8f : 1), g0 = G(0), turn;
                if (g0 < 0)
                {
                    // inside the ball: open until it is on the surface (or as far as the joint can open)
                    if (G(lo) < 0) turn = lo;
                    else { float a = lo, b = 0; for (int i = 0; i < 18; i++) { float m = .5f * (a + b); if (G(m) < 0) b = m; else a = m; } turn = a; }
                }
                else
                {
                    // outside: close until it touches; a finger that never touches closes only part way (a soft open hand round the ball)
                    if (G(hi) > 0)
                    {
                        // nearest approach in range
                        float best = 0, bestG = g0; for (float t = 0; t <= hi; t += 5) { float gt = G(t); if (gt < bestG) { bestG = gt; best = t; } }
                        turn = best;
                    }
                    else { float a = 0, b = hi; for (int i = 0; i < 18; i++) { float m = .5f * (a + b); if (G(m) > 0) a = m; else b = m; } turn = b; }
                }
                if (Mathf.Abs(turn) < .05f) continue;
                joints[k].rotation = Quaternion.AngleAxis(turn * w, axis) * joints[k].rotation;
            }
        }

        /// Turns the hand about the wrist so its palm normal points at `target` (a ball the arm IK brought near), by up to `limit` degrees.
        public static void FacePalm(in Hand h, Vector3 target, float w, float limit = 70)
        {
            if (!Valid(h) || w <= .001f) return;
            Palm(h, out var c, out var n, out _, out _);
            var want = (target - c); if (want.sqrMagnitude < 1e-8f) return;
            var q = Quaternion.FromToRotation(n, want.normalized);
            q.ToAngleAxis(out float ang, out var ax); if (ang > 180) ang -= 360;
            ang = Mathf.Clamp(ang, -limit, limit) * w;
            h.hand.rotation = Quaternion.AngleAxis(ang, ax) * h.hand.rotation;
        }

        /// Palm skin thickness from the bone line (measured on the shipped bodies, after HeroHandShape).
        public static float PalmSkin(bool female) => female ? .014f : .017f;
        public static float FingerPad(bool female) => female ? .0075f : .0085f;
    }
}

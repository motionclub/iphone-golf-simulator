using System;
using UnityEditor;
using UnityEngine;

namespace GolfArcade.EditorTools
{
    /// FRAME_RATE_60: the old match clips were baked in Blender at 30 fps, one key per frame, and the FBX importer joins keys with straight
    /// lines (linear tangents). At a true 60 fps the pose therefore changes speed only every 33 ms and a fast swing is drawn as a polygon of
    /// chords (up to ~9 deg per joint off the smooth arc on the forehand's wrist), which reads as 30 fps motion on a 60 fps picture.
    /// Every key keeps its baked value and time (poses at the 30 Hz frames, contact and clip length are untouched); only the curve between keys
    /// changes, to Unity's ClampedAuto Hermite: C1-smooth, and flat at a local extreme so it never overshoots a hold, a plant or a contact.
    /// OFF by default: the clips are now baked at 60 Hz (FRAME_RATE_60), where straight lines between keys are exact at 60 fps and a 30 -> 15 Hz
    /// test showed smoothing recovers little of what sparse keys lose. Set MH_SMOOTH=1 to import the curves smoothed (for a 120 Hz comparison).
    public sealed class MatchClipSmoothing : AssetPostprocessor
    {
        public static bool Enabled => Environment.GetEnvironmentVariable("MH_SMOOTH") == "1";
        public override uint GetVersion() => Enabled ? 1u : 0u;   // bump to force every match FBX to reimport

        void OnPostprocessAnimation(GameObject root, AnimationClip clip)
        {
            if (!Enabled || !MatchHeroPostprocessor.Owns(assetPath)) return;
            Smooth(clip);
        }

        public static int Smooth(AnimationClip clip)
        {
            int curves = 0;
            foreach (var binding in AnimationUtility.GetCurveBindings(clip))
            {
                var curve = AnimationUtility.GetEditorCurve(clip, binding);
                if (curve == null || curve.length < 3) continue;
                for (int i = 0; i < curve.length; i++)
                {
                    AnimationUtility.SetKeyLeftTangentMode(curve, i, AnimationUtility.TangentMode.ClampedAuto);
                    AnimationUtility.SetKeyRightTangentMode(curve, i, AnimationUtility.TangentMode.ClampedAuto);
                }
                AnimationUtility.SetEditorCurve(clip, binding, curve);
                curves++;
            }
            return curves;
        }
    }
}

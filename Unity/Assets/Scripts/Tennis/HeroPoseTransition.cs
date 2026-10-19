using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Retains the visible skeleton across changes of clip coordinate system.
    /// Root children blend in world space; descendants retain local bone lengths.
    public sealed class HeroPoseTransition
    {
        readonly Transform root;
        readonly Transform[] bones;
        readonly Vector3[] positions;
        readonly Quaternion[] rotations;
        float elapsed, duration;
        public HeroPoseTransition(Transform root)
        {
            this.root = root;
            bones = root.GetComponentsInChildren<Transform>(true);
            positions = new Vector3[bones.Length]; rotations = new Quaternion[bones.Length];
        }
        public void Capture(float seconds)
        {
            duration = seconds; elapsed = 0;
            for (int i = 0; i < bones.Length; i++)
            {
                var b = bones[i]; if (!b || b == root) continue;
                positions[i] = b.parent == root ? b.position : b.localPosition;
                rotations[i] = b.parent == root ? b.rotation : b.localRotation;
            }
        }
        public void Tick(float dt) => elapsed = Mathf.Min(duration, elapsed + Mathf.Max(0, dt));
        public void Apply()
        {
            if (duration <= 0 || elapsed >= duration) return;
            float t = Mathf.SmoothStep(0, 1, elapsed / duration);
            for (int i = 0; i < bones.Length; i++)
            {
                var b = bones[i]; if (!b || b == root) continue;
                if (b.parent == root)
                {
                    b.SetPositionAndRotation(Vector3.Lerp(positions[i], b.position, t), Quaternion.Slerp(rotations[i], b.rotation, t));
                }
                else
                {
                    b.localPosition = Vector3.Lerp(positions[i], b.localPosition, t);
                    b.localRotation = Quaternion.Slerp(rotations[i], b.localRotation, t);
                }
            }
        }
    }
}

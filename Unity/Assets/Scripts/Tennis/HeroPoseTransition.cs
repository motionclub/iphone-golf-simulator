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
        /// The skeleton's top animated bone. The nodes above it (a static armature under the model's root) are never animated, so
        /// blending them leaves them turned for good (the golf rig's Rig_Male: a golfer who idled and then addressed the ball stood
        /// a quarter turn off, facing the TV); the meshes beside the rig are skinned and have nothing to blend.
        Transform hips;
        public HeroPoseTransition(Transform root)
        {
            this.root = root;
            bones = root.GetComponentsInChildren<Transform>(true);
            positions = new Vector3[bones.Length]; rotations = new Quaternion[bones.Length];
            hips = System.Array.Find(bones, t => t && t.name == "Hips");
        }
        bool Blended(Transform b) => b && b != root && (!hips || b == hips || b.IsChildOf(hips));
        bool InWorld(Transform b) => hips ? b == hips : b.parent == root;
        public void Capture(float seconds)
        {
            duration = seconds; elapsed = 0;
            for (int i = 0; i < bones.Length; i++)
            {
                var b = bones[i]; if (!Blended(b)) continue;
                positions[i] = InWorld(b) ? b.position : b.localPosition;
                rotations[i] = InWorld(b) ? b.rotation : b.localRotation;
            }
        }
        public void Tick(float dt) => elapsed = Mathf.Min(duration, elapsed + Mathf.Max(0, dt));
        public void Apply()
        {
            if (duration <= 0 || elapsed >= duration) return;
            float t = Mathf.SmoothStep(0, 1, elapsed / duration);
            for (int i = 0; i < bones.Length; i++)
            {
                var b = bones[i]; if (!Blended(b)) continue;
                if (InWorld(b))
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

using UnityEngine;
using GolfArcade.Tennis;

namespace GolfArcade.Hub
{
    /// HERO PRESENCE (2026-11-11): on the menu the hero looked over the viewer's head (the menu camera sits low). The head now turns
    /// toward the menu camera, clamped, after the idle has posed it. HERO_PRESENCE=0 or MENU_GAZE=0 switches it off.
    [DefaultExecutionOrder(1050)]
    public sealed class MenuHeroGaze : MonoBehaviour
    {
        Camera cam; HubPlayer player; MatchHeroLook look; Transform head; int axis = -1; float weight;
        public static void Attach(HubPlayer player, Camera cam)
        {
            if (!HeroShoeShape.Presence || System.Environment.GetEnvironmentVariable("MENU_GAZE") == "0" || !player || !cam || player.GetComponent<MenuHeroGaze>()) return;
            var g = player.gameObject.AddComponent<MenuHeroGaze>(); g.cam = cam; g.player = player;
        }
        static Vector3 Axis(Transform t, int i) => i switch { 0 => t.forward, 1 => -t.forward, 2 => t.up, 3 => -t.up, 4 => t.right, _ => -t.right };
        void LateUpdate()
        {
            if (!cam || !player) return;
            if (!look) { look = player.look; head = null; axis = -1; }
            if (!look) return;
            if (!head) head = look.Bone(HumanBodyBones.Head);
            if (!head) return;
            var toCam = cam.transform.position - head.position; var flat = toCam; flat.y = 0; if (flat.sqrMagnitude < 1e-6f) return; flat.Normalize();
            if (axis < 0)
            {
                // which of the head bone's axes is the face: the most level one that points at the camera (the menu hero stands facing it)
                float best = -2;
                for (int i = 0; i < 6; i++) { var a = Axis(head, i); if (Mathf.Abs(a.y) > .75f) continue; float d = Vector3.Dot(new Vector3(a.x, 0, a.z).normalized, flat); if (d > best) { best = d; axis = i; } }
                if (best < .5f) { axis = -1; return; }
            }
            weight = Mathf.MoveTowards(weight, 1, Time.unscaledDeltaTime * 1.5f);
            Quaternion.FromToRotation(Axis(head, axis), toCam.normalized).ToAngleAxis(out float angle, out var about); if (angle > 180) angle -= 360;
            head.rotation = Quaternion.AngleAxis(Mathf.Clamp(angle * .85f, -32, 32) * weight, about) * head.rotation;
        }
    }
}

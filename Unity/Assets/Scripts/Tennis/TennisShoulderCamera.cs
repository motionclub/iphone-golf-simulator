using UnityEngine;

namespace GolfArcade.Tennis
{
    public static class TennisShoulderCamera
    {
        public const float ChaseDistance = 5.6f, ChaseHeight = 3.3f, ShoulderOffset = .9f;

        public static void Frame(Vector3 player, bool leftHanded, Vector3 ball, bool overhead, float aspect,
            out Vector3 position, out Vector3 look, out float fov, bool elevated = false, Vector3? landing = null)
        {
            if (elevated)
            {
                // Preserve the previous court camera, including its overhead response.
                float lead = Mathf.Clamp(player.x, -5f, 5f);
                position = new Vector3(lead * .45f, 7f, player.z - 7.8f);
                float lift = overhead ? Mathf.Clamp((ball.y - 2.5f) * .18f, 0, .65f) : 0;
                look = new Vector3(lead * .26f, .95f + lift, player.z + 7.2f);
                fov = aspect < 1 ? 49 : 46;
                return;
            }

            fov = 48;
            // One steady shoulder keeps the player left of centre without a side swap at contact.
            // Handedness changes the stroke, not the camera; both hands retain the same sightline.
            bool liveBall = ball.y >= 0;
            float deep = liveBall ? Mathf.SmoothStep(0, 1, Mathf.InverseLerp(-5f, -11f, ball.z)) : 0;
            float height = ChaseHeight + (liveBall ? Mathf.Clamp((ball.y - 3f) * .12f, 0, .9f) : 0);
            float distance = ChaseDistance + deep;
            float centre = 0;
            float halfAngle = fov * .5f - 4f; // spare room for the felt, trail and smoothing
            float sightlineX = player.x + ShoulderOffset;
            float lookZ = Mathf.Max(3f, player.z + 12f);
            // Keep both the airborne ball and court cues in the vertical frame. Close high lobs
            // need more room than the ordinary one-metre deep-ball retreat, never a lens cut.
            for (int i = 0; i < 65; i++)
            {
                position = new Vector3(sightlineX, height, player.z - distance);
                centre = Mathf.Atan2(1f - height, lookZ - position.z) * Mathf.Rad2Deg;
                if (!liveBall || ball.z <= position.z + .25f) break;
                var ground = new Vector3(ball.x, 0, ball.z);
                float top = VerticalAngle(position, ball) - halfAngle;
                float bottom = VerticalAngle(position, ground) + halfAngle;
                // Leave extra bottom space for the ring radius and the existing timing HUD.
                if (landing.HasValue && landing.Value.z > position.z + .25f)
                    bottom = Mathf.Min(bottom, VerticalAngle(position, landing.Value) + fov * .5f - 10f);
                // Include the net: following a lob must still leave a court reference in view.
                bottom = Mathf.Min(bottom, VerticalAngle(position, new Vector3(player.x, 0, 0)) + halfAngle);
                if (top <= bottom && bottom >= -10f)
                {
                    centre = Mathf.Clamp(centre, top, bottom);
                    break;
                }
                if (i == 64) { centre = (top + bottom) * .5f; break; }
                distance += .25f;
            }
            position = new Vector3(sightlineX, height, player.z - distance);
            // Narrow split-screen halves still keep a cross-court ball inside their side edges.
            float yaw = 0;
            if (liveBall && ball.z > position.z + .25f) {
                float halfWidth = Mathf.Atan(Mathf.Tan(fov * .5f * Mathf.Deg2Rad) * Mathf.Max(.3f, aspect)) * Mathf.Rad2Deg - 4f;
                float ballYaw = Mathf.Atan2(ball.x - position.x, ball.z - position.z) * Mathf.Rad2Deg;
                yaw = Mathf.Clamp(0, ballYaw - halfWidth, ballYaw + halfWidth);
            }
            look = position + new Vector3(Mathf.Tan(yaw * Mathf.Deg2Rad), Mathf.Tan(centre * Mathf.Deg2Rad), 1) * (lookZ - position.z);
        }

        static float VerticalAngle(Vector3 eye, Vector3 point) =>
            Mathf.Atan2(point.y - eye.y, Mathf.Max(.25f, point.z - eye.z)) * Mathf.Rad2Deg;
    }
}

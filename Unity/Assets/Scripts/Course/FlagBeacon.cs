using UnityEngine;

namespace GolfArcade.Course
{
    /// Keeps the flag readable from the tee (Adnan 10-19: "golf flag needs to be more visible"). Close up (a putt, a
    /// chip) the pin is its own size; past GrowFrom yards it grows with the distance, so it keeps about the size it has
    /// on screen at GrowFrom (up to MaxGrow times: about 12 px of flag from a 400-yard tee on a 540-line view), the way
    /// broadcast graphics and arcade golf keep the target in view, and a soft red glow comes up behind the cloth,
    /// holding about the same size on screen, with a faint column of light standing over the cup (as Mario Golf: Super
    /// Rush marks its pins from the tee, refs/_H7Y7Ijug0w). Both are drawn in the world, so a hill or a tree still hides them.
    /// Lives on the pin (HoleView.BuildPin); the flag's own wave (WaterMotion) is untouched.
    public sealed class FlagBeacon : MonoBehaviour
    {
        public const float NearAt = 30f, FarAt = 150f, GrowFrom = 60f, MaxGrow = 6f;
        Vector3 baseScale;
        Renderer cloth;
        Transform halo, beam;
        Material haloMat, beamMat;
        public const float BeamHeight = 30f;
        static readonly Color Glow = new(1f, .32f, .2f);

        public static FlagBeacon Attach(Transform pin, Renderer cloth)
        {
            var b = pin.gameObject.AddComponent<FlagBeacon>();
            b.baseScale = pin.localScale; b.cloth = cloth;
            var shader = Shader.Find("GolfArcade/ParticleAdd");
            if (shader)
            {
                var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
                go.name = "Flag glow"; Destroy(go.GetComponent<Collider>());
                go.transform.SetParent(pin.parent, false);
                b.haloMat = new Material(shader) { name = "Flag glow", mainTexture = GolfArcade.Game.ShotEffects.Soft() };
                var r = go.GetComponent<MeshRenderer>(); r.sharedMaterial = b.haloMat;
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
                go.layer = GolfArcade.Game.BallLook.OverlayLayer;   // the minimap leaves it out
                b.halo = go.transform;
                var column = GameObject.CreatePrimitive(PrimitiveType.Quad);
                column.name = "Pin light column"; Destroy(column.GetComponent<Collider>());
                column.transform.SetParent(pin.parent, false);
                b.beamMat = new Material(shader) { name = "Pin light column", mainTexture = GolfArcade.Game.ShotEffects.Soft() };
                var cr = column.GetComponent<MeshRenderer>(); cr.sharedMaterial = b.beamMat;
                cr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; cr.receiveShadows = false;
                column.layer = GolfArcade.Game.BallLook.OverlayLayer;
                b.beam = column.transform;
            }
            return b;
        }

        /// How far through the grow the pin is at `distance` yards from the camera (0 near, 1 far).
        public static float Far(float distance) { float k = Mathf.Clamp01((distance - NearAt) / (FarAt - NearAt)); return k * k * (3 - 2 * k); }

        /// How many times its own size the pin is drawn from `distance` yards.
        public static float Grow(float distance) => Mathf.Clamp(distance / GrowFrom, 1f, MaxGrow);

        void LateUpdate()
        {
            var cam = Camera.main;
            if (!cam) return;
            float d = Vector3.Distance(cam.transform.position, transform.position), k = Far(d);
            transform.localScale = baseScale * Grow(d);
            if (!halo) return;
            bool show = k > .02f && cloth && cloth.enabled && cloth.gameObject.activeInHierarchy;
            if (halo.gameObject.activeSelf != show) halo.gameObject.SetActive(show);
            if (beam && beam.gameObject.activeSelf != show) beam.gameObject.SetActive(show);
            if (!show) return;
            if (beam)
            {
                // a soft column over the cup, turned to face the camera about the vertical, a few pixels wide
                var foot = transform.position; var toCam = cam.transform.position - foot; toCam.y = 0;
                beam.position = foot + Vector3.up * BeamHeight * .5f;
                if (toCam.sqrMagnitude > 1e-4f) beam.rotation = Quaternion.LookRotation(-toCam.normalized, Vector3.up);
                beam.localScale = new Vector3(Mathf.Max(.8f, d * .012f), BeamHeight, 1);
                var bc = new Color(1f, .9f, .7f, .45f * k); beamMat.color = bc;
            }
            var at = cloth.bounds.center;
            // a little behind the cloth from the camera, about two and a half degrees across on screen
            halo.position = at + (at - cam.transform.position).normalized * .6f;
            halo.rotation = Quaternion.LookRotation(halo.position - cam.transform.position, cam.transform.up);
            halo.localScale = Vector3.one * Mathf.Max(2.5f, Vector3.Distance(cam.transform.position, at) * .06f);
            var c = Glow; c.a = .9f * k; haloMat.color = c;
        }

        void OnDestroy() { if (halo) Destroy(halo.gameObject); if (haloMat) Destroy(haloMat); if (beam) Destroy(beam.gameObject); if (beamMat) Destroy(beamMat); }
    }
}

using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Bowling
{
    /// The pinsetter's setting table, which BowlingGame's sweep moves (a real machine's deck, not pins floating
    /// on their own): a steel plate the width of the lane with ten pin cups under it, hung from two lift rods,
    /// riding in guide rails on the kickbacks. At home it sits up inside the machine, above the shadow-box roof.
    /// It comes down over the pins, grips the standing ones by the head, lifts them while the sweep bar clears
    /// the deadwood, and sets them down again; for a new frame it carries the old rack up into the machine and
    /// lowers ten fresh pins onto the spots.
    public sealed class BowlingPinsetter
    {
        /// Plate-centre heights: home (out of sight in the machine) and gripping (the cups over the pin heads).
        public const float Home = 1.18f, Grip = .43f;
        /// Where a pin's base is while the table holds it.
        public static float PinBase(float tableY) => tableY - Grip;

        readonly Transform table;
        public float Y { get => table.localPosition.y; set => table.localPosition = new Vector3(0, value, table.localPosition.z); }

        BowlingPinsetter(Transform table) => this.table = table;

        public static BowlingPinsetter Build(Transform parent)
        {
            var steel = BowlingAlley.Lit(new Color(.16f, .17f, .19f), .62f);
            var bright = BowlingAlley.Lit(new Color(.55f, .56f, .58f), .75f);
            var black = BowlingAlley.Lit(new Color(.03f, .03f, .035f), .3f);
            float zc = BowlingLane.FoulToHeadPin + .42f, w = 2 * (BowlingLane.HalfWidth + BowlingLane.GutterWidth) - .06f;   // kickback to kickback
            var root = new GameObject("PinsetterTable").transform; root.SetParent(parent, false);
            root.localPosition = new Vector3(0, Home, zc);
            // the plate with a raised rim and cross ribs
            Part(root, "Plate", PrimitiveType.Cube, new Vector3(0, 0, 0), new Vector3(w - .02f, .045f, 1.12f), steel);
            foreach (float s in new[] { -1f, 1f })
            {
                Part(root, "Rim", PrimitiveType.Cube, new Vector3(s * (w / 2 - .02f), .035f, 0), new Vector3(.04f, .07f, 1.14f), bright);
                Part(root, "RimEnd", PrimitiveType.Cube, new Vector3(0, .035f, s * .56f), new Vector3(w, .07f, .04f), bright);
            }
            for (int k = -1; k <= 1; k++) Part(root, "Rib", PrimitiveType.Cube, new Vector3(0, .04f, k * .3f), new Vector3(w - .06f, .035f, .025f), steel);
            // ten cups at the spots, open underneath (a dark lining), each on a short stem
            for (int i = 1; i <= 10; i++)
            {
                var spot = BowlingLane.PinSpot(i);
                var at = new Vector3(spot.x, 0, spot.z - zc);
                Part(root, "CupStem", PrimitiveType.Cylinder, at + new Vector3(0, -.04f, 0), new Vector3(.05f, .03f, .05f), steel);
                Part(root, "Cup", PrimitiveType.Cylinder, at + new Vector3(0, -.1f, 0), new Vector3(.13f, .045f, .13f), bright);
                Part(root, "CupLining", PrimitiveType.Cylinder, at + new Vector3(0, -.146f, 0), new Vector3(.1f, .002f, .1f), black);
            }
            // the lift rods it hangs from, running up into the machine
            foreach (float s in new[] { -1f, 1f })
                Part(root, "LiftRod", PrimitiveType.Cylinder, new Vector3(s * (w / 2 - .12f), .55f, 0), new Vector3(.035f, .55f, .035f), bright);
            // guide rails on the kickbacks (they stay put; the table's rim rides in them)
            foreach (float s in new[] { -1f, 1f })
                foreach (float dz in new[] { -.5f, .5f })
                    Part(parent, "PinsetterRail", PrimitiveType.Cube, new Vector3(s * (BowlingLane.HalfWidth + BowlingLane.GutterWidth - .012f), .55f, zc + dz), new Vector3(.025f, 1.1f, .04f), steel);
            return new BowlingPinsetter(root);
        }

        static void Part(Transform parent, string name, PrimitiveType type, Vector3 pos, Vector3 scale, Material m)
        {
            var go = GameObject.CreatePrimitive(type);
            Object.Destroy(go.GetComponent<Collider>());
            go.name = name; go.transform.SetParent(parent, false);
            go.transform.localPosition = pos; go.transform.localScale = scale;
            var r = go.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off;
        }
    }
}

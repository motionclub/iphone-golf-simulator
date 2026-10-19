using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Plaza hub (concepts/after/hub_plaza_clear.jpg): golden-hour light + grade, bunting from both roof eaves
    /// to the clock tower, navy-and-gold roof flags, blossom beds along the hedges and the tower base, and
    /// people at the café table. Layout from the hub dump: arrival camera (0, 5, -17.3) looking +Z, clock
    /// tower face (0, 11, 14.3), clubhouse x≈9..17, cobbled circle centre (0, 0, 1) r≈7.6.
    public static class MajesticHub
    {
        public static void Build(Transform root, MajesticLook look)
        {
            var mat = MajesticMesh.Dressing();
            var rng = new System.Random(77);
            var m = new MajesticMesh();
            m.Bunting(new Vector3(-8.6f, 5.3f, 1.5f), new Vector3(-1.7f, 8.0f, 12.6f), 1.0f, rng);
            m.Bunting(new Vector3(1.7f, 8.0f, 12.6f), new Vector3(8.6f, 5.3f, 1.5f), 1.0f, rng);
            m.Bunting(new Vector3(-8.6f, 5.3f, 1.5f), new Vector3(8.6f, 5.3f, 1.5f), 1.6f, rng);
            var navy = new Color(.12f, .17f, .36f); var gold = new Color(.92f, .74f, .30f);
            m.Flag(new Vector3(-12.4f, 8.6f, 3.0f), 2.8f, new Vector2(1.5f, .9f), new[] { navy, gold, navy }, .3f);
            m.Flag(new Vector3(12.6f, 9.0f, 2.5f), 2.8f, new Vector2(1.5f, .9f), new[] { navy, gold, navy }, .9f);
            m.Build(root, "Majestic hub bunting and flags", mat, true);

            var flowers = new MajesticMesh();
            Color[] blossoms = { new(.98f, .32f, .48f), new(.96f, .62f, .78f), new(1f, .82f, .30f), new(.62f, .42f, .92f), new(.98f, .96f, .92f), new(1f, .45f, .25f) };
            void Bed(Vector3 a, Vector3 b, int count)
            {
                for (int i = 0; i < count; i++)
                {
                    var p = Vector3.Lerp(a, b, (float)rng.NextDouble()) + new Vector3(((float)rng.NextDouble() - .5f) * .7f, (float)rng.NextDouble() * .25f, ((float)rng.NextDouble() - .5f) * .7f);
                    var c = blossoms[rng.Next(blossoms.Length)];
                    flowers.Blob(p, new Vector3(.11f, .09f, .11f), c, c * .85f, 6);
                }
            }
            Bed(new Vector3(-5.5f, .5f, 9.6f), new Vector3(-2.2f, .5f, 9.6f), 45);
            Bed(new Vector3(2.2f, .5f, 9.6f), new Vector3(5.5f, .5f, 9.6f), 45);
            flowers.Build(root, "Majestic hub blossoms", mat, false);

            // café table on the right (dressing block near (8.3, ~, -0.2)): four seated guests facing the table
            var seats = new List<(Vector3, float)>();
            for (int i = 0; i < 4; i++)
            {
                float a = i * Mathf.PI * .5f + .4f;
                var p = new Vector3(8.3f + Mathf.Cos(a) * 1.15f, .45f, -.2f + Mathf.Sin(a) * 1.15f);
                seats.Add((p, Mathf.Atan2(8.3f - p.x, -.2f - p.z) * Mathf.Rad2Deg - 90));
            }
            MajesticCrowd.Build(root, seats);
        }

        public static void SetMaterials(bool on, MajesticLook look) { }
        public static void Animate(MajesticLook look, float t) { }
    }
}

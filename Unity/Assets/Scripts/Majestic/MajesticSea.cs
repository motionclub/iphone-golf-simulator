using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Sea life meshes shared by venues (golf coasts; the resort uses its own sailboat).
    public static class MajesticSea
    {
        public static void Sailboat(MajesticMesh b)
        {
            var hull = new Color(.96f, .95f, .92f); var stripe = new Color(.16f, .38f, .78f); var sail = new Color(.99f, .98f, .95f);
            Vector3[] top = { new(-.9f, .6f, -3f), new(.9f, .6f, -3f), new(.9f, .6f, 2.2f), new(0, .6f, 3.2f), new(-.9f, .6f, 2.2f) };
            Vector3[] bot = { new(-.5f, -.2f, -2.6f), new(.5f, -.2f, -2.6f), new(.5f, -.2f, 1.9f), new(0, -.2f, 2.6f), new(-.5f, -.2f, 1.9f) };
            for (int i = 0; i < 5; i++) { int j = (i + 1) % 5; b.Quad(top[i], top[j], bot[j], bot[i], i == 0 ? hull : stripe); }
            b.Tri(top[0], top[2], top[1], hull); b.Tri(top[0], top[4], top[2], hull); b.Tri(top[4], top[3], top[2], hull);
            b.Quad(new Vector3(-.06f, .6f, .2f), new Vector3(.06f, .6f, .2f), new Vector3(.06f, 8.6f, .2f), new Vector3(-.06f, 8.6f, .2f), new Color(.85f, .82f, .78f));
            b.Tri(new Vector3(0, 8.4f, .1f), new Vector3(0, 1.1f, .1f), new Vector3(.15f, 1.1f, -2.6f), sail, new Vector2(0, .3f), new Vector2(0, .3f), new Vector2(.05f, .3f));
            b.Tri(new Vector3(0, 7.6f, .35f), new Vector3(0, 1.0f, 2.9f), new Vector3(0, 1.0f, .35f), sail, new Vector2(0, .7f), new Vector2(.04f, .7f), new Vector2(0, .7f));
        }

        /// A friendly cartoon whale (body + flukes + pale belly), ~9 m long, nose along +Z.
        public static void Whale(MajesticMesh m)
        {
            var back = new Color(.18f, .26f, .40f); var belly = new Color(.86f, .88f, .90f);
            m.Blob(new Vector3(0, 0, 0), new Vector3(1.6f, 1.4f, 4.6f), back, belly, 12);
            m.Blob(new Vector3(0, -.1f, -4.6f), new Vector3(.7f, .6f, 1.2f), back, back, 8);
            m.Tri(new Vector3(0, 0, -5.4f), new Vector3(-2.4f, .2f, -6.6f), new Vector3(0, 0, -6.2f), back);
            m.Tri(new Vector3(0, 0, -5.4f), new Vector3(0, 0, -6.2f), new Vector3(2.4f, .2f, -6.6f), back);
            m.Tri(new Vector3(1.4f, -.4f, 1.2f), new Vector3(2.8f, -1.2f, .2f), new Vector3(1.4f, -.6f, -.2f), back);
            m.Tri(new Vector3(-1.4f, -.4f, 1.2f), new Vector3(-1.4f, -.6f, -.2f), new Vector3(-2.8f, -1.2f, .2f), back);
        }
    }
}

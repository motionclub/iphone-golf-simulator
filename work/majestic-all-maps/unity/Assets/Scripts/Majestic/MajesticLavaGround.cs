using System.Collections.Generic;
using UnityEngine;

namespace GolfArcade.Majestic
{
    /// Magma Open's ash rough as cracked basalt with glowing seams (chat 10; shader Resources/Majestic/MajesticLavaGround).
    /// The course's "Course N Ash" material (GolfCourseLook, MAT_ROUGH_ASH / MAT_COAL) is swapped on its renderers, the
    /// surface batches included; meshes, colliders and lies are untouched. Restore() puts every original back.
    public static class MajesticLavaGround
    {
        static readonly List<(Renderer r, Material[] was)> swapped = new();
        static Material lava;

        public static int Apply()
        {
            Restore();
            if (!lava)
            {
                var sh = Shader.Find("GolfArcade/MajesticLavaGround"); if (!sh) return 0;
                lava = new Material(sh) { name = "Majestic lava ground", enableInstancing = true };
            }
            foreach (var r in Object.FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                var mats = r.sharedMaterials; bool hit = false;
                for (int i = 0; i < mats.Length; i++)
                    if (mats[i] && mats[i].name.StartsWith("Course ") && mats[i].name.EndsWith(" Ash")) { hit = true; break; }
                if (!hit) continue;
                swapped.Add((r, (Material[])mats.Clone()));
                for (int i = 0; i < mats.Length; i++)
                    if (mats[i] && mats[i].name.StartsWith("Course ") && mats[i].name.EndsWith(" Ash")) mats[i] = lava;
                r.sharedMaterials = mats;
            }
            return swapped.Count;
        }

        public static void Restore()
        {
            foreach (var (r, was) in swapped) if (r) r.sharedMaterials = was;
            swapped.Clear();
        }
    }
}

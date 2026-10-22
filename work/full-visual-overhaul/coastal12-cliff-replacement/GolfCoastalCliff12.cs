using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace GolfArcade.Course
{
    /// Continuous authored coastal rock volume. Source terrain filters, colliders,
    /// transforms and all playable top-surface indices stay authoritative.
    public sealed class GolfCoastalCliff12 : MonoBehaviour
    {
        readonly List<Mesh> ownedMeshes = new();
        Material material;
        public int ReplacedTerrains { get; private set; }
        public int CliffTriangles { get; private set; }
        public float RegistrationError { get; private set; }

        public static void Apply(GameObject model, Hole hole)
        {
            if (hole.Number != 12 || model.GetComponent<GolfCoastalCliff12>()) return;
            var prefab = Resources.Load<GameObject>("Course/Resort/Coastal12_Cliffs");
            if (!prefab) { Debug.LogError("[GolfCoastalCliff12] missing continuous cliff asset"); return; }
            var owner = model.AddComponent<GolfCoastalCliff12>();
            owner.Install(model, prefab);
        }

        static Transform Find(Transform root, string name)
        {
            foreach (var child in root.GetComponentsInChildren<Transform>(true))
                if (child.name == name) return child;
            return null;
        }

        void Install(GameObject model, GameObject prefab)
        {
            var visual = Instantiate(prefab, model.transform, false);
            visual.name = "COASTAL12_CONTINUOUS_CHALK_RENDER";
            // Three exported source anchors make FBX root-axis conventions explicit.
            var tee = Find(model.transform, "MARKER_TEE");
            var pin = Find(model.transform, "MARKER_PIN");
            var up = Find(model.transform, "MARKER_UP");
            var anchorTee = Find(visual.transform, "COASTAL12_ANCHOR_TEE");
            var anchorPin = Find(visual.transform, "COASTAL12_ANCHOR_PIN");
            var anchorUp = Find(visual.transform, "COASTAL12_ANCHOR_UP");
            if (!tee || !pin || !up || !anchorTee || !anchorPin || !anchorUp)
            {
                Debug.LogError("[GolfCoastalCliff12] missing exact registration anchors; original renderer retained");
                Destroy(visual); return;
            }
            var fromUp = (anchorUp.position - anchorTee.position).normalized;
            var toUp = (up.position - tee.position).normalized;
            var fromAlong = Vector3.ProjectOnPlane(anchorPin.position - anchorTee.position, fromUp);
            var toAlong = Vector3.ProjectOnPlane(pin.position - tee.position, toUp);
            float scale = toAlong.magnitude / Mathf.Max(.001f, fromAlong.magnitude);
            var rotation = Quaternion.LookRotation(toAlong, toUp) * Quaternion.Inverse(Quaternion.LookRotation(fromAlong, fromUp));
            var oldRoot = visual.transform.position;
            var relativeTee = anchorTee.position - oldRoot;
            visual.transform.localScale *= scale;
            visual.transform.rotation = rotation * visual.transform.rotation;
            visual.transform.position = tee.position - rotation * relativeTee * scale;
            RegistrationError = Mathf.Max((anchorTee.position - tee.position).magnitude,
                Mathf.Max((anchorPin.position - pin.position).magnitude, (anchorUp.position - up.position).magnitude));
            if (RegistrationError > .003f)
            {
                Debug.LogError($"[GolfCoastalCliff12] registration {RegistrationError:F6} yd exceeds .003; original renderer retained");
                Destroy(visual); return;
            }
            var look = model.GetComponentInParent<GolfCourseLook>();
            if (!look) look = GolfCourseLook.Current;
            if (!look) { Debug.LogError("[GolfCoastalCliff12] missing course material owner"); Destroy(visual); return; }
            material = new Material(look.Get(GolfCourseLook.Surface.Cliff)) { name = "Coastal 12 authored chalk", enableInstancing = true };
            // Quiet material variation supports the authored planes; small fissures
            // are secondary to geometric shoulders and interrupted bedding.
            material.SetFloat("_PaletteMode", 1); material.SetColor("_BaseColor", Color.white);
            material.SetColor("_LowColor", new Color(.46f,.48f,.44f));
            material.SetColor("_HighColor", new Color(.84f,.81f,.71f));
            material.SetFloat("_DetailContrast", .52f); material.SetFloat("_PaletteDetail", .10f);
            material.SetFloat("_GeologicalMacro", .045f); material.SetFloat("_RockScale", .038f);
            material.SetFloat("_HeightStrength", .16f); material.SetFloat("_BumpScale", .30f);
            material.SetFloat("_StrataStrength", 0); material.SetFloat("_WetFoot", 1);
            material.SetFloat("_Smoothness", .08f); material.SetFloat("_Wrap", .25f);
            foreach (var filter in visual.GetComponentsInChildren<MeshFilter>())
            {
                if (!filter.sharedMesh || !filter.TryGetComponent<MeshRenderer>(out var renderer)) continue;
                var materials = new Material[filter.sharedMesh.subMeshCount];
                for (int i = 0; i < materials.Length; i++) materials[i] = material;
                renderer.sharedMaterials = materials; renderer.shadowCastingMode = ShadowCastingMode.On; renderer.receiveShadows = true;
                for (int i = 0; i < filter.sharedMesh.subMeshCount; i++) CliffTriangles += (int)filter.sharedMesh.GetIndexCount(i) / 3;
            }
            // Keep the original ground renderer's top exactly, removing only the
            // cliff slots from a separate render clone. MeshColliders keep originals.
            foreach (var source in model.GetComponentsInChildren<MeshCollider>())
            {
                if (!source.name.StartsWith("TERRAIN") || !source.sharedMesh || !source.sharedMesh.isReadable ||
                    !source.TryGetComponent<MeshRenderer>(out var renderer)) continue;
                var original = source.sharedMesh; var materials = renderer.sharedMaterials;
                var cliff = new bool[original.subMeshCount]; bool any = false;
                for (int i = 0; i < cliff.Length; i++)
                {
                    string name = i < materials.Length && materials[i] ? materials[i].name : "";
                    cliff[i] = name.Contains(" Basalt") || name.Contains(" Cliff") || name.StartsWith("MAT_BASALT") || name.StartsWith("MAT_CLIFF"); any |= cliff[i];
                }
                if (!any) continue;
                var top = Instantiate(original); top.name = "Coastal12 exact original turf render";
                for (int i = 0; i < cliff.Length; i++) if (cliff[i]) top.SetTriangles(Array.Empty<int>(), i);
                top.RecalculateBounds(); ownedMeshes.Add(top);
                var go = new GameObject("COASTAL12_EXACT_TOP_RENDER"); go.transform.SetParent(source.transform, false);
                go.AddComponent<MeshFilter>().sharedMesh = top;
                var replacement = go.AddComponent<MeshRenderer>(); replacement.sharedMaterials = materials;
                replacement.shadowCastingMode = renderer.shadowCastingMode; replacement.receiveShadows = renderer.receiveShadows;
                renderer.enabled = false; ReplacedTerrains++;
            }
            // Legacy loose shore boulders would interrupt the new connected mass.
            // Their source mesh/collider/obstacle records remain untouched.
            foreach (var renderer in model.GetComponentsInChildren<MeshRenderer>())
                if (renderer.name.StartsWith("ROCK") || renderer.name.StartsWith("BOULDER")) renderer.enabled = false;
            Debug.Log($"[GolfCoastalCliff12] {ReplacedTerrains} source cliff renderers replaced by continuous volume; {CliffTriangles} triangles, exact anchor error {RegistrationError:F6} yd; top indices/collision meshes retained");
        }
        void OnDestroy()
        {
            foreach (var mesh in ownedMeshes) if (mesh) Destroy(mesh);
            if (material) Destroy(material);
        }
    }
}

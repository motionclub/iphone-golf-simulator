using System;
using UnityEngine;

namespace GolfArcade.Tennis
{
    // Experimental source-pattern sweep. Current bone transforms are the only
    // motion inputs. Shared JSON contains no sampled poses or clip identifiers.
    [DefaultExecutionOrder(2100), DisallowMultipleComponent]
    public sealed class FemaleSleeveSweep : MonoBehaviour
    {
        [Serializable] sealed class Weight { public int[] ids; public float[] values; }
        [Serializable] sealed class Mapping { public int vertex, triangle; public Vector3 bary, offset, normal; public float alpha; }
        [Serializable] sealed class ContactMapping { public int vertex, triangle; public Vector3 bary; }
        [Serializable] sealed class Field
        {
            public int version, vertexCount, ringCount, ringSize, chestBone, contactMode;
            public int[] triangles, armBones; public string[] boneNames;
            public Vector3[] controls, centers; public Weight[] rootWeights; public Mapping[] mapping;
            public int[] collisionSource, collisionTriangles, collisionEdges; public ContactMapping[] collisionMap;
            public float[] collisionEdgeLengths, collisionBendLengths, collisionRestAreas, collisionTriangleBlend, collisionMobility;
            public int[] collisionBendPairs, collisionTriangleSide; public Vector3[] collisionRestNormals;
        }
        Field field; SkinnedMeshRenderer source; Mesh sourceMesh, mesh;
        MeshRenderer surface; GameObject surfaceObject;
        Vector3[] rest, restNormals, result, controlPositions, normals;
        BoneWeight[] weights; Matrix4x4[] binds, matrices;
        Quaternion[] rotations; Vector3[] scales; int[] fieldIndices;
        MaterialPropertyBlock propertyBlock;
        bool previousForceOff, previousEnabled;
        Vector3[] shellBase, shellMoved, displacement, smoothDisplacement;
        int[] shellDegree;
        Transform[] shoulder, elbow, wrist;
        Vector3[] capStart, capEnd; float[] capRadiusA, capRadiusB;
        Matrix4x4 chestToMesh, meshToChest;
        public float maximumContactDisplacement { get; private set; }
        public float maximumEdgeStrain { get; private set; }
        public int invertedTriangles { get; private set; }
        Vector3[] shellTargets, orientationTargets;

        public static FemaleSleeveSweep Attach(SkinnedMeshRenderer top)
        {
            if (!top) return null;
            var existing = top.GetComponent<FemaleSleeveSweep>();
            if (existing) return existing;
            var json = Resources.Load<TextAsset>("FemaleGarment/golf_sleeve_field");
            if (!json) { Debug.LogError("FemaleSleeveSweep: missing source pattern field"); return null; }
            var component = top.gameObject.AddComponent<FemaleSleeveSweep>();
            component.Build(top, json.text); return component;
        }

        void Build(SkinnedMeshRenderer top, string json)
        {
            propertyBlock=new MaterialPropertyBlock();
            source = top; sourceMesh = top.sharedMesh;
            field = JsonUtility.FromJson<Field>(json);
            if (field.version != 1 || field.vertexCount != sourceMesh.vertexCount) throw new InvalidOperationException("Sleeve source topology mismatch");
            fieldIndices = new int[field.boneNames.Length];
            for (int i = 0; i < field.boneNames.Length; i++)
            {
                string name = field.boneNames[i];
                fieldIndices[i] = Array.FindIndex(top.bones, bone => bone && bone.name == name);
                if (fieldIndices[i] < 0) throw new InvalidOperationException("Sleeve missing bone: " + name);
            }
            rest = sourceMesh.vertices; restNormals = sourceMesh.normals; weights = sourceMesh.boneWeights; binds = sourceMesh.bindposes;
            result = new Vector3[rest.Length]; normals = new Vector3[rest.Length];
            controlPositions = new Vector3[field.controls.Length];
            matrices = new Matrix4x4[binds.Length]; rotations = new Quaternion[binds.Length]; scales = new Vector3[binds.Length];
            if (field.contactMode != 0 && field.collisionSource != null)
            {
                int count = field.collisionSource.Length;
                shellBase = new Vector3[count]; shellMoved = new Vector3[count]; displacement = new Vector3[count]; smoothDisplacement = new Vector3[count]; shellDegree = new int[count];
                shellTargets = new Vector3[count]; orientationTargets = new Vector3[field.collisionRestNormals.Length];
                foreach (int index in field.collisionEdges) shellDegree[index]++;
                shoulder = new Transform[2]; elbow = new Transform[2]; wrist = new Transform[2];
                var look = top.GetComponentInParent<MatchHeroLook>();
                if (!look) throw new InvalidOperationException("Sleeve contact field requires hero skeleton");
                for (int side = 0; side < 2; side++)
                {
                    shoulder[side] = look.Bone(side == 0 ? HumanBodyBones.LeftUpperArm : HumanBodyBones.RightUpperArm);
                    elbow[side] = look.Bone(side == 0 ? HumanBodyBones.LeftLowerArm : HumanBodyBones.RightLowerArm);
                    wrist[side] = look.Bone(side == 0 ? HumanBodyBones.LeftHand : HumanBodyBones.RightHand);
                }
                capStart = new Vector3[6]; capEnd = new Vector3[6]; capRadiusA = new float[6]; capRadiusB = new float[6];
            }
            mesh = Instantiate(sourceMesh); mesh.name = "Female polo continuous source-pattern sleeve sweep";
            mesh.ClearBlendShapes(); mesh.MarkDynamic();
            surfaceObject = new GameObject("Female sewn sleeve surface"); surfaceObject.transform.SetParent(top.transform, false);
            surfaceObject.layer = top.gameObject.layer; surfaceObject.AddComponent<MeshFilter>().sharedMesh = mesh;
            surface = surfaceObject.AddComponent<MeshRenderer>(); surface.sharedMaterials = top.sharedMaterials;
            surface.shadowCastingMode = top.shadowCastingMode; surface.receiveShadows = top.receiveShadows;
            surface.renderingLayerMask = top.renderingLayerMask;
            previousForceOff = top.forceRenderingOff; previousEnabled=top.enabled; top.forceRenderingOff = true; top.enabled=false;
            Apply();
        }

        Vector3 Skin(Vector3 p, BoneWeight w)
        {
            return matrices[w.boneIndex0].MultiplyPoint3x4(p)*w.weight0 + matrices[w.boneIndex1].MultiplyPoint3x4(p)*w.weight1
                 + matrices[w.boneIndex2].MultiplyPoint3x4(p)*w.weight2 + matrices[w.boneIndex3].MultiplyPoint3x4(p)*w.weight3;
        }

        Vector3 SkinControl(Vector3 p, Weight w)
        {
            Vector3 result = Vector3.zero;
            for (int i = 0; i < w.ids.Length; i++) result += matrices[fieldIndices[w.ids[i]]].MultiplyPoint3x4(p)*w.values[i];
            return result;
        }

        public void Apply()
        {
            if (!source || field == null || !mesh) return;
            var bones = source.bones;
            var local = source.transform.worldToLocalMatrix;
            for (int i = 0; i < matrices.Length; i++)
            {
                matrices[i] = local*bones[i].localToWorldMatrix*binds[i];
                rotations[i] = matrices[i].rotation; scales[i] = matrices[i].lossyScale;
            }
            for (int i = 0; i < rest.Length; i++)
            {
                var w = weights[i]; var n = restNormals[i]; result[i] = Skin(rest[i], w);
                normals[i] = (matrices[w.boneIndex0].MultiplyVector(n)*w.weight0+matrices[w.boneIndex1].MultiplyVector(n)*w.weight1
                    +matrices[w.boneIndex2].MultiplyVector(n)*w.weight2+matrices[w.boneIndex3].MultiplyVector(n)*w.weight3).normalized;
            }
            int stride = field.ringCount*field.ringSize;
            int chest = fieldIndices[field.chestBone];
            for (int side = 0; side < 2; side++)
            {
                int arm = fieldIndices[field.armBones[side]];
                Vector3 restPivot = binds[arm].inverse.MultiplyPoint3x4(Vector3.zero);
                for (int ring = 0; ring < field.ringCount; ring++)
                {
                    float t = ring/(float)(field.ringCount-1);
                    float blend = t*t*(3-2*t);
                    Quaternion q = Quaternion.Slerp(rotations[chest], rotations[arm], blend);
                    Vector3 scale = Vector3.Lerp(scales[chest], scales[arm], blend);
                    Vector3 center = field.centers[side*field.ringCount+ring];
                    // Rotate the center about the anatomical shoulder, too.
                    // A positional LBS chord shrinks this radius during a
                    // crossed/raised arm even when its crosssection stays round.
                    Vector3 posedPivot = Vector3.Lerp(matrices[chest].MultiplyPoint3x4(restPivot), matrices[arm].MultiplyPoint3x4(restPivot), blend);
                    Vector3 posedCenter = posedPivot+q*Vector3.Scale(center-restPivot, scale);
                    for (int k = 0; k < field.ringSize; k++)
                    {
                        int i = side*stride+ring*field.ringSize+k;
                        // Ring crosssections rotate as solid frames rather than
                        // blending opposite radial vectors into a collapsed fold.
                        Vector3 swept = posedCenter+q*Vector3.Scale(field.controls[i]-center, scale);
                        // Exact sewn boundary, with a short continuous transition
                        // into the independent noncollapsing sleeve frame.
                        float rootFade = Mathf.SmoothStep(0, 1, Mathf.Clamp01(t/.22f));
                        controlPositions[i] = Vector3.Lerp(SkinControl(field.controls[i], field.rootWeights[i]), swept, rootFade);
                    }
                }
            }
            foreach (var map in field.mapping)
            {
                int ti = map.triangle*3;
                Vector3 a = controlPositions[field.triangles[ti]], b = controlPositions[field.triangles[ti+1]], c = controlPositions[field.triangles[ti+2]];
                Vector3 u = (b-a).normalized, n = Vector3.Cross(b-a, c-a).normalized, v = Vector3.Cross(n, u);
                if (u.sqrMagnitude < .5f || n.sqrMagnitude < .5f) continue;
                Vector3 point = a*map.bary.x+b*map.bary.y+c*map.bary.z+u*map.offset.x+v*map.offset.y+n*map.offset.z;
                result[map.vertex] = Vector3.Lerp(result[map.vertex], point, map.alpha);
                normals[map.vertex] = Vector3.Lerp(normals[map.vertex], u*map.normal.x+v*map.normal.y+n*map.normal.z, map.alpha).normalized;
            }
            ApplySharedContact();
            mesh.vertices = result; mesh.normals = normals; mesh.RecalculateBounds();
            surface.sharedMaterials = source.sharedMaterials;
            source.GetPropertyBlock(propertyBlock); surface.SetPropertyBlock(propertyBlock);
        }

        Vector3 OutsideBody(Vector3 point)
        {
            // Thorax volume from the accepted source body's metre-space bounds.
            // Project in the chest bind frame, retaining its asymmetric depth.
            Vector3 center = new Vector3(0, -.018f, 1.225f), radius = new Vector3(.141f, .115f, .173f);
            Vector3 p = meshToChest.MultiplyPoint3x4(point), d = p-center;
            Vector3 q = new Vector3(d.x/radius.x, d.y/radius.y, d.z/radius.z);
            float length = q.magnitude;
            if (length < 1 && length > 1e-6f)
                point = chestToMesh.MultiplyPoint3x4(center+Vector3.Scale(q/length, radius));
            // Full-root deltoid + tapered upper arm + forearm. None of these
            // depend on a clip, frame window or sampled sleeve pose.
            for (int i = 0; i < capStart.Length; i++)
            {
                Vector3 axis = capEnd[i]-capStart[i];
                float t = Mathf.Clamp01(Vector3.Dot(point-capStart[i], axis)/Mathf.Max(axis.sqrMagnitude, 1e-10f));
                Vector3 c = capStart[i]+axis*t, radial = point-c;
                float r = Mathf.Lerp(capRadiusA[i], capRadiusB[i], t), distance = radial.magnitude;
                if (distance < r && distance > 1e-6f) point = c+radial*(r/distance);
            }
            return point;
        }

        void ApplySharedContact()
        {
            if (field.contactMode == 0 || shellBase == null) return;
            chestToMesh = matrices[fieldIndices[field.chestBone]]; meshToChest = chestToMesh.inverse;
            var local = source.transform.worldToLocalMatrix;
            for (int side = 0; side < 2; side++)
            {
                Vector3 a = local.MultiplyPoint3x4(shoulder[side].position), b = local.MultiplyPoint3x4(elbow[side].position), c = local.MultiplyPoint3x4(wrist[side].position);
                float scale = Mathf.Abs(scales[fieldIndices[field.armBones[side]]].x);
                int k = side*3;
                capStart[k] = a; capEnd[k] = Vector3.Lerp(a, b, .18f); capRadiusA[k] = .071f*scale; capRadiusB[k] = .064f*scale;
                capStart[k+1] = a; capEnd[k+1] = b; capRadiusA[k+1] = .063f*scale; capRadiusB[k+1] = .048f*scale;
                capStart[k+2] = b; capEnd[k+2] = c; capRadiusA[k+2] = .047f*scale; capRadiusB[k+2] = .032f*scale;
            }
            for (int i = 0; i < shellBase.Length; i++)
            {
                shellBase[i] = result[field.collisionSource[i]];
                shellTargets[i] = shellMoved[i] = OutsideBody(OutsideBody(shellBase[i]));
            }
            float sourceScale = Mathf.Abs(scales[fieldIndices[field.chestBone]].x);
            for (int t = 0; t < orientationTargets.Length; t++)
            {
                int side = field.collisionTriangleSide[t];
                Quaternion rotation = rotations[fieldIndices[field.chestBone]];
                if (side >= 0) rotation = Quaternion.Slerp(rotation, rotations[fieldIndices[field.armBones[side]]], field.collisionTriangleBlend[t]);
                orientationTargets[t] = rotation*field.collisionRestNormals[t];
            }
            if (field.contactMode == 1)
            {
                for (int i = 0; i < shellBase.Length; i++) displacement[i] = Vector3.zero;
                for (int iteration = 0; iteration < 5; iteration++)
                {
                    for (int i = 0; i < shellBase.Length; i++)
                    {
                        Vector3 p = OutsideBody(OutsideBody(shellBase[i]+displacement[i]));
                        displacement[i] = Vector3.ClampMagnitude(p-shellBase[i], .065f);
                        smoothDisplacement[i] = Vector3.zero;
                    }
                    for (int e = 0; e < field.collisionEdges.Length; e += 2)
                    {
                        int a = field.collisionEdges[e], b = field.collisionEdges[e+1];
                        smoothDisplacement[a] += displacement[b]; smoothDisplacement[b] += displacement[a];
                    }
                    for (int i = 0; i < shellBase.Length; i++)
                        if (shellDegree[i] > 0) displacement[i] = Vector3.Lerp(displacement[i], smoothDisplacement[i]/shellDegree[i], .35f);
                }
                for (int i = 0; i < shellBase.Length; i++)
                    shellMoved[i] = shellBase[i]+Vector3.ClampMagnitude(OutsideBody(OutsideBody(shellBase[i]+displacement[i]))-shellBase[i], .065f);
            }
            else
            {
            // Deterministic rest-metric solve. Sewing topology, rest stretch,
            // bending distances and outward orientation are fixed source data.
            // Animation supplies boundary transforms, never lookup keys.
            for (int iteration = 0; iteration < 24; iteration++)
            {
                for (int i = 0; i < shellBase.Length; i++)
                {
                    if (field.collisionMobility[i] == 0) shellMoved[i] = shellTargets[i];
                    else shellMoved[i] = Vector3.Lerp(shellMoved[i], shellTargets[i], .003f);
                }
                SolveDistances(field.collisionEdges, field.collisionEdgeLengths, sourceScale, .98f, 1.04f, .88f, (iteration & 1) != 0);
                SolveDistances(field.collisionBendPairs, field.collisionBendLengths, sourceScale, .98f, 1.02f, .16f, (iteration & 1) == 0);
                for (int t = 0; t < orientationTargets.Length; t++)
                {
                    int start = t*3, a = field.collisionTriangles[start], b = field.collisionTriangles[start+1], c = field.collisionTriangles[start+2];
                    Vector3 ab = shellMoved[b]-shellMoved[a], ac = shellMoved[c]-shellMoved[a], n = orientationTargets[t];
                    float signedArea = Vector3.Dot(Vector3.Cross(ab, ac), n);
                    float minimum = .25f*field.collisionRestAreas[t]*sourceScale*sourceScale;
                    if (signedArea >= minimum) continue;
                    Vector3 gb = Vector3.Cross(ac, n), gc = Vector3.Cross(n, ab), ga = -gb-gc;
                    float wa = field.collisionMobility[a], wb = field.collisionMobility[b], wc = field.collisionMobility[c];
                    float divisor = wa*ga.sqrMagnitude+wb*gb.sqrMagnitude+wc*gc.sqrMagnitude;
                    if (divisor < 1e-14f) continue;
                    float lambda = .70f*(minimum-signedArea)/divisor;
                    shellMoved[a] += ga*(lambda*wa); shellMoved[b] += gb*(lambda*wb); shellMoved[c] += gc*(lambda*wc);
                }
                for (int i = 0; i < shellBase.Length; i++)
                {
                    if (field.collisionMobility[i] == 0) { shellMoved[i] = shellTargets[i]; continue; }
                    Vector3 projected = OutsideBody(OutsideBody(shellMoved[i]));
                    shellMoved[i] = shellBase[i]+Vector3.ClampMagnitude(projected-shellBase[i], .09f);
                }
            }
            }
            maximumContactDisplacement = 0;
            for (int i = 0; i < shellBase.Length; i++)
            {
                displacement[i] = shellMoved[i]-shellBase[i];
                maximumContactDisplacement = Mathf.Max(maximumContactDisplacement, displacement[i].magnitude);
            }
            maximumEdgeStrain = 0; invertedTriangles = 0;
            for (int e = 0; e < field.collisionEdgeLengths.Length; e++)
            {
                float ratio = Vector3.Distance(shellMoved[field.collisionEdges[e*2]], shellMoved[field.collisionEdges[e*2+1]])/Mathf.Max(field.collisionEdgeLengths[e]*sourceScale, 1e-8f);
                maximumEdgeStrain = Mathf.Max(maximumEdgeStrain, Mathf.Abs(ratio-1));
            }
            for (int t = 0; t < orientationTargets.Length; t++)
            {
                int k = t*3; Vector3 a = shellMoved[field.collisionTriangles[k]], b = shellMoved[field.collisionTriangles[k+1]], c = shellMoved[field.collisionTriangles[k+2]];
                if (Vector3.Dot(Vector3.Cross(b-a, c-a), orientationTargets[t]) <= 0) invertedTriangles++;
            }
            foreach (var map in field.collisionMap)
            {
                int t = map.triangle*3;
                int ai = field.collisionTriangles[t], bi = field.collisionTriangles[t+1], ci = field.collisionTriangles[t+2];
                Vector3 delta = displacement[ai]*map.bary.x+displacement[bi]*map.bary.y+displacement[ci]*map.bary.z;
                // Transport the existing smooth source normal through the
                // shared surface differential; lining remains opposite-facing.
                Vector3 oldU = (shellBase[bi]-shellBase[ai]).normalized;
                Vector3 oldN = Vector3.Cross(shellBase[bi]-shellBase[ai], shellBase[ci]-shellBase[ai]).normalized;
                Vector3 newU = (shellMoved[bi]-shellMoved[ai]).normalized;
                Vector3 newN = Vector3.Cross(shellMoved[bi]-shellMoved[ai], shellMoved[ci]-shellMoved[ai]).normalized;
                if (oldN.sqrMagnitude < .5f || newN.sqrMagnitude < .5f) { result[map.vertex] += delta; continue; }
                Vector3 oldV = Vector3.Cross(oldN, oldU), newV = Vector3.Cross(newN, newU), n = normals[map.vertex];
                Vector3 oldCenter = shellBase[ai]*map.bary.x+shellBase[bi]*map.bary.y+shellBase[ci]*map.bary.z;
                Vector3 newCenter = shellMoved[ai]*map.bary.x+shellMoved[bi]*map.bary.y+shellMoved[ci]*map.bary.z;
                Vector3 offset = result[map.vertex]-oldCenter;
                result[map.vertex] = newCenter+newU*Vector3.Dot(offset, oldU)+newV*Vector3.Dot(offset, oldV)+newN*Vector3.Dot(offset, oldN);
                normals[map.vertex] = (newU*Vector3.Dot(n, oldU)+newV*Vector3.Dot(n, oldV)+newN*Vector3.Dot(n, oldN)).normalized;
            }
        }

        void SolveDistances(int[] pairs, float[] restLengths, float scale, float minimum, float maximum, float stiffness, bool reverse)
        {
            for (int k = 0; k < restLengths.Length; k++)
            {
                int e = reverse ? restLengths.Length-1-k : k;
                int a = pairs[e*2], b = pairs[e*2+1];
                Vector3 d = shellMoved[b]-shellMoved[a]; float length = d.magnitude;
                float wa = field.collisionMobility[a], wb = field.collisionMobility[b], weight = wa+wb;
                if (length < 1e-8f || weight < 1e-8f) continue;
                float rest = restLengths[e]*scale;
                float error = length-Mathf.Clamp(length, rest*minimum, rest*maximum);
                Vector3 correction = d*(stiffness*error/(length*weight));
                shellMoved[a] += correction*wa; shellMoved[b] -= correction*wb;
            }
        }

        void LateUpdate() => Apply();
        void OnDestroy()
        {
            if (source) { source.forceRenderingOff = previousForceOff; source.enabled=previousEnabled; }
            if (surfaceObject) { if (Application.isPlaying) Destroy(surfaceObject); else DestroyImmediate(surfaceObject); }
            if (mesh) { if (Application.isPlaying) Destroy(mesh); else DestroyImmediate(mesh); }
        }
    }
}

from pathlib import Path
R=Path(__file__).resolve().parents[3]
p=R/'Unity/Assets/Resources/Tennis/Shaders/TennisCharacter.shader';s=p.read_text()
s=s.replace('_BumpScale ("Normal strength", Range(0,2)) = 1','_BumpScale ("Normal strength", Range(0,2)) = 1\n        [HideInInspector] _PaintLift ("Paint layer separation", Float) = 0\n        [HideInInspector] _FaceRole ("Face: 1 eye, 2 iris, 3 lid, 4 brow", Float) = 0\n        [HideInInspector] _Blink ("Blink", Range(0,1)) = 0\n        [HideInInspector] _Gaze ("Eye gaze", Vector) = (0,0,0,0)\n        [HideInInspector] _EyeL ("Left eye centre", Vector) = (0,0,0,0)\n        [HideInInspector] _EyeR ("Right eye centre", Vector) = (0,0,0,0)\n        [HideInInspector] _FaceUp ("Face up", Vector) = (0,1,0,0)\n        [HideInInspector] _FaceRight ("Face right", Vector) = (1,0,0,0)\n        [HideInInspector] _BrowLift ("Brow lift", Float) = 0')
s=s.replace('float4 _BumpMap_ST;','float4 _EyeL, _EyeR, _FaceUp, _FaceRight, _Gaze; half _PaintLift, _FaceRole, _Blink, _BrowLift;\n                float4 _BumpMap_ST;')
s=s.replace('VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);','''float3 facePos = i.positionOS.xyz;
                if (_FaceRole > .5h) {
                    float3 eye = dot(facePos - (_EyeL.xyz + _EyeR.xyz) * .5, _FaceRight.xyz) < 0 ? _EyeL.xyz : _EyeR.xyz;
                    if (_FaceRole < 3.5h) {
                        // Deform the actual eye paint into its existing closed lid line.
                        // Neutral/open is mathematically identical to the approved mesh.
                        float eyeHeight = dot(facePos - eye, _FaceUp.xyz);
                        facePos -= _FaceUp.xyz * eyeHeight * _Blink;
                        if (_FaceRole > 1.5h && _FaceRole < 2.5h) facePos += (_FaceRight.xyz * _Gaze.x + _FaceUp.xyz * _Gaze.y) * (1 - _Blink);
                    } else facePos += _FaceUp.xyz * _BrowLift;
                }
                facePos += i.normalOS * _PaintLift;
                VertexPositionInputs p = GetVertexPositionInputs(facePos);''')
p.write_text(s)
p=R/'Unity/Assets/Scripts/Tennis/MatchHeroLook.cs';s=p.read_text().replace('SkinBump = .10f','SkinBump = 0f').replace('if (bump && SkinBumpMap)','if (bump && SkinBump > 0 && SkinBumpMap)')
s=s.replace('Material[] skinMaterials; Material frameMaterial;', 'Material[] skinMaterials; Material[] faceMaterials; Color authoredSkin;\n        readonly System.Collections.Generic.Dictionary<Material, Color> anatomicalPaint = new();\n        Material frameMaterial;')
s=s.replace('var shared = body.sharedMaterials; skinMaterials = new Material[shared.Length];','var shared = body.sharedMaterials; skinMaterials = new Material[shared.Length];\n                authoredSkin = shared.Length > 0 && shared[0] ? (shared[0].HasProperty("_BaseColor") ? shared[0].GetColor("_BaseColor") : shared[0].color) : skinTone;')
s=s.replace('owned.Add(fm[i]); changed = true;', '''ConfigureFaceRole(fm[i], src.name);
                    if (FollowsSkin(src.name)) anatomicalPaint[fm[i]] = fm[i].GetColor("_BaseColor");
                    owned.Add(fm[i]); changed = true;''')
s=s.replace('if (changed) face.sharedMaterials = fm;','if (changed) face.sharedMaterials = fm;\n                faceMaterials = fm;\n                ConfigureEyeGeometry();')
s=s.replace('void Awake()\n        {\n            OwnMaterials();','void Awake()\n        {\n            OwnMaterials();\n            if (face && !GetComponent<MatchHeroFacePerformance>()) gameObject.AddComponent<MatchHeroFacePerformance>().look = this;')
s=s.replace('            foreach (var m in skinMaterials) if (m)', '''            foreach (var pair in anatomicalPaint) if (pair.Key) {
                var c = pair.Value;
                pair.Key.SetColor("_BaseColor", new Color(Mathf.Clamp01(tone.r * c.r / Mathf.Max(.01f, authoredSkin.r)), Mathf.Clamp01(tone.g * c.g / Mathf.Max(.01f, authoredSkin.g)), Mathf.Clamp01(tone.b * c.b / Mathf.Max(.01f, authoredSkin.b)), 1));
            }
            foreach (var m in skinMaterials) if (m)''')
anchor='        /// The skin tone on the whole body'
code='''        static bool FollowsSkin(string name) => new[] { "Face_Lip", "Face_LipUp", "Face_Seam", "Face_Nostril", "Face_LidCrease", "Face_LidLower" }.Any(n => name.Contains(n));
        static void ConfigureFaceRole(Material m, string name)
        {
            float role = 0, lift = .00015f;
            if (name.Contains("Sclera")) { role = 1; lift = .00025f; }
            else if (new[] { "Iris", "Pupil", "Limbal", "Catch" }.Any(n => name.Contains(n))) { role = 2; lift = name.Contains("Catch") ? .0006f : name.Contains("Pupil") ? .0005f : .0004f; }
            else if (name.Contains("LidLine")) { role = 3; lift = .00045f; }
            else if (name.Contains("Brow")) { role = 4; lift = name.Contains("BrowSoft") ? .00015f : .00045f; }
            m.SetFloat("_FaceRole", role); m.SetFloat("_PaintLift", lift);
        }
        void ConfigureEyeGeometry()
        {
            var filter = face.GetComponent<MeshFilter>(); if (!filter || !filter.sharedMesh || !filter.sharedMesh.isReadable) return;
            var mesh = filter.sharedMesh; var vertices = mesh.vertices;
            var up = face.transform.InverseTransformDirection(transform.up).normalized;
            var right = face.transform.InverseTransformDirection(transform.right).normalized;
            var bounds = new[] { new Bounds(), new Bounds() }; var found = new bool[2];
            var mid = mesh.bounds.center;
            for (int sub = 0; sub < faceMaterials.Length; sub++) if (faceMaterials[sub] && faceMaterials[sub].name.Contains("Sclera"))
                foreach (int i in mesh.GetTriangles(sub)) {
                    int side = Vector3.Dot(vertices[i] - mid, right) < 0 ? 0 : 1;
                    if (!found[side]) { bounds[side] = new Bounds(vertices[i], Vector3.zero); found[side] = true; } else bounds[side].Encapsulate(vertices[i]);
                }
            if (!found[0] || !found[1]) return;
            foreach (var m in faceMaterials) if (m) {
                m.SetVector("_EyeL", bounds[0].center); m.SetVector("_EyeR", bounds[1].center);
                m.SetVector("_FaceUp", up); m.SetVector("_FaceRight", right);
            }
        }
        /// Bounded existing-face deformation shared with the native geometry modifier.
        public void SetFacePerformance(float blink, Vector2 gaze, float browLift = 0)
        {
            OwnMaterials(); if (faceMaterials == null) return;
            gaze = Vector2.ClampMagnitude(gaze, .0018f);
            foreach (var m in faceMaterials) if (m) {
                m.SetFloat("_Blink", Mathf.Clamp01(blink)); m.SetVector("_Gaze", new Vector4(gaze.x, gaze.y, 0, 0));
                m.SetFloat("_BrowLift", Mathf.Clamp(browLift, -.001f, .001f));
            }
        }

'''
s=s.replace(anchor,code+anchor);p.write_text(s)
# Native paint follows the same source-skin ratio; brows/eye colours retain their identity.
p=R/'GolfArcade/Unity/MatchHeroData.swift';s=p.read_text().replace('let colour = picks.colour(sub.material)','''var colour = picks.colour(sub.material)
                if colour == nil, ["Face_Lip", "Face_LipUp", "Face_Seam", "Face_Nostril", "Face_LidCrease", "Face_LidLower"].contains(sub.material),
                   let tone = picks.colour("Skin"), let paint = sub.look?.color, paint.count >= 3,
                   let base = m.parts.first(where: { $0.name == "Body" })?.submeshes.first?.look?.color, base.count >= 3 {
                    colour = SIMD3(min(1,tone.x*paint[0]/max(0.01,base[0])), min(1,tone.y*paint[1]/max(0.01,base[1])), min(1,tone.z*paint[2]/max(0.01,base[2])))
                }''');p.write_text(s)
print('Actual face geometry deformation + stable paint layers + anatomical paint tint')

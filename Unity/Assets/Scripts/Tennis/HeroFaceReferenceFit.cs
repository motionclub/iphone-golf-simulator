using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace GolfArcade.Tennis
{
    /// Local, continuous head correction. Body, neck base, weights, bindposes,
    /// topology and animation sources are retained. Blink endpoints follow the
    /// same mapping as the resting face, so the lid remains attached.
    public static class HeroFaceReferenceFit
    {
        static readonly Dictionary<Mesh, Mesh> cache = new();
        /// The orbit term lowers the eyes (and the face measured from them) by 10 mm; the bald-base numbers were taken on the finished face.
        const float Settle = -.010f;
        // Male proportions pass 2026-10-17 (chat 11, male reference pack sheet 07, Adnan: "match ref on all three"): eyes back to the
        // source almond (no vertical stretch / iris spread, eye opening 33 x 12.5 mm), the skull 2 % narrower than the source instead of
        // 8.5 % wider (the jaw and neck keep the old width), ears nearly full size (were 2 x 14 % smaller). Female values unchanged.
        const float MaleEyeStretch = 0f, MaleIrisSpread = 0f, MaleEarShrink = .02f, MaleEyeGrow = 1.06f;
        // Male face pass 2026-10-18 (sheet 17): the iris fills the opening height and tucks under the upper lid; the opening a little
        // taller (the almond read as a white stare in the flat game light). Were 1.10 / 1.0.
        const float MaleEyeTall = 1.18f, MaleIris = 1.12f;
        const float MaleSkull = -.02f, MaleJaw = .085f;
        // Male nose (same pass): a straight, higher dorsum (+15 mm target bump at y -36, 14 mm tall, 12 mm wide), the pull eased to .70
        // and ending just under the nose base (y -.064..-.056) so it no longer pins the upper lip, which is now sculpted.
        const float MaleDorsum = .012f, MaleDorsumY = -.038f, MaleDorsumH = .010f, MaleDorsumW = .012f, MaleNoseBlend = .70f, MaleNoseFloor0 = -.064f, MaleNoseFloor1 = -.056f;
        // Male eyes stay at the source height (the reference's: 47 % of crown-chin): the orbit term no longer lowers them 10 mm.
        // HeroFaceSkin / TennisCharacter / MatchHeroSurfaces add the old drop back to their male face frame below the orbit, so the
        // mouth, beard and jaw paint stay on the same geometry. Tip .024 (was .019).
        public const float MaleOrbitDrop = 0f; const float MaleScleraInset = .06f, MaleEarDrop = .004f; const float MaleTip = .024f;
        const float MaleAlarX = .022f, MaleAlarAmp = .009f, MaleNoseNarrow = .10f;   // wider, fuller alar wings (were .020 / .006 / .24)
        // Male nose 2026-10-18 (sheets 07/17; Adnan: "way too pointy", then "make it realistic"): an anatomical nose built after the face
        // fit, in the fitted face frame (mm). The reference is narrow at the bridge, has a ball-shaped tip lobule and two round alar lobes
        // out to +-23 mm, set back ~11 mm, with real creases between them; our nose was a narrow wedge. Components: a ridge that follows the
        // sheet-17 midline profile (aligned at the nasion; designed offline in work/male-face-pass-1018/tools/nose2.py), a wider rounder
        // tip lobule, two alar ellipsoids, a smooth-max union (the alar creases are its valleys), then a union with the cheek. The old
        // narrow nose is carved to the new surface; the wings' vertices are first spread sideways so the lobes have geometry to sit on.
        static readonly float[] MaleNoseProfileZ = { 38.7f,38.1f,37.3f,37.3f,37.3f,38.2f,39.3f,40.6f,42.0f,43.6f,45.3f,46.6f,47.7f,48.8f,49.8f,50.8f,51.9f,53.1f,54.4f,55.6f,
            57.0f,58.9f,60.9f,62.3f,63.6f,64.8f,65.7f,65.8f,65.7f,65.3f,64.9f,63.8f,62.2f,56.0f,49.7f,47.6f,45.7f };   // y = +10, +8 .. -62 mm
        static float NoseProfile(float y) { float t = Mathf.Clamp((10 - y) / 2, 0, MaleNoseProfileZ.Length - 1.001f); int i = (int)t; return Mathf.Lerp(MaleNoseProfileZ[i], MaleNoseProfileZ[i + 1], t - i); }
        static float Lerp4(float y, float y0, float y1, float a, float b) => Mathf.Lerp(a, b, Mathf.Clamp01((y - y0) / (y1 - y0)));
        static float SmoothMax(float a, float b, float k) { float h = Mathf.Clamp01(.5f + .5f * (a - b) / k); return b + (a - b) * h + k * h * (1 - h); }
        const float NoseFlare = 6.5f, NoseFlareX0 = 12, NoseFlareX1 = 40, NoseFlareY = -47, NoseFlareH = 7, NoseTop = 8, NoseBottom = -56.5f, NoseBlend = .88f;
        const float NoseWidthTop = 7, NoseWidthMid = 8.5f, NoseWidthTip = 8.5f, NoseRidgeDrop = 6, NoseTipDrop = 8;   // tip lobule narrow enough that the wings stand out as their own lobes
        const float AlaX = 14.5f, AlaY = -50.5f, AlaRX = 8.5f, AlaRY = 7.5f, AlaRZ = 8, AlaBack = 10, AlaCrease = 1, AlaBaseBlend = 6, CheekBlend = 2.5f, BaseSoft = 4.5f;
        static Vector3 MaleNose(Vector3 m)
        {
            float x = m.x * 1000, y = m.y * 1000, z = m.z * 1000, ax = Mathf.Abs(x);
            float Sm(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
            float prof = ax < NoseFlareX0 ? ax / NoseFlareX0 : Mathf.Clamp01(1 - (ax - NoseFlareX0) / (NoseFlareX1 - NoseFlareX0)); prof = prof * prof * (3 - 2 * prof);
            x += Mathf.Sign(x) * NoseFlare * prof * Mathf.Exp(-Mathf.Pow((y - NoseFlareY) / NoseFlareH, 4)) * Sm(22, 34, z) * Sm(NoseBottom - 1.5f, NoseBottom + 1.5f, y); ax = Mathf.Abs(x);
            float w = y < -47 ? NoseWidthTip : y < -38 ? Lerp4(y, -38, -47, NoseWidthMid, NoseWidthTip) : y < -25 ? Lerp4(y, -25, -38, NoseWidthMid * .95f, NoseWidthMid) : y < -10 ? Lerp4(y, -10, -25, NoseWidthTop, NoseWidthMid * .95f) : NoseWidthTop;
            float drop = y < -44 ? NoseTipDrop : y < -36 ? Lerp4(y, -36, -44, NoseRidgeDrop, NoseTipDrop) : NoseRidgeDrop;
            float ridge = NoseProfile(y) - drop * (ax / w) * (ax / w);
            float zc = NoseProfile(AlaY) - AlaBack - AlaRZ, q = 1 - Mathf.Pow((ax - AlaX) / AlaRX, 2) - Mathf.Pow((y - AlaY) / AlaRY, 2);
            float ala = zc + AlaRZ * Mathf.Sign(q) * Mathf.Pow(Mathf.Abs(q), 1.5f);   // smooth rim (zero slope where the wing meets the cheek: an ellipsoid's vertical rim made a hard, jaggy crease)
            // crease only along the top of each wing; toward the base the wings flow into the tip as one rounded base (Adnan: they read as separate circles)
            float n = SmoothMax(ridge, ala, Mathf.Lerp(AlaCrease, AlaBaseBlend, Sm(-44, -50, y)));
            if (y > NoseTop || y < NoseBottom) n = -1000;
            n -= 25 * Sm(NoseBottom + BaseSoft, NoseBottom, y) + 60 * Sm(NoseTop - 3, NoseTop, y);
            // no carve next to the base (it folded the columella). 10-25: the carve fades in over 12..14 mm across and 1 mm round its y limits; switching
            // on at ax 13 left a 12 mm step that turned the warp over (minJacobian -0.087 -> +0.033)
            float carve = (1 - Sm(12, 14, ax)) * (1 - Sm(-29, -27, y)) * Sm(NoseBottom + 2, NoseBottom + 4, y);
            float zo = Mathf.Lerp(z, Mathf.Min(z, n), carve);
            float target = SmoothMax(zo, n, CheekBlend);
            float zone = (1 - Sm(26, 32, ax)) * Sm(18, 28, z) * Sm(NoseBottom - 4, NoseBottom - 1, y) * (1 - Sm(NoseTop, NoseTop + 4, y));
            zone *= 1 - Mathf.Exp(-Mathf.Pow((ax - 7.5f) / 4.5f, 2) - Mathf.Pow((y + 54) / 3.5f, 2));   // the nostril rims stay over their cavities (pulling them folded the walls)
            z += NoseBlend * zone * (target - z);
            return new Vector3(x / 1000, m.y, z / 1000);
        }
        /// Where MaleNose replaces the surface (face frame, metres): 1 on the nose, 0 off it (normals there come from the new geometry).
        static float MaleNoseZone(Vector3 m)
        {
            float x = Mathf.Abs(m.x * 1000), y = m.y * 1000, z = m.z * 1000;
            float Sm(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
            return (1 - Sm(24, 30, x)) * Sm(20, 30, z) * Sm(NoseBottom - 5, NoseBottom - 2, y) * (1 - Sm(NoseTop - 2, NoseTop + 2, y));
        }
        static float SmZ(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
        /// The male mouth area (face frame, metres): below the nose base to under the chin, up to the cheeks beside the mouth.
        static float MaleMouthZone(Vector3 m) { float x = Mathf.Abs(m.x * 1000), y = m.y * 1000, z = m.z * 1000; return (1 - SmZ(42, 55, x)) * SmZ(-128, -118, y) * (1 - SmZ(-62, -56, y)) * SmZ(-20, 0, z); }
        /// The male jaw underside (face frame, metres): the band under the chin and jaw line.
        static float MaleJawUnderZone(Vector3 m) { float x = Mathf.Abs(m.x * 1000), y = m.y * 1000, z = m.z * 1000; return (1 - SmZ(55, 70, x)) * SmZ(-150, -140, y) * (1 - SmZ(-112, -104, y)) * SmZ(-60, -40, z); }
        /// A clean lip volume in mm on the smoothed mouth (face frame, mm in, mm of depth out): upper-lip bulge with a slight bow, a lower-lip
        /// roll and a soft seam groove. Seam y -78.5 at the middle, 1.2 mm lower at the corners (x +-29); the paint frame sits 8.5 mm higher.
        static float MaleLips(Vector3 p)
        {
            const float Seam = -78.5f, CornerDrop = 1.2f, W = 29, UpH = 3.2f, UpTop = 8, LoH = 3.0f, LoBot = 10, Groove = 1.0f, GrooveW = .9f, Bow = .8f;
            float ax = Mathf.Abs(p.x), u = Mathf.Clamp01(ax / W), f = Mathf.Pow(Mathf.Clamp01(1 - u * u), 1.3f), ys = Seam - CornerDrop * u * u;
            float top = ys + UpTop + Bow * Mathf.Exp(-Mathf.Pow((ax - 7) / 4.5f, 2)) - Bow * Mathf.Exp(-Mathf.Pow(ax / 2.2f, 2));
            float upper = p.y > ys && p.y < top ? UpH * Mathf.Pow(Mathf.Sin(Mathf.PI * Mathf.Clamp01((p.y - ys) / Mathf.Max(top - ys, .001f))), 1.2f) : 0;
            float lower = p.y < ys && p.y > ys - LoBot ? LoH * Mathf.Sin(Mathf.PI * Mathf.Clamp01((ys - p.y) / LoBot)) : 0;
            return (upper + lower) * f - Groove * Mathf.Exp(-Mathf.Pow((p.y - ys) / GrooveW, 2)) * Mathf.Sqrt(f);
        }
        /// The male philtrum (face frame, metres): under the nose base, fading out before the upper lip line.
        static float MalePhiltrumZone(Vector3 m)
        {
            float x = Mathf.Abs(m.x * 1000), y = m.y * 1000, z = m.z * 1000;
            float Sm(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
            return (1 - Sm(12, 18, x)) * Sm(-74, -70, y) * (1 - Sm(-51, -48, y)) * Sm(20, 30, z);
        }
        /// The male cheeks (face frame, metres) that get a few relax passes: beside the nose to in front of the ear, below the eyes, above the jaw.
        /// 10-19 repair (chat F): the side of the neck from under the ear to the jaw angle was lumpy at 3/4 (s13 sculpt leftovers); relaxed like the jaw underside.
        static float MaleNeckSideZone(Vector3 m)
        {
            float x = Mathf.Abs(m.x * 1000), y = m.y * 1000, z = m.z * 1000;
            float Sm(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
            return Sm(40, 50, x) * Sm(-165, -150, y) * (1 - Sm(-95, -85, y)) * Sm(-115, -100, z) * (1 - Sm(-45, -35, z));
        }
        static float MaleCheekZone(Vector3 m)
        {
            float x = Mathf.Abs(m.x * 1000), y = m.y * 1000, z = m.z * 1000;
            float Sm(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
            return Sm(26, 34, x) * (1 - Sm(74, 82, x)) * Sm(-118, -108, y) * (1 - Sm(-28, -20, y)) * Sm(-60, -40, z);   // 10-19: out to the jaw angle and down to the jaw line (cheekbone-to-jaw band, crease in front of the ear)
        }
        public static Mesh Prepare(SkinnedMeshRenderer source, SkinnedMeshRenderer body, SkinnedMeshRenderer features, string headName, bool female)
        {
            if (!source || !body || !features || !source.sharedMesh.isReadable) return source ? source.sharedMesh : null;
            var mesh = source.sharedMesh;
            if (cache.TryGetValue(mesh, out var ready) && ready) return ready;
            int hi = Array.FindIndex(body.bones, b => b && b.name == headName);
            int fi = Array.FindIndex(features.bones, b => b && b.name == headName);
            int si = Array.FindIndex(source.bones, b => b && b.name == headName);
            if (hi < 0 || fi < 0 || si < 0) return mesh;
            var rest = body.sharedMesh.bindposes[hi].inverse;
            var featureMap = rest * features.sharedMesh.bindposes[fi];
            var sourceMap = rest * mesh.bindposes[si];
            var fv = features.sharedMesh.vertices; var fn = features.sharedMesh.normals;
            var indices = new List<int>();
            for (int s = 0; s < features.sharedMaterials.Length; s++)
                if (features.sharedMaterials[s].name.Contains("Sclera")) indices.AddRange(features.sharedMesh.GetTriangles(s));
            if (indices.Count == 0) return mesh;
            Vector3 up = rest.MultiplyVector(Vector3.up).normalized;
            Vector3 forward = featureMap.inverse.transpose.MultiplyVector(indices.Aggregate(Vector3.zero, (sum, i) => sum + fn[i]));
            forward = (forward - up * Vector3.Dot(forward, up)).normalized;
            Vector3 right = Vector3.Cross(up, forward).normalized; up = Vector3.Cross(forward, right).normalized;
            Vector3 eye = featureMap.MultiplyPoint3x4(indices.Aggregate(Vector3.zero, (sum, i) => sum + fv[i]) / indices.Count);
            Vector3 ToFace(Vector3 p) { var d = sourceMap.MultiplyPoint3x4(p) - eye; return new Vector3(Vector3.Dot(d, right), Vector3.Dot(d, up), Vector3.Dot(d, forward)); }
            Vector3 FromFace(Vector3 p) => sourceMap.inverse.MultiplyPoint3x4(eye + right * p.x + up * p.y + forward * p.z);
            float Smooth(float a, float b, float x) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((x - a) / (b - a)));
            var browVertices = new HashSet<int>(); var irisVertices = new HashSet<int>();
            if (source == features) for (int sub = 0; sub < features.sharedMaterials.Length; sub++) {
                string role = features.sharedMaterials[sub].name;
                if (role.Contains("Brow")) foreach (int i in mesh.GetTriangles(sub)) browVertices.Add(i);
                if (new[] { "Iris", "Pupil", "Limbal", "Catch" }.Any(role.Contains)) foreach (int i in mesh.GetTriangles(sub)) irisVertices.Add(i);
            }
            Vector3 Warp(Vector3 original, int vertex)
            {
                var p = ToFace(original);
                float head = Smooth(-.17f, -.12f, p.y) * (1 - Smooth(.16f, .20f, Mathf.Abs(p.x)));
                if (head < .00001f) return original;
                float front = Smooth(-.075f, -.045f, p.z);
                float eyeCenter = female ? .0453f : .0367f;
                float orbit = Smooth(-.085f, -.022f, p.y) * (1 - Smooth(.060f, .110f, p.y)) * front;
                float eyeRegion = Mathf.Exp(-Mathf.Pow((Mathf.Abs(p.x)-eyeCenter)/.027f,4)-Mathf.Pow(p.y/.018f,4)) * front;
                if(female && source==body && p.y>0){
                    float lid=Mathf.Exp(-Mathf.Pow((Mathf.Abs(p.x)-eyeCenter)/.025f,4)-Mathf.Pow((p.y-.010f)/.011f,4))*Smooth(0,.005f,p.y)*front;
                    p.y+=.0035f*lid;
                }
                float side = p.x / Mathf.Sqrt(p.x * p.x + .0001f);
                if (!female && !browVertices.Contains(vertex)) {
                    p.y += p.y * MaleEyeStretch * eyeRegion;
                    float irisRegion = Mathf.Exp(-Mathf.Pow((Mathf.Abs(p.x) - eyeCenter) / .030f, 4)) * eyeRegion;
                    p.x += (p.x - side * eyeCenter) * MaleIrisSpread * irisRegion;
                }
                float orbitalSides = Smooth(.012f, .030f, Mathf.Abs(p.x)) * Mathf.Exp(-Mathf.Pow(p.y/.050f,4));
                p.x -= side * (female ? .0028f : .0035f) * orbit * orbitalSides;
                p.y -= (female ? .010f : MaleOrbitDrop) * orbit;
                if (browVertices.Contains(vertex) && female) p.y = .0249f + (p.y - .0249f) * .88f;
                float mouth = Mathf.Exp(-Mathf.Pow((p.y + .079f) / .022f, 4)) * (1 - Smooth(.045f, .075f, Mathf.Abs(p.x))) * front;
                if (!female) p.x *= 1 + .06f * mouth;   // bald-base pass 2: was .16, the wide stretched grin
                if(source==body){
                    if(!female) {
                        // Open the existing auricle toward the front view while
                        // retaining its attachment and authored cartilage folds.
                        float ear=Smooth(.072f,.100f,Mathf.Abs(p.x))*(1-Smooth(-.085f,-.025f,p.z))
                            *Smooth(-.100f,-.060f,p.y)*(1-Smooth(.010f,.055f,p.y));
                        float angle=20*Mathf.Deg2Rad*ear;
                        float dx=Mathf.Abs(p.x)-.078f,dz=p.z+.090f;
                        p.x=Mathf.Sign(p.x)*(.078f+dx*Mathf.Cos(angle)-dz*Mathf.Sin(angle));
                        p.z=-.090f+dx*Mathf.Sin(angle)+dz*Mathf.Cos(angle);
                    }
                    // Bald-base pass 2026-10-12: a smaller, tidier auricle. Measured on this fitted head, the ear spans male y -.052..+.021,
                    // z -.118..-.071 (up to 26 mm proud of the skull) and female y -.052..+.040, z -.170..-.109 (31 mm). It shrinks toward its
                    // own centre on the skull side; a soft elliptical falloff lets the scalp around it slide along itself instead of denting.
                    // (Measured on the finished face: here y is Settle lower and the male x is before its 1.085 head scale.)
                    {
                        float yc=(female?-.003f:-.017f)+Settle,zc=female?-.138f:-.092f,root=female?.0888f:.0906f/1.085f;
                        float ry=female?.048f:.040f,rz=female?.032f:.026f,shrink=female?.16f:MaleEarShrink;
                        float reach=Mathf.Sqrt(Mathf.Pow((p.y-yc)/ry,2)+Mathf.Pow((p.z-zc)/rz,2));
                        float earShrink=shrink*(1-Smooth(1f,1.6f,reach))*Smooth(root-.030f,root-.015f,Mathf.Abs(p.x));
                        if(earShrink>0){
                            p.y=yc+(p.y-yc)*(1-earShrink);p.z=zc+(p.z-zc)*(1-earShrink);
                            float lateral=Mathf.Abs(p.x)-root;
                            p.x-=Mathf.Sign(p.x)*earShrink*Smooth(0,.006f,lateral)*Mathf.Max(lateral,0);
                        }
                    }
                    // Restore the rounded malar volume below the outer eyes.
                    // A broad, continuous support avoids a hard cosmetic ridge.
                    float cheek=Mathf.Exp(-2*Mathf.Pow((Mathf.Abs(p.x)-(female?.058f:.052f))/.030f,2)
                        -2*Mathf.Pow((p.y+.049f)/.032f,2))*Smooth(-.055f,-.010f,p.z);
                    p.z+=(female?.0045f:.0015f)*cheek;   // male 2026-10-18: softer cheekbones (Adnan: too pronounced; was .0035)
                    p.x+=side*.0012f*cheek;
                    if(female) {
                        float nose=Mathf.Exp(-Mathf.Pow(p.x/.029f,4)-Mathf.Pow((p.y+.055f)/.021f,4))*Smooth(.014f,.023f,p.z);
                        p.y+=.0055f*nose;
                        p.x*=1+.12f*nose;
                    }
                    // Round the nose's broad planes into a tip and separate alar
                    // wings. A partial blend retains the source identity and
                    // joins continuously into the untouched cheek surface.
                    float tip=Mathf.Exp(-2*Mathf.Pow(p.x/(female?.016f:.023f),2)-2*Mathf.Pow((p.y+(female?.043f:.049f))/(female?.015f:.019f),2));
                    float bridge=Mathf.Exp(-2*Mathf.Pow(p.x/(female?.0075f:.010f),2)-2*Mathf.Pow((p.y+.019f)/.035f,2));
                    float alar=Mathf.Exp(-2*Mathf.Pow((Mathf.Abs(p.x)-(female?.016f:MaleAlarX))/.009f,2)-2*Mathf.Pow((p.y+.053f)/.011f,2));
                    float targetNose=(female?.015f:.035f)+(female?.020f:MaleTip)*tip+(female?.008f:.014f)*bridge+(female?.006f:MaleAlarAmp)*alar;
                    if(!female) targetNose+=MaleDorsum*Mathf.Exp(-2*Mathf.Pow(p.x/MaleDorsumW,2)-Mathf.Pow((p.y-MaleDorsumY)/MaleDorsumH,2));
                    float noseBlend=Mathf.Exp(-Mathf.Pow(p.x/.032f,4)-Mathf.Pow((p.y+.047f)/.032f,4))*Smooth(female?0:.020f,female?.028f:.052f,p.z);
                    noseBlend*=female?Smooth(-.074f,-.060f,p.y):Smooth(MaleNoseFloor0,MaleNoseFloor1,p.y);
                    p.z=Mathf.Lerp(p.z,targetNose,noseBlend*(female?.25f:MaleNoseBlend));
                    float lipWidth=female?.034f:.041f;
                    float lipShape=Mathf.Pow(Mathf.Clamp01(1-p.x*p.x/(lipWidth*lipWidth)),2)*front;
                    float lower=Mathf.Exp(-Mathf.Pow((p.y+(female?.0875f:.084f))/.0070f,2));
                    p.z+=(female?.0025f:.0018f)*lower*lipShape;
                }
                // Male plate has a fuller cranium and mandible. Fade completely
                // above the neck base; no body or skeletal scaling.
                if (!female) p.x *= 1 + Mathf.Lerp(MaleJaw, MaleSkull, Smooth(-.115f, -.095f, p.y)) * head;   // 2026-10-17: skull narrower, jaw/neck as before
                // Bald-base pass 2 (2026-10-12), in this finished face's own measurements (mm in comments, centred on the finished eyes;
                // this warp's frame is centred on the source eyes, which the orbit term above lowered by Settle):
                // eyes a little bigger and rounder, irises round and slightly larger, the female eyes 3 mm closer together,
                // a smaller, narrower nose, and the ears a second step smaller. Head only; every term fades to zero before the neck.
                {
                    float sx = Mathf.Sign(p.x), ax = Mathf.Abs(p.x);
                    // eye openings: male 39 x 15 centred (38.5, -1.5); female 58 x 32 centred (46.7, -0.6)
                    float ec = female ? .0467f : .0385f, ey = female ? -.0006f + Settle : -.0015f - MaleOrbitDrop, hw = female ? .029f : .020f, hh = female ? .016f : .0075f;
                    float grow = female ? 1.0f : MaleEyeGrow, tall = female ? 1.20f : MaleEyeTall, inward = female ? .003f : 0;
                    float dx = ax - ec, dy = p.y - ey, reach = Mathf.Sqrt(dx * dx / (hw * hw) + dy * dy / (hh * hh));
                    float eyeFront = Smooth(-.060f, -.035f, p.z);
                    float eyeWeight = (1 - Smooth(1.0f, 2.6f, reach)) * eyeFront;
                    if (irisVertices.Contains(vertex)) {
                        // the iris stays round: one uniform scale about its own centre (male (36.6, 1.4), female (42.6, 0.7))
                        float ic = female ? .0426f : .0366f, iy = female ? .0007f + Settle : .0014f - MaleOrbitDrop, iris = female ? 1.06f : MaleIris;
                        ax = ic + (ax - ic) * iris; p.y = iy + (p.y - iy) * iris;
                    }
                    else if (!browVertices.Contains(vertex) && eyeWeight > 0) {
                        float g = grow - (!female && source != body ? MaleScleraInset : 0);   // male 2026-10-17: the sclera 3 % narrower than its lid opening (white specks showed at the corners)
                        ax = ec + dx * (1 + (g - 1) * eyeWeight); p.y = ey + dy * (1 + (tall - 1) * eyeWeight);
                    }
                    ax -= inward * (1 - Smooth(1.3f, 3.2f, reach)) * eyeFront * Smooth(.004f, .022f, ax);   // nothing crosses the midline
                    p.x = sx * ax;
                    if (source == body) {
                        // nose: narrower at the nostrils and a little less proud (only what stands in front of the cheek plane)
                        float noseFront = female ? Smooth(.004f, .016f, p.z) : Smooth(.031f, .045f, p.z);
                        float nose = Mathf.Exp(-Mathf.Pow(p.x / .028f, 4) - Mathf.Pow((p.y - Settle + (female ? .047f : .048f)) / .030f, 4)) * noseFront;
                        p.x *= 1 - (female ? .22f : MaleNoseNarrow) * nose;
                        p.z -= (female ? .0040f : .0045f) * nose * Smooth(0, 1, nose);
                        // ears, second step: male 65 mm tall centred (y -15.2, z -93.2), female 95 mm (y -1.6, z -138.4)
                        float yc = (female ? -.0016f : -.0152f) + Settle, zc = female ? -.1384f : -.0932f, root = female ? .0892f : .0909f;
                        float ry = female ? .052f : .036f, rz = female ? .032f : .022f, shrink = female ? .16f : MaleEarShrink;
                        float earReach = Mathf.Sqrt(Mathf.Pow((p.y - yc) / ry, 2) + Mathf.Pow((p.z - zc) / rz, 2));
                        float earShrink = shrink * (1 - Smooth(1f, 1.6f, earReach)) * Smooth(root - .030f, root - .015f, Mathf.Abs(p.x));
                        if (earShrink > 0) {
                            p.y = yc + (p.y - yc) * (1 - earShrink); p.z = zc + (p.z - zc) * (1 - earShrink);
                            float lateral = Mathf.Abs(p.x) - root;
                            p.x -= Mathf.Sign(p.x) * earShrink * Smooth(0, .006f, lateral) * Mathf.Max(lateral, 0);
                        }
                        if (!female) p.y -= MaleEarDrop * (1 - Smooth(1f, 1.6f, earReach)) * Smooth(root - .030f, root - .015f, Mathf.Abs(p.x));   // 2026-10-17: ear 4 mm lower (reference: top at the brow line, lobe at the nose base)
                    }
                }
                if (!female && (source == body || p.y < -.020f)) p = MaleNose(p);   // feature decals below the eyes (nostril pieces) ride the new nose too
                return FromFace(p);
            }
            var before = mesh.vertices; var after = new Vector3[before.Length]; var normals = mesh.normals;
            var adjusted = (Vector3[])normals.Clone(); int changed = 0, belowHeadChanges = 0; float minimumJacobian = 1;
            const float epsilon = .0001f;
            for (int i = 0; i < before.Length; i++) {
                after[i] = Warp(before[i], i);
                if ((after[i] - before[i]).sqrMagnitude < 1e-14f) { after[i] = before[i]; continue; }
                changed++;
                if(ToFace(before[i]).y<=-.17f)belowHeadChanges++;
                var jacobian = Matrix4x4.identity;
                jacobian.SetColumn(0, (Warp(before[i] + Vector3.right * epsilon, i) - after[i]) / epsilon);
                jacobian.SetColumn(1, (Warp(before[i] + Vector3.up * epsilon, i) - after[i]) / epsilon);
                jacobian.SetColumn(2, (Warp(before[i] + Vector3.forward * epsilon, i) - after[i]) / epsilon);
                minimumJacobian=Mathf.Min(minimumJacobian,jacobian.determinant);
                adjusted[i] = jacobian.inverse.transpose.MultiplyVector(normals[i]).normalized;
            }
            if (!female && source == body) {
                // Male nose 2026-10-18: the anatomical nose replaces the surface, so its shading comes from the new geometry (area-weighted face
                // normals over position-welded vertices), blended in by the nose zone; the warp Jacobian is kept everywhere else.
                var tris = mesh.triangles; var weld = new Dictionary<Vector3Int, int>(); var id = new int[after.Length]; var acc = new List<Vector3>();
                for (int i = 0; i < after.Length; i++) {
                    var key = new Vector3Int(Mathf.RoundToInt(after[i].x * 1e6f), Mathf.RoundToInt(after[i].y * 1e6f), Mathf.RoundToInt(after[i].z * 1e6f));
                    if (!weld.TryGetValue(key, out int w)) { w = acc.Count; weld[key] = w; acc.Add(Vector3.zero); } id[i] = w;
                }
                // two relax passes over the nose zone (position-welded Laplacian): irons out the old mesh's pits and folds under the new surface
                var zw = new float[acc.Count]; var cw = new float[acc.Count]; var pw = new float[acc.Count]; var lw = new float[acc.Count]; var jw = new float[acc.Count]; var nw = new float[acc.Count]; var pos = new Vector3[acc.Count];
                for (int i = 0; i < after.Length; i++) { pos[id[i]] = after[i]; zw[id[i]] = MaleNoseZone(ToFace(after[i])); cw[id[i]] = MaleCheekZone(ToFace(after[i])); pw[id[i]] = MalePhiltrumZone(ToFace(after[i])); lw[id[i]] = MaleMouthZone(ToFace(after[i])); jw[id[i]] = MaleJawUnderZone(ToFace(after[i])); nw[id[i]] = MaleNeckSideZone(ToFace(after[i])); }
                var nbr = new List<int>[acc.Count];
                void Link(int a, int b) { if (zw[a] <= 0 && zw[b] <= 0 && cw[a] <= 0 && cw[b] <= 0 && pw[a] <= 0 && pw[b] <= 0 && lw[a] <= 0 && lw[b] <= 0 && jw[a] <= 0 && jw[b] <= 0 && nw[a] <= 0 && nw[b] <= 0) return; (nbr[a] ??= new List<int>()).Add(b); (nbr[b] ??= new List<int>()).Add(a); }
                for (int t = 0; t < tris.Length; t += 3) { Link(id[tris[t]], id[tris[t + 1]]); Link(id[tris[t + 1]], id[tris[t + 2]]); Link(id[tris[t + 2]], id[tris[t]]); }
                for (int pass = 0; pass < 2; pass++) {
                    var next = (Vector3[])pos.Clone();
                    for (int w = 0; w < pos.Length; w++) {
                        if (zw[w] <= 0 || nbr[w] == null) continue;
                        var avg = Vector3.zero; foreach (int b in nbr[w]) avg += pos[b]; avg /= nbr[w].Count;   // duplicate links weight shared edges twice, as the offline relax
                        next[w] = pos[w] + .5f * zw[w] * (avg - pos[w]);
                    }
                    pos = next;
                }
                // 10-19 (Adnan: "above the lip looks disfigured and blurred"): 12 passes over the philtrum, nose base to just above the lip line
                // (the source mesh's sharp ridges there showed as light vertical streaks - the game keeps creases over 45 deg hard; offline over 45 deg 24 -> 0)
                for (int pass = 0; pass < 12; pass++) {
                    var next = (Vector3[])pos.Clone();
                    for (int w = 0; w < pos.Length; w++) {
                        if (pw[w] <= 0 || nbr[w] == null) continue;
                        var avg = Vector3.zero; foreach (int b in nbr[w]) avg += pos[b]; avg /= nbr[w].Count;
                        next[w] = pos[w] + .5f * pw[w] * (avg - pos[w]);
                    }
                    pos = next;
                }
                // 10-19 (Adnan: "it's wrinkled ... might be the lips"): the source mouth was lumpy (wavy lip outline, corner creases, a zigzag
                // seam) and the chin's underside scalloped. 8 passes over the mouth area and 4 along the jaw underside, then a clean lip volume
                // (MaleLips) on the smoothed mouth. Designed offline (tools/nose2.py lips_op, nose/jw4.json).
                void Relax(float[] weight, int passes) {
                    for (int pass = 0; pass < passes; pass++) {
                        var next = (Vector3[])pos.Clone();
                        for (int w = 0; w < pos.Length; w++) {
                            if (weight[w] <= 0 || nbr[w] == null) continue;
                            var avg = Vector3.zero; foreach (int b in nbr[w]) avg += pos[b]; avg /= nbr[w].Count;
                            next[w] = pos[w] + .5f * weight[w] * (avg - pos[w]);
                        }
                        pos = next;
                    }
                }
                Relax(lw, 8); Relax(jw, 4); Relax(nw, 10);   // 10-19 repair: neck side
                for (int w = 0; w < pos.Length; w++) if (lw[w] > 0) { var f = ToFace(pos[w]); f.z += MaleLips(f * 1000) / 1000; pos[w] = FromFace(f); }
                // then 8 more over the side walls only (bridge edge to cheek, above the wings): the game keeps creases over 45 degrees sharp,
                // and the ridge met the cheek steeply enough to leave faceted lines there (offline gate: edges over 20 degrees 57 -> 13)
                var sw = new float[pos.Length];
                for (int w = 0; w < pos.Length; w++) {
                    if (zw[w] <= 0) continue; var f = ToFace(pos[w]) * 1000; float ax = Mathf.Abs(f.x);
                    float Sm(float a, float b, float v) => Mathf.SmoothStep(0, 1, Mathf.Clamp01((v - a) / (b - a)));
                    sw[w] = Sm(4, 7, ax) * (1 - Sm(17, 23, ax)) * Sm(-48, -42, f.y) * (1 - Sm(-10, -4, f.y)) * zw[w];
                }
                for (int pass = 0; pass < 8; pass++) {
                    var next = (Vector3[])pos.Clone();
                    for (int w = 0; w < pos.Length; w++) {
                        if (sw[w] <= 0 || nbr[w] == null) continue;
                        var avg = Vector3.zero; foreach (int b in nbr[w]) avg += pos[b]; avg /= nbr[w].Count;
                        next[w] = pos[w] + .5f * sw[w] * (avg - pos[w]);
                    }
                    pos = next;
                }
                // softer cheekbones (Adnan: too pronounced): 4 passes over the cheeks, between the nose zone and the jaw (chat 11's jaw rows untouched)
                for (int pass = 0; pass < 6; pass++) {
                    var next = (Vector3[])pos.Clone();
                    for (int w = 0; w < pos.Length; w++) {
                        if (cw[w] <= 0 || nbr[w] == null) continue;
                        var avg = Vector3.zero; foreach (int b in nbr[w]) avg += pos[b]; avg /= nbr[w].Count;
                        next[w] = pos[w] + .5f * cw[w] * (avg - pos[w]);
                    }
                    pos = next;
                }
                // 10-25 untangle: pressing the old, steep nose side walls onto the new nose along z turns a few triangles over at the wing tops
                // (14 after the relax passes, a pale crack on the wing). Smooth only their corners and two rings round them until none is turned
                // over (12 passes; 141 vertices of the nose zone move, at most 2.4 mm; work/male-nose-fold-preview).
                for (int pass = 0; pass < 60; pass++) {
                    var hot = new HashSet<int>();
                    for (int t = 0; t < tris.Length; t += 3) {
                        var c0 = Vector3.Cross(before[tris[t + 1]] - before[tris[t]], before[tris[t + 2]] - before[tris[t]]);
                        var c1 = Vector3.Cross(pos[id[tris[t + 1]]] - pos[id[tris[t]]], pos[id[tris[t + 2]]] - pos[id[tris[t]]]);
                        if (Vector3.Dot(c0, c1) < 0) { hot.Add(id[tris[t]]); hot.Add(id[tris[t + 1]]); hot.Add(id[tris[t + 2]]); }
                    }
                    if (hot.Count == 0) break;
                    for (int ring = 0; ring < 2; ring++) foreach (int w in hot.ToArray()) if (nbr[w] != null) foreach (int b in nbr[w]) hot.Add(b);
                    var next = (Vector3[])pos.Clone();
                    foreach (int w in hot) {
                        if (zw[w] <= 0 || nbr[w] == null) continue;
                        var avg = Vector3.zero; foreach (int b in nbr[w]) avg += pos[b]; avg /= nbr[w].Count;
                        next[w] = pos[w] + .5f * (avg - pos[w]);
                    }
                    pos = next;
                }
                for (int i = 0; i < after.Length; i++) if (zw[id[i]] > 0 || cw[id[i]] > 0 || pw[id[i]] > 0 || lw[id[i]] > 0 || jw[id[i]] > 0 || nw[id[i]] > 0) after[i] = pos[id[i]];
                for (int t = 0; t < tris.Length; t += 3) {
                    var c = Vector3.Cross(after[tris[t + 1]] - after[tris[t]], after[tris[t + 2]] - after[tris[t]]);
                    acc[id[tris[t]]] += c; acc[id[tris[t + 1]]] += c; acc[id[tris[t + 2]]] += c;
                }
                // which side the triangle winding faces: one global sign, voted over the zone (per-vertex checks against the imported normals
                // flipped the old nostril pockets, whose normals pointed into the pocket)
                float vote = 0; for (int i = 0; i < after.Length; i++) if (zw[id[i]] > 0) vote += Vector3.Dot(acc[id[i]], normals[i]);
                float side = vote < 0 ? -1 : 1;
                for (int i = 0; i < after.Length; i++) {
                    float zone = zw[id[i]] > 0 || pw[id[i]] > 0 || cw[id[i]] > 0 || lw[id[i]] > 0 || jw[id[i]] > 0 || nw[id[i]] > 0 ? 1 : 0; if (zone <= 0) continue;   // full geometric normal wherever a region moved the surface (a partial blend kept bad warp-Jacobian normals at the zone edge: light drips under the nose)
                    var g = acc[id[i]]; float gl = g.magnitude; if (gl < 1e-12f) continue; g *= side / gl;   // manual: Vector3.normalized returns zero under 1e-5 (these sums are ~5e-6 m2)   // winding-independent: the side the imported normal faced
                    adjusted[i] = Vector3.Slerp(adjusted[i], g, zone).normalized;
                }
            }
            ready = UnityEngine.Object.Instantiate(mesh); ready.name = mesh.name + " (reference face fit)"; ready.hideFlags = HideFlags.DontSave;
            ready.vertices = after; ready.normals = adjusted; ready.ClearBlendShapes();
            if (source == body) {
                // Distance to the actual open eyelid boundary travels with the
                // skinned surface, including every blink, instead of projecting
                // a stationary painted arc onto the face.
                var welded = new Dictionary<Vector3Int,int>();
                var alias = new int[before.Length]; var facePoints = new List<Vector3>();
                for(int i=0;i<before.Length;i++) {
                    var p=ToFace(before[i]); var key=new Vector3Int(Mathf.RoundToInt(p.x*1000000),Mathf.RoundToInt(p.y*1000000),Mathf.RoundToInt(p.z*1000000));
                    if(!welded.TryGetValue(key,out int id)){id=facePoints.Count;welded[key]=id;facePoints.Add(p);} alias[i]=id;
                }
                var edges=new Dictionary<(int,int),int>(); var triangles=mesh.triangles;
                void Edge(int a,int b){if(a>b)(a,b)=(b,a);edges.TryGetValue((a,b),out int count);edges[(a,b)]=count+1;}
                for(int t=0;t<triangles.Length;t+=3){Edge(alias[triangles[t]],alias[triangles[t+1]]);Edge(alias[triangles[t+1]],alias[triangles[t+2]]);Edge(alias[triangles[t+2]],alias[triangles[t]]);}
                var upper=new List<(Vector3,Vector3)>();var lower=new List<(Vector3,Vector3)>();
                foreach(var edge in edges)if(edge.Value==1){
                    var a=facePoints[edge.Key.Item1];var b=facePoints[edge.Key.Item2];var mid=(a+b)*.5f;
                    if(Mathf.Abs(mid.x)>.014f && Mathf.Abs(mid.x)<.085f && Mathf.Abs(mid.y)<.032f && mid.z>-.028f)
                        (mid.y>0?upper:lower).Add((a,b));
                }
                float Distance(Vector3 p,List<(Vector3,Vector3)> segments){float d=.1f;foreach(var edge in segments){var v=edge.Item2-edge.Item1;float t=Mathf.Clamp01(Vector3.Dot(p-edge.Item1,v)/Mathf.Max(v.sqrMagnitude,1e-12f));d=Mathf.Min(d,Vector3.Distance(p,edge.Item1+v*t));}return d;}
                var rim=new List<Vector2>(before.Length);
                foreach(var p in before){var f=ToFace(p);rim.Add(new Vector2(Distance(f,upper),Distance(f,lower)));}
                ready.SetUVs(2,rim);
            }
            for (int shape = 0; shape < mesh.blendShapeCount; shape++) for (int frame = 0; frame < mesh.GetBlendShapeFrameCount(shape); frame++) {
                var dp = new Vector3[before.Length]; var dn = new Vector3[before.Length]; var dt = new Vector3[before.Length];
                mesh.GetBlendShapeFrameVertices(shape, frame, dp, dn, dt);
                for (int i = 0; i < dp.Length; i++) if (dp[i].sqrMagnitude > 1e-14f) dp[i] = Warp(before[i] + dp[i], i) - after[i];
                ready.AddBlendShapeFrame(mesh.GetBlendShapeName(shape), mesh.GetBlendShapeFrameWeight(shape, frame), dp, dn, dt);
            }
            if (source == features) {
                var eyeVertices = new HashSet<int>();
                for (int sub=0;sub<features.sharedMaterials.Length;sub++) {
                    string role=features.sharedMaterials[sub].name;
                    if(new[]{"Iris","Pupil","Limbal","Catch"}.Any(role.Contains))
                        foreach(int i in mesh.GetTriangles(sub))eyeVertices.Add(i);
                }
                void Expression(string name, HashSet<int> selected, Vector3 displacement) {
                    var delta=new Vector3[after.Length];
                    foreach(int i in selected)delta[i]=sourceMap.inverse.MultiplyVector(displacement);
                    ready.AddBlendShapeFrame(name,100,delta,new Vector3[after.Length],new Vector3[after.Length]);
                }
                Expression("Face_GazeRight",eyeVertices,right*.0018f);Expression("Face_GazeLeft",eyeVertices,-right*.0018f);
                Expression("Face_GazeUp",eyeVertices,up*.0018f);Expression("Face_GazeDown",eyeVertices,-up*.0018f);
                Expression("Face_BrowUp",browVertices,up*.004f);Expression("Face_BrowDown",browVertices,-up*.003f);
            }
            // Matched skin and feature targets move together; neutral weight keeps
            // the accepted head mesh exactly intact. Mouth corners carry emotion
            // even when a cap obscures the eyebrows.
            foreach (string expression in new[] { "Face_Smile", "Face_Sad", "Face_Shock" })
            {
                var delta = new Vector3[after.Length];
                for (int i = 0; i < after.Length; i++)
                {
                    var p = ToFace(after[i]);
                    float front = Smooth(-.045f, -.005f, p.z);
                    float mouth = Mathf.Exp(-Mathf.Pow((p.y + .089f) / .025f, 4))
                        * (1 - Smooth(.045f, .07f, Mathf.Abs(p.x))) * front;
                    float corner = Smooth(.008f, .038f, Mathf.Abs(p.x));
                    float dy = expression == "Face_Smile" ? .005f * corner
                        : expression == "Face_Sad" ? -.004f * corner
                        : Mathf.Clamp((p.y + .089f) * .35f, -.006f, .003f);
                    delta[i] = sourceMap.inverse.MultiplyVector(up * (mouth * dy));
                }
                ready.AddBlendShapeFrame(expression, 100, delta, null, null);
            }
            ready.RecalculateBounds(); cache[mesh] = ready;
            bool topologySame=mesh.triangles.SequenceEqual(ready.triangles),weightsSame=mesh.boneWeights.SequenceEqual(ready.boneWeights),bindsSame=mesh.bindposes.SequenceEqual(ready.bindposes);
            Debug.Log($"[HeroFaceReferenceFit] {(female ? "female" : "male")} {source.name}: moved={changed}; belowHeadChanges={belowHeadChanges}; minJacobian={minimumJacobian:R}; topologySame={topologySame}; weightsSame={weightsSame}; bindsSame={bindsSame}");
            if(belowHeadChanges!=0 || minimumJacobian<=0 || !topologySame || !weightsSame || !bindsSame)
                Debug.LogError("[HeroFaceReferenceFit] head-only deformation invariant failed");
            return ready;
        }
        public static void ApplyExpression(MatchHeroLook hero, float blink, Vector2 gaze, float brow)
        {
            var face=hero ? hero.face as SkinnedMeshRenderer : null;
            if(!face || !face.sharedMesh)return;
            void Weight(string name,float value){int index=face.sharedMesh.GetBlendShapeIndex(name);if(index>=0)face.SetBlendShapeWeight(index,Mathf.Clamp01(value)*100);}
            gaze=Vector2.ClampMagnitude(gaze,.0018f)*(1-Mathf.Clamp01(blink));
            Weight("Face_GazeRight",gaze.x/.0018f);Weight("Face_GazeLeft",-gaze.x/.0018f);
            Weight("Face_GazeUp",gaze.y/.0018f);Weight("Face_GazeDown",-gaze.y/.0018f);
            Weight("Face_BrowUp",brow/.001f);Weight("Face_BrowDown",-brow/.001f);
        }
        public static void ApplyMood(MatchHeroLook hero, float smile, float sad, float shock)
        {
            if (!hero) return;
            foreach (var skin in new[] { hero.body, hero.face as SkinnedMeshRenderer })
            {
                if (!skin || !skin.sharedMesh) continue;
                void Set(string name, float value) { int i = skin.sharedMesh.GetBlendShapeIndex(name); if (i >= 0) skin.SetBlendShapeWeight(i, Mathf.Clamp01(value) * 100); }
                Set("Face_Smile", smile); Set("Face_Sad", sad); Set("Face_Shock", shock);
            }
        }
    }
}

# Unity staging (NOT installed in Unity/Assets)
- Materials/Std_White_Lit.mat, Std_Black_Lit.mat: URP Lit, Opaque, Smoothness 0.30, Metallic 0, BaseColor sRGB white 0.93 / black (0.035,0.035,0.04). Built from the project's Base_Grey.mat template.
- FBX materials are named Std_White_Lit / Std_Black_Lit: remap the two slots to these .mat files in the Model importer (Materials tab).
- Scratch-project import test (Unity 6000.3.24f1): proof/unity_import_report.json = PASS (scale 1, UV + normals, URP Lit shader). proof/unity_align_report.json holds body-vs-kit world bounds (saved, not reviewed in detail).

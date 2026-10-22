#!/usr/bin/env python3
"""Set up only the approved new Editor scratch namespace; never copy installed FBX.

This setup does NOT launch Unity. Parent must serialize the subsequent Unity run.
All physical proof-tool/FBX/meta files are under v3; Assets contains directory and
folder-meta symlinks only. Refuse existing non-symlink paths.
"""
import argparse
import pathlib
import shutil
import uuid


def link(dst, src):
    if dst.is_symlink():
        if dst.resolve() != src.resolve():
            raise SystemExit(f"Refusing different existing symlink: {dst}")
    elif dst.exists():
        raise SystemExit(f"Refusing existing non-symlink: {dst}")
    else:
        dst.symlink_to(src, target_is_directory=src.is_dir())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=pathlib.Path)
    p.add_argument("--fixture-dir", required=True, type=pathlib.Path)
    p.add_argument("--include-phase5", action="store_true", help="Copy authorized staged gameplay / Split / frame-counter drafts; parent must serialize installation")
    p.add_argument("--unity-project", type=pathlib.Path, help="Default primary Unity; an approved proof clone may be used")
    a = p.parse_args()
    r = a.root.resolve()
    v3 = r / "work/postcard-look/v3"
    fixture = a.fixture_dir.resolve()
    if not fixture.is_relative_to(v3.resolve()):
        raise SystemExit("Fixture directory must physically reside under v3")
    if not fixture.is_dir():
        raise SystemExit("Fixture directory missing")
    scratch = v3 / "unity-proof"
    scratch.mkdir(parents=True, exist_ok=True)
    names=["PostcardV3FrameProof.cs", "PostcardV3Proof.shader", "PostcardV3IOSExport.cs", "PostcardV3FixtureCapture.cs", "PostcardV3ScratchImporter.cs", "PostcardV3FixtureSway.cs"]
    if a.include_phase5:names += ["PostcardV3StageModel.cs","PostcardV3ProofMasks.cs","PostcardV3SplitOutline.cs","PostcardV3FrameCosts.cs","PostcardV3CostDriver.cs"]
    for name in names:
        shutil.copyfile(v3 / "proof-tools" / name, scratch / name)
    link(scratch / "fixtures", fixture)
    meta = v3 / "unity-proof.folder.meta"
    if not meta.exists():
        meta.write_text("fileFormatVersion: 2\nguid: " + uuid.uuid4().hex + "\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n")
    unity=(a.unity_project or r/"Unity").resolve()
    if unity != (r/"Unity").resolve() and not unity.is_relative_to(v3.resolve()):raise SystemExit("Proof clone must be beneath actual v3")
    editor = unity / "Assets/Editor"
    link(editor / "PostcardV3Scratch", scratch)
    link(editor / "PostcardV3Scratch.meta", meta)
    print("Prepared Assets/Editor/PostcardV3Scratch ->", scratch)
    print("Fixture prefix: Assets/Editor/PostcardV3Scratch/fixtures/")
    print("No Unity run or installed model copy performed.")


if __name__ == "__main__":
    main()

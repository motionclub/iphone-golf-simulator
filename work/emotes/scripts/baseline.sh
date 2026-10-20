#!/bin/zsh
# baseline.sh <before|after> : hash manifests of everything this job must not change + the media inventory + git state.
# Taken ONCE as `before` at job start (the re-run guard below refuses to overwrite it); `after` is taken by verify_repo.py's caller at the end.
set -u
R=/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator
D=$R/work/emotes/data/baseline
tag=$1
mkdir -p $D
if [ "$tag" = before ] && [ -f $D/job_start.txt ]; then echo "baseline already taken at $(cat $D/job_start.txt); refusing to retake"; exit 1; fi
cd $R
date '+%Y-%m-%d %H:%M:%S' > $D/job_start.txt.tmp
{
  # sha256 of every project file we could touch (Unity assets + settings + packages manifest, the Swift app, the Xcode projects)
  find Unity/Assets Unity/ProjectSettings Unity/Packages GolfArcade GolfArcadeTests GolfArcadeUITests -type f \
       -not -name .DS_Store -not -path '*/xcuserdata/*' -not -path '*/DerivedData/*' -print0 2>/dev/null | xargs -0 shasum -a 256
  shasum -a 256 project.yml project-unity.yml AGENTS.md 2>/dev/null
  find GolfArcade.xcodeproj GolfArcadeUnity.xcodeproj GolfArcadeUnity.xcworkspace -type f -not -path '*/xcuserdata/*' -not -name .DS_Store -print0 2>/dev/null | xargs -0 shasum -a 256
} | sort -k2 > $D/sha_project_$tag.txt
# stat manifest (size + mtime) of ArtDir and work/ minus this job (hashing 30 GB is not needed: only "did a path appear / change / vanish")
{
  find ArtDir blender Tools docs -type f -not -name .DS_Store -exec stat -f '%z %m %N' {} + 2>/dev/null
  find work -type f -not -path 'work/emotes/*' -not -name .DS_Store -not -path '*/__pycache__/*' -exec stat -f '%z %m %N' {} + 2>/dev/null
} | sort -k3 > $D/stat_other_$tag.txt
# media inventory (video / audio / animated image), whole repo except Unity/Library, Builds and .git
find . -type f \( -iname '*.mp4' -o -iname '*.mov' -o -iname '*.m4v' -o -iname '*.webm' -o -iname '*.mkv' -o -iname '*.avi' -o -iname '*.gif' -o -iname '*.mp3' -o -iname '*.wav' -o -iname '*.m4a' -o -iname '*.aac' -o -iname '*.ogg' -o -iname '*.flac' -o -iname '*.opus' \) \
     -not -path './Unity/Library/*' -not -path './.git/*' -not -path './Unity/Builds/*' -exec stat -f '%z %m %N' {} + 2>/dev/null | sort -k3 > $D/media_$tag.txt
# animation-ish files (the "no other new clip" inventory)
find . -type f \( -iname '*.fbx' -o -iname '*.anim' -o -iname '*.controller' -o -iname '*.overrideController' -o -iname '*.bvh' -o -iname '*.dae' -o -iname '*.glb' -o -iname '*.gltf' \) \
     -not -path './Unity/Library/*' -not -path './.git/*' -not -path './Unity/Builds/*' -exec shasum -a 256 {} + 2>/dev/null | sort -k2 > $D/anim_files_$tag.txt
git rev-parse HEAD > $D/git_head_$tag.txt
git status --short > $D/git_status_$tag.txt
git diff --stat HEAD > $D/git_diffstat_$tag.txt 2>/dev/null
# running processes that could be writing at the same time
ps -Ao pid,etime,command | grep -E 'Unity|Blender|xcodebuild|swift-build|claude' | grep -v grep | cut -c1-200 > $D/procs_$tag.txt
mv $D/job_start.txt.tmp $D/job_start.txt 2>/dev/null || true
[ "$tag" = after ] && date '+%Y-%m-%d %H:%M:%S' > $D/job_end.txt
echo "baseline $tag done: $(wc -l < $D/sha_project_$tag.txt) project files hashed, $(wc -l < $D/media_$tag.txt) media, $(wc -l < $D/anim_files_$tag.txt) anim files"

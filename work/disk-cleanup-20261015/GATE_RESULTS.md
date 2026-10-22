# Disk cleanup — 2026-10-15

GATE: DISK CLEANUP PASS

- Free space before: approximately 3.4 GiB; the concurrent archive build briefly exhausted the disk during the sweep.
- Free space after: 23.18 GiB (live value; other builds continue writing).
- Net available-space increase: approximately 19.8 GiB.
- Deleted 426 generated cache/build entries. No deletion errors.
- Inactive Unity copies: removed only known generated import, package, shader and compilation caches.
- Xcode/Swift: removed inactive build products, compiler caches and indexing data.
- Preserved source trees, all art and meshes, clothing work, proof folders, custom Unity Captures/TestResults/TropicalReview, Xcode archives, Git history and all Git LFS objects.
- Preserved caches associated with active processes/open files, including the App Store archive build and its phone-build-20261014 Unity export.
- Every repo deletion was checked against tracked paths; zero tracked files were selected.
- Verified every deleted entry is absent and the locked reference files and principal source directories remain present.
- No commits, staging, checkout, stash, history rewrite, app changes, or simulator resets.
- Builds/tests were not run: this cleanup changes only generated data. Inactive projects regenerate their caches when opened/built.

## Evidence

`preflight.json`: inspected candidate roots and active-use exclusions. Candidate sizes include retained captures, so they are not bytes reclaimed.

`results.json` and `native_results.json`: exact deletions and exclusions.

`journal.jsonl`: deletion journal (the first emergency build-cache removal is recorded in results.json).

`disk_after.txt`: final disk availability.

APFS clone sharing means adding deleted folder sizes overstates physical space recovered. The reported improvement uses filesystem free space instead.

The disk still contains large source and evidence collections (notably Git/LFS and work/proof outputs). They were preserved; this sweep targeted disposable generated data.

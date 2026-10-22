# Male garments (ref pack 2026-10-17): install notes for the integration chat

## Already installed + staged (owned garment files, 67 paths, list in `installed_files.txt`; golf male re-staged 10-17 late for the slim trousers)
`Unity/Assets/Characters/KitsV2/{MatchHero_Male,GolfKitHero_Male}/*.asset` (new meshes: shoes, socks, shorts, golf polo, belt; pipeline weights
+ pose correctives on every piece) and `Unity/Assets/Resources/{Tennis,Golf}/KitsV2/Male/*` (N/M maps, hide lists, correctives json, offsets).
These ONLY work together with the prefab patch below (the prefabs carry the renderer bone lists the new meshes are skinned to).

## Shared files: NOT installed, apply these
00. **10-18 round 9 (current): APPLIED 18:22 (Adnan OK, unstaged, backup backup_prefabs_1018_1822/).** Was: on top of the 10-17 and r6 patches: `male_prefabs_r9_p0.patch` (`git apply -p0`;
   --check passes 10-18 17:4x; result == the clone's prefabs; bone check 0 BAD; tennis Kit_Top / Kit_Bottom renderers carry chat 5's 32/16
   corrective shapes, all shoes the skin-weight bones). Revert: `git apply -R -p0` with the same file.
0. **10-18 round 6 (current): BOTH APPLIED in the working tree (Adnan OK'd, unstaged; r6 at 11:09, backup backup_prefabs_1018_1109/).** Was: on top of the 10-17 patch apply
   `male_prefabs_r6_p0.patch` (`git apply -p0`; `--check` passes on the tree of 10-18 07:4x; result == the clone's prefabs; bone check 0 BAD):
   golf prefab gains Kit_Sock_L/R (short golf socks), every male garment renderer re-created by the installers. Revert: `git apply -R -p0` with
   the same file. The owned files it needs are staged (installed_files.txt, 87 paths).
1. USE `male_prefabs_p0.patch` (`git apply -p0`; 10-18 fix: the old `male_prefabs.patch` has the clone path on its `+++` side, so git treats it
   as a RENAME of the prefabs into `Users/...` — never apply that file). Backup of both prefabs before applying (10-18 00:41):
   `backup_prefabs_1018_0041/`. Revert: `git apply -R -p0 male_prefabs_p0.patch` or copy the backups back. Content: `PlayerMale.prefab`, `PlayerMaleGolfKit.prefab` exactly as `ClothingV2Install` +
   `GarmentPipelineInstall` saved them in `~/male-garments-UnityClone` (renderer meshes/bones for the new pieces). Made against the working tree
   of 2026-10-17 ~22:20, which already has someone else's UNSTAGED edits to both prefabs; `git apply --check` passed then. Regenerated after the
   slim-trousers install (golf prefab only: Kit_Bottom 9 bones, re-created helper objects with new fileIDs; tennis section unchanged); `--check` passes. If the prefabs change
   again, re-run the installers instead: `tools/install_batch.sh MatchHero_Male:MG_MT:<refpack>/out GolfKitHero_Male:MG_GM:<refpack>/out steps=cv2,install`
   in a clone, then copy the two prefabs.
2. `MatchHeroLook_shoe_trim.patch`: male tennis shoe default trim -> StarterNavy (golf already navy; female unchanged). Without it the tennis
   shoe's panels render white-on-white until the player picks a colour.

## Lobby (SceneKit)
See `../LOBBY.md` (exported files + .ktx in `../lobby/assets`, list of changed files, parity sheets). Not copied into
`GolfArcade/Unity/CharacterAssets` because other chats install there too.

## Rollback
Owned files: `git restore --staged --worktree -- $(sed 's|^|Unity/|' installed_files.txt)` restores the 10-13 garments (do it only for
these paths). Builders keep today's behaviour unless the new env vars / designs are used (shoe4.py is new; maps.py additions are opt-in by detail name).

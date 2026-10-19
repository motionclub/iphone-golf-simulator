# Female top revision — user feedback

User rejected the tennis armhole cut and painted-on read; polo appearance is usable but must remain intact through animation. Skirts and original face are preserved.

Reference 09: round deep side opening below axilla; substantial curved binding, shoulder straps that bridge the shoulder rather than hug the neck, eased lower ribs and soft hanging folds. Current opening is too high, with an abrupt pinched boundary; rectangular lower torso lacks convincing cloth folds.

Use Blender Director, Character Artist, Cloth Sim, Rigging and Unity CLI. Separate top pattern meshes, <=20k triangles each, existing 2K maps/custom colors. Revise tennis silhouette first; inspect golf at several real clip times and remove unstable garment deformation. Body/rig/clips/world remain unchanged. Deliver actual Unity neutral and motion images and muted clips. Stage scoped files only, no commits.

2026-10-16 user steering: arm proportions must remain consistent throughout animation. Body arm weight repair and volume preservation are now explicitly in scope; retain neutral body positions, face, source rig and clips. User accepted the revised arms ("arms look way better now"). Measured arm surface sections across all 51 female clips retain 89.9–111.7% of neutral area, compared with 14–26% in the old overhead pose.

2026-10-16 user steering: shaders are a main part of the remaining implementation, covering skin, clothes and the rest of the character. Use the reference pack's soft skin/satin response and matte substantial fabric. Work on female material instances and explicitly gated shader branches; preserve male appearance, customization and existing map lighting/camera. Finish sleeve clearance with the repaired arms, then run matched material comparisons in studio and actual game. User owns visual acceptance; paste images in chat. Keep audio muted.

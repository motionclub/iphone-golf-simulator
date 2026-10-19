# Hole 14 support visibility

The original fixed audit positions ignored local terrain elevation and allowed CameraRig to continue updating after assigning the diagnostic transform. Effective-state measurements place approach 3.58 yards and green 5.66 yards below the sampled terrain. Those original shots remain in the full comparison, with this limitation.

The supplemental scratch-only fixture disables the camera driver and sets the two view heights to local raycast ground+3/+6 yards. Both stage0 and stage7 use identical positions, field of view and seed. Supporting land is visible in both. The resulting images resolve the audit's missing-land question; they do not establish production camera behavior or justify changing terrain. No production camera or geometry was edited.

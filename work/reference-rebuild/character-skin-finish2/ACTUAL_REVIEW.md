# Corrected Unity skin-finish2 review

Root confirms the corrected candidate/control queue completed in 23.74s/24.03s without shader or C# errors. The earlier unchanged output audit is invalidated in stale-run-pixel-audit.json.

ART FAIL for adoption. Ready front and threequarter portraits are visibly different, but delta size does not establish a better skin finish. Both sexes gain darker form contrast; male mouth corners and eye sockets become harsher and the cheek highlights follow uneven existing planes. Female lip pigment becomes a flat rectangular band with an abrupt upper edge. Serve open/closed geometry and blink identity remain unchanged by this material patch.

Compared with the target portraits, the result lacks their continuous lip transitions, soft socket shadows, and clean broad forehead/cheek highlights. The targets' dimensional improvement also depends on surface anatomy that this material-only scope preserves.

Cause: the candidate's smoothstep transfers map source lip weights up to .70 and seam weights up to .46 nearly to 1, amplifying the coarse source contour and dark line. Its .70 ambient factor and .20 wrap raise contrast on malformed normal/form patches. The new specular lobe adds conspicuous white marks on those patches.

One targeted revision is staged under revision1: return to linear existing masks with restrained pigment; ambient .82 and wrap .28; broad specular maximum .075 with no narrow lobe. No invented lip contour or mesh/normal edits. This is a single attempt to reduce the demonstrated cause, not a reference-fidelity claim. Root actual render/art gate is pending.

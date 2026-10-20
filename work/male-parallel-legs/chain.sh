#!/bin/bash
# Male HeroBase legs/feet zone: deterministic chain  V_start(base) -> V_final  (zone = z<0.765, |x|<0.27 ; everything else bit-identical)
# run from work/male-parallel-legs :  PYTHONPATH=../male-micro1i/pylib ./chain.sh
set -e
PY=/Applications/Blender.app/Contents/Resources/5.2/python/bin/python3.13
$PY stepA.py                                                       # A  : de-banding (vertical anisotropic Taubin, 40 it) -> data/V_A40.npy
$PY stepW2.py data/V_A40.npy data/V_W2.npy 3 0.017 -0.0125 0.020 0.19   # W  : foot/ankle placement from plate profiles (heel +17, toe -12.5, ankle +20 mm, toe-out 3 deg)
$PY stepF5.py data/V_W2.npy data/V_F5_40.npy 40 1.0                # F5 : biharmonic fairing of the feet (lam 40)
$PY stepP.py data/V_F5_40.npy data/V_P1.npy 1.0                    # P  : sagittal profile warp onto the plate near-foot contour (instep/ankle)
$PY stepF6.py data/V_P1.npy data/V_P2.npy 25 0.22                  # F6 : fairing after the warp
$PY stepR.py data/V_P2.npy data/V_R1.npy 25                        # R  : tangential relaxation (even spacing)
$PY stepL.py data/V_R1.npy data/V_L1.npy 4.0 0.17 0.74            # L  : light isotropic fairing of the leg tube (cm-scale lumps)
$PY stepK.py data/V_L1.npy data/V_final.npy 8 0.52 0.040 0.042     # K  : kneecap relief
echo CHAIN_DONE

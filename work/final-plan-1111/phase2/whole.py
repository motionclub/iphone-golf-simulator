"""whole.py [key=value ...]: the whole-body set on the base body, measured (figure.measure) against the base. Keys starting
with 'a.' override armfield.P, others torsofield.P."""
import sys, numpy as np, posed, fit, figure, armio, armfield as af, torsofield as tf
for a in sys.argv[1:]:
    k, v = a.split("=")
    if k.startswith("a."): af.P[k[2:]] = float(v)
    else: tf.P[k] = float(v)
base = posed.load("male_build0"); base['Kit_Bottom'] = armio.read("export/male_build0/Kit_Bottom.bin")
new = fit.dress(base, posed.B, posed.mL, posed.mR, fit=False)
m0, m1 = figure.measure(base), figure.measure(new)
print(f"{'':12}{'base':>8}{'whole':>8}")
for k in ('neck_w','shoulders','chest_w','chest_d','chest_g','waist_w','waist_d','waist_g','hip_w','hip_d','hip_g','uparm_w','uparm_d','uparm_g','forearm_w','forearm_g','thigh_g','calf_g'): print(f"{k:12}{m0[k]:8.1f}{m1[k]:8.1f}")
print("chest/waist girth", round(m1['chest_g']/m1['waist_g'], 2), " hip/waist", round(m1['hip_g']/m1['waist_g'], 2), " shoulders/waist width", round(m1['shoulders']/m1['waist_w'], 2), " upper arm/forearm", round(m1['uparm_g']/m1['forearm_g'], 2))
b = base['Body']['pos']; nb = new['Body']['pos']; s = (np.abs(b[:, 0]) < .14)
print("front (z max) and back (z min) by height, base -> whole:")
for y0 in (1.42, 1.36, 1.33, 1.30, 1.27, 1.24, 1.21, 1.18, 1.15, 1.10, 1.05, 1.00, 0.95, 0.90):
    q = s & (abs(b[:, 1] - y0) < .012); print(f"  {y0:4.2f}  front {b[q][:, 2].max()*100:5.1f} -> {nb[q][:, 2].max()*100:5.1f}   back {b[q][:, 2].min()*100:6.1f} -> {nb[q][:, 2].min()*100:6.1f}")

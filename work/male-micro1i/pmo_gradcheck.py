import sys, time
sys.path.insert(0, '.')
exec(open('pmo_test.py').read().split("# starting residual at h=0")[0])
h = h_true[pb.idx] * 0.0
rows, cols, vals, r0 = build_jacobian(pb, h, verbose=True)
J = Sparse(rows, cols, vals, len(r0), len(pb.idx))
rng = np.random.default_rng(5)
for trial in range(3):
    v = rng.normal(0, 1, len(pb.idx)) * (rng.random(len(pb.idx)) < 0.3)
    # smooth-ish random direction: use a few bumps instead
    eps = 0.3
    r1 = pb.residuals(h + eps * v)
    pred = J.dot(eps * v)
    act = r1 - r0
    print('trial %d: |actual| %.3f |pred| %.3f  corr %.4f  ratio %.3f' % (trial, np.linalg.norm(act), np.linalg.norm(pred), np.corrcoef(act, pred)[0, 1], np.linalg.norm(pred) / np.linalg.norm(act)))

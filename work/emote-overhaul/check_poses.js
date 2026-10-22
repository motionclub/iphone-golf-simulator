// Headless self-check of the pose model in pose_preview.html (math + emote definitions only; no DOM).
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/pose_preview.html', 'utf8');
const m = html.match(/<script>([\s\S]*)<\/script>/);
let src = m[1];
src = src.slice(0, src.indexOf('const VIEWS='));
const api = new Function(src + '; return {EM, solve, add, sub, mul, norm, len, dot, D2R};')();
const { EM, solve, add, sub, mul, norm, len, dot, D2R } = api;
const r3 = x => +x.toFixed(3);
const frames = (E, dt = 1 / 30) => { const a = []; for (let t = 0; t <= E.dur + 1e-9; t += dt) a.push([t, solve(E.pose(t))]); return a; };
const out = {};

// SPIKE
{
  const F = frames(EM.spike); let prevW = null, maxV = 0, maxFree = -9, minTip = 9, tipAt = 0;
  let wTop = [-9, 0], wLow = [9, 0];
  F.forEach(([t, S]) => {
    const d = norm(S.rk.dir), tip = add(S.rk.butt, mul(d, 0.69));
    if (t > 0.6 && t < 1.2 && tip[1] < minTip) { minTip = tip[1]; tipAt = t; }
    if (t > 0.5 && t < 1.2) { if (S.aR.W[1] > wTop[0]) wTop = [S.aR.W[1], t]; if (t > 0.9 && S.aR.W[1] < wLow[0]) wLow = [S.aR.W[1], t]; }
    maxFree = Math.max(maxFree, S.aL.W[1] - S.shL[1]);
  });
  let pw = null, fv = 0;
  F.forEach(([t, S]) => { const rel = sub(S.aL.W, S.shL); if (pw) fv = Math.max(fv, len(sub(rel, pw)) * 30); pw = rel; });
  const at = t => { const S = solve(EM.spike.pose(t)); const d = norm(S.rk.dir); const tip = add(S.rk.butt, mul(d, 0.69)); return { t, tipY: r3(tip[1]), trunkDeg: r3(Math.acos(norm(sub(S.neck, S.pel))[1]) / D2R), kneeFlexR: r3(180 - Math.acos(dot(norm(sub(S.lR.H, S.lR.K)), norm(sub(S.lR.A, S.lR.K)))) / D2R) }; };
  out.spike = { impact1: at(1.08), impact2: at(1.72), cock: at(0.75), wristTop_t: r3(wTop[1]), wristLow_t: r3(wLow[1]), topToImpact_s: r3(wLow[1] - wTop[1]), freeWristMaxAboveShoulder_m: r3(maxFree), freeWristMaxSpeedRelToShoulder_mps: r3(fv) };
}
// SCUBA
{
  const E = EM.scuba, F = frames(E).filter(([t]) => t >= 0.6 && t <= 3.3);
  let nose = 0, xs = [], kn = [], feet = [];
  F.forEach(([t, S]) => { nose = Math.max(nose, len(sub(S.aR.tip, S.nose))); xs.push([t, S.aL.W[0]]); kn.push([t, S.lL.K[0] - S.lR.K[0]]); feet.push(len(sub(S.lL.A, [0.36, 0.085, 0])) + len(sub(S.lR.A, [-0.36, 0.085, 0]))); });
  const rng = a => [Math.min(...a), Math.max(...a)];
  const xr = rng(xs.map(v => v[1])), kr = rng(kn.map(v => v[1]));
  // period: positive-going zero crossings of (x - mean)
  const mean = (xr[0] + xr[1]) / 2, cr = []; for (let i = 1; i < xs.length; i++) if (xs[i - 1][1] < mean && xs[i][1] >= mean) cr.push(xs[i][0]);
  const per = cr.length > 1 ? (cr[cr.length - 1] - cr[0]) / (cr.length - 1) : NaN;
  out.scuba = { nosePinchMaxDist_m: r3(nose), freeWristLateralP2P_m: r3(xr[1] - xr[0]), period_s: r3(per), kneeSpreadP2P_m: r3(kr[1] - kr[0]), cycles: cr.length };
  const f0 = solve(E.pose(1.0)); const cw = sub(f0.aL.W, f0.neck);
  out.scuba.freeWristFromNeckVec_m = cw.map(r3);
}
// THRUST
{
  const E = EM.thrust, F = frames(E);
  const hits = [0.60, 1.15, 1.70], res = [];
  hits.forEach(h => {
    const win = F.filter(([t]) => t > h - 0.1 && t < h + 0.25);
    let zmax = [-9, 0], dmin = [9, 0], zbackMin = [9, 0];
    win.forEach(([t, S]) => { if (S.pel[2] > zmax[0]) zmax = [S.pel[2], t]; const d = Math.min(len(sub(S.aL.W, S.pel)), len(sub(S.aR.W, S.pel))); const dl = Math.max(len(sub(S.aL.W, S.pel)), len(sub(S.aR.W, S.pel))); const dm = dl; if (dm < dmin[0]) dmin = [dm, t]; });
    const back = F.filter(([t]) => t > h - 0.45 && t < h - 0.12).reduce((a, [t, S]) => Math.min(a, S.pel[2]), 9);
    res.push({ hit: h, pelZfront: r3(zmax[0]), tZfront: r3(zmax[1]), pelZback: r3(back), travel_m: r3(zmax[0] - back), wristsAtPelvisFrameDiff_frames: r3((dmin[1] - zmax[1]) * 30), maxWristPelvisDistAtHit_m: r3(dmin[0]) });
  });
  const between = F.filter(([t]) => t > 0.93 && t < 0.99).map(([t, S]) => Math.min(len(sub(S.aL.W, S.pel)), len(sub(S.aR.W, S.pel))));
  const kneeFlex = t => { const S = solve(E.pose(t)); const a = sub(S.lL.H, S.lL.K), b = sub(S.lL.A, S.lL.K); return r3(180 - Math.acos(dot(norm(a), norm(b))) / D2R); };
  out.thrust = { hits: res, minWristPelvisDistBetweenHits_m: r3(Math.min(...between)), leftKneeFlexion_deg: { hit1: kneeFlex(0.60), back: kneeFlex(0.95), hit3: kneeFlex(1.70) } };
}
console.log(JSON.stringify(out, null, 1));

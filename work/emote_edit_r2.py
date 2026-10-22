from pathlib import Path
p=Path('work/emote-overhaul/scripts/emo_clips2.py');s=p.read_text()
a=s.index('class Thrust2(');b=s.index("REGISTRY['Emote_Thrust']",a);part=s[a:b]
start=part.index('    CROSS_SHAFT =');end=part.index('    L_ST =',start)
part=part[:start]+part[end:]
part=part.replace('Pelvic-thrust taunt with a crossed-forearm chop.', 'Pelvic-thrust taunt with the classic forward-to-hip arm pull.').replace('forearms land on the pelvis','fists land beside the hips').replace('fists re-cock at the shoulders','arms extend forward').replace('settle (hips back, fists up)','settle (hips back, arms forward)')
part=part.replace("(('cock', 0.45, 'c', [-1.0, 0.1, 0.0]), ('cross', 0.6, 'p', [0.2, 0.95, 0.0])", "(('forward', 0.45, 'w', [-1.0, 0.1, 0.0]), ('back', 0.6, 'w', [-1.0, 0.1, 0.0])")
part=part.replace("if frame == 'c':\n                Rm = info['R_chest']\n            else:","if frame == 'w':\n                Rm = np.eye(3)\n            else:")
start=part.index('        # ---- weights: READY | cocked | crossed | strut');end=part.index('        return P',start)
part=part[:start]+'''        # ---- same th driver as the hips: READY | arms forward | yank to hips | unchanged strut
        w_rd, w_fw, w_bk, w_st = 1 - e, e * (1 - strut) * (1 - th), e * (1 - strut) * th, e * strut
        Rp = self.pelvis_R(info)
        hips = self.A(info['Pos'][self.H.rig.idx['Hips']])
        # Forward fists stay at the shoulder line; the back fists sit beside the belt.
        # World authoring targets avoid a chest-pitch rotation lifting the fists above the shoulders.
        l_rd = self.chest_to_auth(info, self.left_ready['w'])
        l_fw = self.shoulder(info, 'L') + np.array([0.0, 0.545, -0.045]) * k
        l_bk = hips + np.array([-0.28, 0.015, 0.09]) * k
        l_st = self.pelvis_to_auth(info, np.array(self.L_ST) * k)
        P['l_frame'] = 'w'
        P['l_wrist'] = w_rd * l_rd + w_fw * l_fw + w_bk * l_bk + w_st * l_st
        fd_rd = self.chest_dir_to_auth(info, self.left_ready['fd'])
        pm_rd = self.chest_dir_to_auth(info, self.left_ready['pm'])
        fd_fw, pm_fw = np.array([0.0, 1.0, 0.0]), np.array([1.0, 0.0, 0.0])
        fd_bk, pm_bk = np.array([0.0, 0.9, -0.3]), np.array([1.0, 0.0, 0.0])
        fd_st = w2a(Rp @ a2w(unit(np.array(self.FD_ST))))
        pm_st = w2a(Rp @ a2w(np.array([0.95, -0.1, 0.1])))
        P['l_fdir'] = unit(w_rd * fd_rd + w_fw * fd_fw + w_bk * fd_bk + w_st * fd_st)
        P['l_palm'] = unit(w_rd * pm_rd + w_fw * pm_fw + w_bk * pm_bk + w_st * pm_st)
        pl_rd = self.chest_dir_to_auth(info, self.left_ready['pl'])
        pl_st = self.chest_dir_to_auth(info, np.array([-0.8, -0.5, -0.3]))
        P['l_pole'] = unit(w_rd * pl_rd + w_fw * np.array([-0.25, -0.1, -1.0]) + w_bk * np.array([-0.35, -1.0, 0.05]) + w_st * pl_st)
        P['l_fing'] = lerp(self.R['l_fing'], self.fist_L, e * (1 - strut * 0.6))
        P['l_wlim'] = (math.radians(85.0), math.radians(178.0))
        # Right hand follows the same wrist path, racket rigid on its existing socket.
        g0, s0, f0 = self.grip0
        r_rd, sh_rd, fa_rd = self.chest_to_auth(info, g0), self.chest_dir_to_auth(info, s0), self.chest_dir_to_auth(info, f0)
        wr_rd = self.A(self.info_ready['R_wrist'])
        wr_rd_c = w2a(self.info_ready['R_chest'].T @ (self.info_ready['R_wrist'] - self.info_ready['chest_center']))
        wr_rd = self.chest_to_auth(info, wr_rd_c)
        wr_fw = self.shoulder(info, 'R') + np.array([0.0, 0.545, -0.045]) * k
        wr_bk = hips + np.array([0.28, 0.015, 0.09]) * k
        sh_fw, sh_bk = unit(np.array([0.0, 0.28, 0.96])), unit(np.array([0.0, -0.30, 0.95]))
        fa_fw = self.faces['forward'] if self.faces else np.array([-1.0, 0.0, 0.0])
        fa_bk = self.faces['back'] if self.faces else np.array([-1.0, 0.0, 0.0])
        r_st = self.pelvis_to_auth(info, np.array(self.R_ST) * k)
        sh_st = w2a(Rp @ a2w(unit(np.array(self.SH_ST))))
        fa_st = w2a(Rp @ a2w(self.faces['strut'])) if self.faces else w2a(Rp @ a2w(np.array([-1.0, 0.1, 0.0])))
        sh = unit(w_rd * sh_rd + w_fw * sh_fw + w_bk * sh_bk + w_st * sh_st)
        fa = w_rd * fa_rd + w_fw * fa_fw + w_bk * fa_bk + w_st * fa_st
        fa = unit(fa - np.dot(fa, sh) * sh)
        Qhand = A2W_ @ PS.frame_from_axes(sh, fa) @ self.H.S.R_rh.T
        # Translate the wrist targets to grip targets for the racket-first solve.
        wrist_mix = w_rd * wr_rd + w_fw * wr_fw + w_bk * wr_bk
        grip_mix = wrist_mix + (w_rd + w_fw + w_bk) * w2a(Qhand @ self.H.S.t_rh)
        P['r_frame'] = 'w'
        P['r_rk_pos'] = grip_mix + w_st * r_st
        P['r_rk_shaft'], P['r_rk_face'] = sh, fa
        pr_rd = self.chest_dir_to_auth(info, self.R['r_pole'])
        P['r_pole'] = unit(w_rd * pr_rd + w_fw * np.array([0.25, -0.1, -1.0]) + w_bk * np.array([0.35, -1.0, 0.05]) + w_st * self.chest_dir_to_auth(info, np.array([0.8, -0.4, -0.3])))
        P['r_wlim'] = (math.radians(85.0), math.radians(178.0))
        P['r_fing'] = lerp(self.grip_fing, self.grip_tight, e * th)
''' + part[end:]
s=s[:a]+part+s[b:]
a=s.index('class Scuba2(');part=s[a:]
old='''        dr = (-0.10 + 0.14 * math.sin(ph) * env) * k
        df = (0.40 - 0.02 * math.cos(ph) * env) * k
        du = (-0.13 + 0.03 * math.cos(ph + 0.6) * env) * k'''
new='''        dr = (-0.02 + 0.14 * math.sin(ph) * env) * k
        df = (0.545 - 0.005 * math.cos(ph) * env) * k
        du = (-0.06 + 0.01 * math.cos(ph + 0.6) * env) * k'''
assert old in part;part=part.replace(old,new)
old='''        psi = math.radians(-35.0) * math.cos(ph) * env
        fd_sw = unit(np.array([math.sin(psi), math.cos(psi), -0.10]))
        pm_sw = np.array([0.05, 0.10, -1.0])
        pl_sw = np.array([0.45, -0.55, -0.55])'''
new='''        psi = math.radians(-25.04) * math.cos(ph) * env
        Rp = self.pelvis_R(info)
        fd_sw_p = unit(np.array([math.sin(psi), math.cos(psi), -0.07]))
        # Palm faces left, orthogonal to the sweeping fingers; +X remains the upward thumb edge.
        pm_sw_p = unit(np.array([-1.0, 0.0, 0.0]) - np.dot([-1.0, 0.0, 0.0], fd_sw_p) * fd_sw_p)
        fd_sw = w2a(Rp @ a2w(fd_sw_p))
        pm_sw = w2a(Rp @ a2w(pm_sw_p))
        pl_sw = np.array([0.20, -0.15, -1.0])'''
assert old in part;part=part.replace(old,new);s=s[:a]+part;p.write_text(s)
print('Edited only Thrust2 and Scuba2')

from pathlib import Path
p=Path(__file__).with_name('serve_dj.py')
s=p.read_text()
a=s.index('    # ------------------------------------------------------------------------------------------------ feet')
b=s.index('    # ------------------------------------------------------------------------------------------------ the tossing',a)
new='''    # Grounded toss, trophy squash, one drive jump, front-foot landing.
    xr, xl = 0.26, -0.18
    pR, pL = (xr, f0 - 0.08), (xl, f0 + 0.14)
    FT('rf', [(T_S,pR,0,75,0),(T_R,pR,0,75,0),(T_T,pR,0,75,0),(T_D,pR,0,75,0),
              (F(46),pR,0,75,6),(F(47),pR,0,75,18),
              (F(48),pR,0.020,74,42),(F(49),(xr-.02,f0-.10),.11,70,58),
              (F(50),(xr-.04,f0-.20),.25,62,66),(T_C,(xr-.07,f0-.32),.42,55,70),
              (F(53),(.12,f0-.40),.58,40,70),(F(56),(.10,f0-.42),.62,22,70),
              (F(60),(.10,f0-.40),.58,20,66),(F(62),(.11,f0+.02),.34,10,50),
              (F(64),(.13,f0+.30),.08,5,24),(T_STEP,(.15,f0+.36),0,5,0),
              (T_END,(.15,f0+.36),0,5,0)], 'GROUND/DRIVE/KICK/LAND')
    FT('lf', [(T_S,pL,0,38,0),(T_R,pL,0,38,0),(T_T,pL,0,38,0),(T_D,pL,0,38,0),
              (F(46),pL,0,38,6),(F(47),pL,0,38,20),
              (F(48),pL,.025,36,45),(F(49),(xl+.005,f0+.17),.09,31,54),
              (F(50),(xl+.01,f0+.20),.16,26,60),(T_C,(xl+.02,f0+.25),.205,20,62),
              (F(53),(xl+.03,f0+.31),.24,10,56),(F(55),(xl+.04,f0+.37),.20,2,48),
              (F(58),(xl+.04,f0+.39),.10,-2,40),(F(60),(xl+.04,f0+.39),.02,-2,30),
              (F(61),(xl+.04,f0+.39),0,-2,24),(F(63),(xl+.04,f0+.39),0,-2,4),
              (F(65),(xl+.04,f0+.39),0,-2,0),(T_END,(xl+.04,f0+.39),0,-2,0)], 'GROUND/DRIVE/FRONT_TOUCH')

    def body(t, pel, pyaw, ppitch, proll, cyaw, cpitch, croll, src, ease=None):
        keys.append(K(t, src, ease=ease, pel=[pel[1],pel[0],pel[2]],
                      pel_rot=[pyaw,ppitch,proll],chest_rot=[cyaw-pyaw,cpitch,croll]))
    body(T_S,(0,0,0),30,9,0,42,8,0,'STANCE')
    body(F(10),(-.025,0,-.012),31,9,0,44,5,0,'ROCK_BACK')
    body(F(14),(-.01,0,-.006),34,4,0,50,-6,0,'TOSS')
    body(F(17),(0,0,0),35,2,0,55,-10,0,'TOSS')
    body(T_R,(.01,0,0),36,2,0,58,-8,0,'RELEASE')
    body(F(27),(.02,0,-.035),40,3,1,66,-10,2,'LOAD')
    body(F(33),(.025,0,-.075),48,4,2,78,-12,4,'LOAD')
    body(F(38),(.025,0,-.115),56,4,4,88,-14,6,'SQUASH',ease=1)
    body(T_T,(.025,0,-.115),58,4,4,92,-14,6,'TROPHY',ease=1)
    body(F(42),(.02,0,-.108),62,4,5,100,-14,7,'COCK')
    body(T_D,(.01,0,-.095),70,4,6,108,-14,8,'COCK')
    body(F(47),(.00,0,-.065),52,6,4,90,-14,8,'DRIVE')
    body(F(49),(.04,0,.025),28,6,0,58,-12,-2,'EXPLODE')
    body(F(50),(.09,0,.09),12,5,-2,26,-10,-8,'STRETCH')
    body(T_C,(.15,0,.15),4,2,-4,-6,-8,-14,'CONTACT')
    body(F(53),(.19,0,.19),-8,4,-4,-24,-2,-10,'APEX',ease=1)
    body(F(55),(.22,0,.18),-22,14,0,-44,12,-4,'HANG')
    body(F(58),(.24,0,.10),-26,24,0,-50,20,0,'DESCEND')
    body(F(61),(.26,0,-.035),-24,24,0,-48,20,0,'LEFT_TOUCH')
    body(F(64),(.28,0,-.09),-14,22,0,-30,16,0,'LAND_SQUASH')
    body(F(68),(.29,0,-.035),-6,13,0,-12,10,0,'REBOUND')
    body(F(71),(.28,0,-.025),0,9,0,0,8,0,'SETTLE')
    body(T_END,(.28,0,0),0,9,0,0,8,0,'LOCK')

'''
s=s[:a]+new+s[b:]
s=s.replace('T_LAND = F(57)','T_LAND = F(61)').replace("'the pre-toss fold and hop are requested by Adnan (2026-10-03), not read from the video'","'grounded toss and one cartoon drive jump requested by Adnan (2026-10-05)'")
p.write_text(s)

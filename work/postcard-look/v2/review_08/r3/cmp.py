import pickle, numpy as np
a=pickle.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/review_08/r3/g_base.pkl','rb'))
b=pickle.load(open('/Users/adnanyonathan/Documents/Codex/2026-09-20/wh/outputs/iphone-golf-simulator/work/postcard-look/v2/review_08/r3/g_stage.pkl','rb'))
print(sorted(a)==sorted(b))
for k in a:
    A,B=a[k],b[k]
    print(k,len(A['V']),len(B['V']),'maxdv',np.abs(A['V']-B['V']).max() if len(A['V'])==len(B['V']) else 'NA','faces equal',A['faces']==B['faces'],'nrm',np.abs(A['nrm']-B['nrm']).max() if len(A['nrm'])==len(B['nrm']) else 'NA')

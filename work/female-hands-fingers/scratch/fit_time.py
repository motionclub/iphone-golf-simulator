import time, json
import fit_f
t = time.time(); r = fit_f.evaluate({}); print('eval %.2fs' % (time.time() - t)); print(json.dumps({k: v for k, v in r.items() if k != 'per'}))
t = time.time(); r = fit_f.evaluate({'curl': 1.2, 'B_gain': 1.4}); print('eval %.2fs' % (time.time() - t)); print(json.dumps({k: v for k, v in r.items() if k != 'per'}))

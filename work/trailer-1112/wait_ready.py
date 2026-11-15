import os,time,sys
t0=time.time()
while time.time()-t0<540:
    if os.path.exists('stage/ready.txt'): print('READY', round(time.time()-t0)); sys.exit(0)
    lg='stage/unity.log'
    if os.path.exists(lg):
        s=open(lg,errors='ignore').read()
        if 'error CS' in s: print('\n'.join(sorted(set(l for l in s.splitlines() if 'error CS' in l)))[:3000]); sys.exit(1)
    time.sleep(2)
print('timeout'); sys.exit(2)

from pathlib import Path
import subprocess,re,json,collections,sys
W=Path(__file__).resolve().parents[1];D=W/'compile'/sys.argv[-1]
metal=Path('/private/var/run/com.apple.security.cryptexd/mnt/com.apple.MobileAsset.MetalToolchain-v27.1.266.1.N2xUMW/Metal.xctoolchain/usr/bin/metal');assert metal.exists()
results={}
for p in sorted(D.glob('*.bin')):
 data=p.read_bytes();start=data.find(b'#include')
 if start<0:continue
 src=data[start:].split(b'\0')[0];msl=p.with_suffix('.msl');msl.write_bytes(src);out=D/(p.stem.split('_<')[0]+'.ll')
 q=subprocess.run([str(metal),'-fmodules-cache-path='+str(D/'module-cache'),'-S','-emit-llvm','-x','metal','-std=ios-metal2.4','-mios-version-min=15.0',str(msl),'-o',str(out)],capture_output=True,text=True)
 if q.returncode:results[out.stem]={'error':q.stderr};continue
 s=out.read_text();ops=collections.Counter(re.findall(r' = (fadd|fsub|fmul|fdiv|fneg|fcmp)\b',s));intr=collections.Counter(re.findall(r'call[^\n]*@air\.([\w]+)',s));results[out.stem]={'floating_IR_instructions':dict(ops),'floating_IR_count':sum(ops.values()),'AIR_intrinsics':dict(intr),'sample_calls':sum(v for k,v in intr.items() if k.startswith('sample'))}
report={'basis':'Unity Metal variants compiled to optimized iOS AIR; vector IR inventory, not GPU hardware ALU counts or Xcode Compiler Statistics','compiler':subprocess.check_output([str(metal),'--version'],text=True),'variants':results};(D/'air_instruction_inventory.json').write_text(json.dumps(report,indent=2))
for k,v in results.items():print(k,v.get('floating_IR_count'),v.get('sample_calls'),v.get('error','')[:100])

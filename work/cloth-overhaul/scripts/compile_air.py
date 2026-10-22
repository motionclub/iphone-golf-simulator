from pathlib import Path
import subprocess,re,json,collections
W=Path(__file__).resolve().parents[1];D=W/'compile_final';metal=Path('/private/var/run/com.apple.security.cryptexd/mnt/com.apple.MobileAsset.MetalToolchain-v27.1.266.1.N2xUMW/Metal.xctoolchain/usr/bin/metal');assert metal.exists();results={}
for p in sorted(D.glob('*.bin')):
 data=p.read_bytes();start=data.find(b'#include');assert start>=0;src=data[start:].split(b'\0')[0];msl=p.with_suffix('.msl');msl.write_bytes(src);out=D/(p.stem.split('_<')[0]+'.ll')
 subprocess.run([str(metal),'-S','-emit-llvm','-x','metal','-std=ios-metal2.4','-mios-version-min=15.0',str(msl),'-o',str(out)],check=True)
 s=out.read_text();ops=collections.Counter(re.findall(r' = (fadd|fsub|fmul|fdiv|fneg|fcmp)\b',s));intr=collections.Counter(re.findall(r'call[^\n]*@air\.([\w]+)',s));results[out.stem]={'floating_IR_instructions':dict(ops),'floating_IR_count':sum(ops.values()),'AIR_intrinsics':dict(intr),'sample_calls':sum(v for k,v in intr.items() if k.startswith('sample'))}
report={'basis':'Unity Metal CompileVariant output compiled to optimized iOS AIR; vector IR instruction inventory, not GPU hardware ALU counts or Xcode Compiler Statistics','compiler':subprocess.check_output([str(metal),'--version'],text=True),'variants':results};(D/'air_instruction_inventory.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

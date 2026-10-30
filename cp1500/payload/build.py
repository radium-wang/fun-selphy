"""Build a position-independent ARMv5 leaf payload; extract ELF .text without objcopy."""
from pathlib import Path
import struct, subprocess, sys, hashlib, json
p = Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv)>1 else 'return_ok'
subprocess.run(['clang','--target=arm-none-eabi','-march=armv5te','-marm','-c',str(p/(name+'.S')),'-o',str(p/(name+'.o'))],check=True)
b=(p/(name+'.o')).read_bytes()
assert b[:7]==b'\x7fELF\x01\x01\x01'
assert struct.unpack_from('<H',b,18)[0]==40
shoff=struct.unpack_from('<I',b,32)[0]
entsize,count,names=struct.unpack_from('<HHH',b,46)
sections=[struct.unpack_from('<10I',b,shoff+i*entsize) for i in range(count)]
ns=sections[names]; strings=b[ns[4]:ns[4]+ns[5]]
section_names=[strings[s[0]:].split(b'\0')[0].decode() for s in sections]
idx=section_names.index('.text');s=sections[idx]
assert not any(x[1] in (4,9) and x[7]==idx and x[5] for x in sections),'text has relocations'
code=b[s[4]:s[4]+s[5]]
assert len(code)>0 and len(code)%4==0
if name=='return_ok': assert len(code)==32
(p/(name+'.bin')).write_bytes(code)
sys.path.insert(0,str(p.parent/'tools-python'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN
lines=[f'{i.address:04x}: {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in Cs(CS_ARCH_ARM,CS_MODE_ARM|CS_MODE_LITTLE_ENDIAN).disasm(code,0)]
(p/(name+'.disasm.txt')).write_text('\n'.join(lines)+'\n')
manifest={'architecture':'ARMv5TE little endian ARM state','entry_offset':0,'size':len(code),'sha256':hashlib.sha256(code).hexdigest(),'relocations':0,'stack_bytes':{'return_ok':0,'allocator_probe':24,'lcd_probe':32}.get(name),'absolute_addresses':name!='return_ok','expected_reply_hex':'4f4b' if name=='return_ok' else None,'target_execution_verified':False}
(p/(name+'.manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2));print('\n'.join(lines))

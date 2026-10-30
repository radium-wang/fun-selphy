from pathlib import Path
import sys,struct,re
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools-python'))
from capstone import *
from capstone.arm import *
p=Path(__file__).resolve().parent
b=(p/'unpacked/1070/main.bin').read_bytes();base=0
md=Cs(CS_ARCH_ARM,CS_MODE_ARM|CS_MODE_LITTLE_ENDIAN);md.detail=True
strings={base+m.start():m.group().decode('ascii') for m in re.finditer(rb'[ -~]{5,}',b)}
lo=int(sys.argv[1],0) if len(sys.argv)>1 else 0x502000
hi=int(sys.argv[2],0) if len(sys.argv)>2 else 0x502700
for o in range(lo-base,hi-base,4):
 i=next(md.disasm(b[o:o+4],base+o),None)
 if not i:continue
 note='';t=None
 if i.id in (ARM_INS_ADD,ARM_INS_SUB) and len(i.operands)==3 and i.operands[1].type==ARM_OP_REG and i.operands[1].reg==ARM_REG_PC and i.operands[2].type==ARM_OP_IMM:
  t=i.address+8+(i.operands[2].imm if i.id==ARM_INS_ADD else -i.operands[2].imm)
 if i.id==ARM_INS_LDR and len(i.operands)==2 and i.operands[1].type==ARM_OP_MEM and i.operands[1].mem.base==ARM_REG_PC:
  off=i.address+8+i.operands[1].mem.disp-base
  if 0<=off<=len(b)-4:t=struct.unpack_from('<I',b,off)[0];note=f' ; literal={t:#x}'
 if t in strings:note+=' '+repr(strings[t])
 print(f'{i.address:08x}: {i.bytes.hex()} {i.mnemonic:9} {i.op_str}{note}')

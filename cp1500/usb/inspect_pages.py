from program_service import ProgramService
import struct
with ProgramService() as p:
 b=p.s.read(0x77aca4,16);print('pool',struct.unpack('<IHHII',b),flush=True)
 scratch=p.alloc(64)
 try:
  prev=0;pages=[]
  for i in range(8):
   st=p.call(0x324c0c,scratch,prev,0,0);assert st==0,st
   idx=int.from_bytes(p.s.read(scratch,2),'little');addr=p.call(0x324b84,idx);pages.append(idx);prev=idx
   print('page',idx,hex(addr),flush=True)
 finally:
  for idx in pages:assert p.call(0x324eac,0,idx)==0
  p.free(scratch)

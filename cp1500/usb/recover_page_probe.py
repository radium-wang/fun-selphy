from program_service import ProgramService
import struct
with ProgramService() as p:
 b=p.s.read(0x2b391ec,16);print('saved page output slots',b.hex(),flush=True)
 ids=[struct.unpack_from('<H',b,i*4)[0] for i in range(4)]
 assert len(set(ids))==4 and all(3<=i<=519 for i in ids),ids
 for i in ids:print('release',i,p.call(0x324eac,0,i),flush=True)
 print('pool',p.s.read(0x77aca4,16).hex(),flush=True)

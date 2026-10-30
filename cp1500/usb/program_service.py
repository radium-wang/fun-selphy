"""Temporary named function-call extension with state restoration."""
from test_return_ok import TestSession,BASE,META,ROOT
from bulk_transfer_helpers import BulkTransfer
import struct
class ProgramService:
 def __init__(self):self.s=TestSession();self.bulk=BulkTransfer(self.s,batch_size=1);self.published=False
 def __enter__(self):
  self.s.open();self.meta=self.s.read(META,12);cap,self.used,req=struct.unpack('<III',self.meta);assert self.used==req
  self.table=self.s.read(BASE,cap);self.code=(ROOT.parent/'payload'/'call_service.bin').read_bytes()
  self.low=(BASE+cap-len(self.code))&~31;self.entry=self.low|0x40000000
  assert self.used+36<self.low-BASE
  assert b'cp_call\0' not in self.table[:self.used]
  self.original=self.s.read(self.entry,len(self.code))
  self.s.write(self.entry,self.code);assert self.s.read(self.entry,len(self.code))==self.code
  self.name=b'cp_call\0';record=struct.pack('<II',28,6)+self.name.ljust(12,b'\0')+struct.pack('<II',0,self.entry)
  self.s.write(BASE+self.used,record+self.table[self.used:self.used+8]);self.s.word(META+8,self.used+28);self.s.word(META+4,self.used+28);self.published=True
  return self
 def call(self,address,*args):
  assert len(args)<=11
  body=self.name.ljust(16,b'\0')+struct.pack('<I',address)+struct.pack('<11I',*(list(args)+[0]*(11-len(args))))
  cmd=b'\x1bDC\0'+struct.pack('<H',len(body))+b'\0\0'+body
  sub=self.s.exchange([cmd])[0];assert sub[6:10]==b'\x1bDC\0' and len(sub)==18,sub.hex()
  return struct.unpack_from('<I',sub,14)[0]
 def calls(self,items):
  commands=[]
  for address,args in items:
   body=self.name.ljust(16,b'\0')+struct.pack('<I',address)+struct.pack('<11I',*(list(args)+[0]*(11-len(args))))
   commands.append(b'\x1bDC\0'+struct.pack('<H',len(body))+b'\0\0'+body)
  results=[]
  for start in range(0,len(commands),1):
   for sub in self.s.exchange(commands[start:start+1]):
    assert sub[6:10]==b'\x1bDC\0' and len(sub)==18,sub.hex()
    results.append(struct.unpack_from('<I',sub,14)[0])
  return results
 def alloc(self,n):
  p=self.call(0x32d524,n);assert p,('malloc failed',n);return p
 def free(self,p):assert self.call(0x31db84,0x70bae0,p)==0
 def __exit__(self,*exc):
  try:
   if self.published:
    self.s.word(META+4,self.used);self.s.word(META+8,self.used)
    self.s.write(BASE+self.used,self.table[self.used:self.used+36]);self.s.write(self.entry,self.original)
    assert self.s.read(META,12)==self.meta
    assert self.s.read(self.entry,len(self.code))==self.original
    print('temporary call service restored',flush=True)
  finally:self.s.close()
if __name__=='__main__':
 with ProgramService() as p:
  original=p.alloc(4096);print('allocated',hex(original),flush=True)
  try:
   data=bytes(range(256))*4
   p.bulk.write(original,data,verify=True)
   print('bulk1024-byte roundtrip passed',flush=True)
   import time
   t=p.call(0x2c1720);start=time.monotonic();time.sleep(1);t2=p.call(0x2c1720)
   print('tick_hz',round((t2-t)/(time.monotonic()-start)),flush=True)
  finally:p.free(original)

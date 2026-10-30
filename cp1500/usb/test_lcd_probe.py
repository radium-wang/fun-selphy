"""Reversible RAM-only CP1500 returning-payload test; no flash operations."""
from read_runtime_state import Session,ROOT
from pathlib import Path
import struct,time,json
BASE=0x7d7e6c;META=0x70c71c;NAME=b'cp_lcd\0'
class TestSession(Session):
 def exchange(self,commands):
  self.l.packet(b''.join(struct.pack('<BBHBB',0,1,6+len(c),1,0)+c for c in commands),len(commands))
  responses=[]
  while len(responses)<len(commands):
   body=self.poll();o=0
   while o<len(body):
    n=int.from_bytes(body[o+2:o+4],'little');assert n>=6 and o+n<=len(body)
    sub=body[o:o+n];o+=n
    if sub[1]==1:responses.append(sub)
   if len(responses)<len(commands):time.sleep(.05);self.l.packet()
  return responses
 def write(self,address,data):
  for o in range(0,len(data),64):
   self.exchange([b'\x1bDW'+struct.pack('<I',address+o+i)+bytes([v]) for i,v in enumerate(data[o:o+64])])
 def word(self,address,v):self.write(address,struct.pack('<I',v))
s=TestSession();result={'target':'CP1500','flash_operations':False};backup={};restored=False
try:
 s.open();metadata=s.read(META,12);capacity,used,required=struct.unpack('<III',metadata)
 assert capacity==5000 and used==required and 0<used<capacity
 table=s.read(BASE,capacity)
 # Keep code in a separate32-byte cache line at the end of the reserved table.
 code=(ROOT.parent/'payload'/'lcd_probe.bin').read_bytes();code_size=len(code)
 code_low=(BASE+capacity-code_size)&~31;code_high=code_low|0x40000000
 assert used+28+8 < code_low-BASE
 assert NAME not in table[:used]
 assert s.read(code_high,code_size)==table[code_low-BASE:code_low-BASE+code_size]
 record=struct.pack('<II',28,6)+NAME.ljust(12,b'\0')+struct.pack('<II',0,code_high)
 backup={'metadata_address':hex(META),'metadata_hex':metadata.hex(),'slot_address':hex(BASE+used),'slot_hex':table[used:used+36].hex(),'code_address':hex(code_high),'code_hex':table[code_low-BASE:code_low-BASE+code_size].hex(),'used':used}
 (ROOT/'lcd-probe-backup.json').write_text(json.dumps(backup,indent=2)+'\n')
 result.update(capacity=capacity,original_used=used,entry_address=hex(code_high),symbol_address=hex(BASE+used))
 print('BACKUP_SAVED',result,flush=True)
 try:
  # High alias is noncached in the inspected MMU mapping; use it for instruction
  # storage/fetch. No pre-existing low-alias dirty writes to this separate line.
  s.write(code_high,code);assert s.read(code_high,code_size)==code
  print('CODE_WRITE_READBACK_OK',flush=True)
  s.write(BASE+used,record+table[used:used+8])
  assert s.read(BASE+used,36)==record+table[used:used+8]
  s.word(META+8,used+28);s.word(META+4,used+28)
  assert s.read(META+4,8)==struct.pack('<II',used+28,used+28)
  print('SYMBOL_PUBLISHED',flush=True)
  command=b'\x1bDC\0'+struct.pack('<H',len(NAME))+b'\0\0'+NAME
  reply=s.exchange([command]);result['reply_hex']=[x.hex() for x in reply]
  print('CALL_REPLY',result['reply_hex'],flush=True)
  assert len(reply)==1 and reply[0][6:9]==b'\x1bDC',reply
  assert reply[0][9]==0 and reply[0][14:18]==b'LCD1',reply
  pointer,display_status,free_status,buttons=struct.unpack('<IIII',reply[0][18:34])
  result.update(pointer=hex(pointer),display_status=display_status,free_status=free_status,buttons=hex(buttons))
  assert pointer!=0 and display_status==0 and free_status==0,result
  result['returned_ok']=True
 finally:
  # Unpublish before restoring the overwritten slot and code.
  s.word(META+4,used);s.word(META+8,required)
  s.write(BASE+used,table[used:used+36]);s.write(code_high,table[code_low-BASE:code_low-BASE+code_size])
  assert s.read(META,12)==metadata
  assert s.read(BASE+used,36)==table[used:used+36]
  assert s.read(code_high,code_size)==table[code_low-BASE:code_low-BASE+code_size]
  restored=True;result['restored']=True;print('RESTORED_AND_VERIFIED',flush=True)
except Exception as e:
 result['error']=repr(e);print('ERROR',repr(e),flush=True);raise
finally:
 result.setdefault('restored',restored)
 (ROOT/'lcd-probe-result.json').write_text(json.dumps(result,indent=2)+'\n')
 s.close()

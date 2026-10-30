"""Ask firmware for its normal reboot; all temporary state is RAM-only."""
from test_return_ok import TestSession,BASE,META,ROOT
import struct,json,time
s=TestSession();published=False;sent=False
try:
 s.open();meta=s.read(META,12);cap,used,req=struct.unpack('<III',meta)
 assert cap==5000 and used==req
 table=s.read(BASE,cap)
 # ARM: mov r0,#1; ldr r3,[pc]; bx r3; .word normal-reboot runtime.
 code=struct.pack('<4I',0xe3a00001,0xe59f3000,0xe12fff13,0x336944)
 low=(BASE+cap-32)&~31;entry=low|0x40000000;name=b'cp_boot\0'
 assert used+36<low-BASE and name not in table[:used]
 backup={'meta_hex':meta.hex(),'slot_address':hex(BASE+used),'slot_hex':table[used:used+36].hex(),'code_address':hex(entry),'code_hex':table[low-BASE:low-BASE+16].hex()}
 (ROOT/'restore-normal-backup.json').write_text(json.dumps(backup,indent=2)+'\n')
 try:
  s.write(entry,code);assert s.read(entry,len(code))==code
  rec=struct.pack('<II',28,6)+name.ljust(12,b'\0')+struct.pack('<II',0,entry)
  s.write(BASE+used,rec+table[used:used+8]);s.word(META+8,used+28);s.word(META+4,used+28);published=True
  command=b'\x1bDC\0'+struct.pack('<H',len(name))+b'\0\0'+name
  body=struct.pack('<BBHBB',0,1,6+len(command),1,0)+command
  s.l.packet(body,1);sent=True
  print('NORMAL_REBOOT_REQUEST_SENT',flush=True)
  # No command reply is expected because the firmware reboot never returns.
  time.sleep(.3)
 except Exception:
  if not sent:
   s.word(META+4,used);s.word(META+8,req);s.write(BASE+used,table[used:used+36]);s.write(entry,table[low-BASE:low-BASE+16])
  raise
finally:s.close()

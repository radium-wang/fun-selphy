from dbgmon_link import Link
from pathlib import Path
import struct
import time
l=Link()
try:
 assert l.control(0x41,0,0x81,2)==0
 l.packet()
 print('RESET_REPLY',l.receive(),flush=True)
 l.packet(bytes.fromhex('00 00 0f 00 01 00 01 01 01 0e 04 0e 04 00 00'),1)
 for i in range(8):
  reply=l.receive();print('OPEN_REPLY',reply,flush=True)
  if reply and reply[1]:
   assert reply[1][6:10]==bytes.fromhex('81 00 01 01'),reply
   break
  if reply is None:break
  time.sleep(0.15)
  l.packet()
 else:raise RuntimeError('no successful channel open')
 payload=b''
 for address in range(0x900,0x910):
  command=b'\x1bDR'+struct.pack('<I',address)+b'\x00'
  payload+=struct.pack('<BBHBB',0,1,14,1,0)+command
 l.packet(payload,16)
 values=[]
 for poll in range(16):
  response=l.receive()
  if response is None:raise RuntimeError('read response timeout')
  h,body=response
  offset=0
  while offset<len(body):
   length=int.from_bytes(body[offset+2:offset+4],'little')
   assert length>=6 and offset+length<=len(body),(offset,length,body.hex())
   sub=body[offset:offset+length]
   if sub[1]==1 and len(sub)==14 and sub[6:9]==b'\x1bDR':values.append(sub[13])
   offset+=length
  if len(values)>=16:break
  time.sleep(0.15);l.packet()
 assert len(values)==16,values
 data=bytes(values)
 Path(__file__).with_name('ram-00000900.bin').write_bytes(data)
 print('RAM_0x900',data.hex(),flush=True)
 for version in ['1060','1070']:
  expected=(Path(__file__).resolve().parents[1]/'unpacked'/version/'main.bin').read_bytes()[0x980:0x990]
  print('MATCH',version,data==expected,'expected',expected.hex(),flush=True)
finally:l.close()

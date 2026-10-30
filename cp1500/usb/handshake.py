from dbgmon_link import Link
import time
l=Link()
try:
 assert l.control(0x41,0,0x81,2)==0
 l.packet()
 print('RESET_REPLY',l.receive(),flush=True)
 l.packet(bytes.fromhex('00 00 0f 00 01 00 01 01 01 0e 04 0e 04 00 00'),1)
 for i in range(8):
  reply=l.receive();print('OPEN_REPLY',reply,flush=True)
  if reply and reply[1]:break
  if reply is None:break
  time.sleep(0.15)
  l.packet()
finally:l.close()

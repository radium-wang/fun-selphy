from read_runtime_state import Session,ROOT
import json,struct,time
f=ROOT/'doom-runtime.json';j=json.loads(f.read_text());sy={k:int(v,16) for k,v in j['symbols'].items()};s=Session()
try:
 s.open();s.l.log=lambda op,rc,data=b'':s.l.events.append({'op':op,'result':rc,'hex':data.hex()})
 # W only changes the owned game's stop flag.
 for i,v in enumerate(struct.pack('<I',1)):
  cmd=b'\x1bDW'+struct.pack('<I',sy['cp_stop']+i)+bytes([v]);s.l.packet(struct.pack('<BBHBB',0,1,14,1,0)+cmd,1);s.poll()
 for i in range(30):
  st=int.from_bytes(s.read(int(j['tcb'],16)+0x30,4),'little');status=int.from_bytes(s.read(sy['cp_status'],4),'little')
  if st==1:break
  time.sleep(.05)
 print('thread_state',st,'game_status',hex(status),flush=True)
 assert st==1 and status==4
 j.update(game_stopped=True,thread_state=st,status=hex(status));f.write_text(json.dumps(j,indent=2)+'\n')
finally:s.close()

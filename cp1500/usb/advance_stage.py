from program_service import ProgramService,ROOT
import json,struct,time,sys
f=ROOT/'doom-runtime.json';j=json.loads(f.read_text());stage=int(sys.argv[1]);sy={k:int(v,16) for k,v in j['symbols'].items()};tcb=int(j['tcb'],16);stack=int(j['stack'],16)
with ProgramService() as p:
 state=struct.unpack('<I',p.s.read(tcb+0x30,4))[0];assert state==1,('prior task not completed',state)
 assert p.call(0x2c2fbc,tcb)==0
 p.s.word(sy['cp_stage_limit'],stage)
 p.bulk.write(tcb,b'\0'*0x220)
 name=stack+256*1024
 assert p.call(0x2c2d74,tcb,name,sy['cp_thread'],0,stack,256*1024,30,30,1,0,0x220)==0
 assert p.call(0x2c3138,tcb)==0
 for i in range(5):
  time.sleep(.1)
  status=struct.unpack('<I',p.s.read(sy['cp_status'],4))[0];state=struct.unpack('<I',p.s.read(tcb+0x30,4))[0]
  print('STAGE',stage,'STATUS',hex(status),'THREAD',state,flush=True)
  if state==1:break
 log=p.bulk.read(sy['cp_log'],4096);print('LOG',log.rstrip(b'\0').decode(errors='replace'),flush=True)
 j.update(stage=stage,status=hex(status),thread_state=state);f.write_text(json.dumps(j,indent=2)+'\n')
 (ROOT/f'doom-stage{stage}-log.bin').write_bytes(log)

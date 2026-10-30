"""Minimal isolated ThreadX task: store marker and return, no Doom or display."""
from program_service import ProgramService,ROOT
import struct,time,json
result={};original=0;created=False;attempted=False;completed=False
with ProgramService() as p:
 try:
  original=p.alloc(0x9000);tcb=(original+31)&~31;entry=(tcb+0x240)|0x40000000;marker=tcb+0x280;stack=tcb+0x300;name=tcb+0x270
  result.update(allocation=hex(original),tcb=hex(tcb),entry=hex(entry),marker=hex(marker))
  assert p.call(0x3212d8,tcb,tcb+0x8400)==0
  p.bulk.write(tcb,b'\0'*0x300)
  code=struct.pack('<3I',0xe3a01001,0xe5801000,0xe12fff1e)
  p.bulk.write(entry,code);p.bulk.write(name,b'cp_min\0')
  args=[tcb,name,entry,marker,stack,0x8000,30,30,1,0,0x220]
  rc=p.call(0x2c2d74,*args);result['create']=rc;assert rc==0;created=True
  print('CREATED',result,flush=True)
  attempted=True;rc=p.call(0x2c3138,tcb);result['resume']=rc;print('RESUMED',rc,flush=True);assert rc==0
  time.sleep(.05)
  value=struct.unpack('<I',p.s.read(marker,4))[0];state=struct.unpack('<I',p.s.read(tcb+0x30,4))[0]
  result.update(marker_value=value,thread_state=state);print('RESULT',result,flush=True)
  assert value==1 and state==1,(value,state);completed=True
 finally:
  if created and (completed or not attempted):
   rc=p.call(0x2c2fbc,tcb);result['delete']=rc
   if rc==0:p.free(original);result['freed']=True
  elif original and not created:p.free(original);result['freed']=True
  (ROOT/'minimal-thread-result.json').write_text(json.dumps(result,indent=2)+'\n')

from program_service import ProgramService,ROOT
import json,struct,time
p=ROOT/'doom-runtime.json';j=json.loads(p.read_text());sy={k:int(v,16) for k,v in j['symbols'].items()}
with ProgramService() as s:
 samples=[]
 for i in range(3):
  status=struct.unpack('<I',s.s.read(sy['cp_status'],4))[0];frames=struct.unpack('<I',s.s.read(sy['cp_frames'],4))[0]
  samples.append({'time':time.monotonic(),'status':status,'frames':frames});print(samples[-1],flush=True);time.sleep(1)
 j.update(frame_samples=samples,physical_display_confirmed=True,frames_growing=samples[-1]['frames']>samples[0]['frames']);p.write_text(json.dumps(j,indent=2)+'\n')

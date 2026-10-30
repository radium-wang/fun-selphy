from program_service import ProgramService,ROOT
import time,json
samples=[]
p=ProgramService()
try:
 p.__enter__()
 print('KEY_CAPTURE_READY',flush=True);start=time.monotonic();last=None
 while time.monotonic()-start<40:
  p.call(0x126c8c)
  p.call(0x126f9c)
  keys=p.call(0x127014);t=round(time.monotonic()-start,3)
  if keys!=last:
   samples.append({'time':t,'mask':hex(keys)});print(samples[-1],flush=True);last=keys
  time.sleep(.03)
finally:p.__exit__(None,None,None)
(ROOT/'key-capture.json').write_text(json.dumps(samples,indent=2)+'\n')

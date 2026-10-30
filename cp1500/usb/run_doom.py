"""Build/upload Doom in allocated RAM and start a dedicated firmware task."""
from program_service import ProgramService
from pathlib import Path
import struct,time,json,subprocess,os
STAGE=int(os.environ.get("CP_STAGE","1"))
IMAGE_PAGES=116
ROOT=Path(__file__).resolve().parents[1];PORT=ROOT/'doom'/'port';STATE=ROOT/'usb'/'doom-runtime.json'
state={'stage':STAGE};allocated=[];started=False
needed=116 if STAGE<=2 else 221
with ProgramService() as p:
 try:
  pool=p.s.read(0x77aca4,16);free_pages=struct.unpack_from('<I',pool,8)[0]
  scratch=p.alloc(free_pages*4+64);allocated.append(scratch)
  all_pages=[]
  for offset in range(0,free_pages,1):
   count=min(1,free_pages-offset)
   results=p.calls([(0x324c0c,[scratch+4*(offset+i),0,0,0]) for i in range(count)])
   assert all(x==0 for x in results),results
   handles=p.s.read(scratch+offset*4,count*4)
   all_pages.extend(struct.unpack_from('<H',handles,i*4)[0] for i in range(count))
   state['all_pages']=all_pages;STATE.write_text(json.dumps(state,indent=2)+'\n')
   if len(all_pages)>=needed and all_pages[-1]-all_pages[-needed]==needed-1:break

   if len(all_pages)%32==0 or len(all_pages)==free_pages:print('PAGES',len(all_pages),free_pages,flush=True)
  assert len(set(all_pages))==len(all_pages) and min(all_pages)>=3,all_pages
  ids=sorted(all_pages)
  run=[]
  for page in ids:
   if run and page!=run[-1]+1:run=[]
   run.append(page)
   if len(run)==needed:break
  assert len(run)==needed,'no sufficiently large consecutive page range'
  pages=run;extra=[i for i in all_pages if i not in pages]
  assert all(x==0 for x in p.calls([(0x324eac,[0,i]) for i in extra]))
  base=p.call(0x324b84,pages[0])&~0x40000000
  image_ptr=base
  wad=(ROOT/'doom'/'doom1.nosound.wad').read_bytes() if STAGE>2 else b'';wad_ptr=base+116*32768
  assert 116*32768+len(wad)<=len(pages)*32768
  state['dmb_pages']=pages
  state['all_pages']=pages
  addresses=p.calls([(0x324b84,[page]) for page in pages])
  assert addresses==[base+0x40000000+i*32768 for i in range(len(pages))], 'page physical addresses not consecutive'

  task_ptr=p.alloc(0x220+256*1024+64);allocated.append(task_ptr);tcb=(task_ptr+7)&~7;stack=(tcb+0x220+31)&~31
  state.update(image_allocation=hex(image_ptr),base=hex(base),wad_allocation=hex(wad_ptr),wad_size=len(wad),task_allocation=hex(task_ptr),tcb=hex(tcb),stack=hex(stack),allocations=[hex(x) for x in allocated],started=False)
  STATE.write_text(json.dumps(state,indent=2)+'\n');print('ALLOCATIONS', {k:v for k,v in state.items() if k not in ['all_pages','dmb_pages']},flush=True)
  subprocess.run(['python3',str(PORT/'build.py'),hex(base)],check=True)
  symbols={}
  for line in (PORT/'build'/'symbols.txt').read_text().splitlines():
   parts=line.split()
   if len(parts)==3:symbols[parts[2]]=int(parts[0],16)
  assert symbols['__bss_end__']<base+116*32768
  binary=(PORT/'build'/'doom.bin').read_bytes()
  def progress(n,total):
   if n==total or n%(1024*1024)<8192:print('UPLOAD',n,total,flush=True)
  p.bulk.write(base,binary,progress=progress)
  print('DOOM_CODE_UPLOADED_NO_READBACK',len(binary),flush=True)
  p.bulk.write(wad_ptr,wad,progress=progress)
  print('WAD_UPLOADED_NO_READBACK',flush=True)
  state['wad_loaded']=bool(wad)
  STATE.write_text(json.dumps(state,indent=2)+'\n')
  assert p.call(0x3211e4,base,base+len(binary))==0
  assert p.call(0x10d84,base,base+len(binary))==0
  p.call(symbols['cp_init'],wad_ptr,len(wad),1000)
  p.s.word(symbols['cp_stage_limit'],STAGE)
  p.bulk.write(tcb,b'\0'*0x220)
  name=stack+256*1024;p.bulk.write(name,b'cp_doom\0')
  args=[tcb,name,symbols['cp_thread'],0,stack,256*1024,30,30,1,0,0x220]
  status=p.call(0x2c2d74,*args);state['create_status']=status;assert status==0,('thread create',status)
  started=True  # From resume onward preserve allocations on ambiguous USB failures.
  status=p.call(0x2c3138,tcb);state['resume_status']=status;assert status==0,('thread resume',status)
  started=True;state.update(started=True,symbols={k:hex(symbols[k]) for k in ['cp_status','cp_frames','cp_stop','cp_log','cp_log_used','cp_thread','cp_stage_limit']});STATE.write_text(json.dumps(state,indent=2)+'\n')
  print('DOOM_THREAD_STARTED',flush=True)
  for i in range(12):
   time.sleep(1)
   status=struct.unpack('<I',p.s.read(symbols['cp_status'],4))[0];frames=struct.unpack('<I',p.s.read(symbols['cp_frames'],4))[0]
   print('DOOM_STATUS',hex(status),'FRAMES',frames,flush=True)
   state.update(status=hex(status),frames=frames);STATE.write_text(json.dumps(state,indent=2)+'\n')
   if frames>2 or (STAGE<=2 and status in (0x11,0x14)):break
  log=p.bulk.read(symbols['cp_log'],4096);(ROOT/'usb'/'doom-log.bin').write_bytes(log);print('LOG',log.rstrip(b'\0').decode(errors='replace'),flush=True)
 except Exception as e:
  state['error']=repr(e);STATE.write_text(json.dumps(state,indent=2)+'\n')
  if not started:
   for idx in dict.fromkeys(state.get('dmb_pages',state.get('all_pages',[]))):
    if idx>=3:p.call(0x324eac,0,idx)
   for ptr in reversed(allocated):p.free(ptr)
  raise

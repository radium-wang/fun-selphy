from program_service import ProgramService,ROOT
import json,subprocess,struct,time,sys
port=ROOT.parent/'doom'/'port';f=ROOT/'doom-runtime.json';j=json.loads(f.read_text());base=int(j['base'],16);tcb=int(j['tcb'],16);stack=int(j['stack'],16);stage=int(sys.argv[1])
subprocess.run(['python3',str(port/'build.py'),hex(base)],check=True)
sy={}
for line in (port/'build'/'symbols.txt').read_text().splitlines():
 a=line.split()
 if len(a)==3:sy[a[2]]=int(a[0],16)
with ProgramService() as p:
 previous_state=struct.unpack('<I',p.s.read(tcb+0x30,4))[0]
 if previous_state!=1:assert p.call(0x2c3188,tcb)==0
 assert p.call(0x2c2fbc,tcb)==0
 if stage>=5 and not j.get('wad_loaded'):
  old=j['dmb_pages'];scratch=int(j['allocations'][0],16);new=[]
  for i in range(105):
   assert p.call(0x324c0c,scratch,0,0,0)==0
   page=int.from_bytes(p.s.read(scratch,2),'little');new.append(page)
   assert page==old[-1]+len(new),('page gap',new)
   j['extra_pages']=new;f.write_text(json.dumps(j,indent=2)+'\n')
  wad=(ROOT.parent/'doom'/'doom1.nosound.wad').read_bytes();wp=base+116*32768
  p.bulk.write(wp,wad,progress=lambda n,t:print('WAD',n,t,flush=True) if n==t or n%1048576==0 else None)
  j.update(wad_loaded=True,wad_size=len(wad),wad_allocation=hex(wp));f.write_text(json.dumps(j,indent=2)+'\n')
 binary=(port/'build'/'doom.bin').read_bytes();p.bulk.write(base,binary)
 assert p.call(0x3211e4,base,base+len(binary))==0
 assert p.call(0x10d84,base,base+len(binary))==0
 p.call(sy['cp_init'],int(j['wad_allocation'],16) if j.get('wad_loaded') else 0,j['wad_size'] if j.get('wad_loaded') else 0,1000);p.s.word(sy['cp_stage_limit'],stage)
 p.bulk.write(tcb,b'\0'*0x220)
 assert p.call(0x2c2d74,tcb,stack+256*1024,sy['cp_thread'],0,stack,256*1024,30,30,1,0,0x220)==0
 assert p.call(0x2c3138,tcb)==0
 j.update(symbols={k:hex(sy[k]) for k in ['cp_status','cp_frames','cp_stop','cp_log','cp_log_used','cp_thread','cp_stage_limit','cp_keymask','cp_keydowns','cp_keyups']},stage=stage);f.write_text(json.dumps(j,indent=2)+'\n')
 for i in range(4):
  time.sleep(.1);st=struct.unpack('<I',p.s.read(sy['cp_status'],4))[0];ts=struct.unpack('<I',p.s.read(tcb+0x30,4))[0];print('STATUS',hex(st),'THREAD',ts,flush=True)
  if ts==1:break
 log=p.bulk.read(sy['cp_log'],4096);print('LOG',log.rstrip(b'\0').decode(errors='replace'),flush=True);(ROOT/f'doom-stage{stage}-log.bin').write_bytes(log)

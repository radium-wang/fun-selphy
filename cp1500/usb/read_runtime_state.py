"""Read-only live symbol-table and RAM alias audit via established DBGmon R command."""
from dbgmon_link import Link
from pathlib import Path
import struct,time,json
ROOT=Path(__file__).resolve().parent
class Session:
 def __init__(self):
  self.l=Link()
  def log(op,rc,data=b''):self.l.events.append({'op':op,'result':rc,'hex':data.hex()})
  self.l.log=log
 def poll(self):
  for i in range(100):
   response=self.l.receive();assert response is not None,'transport timeout'
   if response[1]:return response[1]
   time.sleep(.005);self.l.packet()
  raise RuntimeError('no command response')
 def open(self):
  assert self.l.control(0x41,0,0x81,2)==0
  self.l.packet();h,b=self.l.receive();assert h[0]&16
  self.l.packet(bytes.fromhex('00 00 0f 00 01 00 01 01 01 0e 04 0e 04 00 00'),1)
  reply=self.poll();assert reply[6:10]==bytes.fromhex('81 00 01 01'),reply.hex()
  print('channel1 open success',flush=True)
 def read(self,address,length):
  result=bytearray()
  while len(result)<length:
   start=address+len(result);n=min(64,length-len(result));payload=b''
   for a in range(start,start+n):payload+=struct.pack('<BBHBB',0,1,14,1,0)+b'\x1bDR'+struct.pack('<I',a)+b'\x00'
   self.l.packet(payload,n);values={}
   while len(values)<n:
    body=self.poll();offset=0
    while offset<len(body):
     size=int.from_bytes(body[offset+2:offset+4],'little');assert size>=6 and offset+size<=len(body)
     sub=body[offset:offset+size];offset+=size
     if sub[1]==1 and size==14 and sub[6:9]==b'\x1bDR':
      a=int.from_bytes(sub[9:13],'little');assert start<=a<start+n;values[a]=sub[13]
    if len(values)<n:time.sleep(.005);self.l.packet()
   result.extend(values[a] for a in range(start,start+n))
  return bytes(result)
 def close(self):self.l.close()

def main():
 s=Session();summary={}
 try:
  s.open()
  for a,n in [(0x70c71c,20),(0x4070c71c,20),(0x900,32),(0x40000900,32),(0x70bae0,128),(0x76aacc,64),(0x77aca4,128)]:
   data=s.read(a,n);(ROOT/f'ram-{a:08x}.bin').write_bytes(data);summary[hex(a)]=data.hex();print(hex(a),n,data.hex(),flush=True)
  capacity,used,required=struct.unpack_from('<3I',bytes.fromhex(summary['0x70c71c']))
  assert 0<capacity<=0x10000 and 0<used<=capacity,(capacity,used,required)
  table=s.read(0x7d7e6c,capacity);(ROOT/'symbol-table.bin').write_bytes(table)
  records=[];off=0
  while off<used:
   size,kind=struct.unpack_from('<II',table,off)
   stride={0:0x98,1:0x1c,2:8,3:0x20,5:0x1c,6:0x1c}.get(kind,0x20)
   assert off+stride<=used,(off,kind,stride,used)
   row={'offset':hex(off),'address':hex(0x7d7e6c+off),'record_size_word':size,'type':kind}
   if kind in (1,3,5,6):
    row.update(name=table[off+8:off+20].split(b'\0')[0].decode('ascii','replace'),size=struct.unpack_from('<I',table,off+20)[0],pointer=hex(struct.unpack_from('<I',table,off+24)[0]))
   records.append(row);off+=stride
  summary.update(capacity=capacity,used=used,required=required,unused=capacity-used,records=records,
   metadata_alias_match=summary['0x70c71c']==summary['0x4070c71c'],code_alias_match=summary['0x900']==summary['0x40000900'])
  (ROOT/'runtime-state.json').write_text(json.dumps(summary,indent=2)+'\n')
  print(json.dumps({k:v for k,v in summary.items() if k in ['capacity','used','unused','metadata_alias_match','code_alias_match','records']},indent=2),flush=True)
 finally:s.close()
if __name__=='__main__':main()

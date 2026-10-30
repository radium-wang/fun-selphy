"""CP1500 USB DBGmon transport primitives. No RAM writes or execution commands."""
import ctypes as C
import contextlib,io,json,time
from pathlib import Path
with contextlib.redirect_stdout(io.StringIO()):
 import inspect_usb as s
u=s.u;ptr=C.c_void_p
for name,ret,args in [
 ('libusb_open',C.c_int,[ptr,C.POINTER(ptr)]),('libusb_close',None,[ptr]),
 ('libusb_claim_interface',C.c_int,[ptr,C.c_int]),('libusb_release_interface',C.c_int,[ptr,C.c_int]),
 ('libusb_set_interface_alt_setting',C.c_int,[ptr,C.c_int,C.c_int]),
 ('libusb_control_transfer',C.c_int,[ptr,C.c_uint8,C.c_uint8,C.c_uint16,C.c_uint16,ptr,C.c_uint16,C.c_uint]),
 ('libusb_bulk_transfer',C.c_int,[ptr,C.c_ubyte,ptr,C.c_int,C.POINTER(C.c_int),C.c_uint])]:s.bind(name,ret,args)
class Link:
 def __init__(self):
  self.ctx=ptr();assert u.libusb_init(C.byref(self.ctx))==0
  self.lst=C.POINTER(ptr)();n=u.libusb_get_device_list(self.ctx,C.byref(self.lst));self.h=ptr();self.claimed=False;self.events=[]
  for i in range(n):
   d=s.DeviceDescriptor();u.libusb_get_device_descriptor(self.lst[i],C.byref(d))
   if (d.vid,d.pid)==(0x04a9,0x3302):
    rc=u.libusb_open(self.lst[i],C.byref(self.h));assert rc==0,('open',rc);break
  assert self.h,'CP1500 not found'
  rc=u.libusb_claim_interface(self.h,2);assert rc==0,('claim2',rc);self.claimed=True
 def log(self,op,rc,data=b''):
  row={'op':op,'result':rc,'hex':data.hex()};self.events.append(row);print(row,flush=True)
 def control(self,bm,req,value,index):
  rc=u.libusb_control_transfer(self.h,bm,req,value,index,None,0,2000);self.log(f'control {bm:02x}/{req:02x}/{value:04x}/{index:04x}',rc);return rc
 def out(self,data):
  buf=C.create_string_buffer(data);n=C.c_int();rc=u.libusb_bulk_transfer(self.h,7,buf,len(data),C.byref(n),2000);self.log('OUT',rc,data[:n.value]);assert rc==0 and n.value==len(data),(rc,n.value)
 def read(self,n=8):
  buf=C.create_string_buffer(n);actual=C.c_int();rc=u.libusb_bulk_transfer(self.h,0x87,buf,n,C.byref(actual),2000);data=buf.raw[:actual.value];self.log('IN',rc,data);return rc,data
 def packet(self,payload=b'',count=0):
  import struct
  h=bytearray(struct.pack('<BBHHBB',4,count,len(payload),0,0,0));h[7]=(255-sum(h[:7]))&255
  self.out(bytes(h))
  if payload:self.out(payload)
 def receive(self):
  rc,h=self.read()
  if rc:return None
  assert len(h)==8 and sum(h)%256==255,('invalid header',h)
  n=int.from_bytes(h[2:4],'little');body=b''
  if h[1]:
   rc,body=self.read(n);assert rc==0 and len(body)==n,(rc,len(body),n)
  return h,body
 def close(self):
  if self.claimed:u.libusb_release_interface(self.h,2)
  if self.h:u.libusb_close(self.h)
  u.libusb_free_device_list(self.lst,1);u.libusb_exit(self.ctx)
  Path(__file__).with_name('handshake-events.json').write_text(json.dumps(self.events,indent=2)+'\n')

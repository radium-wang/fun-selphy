"""One-shot CP1500 debug-interface enable. No RAM or flash operations."""
import ctypes as C
import inspect_usb as s
u=s.u;ptr=C.c_void_p
for name,ret,args in [
 ('libusb_open',C.c_int,[ptr,C.POINTER(ptr)]),
 ('libusb_close',None,[ptr]),
 ('libusb_claim_interface',C.c_int,[ptr,C.c_int]),
 ('libusb_release_interface',C.c_int,[ptr,C.c_int]),
 ('libusb_set_interface_alt_setting',C.c_int,[ptr,C.c_int,C.c_int]),
 ('libusb_bulk_transfer',C.c_int,[ptr,C.c_ubyte,ptr,C.c_int,C.POINTER(C.c_int),C.c_uint]),
 ('libusb_error_name',C.c_char_p,[C.c_int])]:s.bind(name,ret,args)
ctx=ptr();assert u.libusb_init(C.byref(ctx))==0
lst=C.POINTER(ptr)();n=u.libusb_get_device_list(ctx,C.byref(lst));sent=False
try:
 for i in range(n):
  d=s.DeviceDescriptor();u.libusb_get_device_descriptor(lst[i],C.byref(d))
  if (d.vid,d.pid)!=(0x04a9,0x3302):continue
  h=ptr();rc=u.libusb_open(lst[i],C.byref(h));assert rc==0,('open',rc)
  claimed=False
  try:
   rc=u.libusb_claim_interface(h,0);assert rc==0,('claim',rc);claimed=True
   rc=u.libusb_set_interface_alt_setting(h,0,0);assert rc==0,('raw printer alt0',rc)
   cmd=bytes.fromhex('2b 01 00 00 00 00 00 00 00 00 00 00');buf=C.create_string_buffer(cmd);actual=C.c_int()
   rc=u.libusb_bulk_transfer(h,1,buf,len(cmd),C.byref(actual),2000)
   print('enable command: result=',rc,u.libusb_error_name(rc).decode(),'bytes=',actual.value)
   sent=True
  finally:
   if claimed:print('release',u.libusb_release_interface(h,0))
   u.libusb_close(h)
  break
finally:
 u.libusb_free_device_list(lst,1);u.libusb_exit(ctx)
assert sent,'CP1500 not found / no command sent'

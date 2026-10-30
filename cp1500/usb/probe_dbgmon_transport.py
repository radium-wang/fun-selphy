"""Read printer IEEE1284 ID and test claiming interface; sends no bulk data."""
import ctypes as C
import inspect_usb as s
u=s.u;ptr=C.c_void_p
s.bind('libusb_open',C.c_int,[ptr,C.POINTER(ptr)])
s.bind('libusb_close',None,[ptr])
s.bind('libusb_claim_interface',C.c_int,[ptr,C.c_int])
s.bind('libusb_release_interface',C.c_int,[ptr,C.c_int])
s.bind('libusb_control_transfer',C.c_int,[ptr,C.c_uint8,C.c_uint8,C.c_uint16,C.c_uint16,ptr,C.c_uint16,C.c_uint])
s.bind('libusb_error_name',C.c_char_p,[C.c_int])
s.bind('libusb_bulk_transfer',C.c_int,[ptr,C.c_ubyte,ptr,C.c_int,C.POINTER(C.c_int),C.c_uint])
ctx=ptr();assert u.libusb_init(C.byref(ctx))==0
lst=C.POINTER(ptr)();n=u.libusb_get_device_list(ctx,C.byref(lst))
for i in range(n):
 d=s.DeviceDescriptor();u.libusb_get_device_descriptor(lst[i],C.byref(d))
 if (d.vid,d.pid)!=(0x04a9,0x3302):continue
 h=ptr();rc=u.libusb_open(lst[i],C.byref(h));print('open',rc,u.libusb_error_name(rc).decode())
 if rc:continue
 rc=u.libusb_claim_interface(h,2);print('claim_interface_2',rc,u.libusb_error_name(rc).decode())
 if not rc:
  hello=C.create_string_buffer(bytes.fromhex('04 00 00 00 00 00 00 fb')); sent=C.c_int()
  rc=u.libusb_bulk_transfer(h,0x07,hello,8,C.byref(sent),1500)
  print('transport credit header OUT',rc,sent.value)
  buf=C.create_string_buffer(8);actual=C.c_int()
  rc=u.libusb_bulk_transfer(h,0x87,buf,8,C.byref(actual),1500)
  print('DBGmon IN',rc,'bytes',actual.value,buf.raw[:actual.value].hex(' '))
  print('release_interface_2',u.libusb_release_interface(h,2))
 u.libusb_close(h)
u.libusb_free_device_list(lst,1);u.libusb_exit(ctx)

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
ctx=ptr();assert u.libusb_init(C.byref(ctx))==0
lst=C.POINTER(ptr)();n=u.libusb_get_device_list(ctx,C.byref(lst))
for i in range(n):
 d=s.DeviceDescriptor();u.libusb_get_device_descriptor(lst[i],C.byref(d))
 if (d.vid,d.pid)!=(0x04a9,0x3302):continue
 h=ptr();rc=u.libusb_open(lst[i],C.byref(h));print('open',rc,u.libusb_error_name(rc).decode())
 if rc:continue
 buf=C.create_string_buffer(4096)
 rc=u.libusb_control_transfer(h,0x80,6,0x0200,0,buf,4096,1500)
 print('RAW_CONFIG',rc,buf.raw[:rc].hex(' ') if rc>0 else u.libusb_error_name(rc));
 if rc>0: __import__('pathlib').Path(__file__).with_name('raw-config.bin').write_bytes(buf.raw[:rc])
 rc=u.libusb_claim_interface(h,0);print('claim_interface_0',rc,u.libusb_error_name(rc).decode())
 if not rc:print('release_interface_0',u.libusb_release_interface(h,0))
 u.libusb_close(h)
u.libusb_free_device_list(lst,1);u.libusb_exit(ctx)

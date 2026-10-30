"""Read-only libusb enumeration; no configuration/interface changes or OUT data."""
import ctypes as C
import json
import os
import ctypes.util
from pathlib import Path
library=os.environ.get('LIBUSB_LIBRARY') or ctypes.util.find_library('usb-1.0')
if not library:
 raise RuntimeError('libusb not found; install libusb or set LIBUSB_LIBRARY')
u=C.CDLL(library)
class DeviceDescriptor(C.Structure):
 _fields_=[('length',C.c_uint8),('type',C.c_uint8),('usb',C.c_uint16),('cls',C.c_uint8),('sub',C.c_uint8),('proto',C.c_uint8),('packet0',C.c_uint8),('vid',C.c_uint16),('pid',C.c_uint16),('bcd',C.c_uint16),('manufacturer',C.c_uint8),('product',C.c_uint8),('serial',C.c_uint8),('configs',C.c_uint8)]
class Endpoint(C.Structure):
 _fields_=[('length',C.c_uint8),('type',C.c_uint8),('address',C.c_uint8),('attributes',C.c_uint8),('max_packet',C.c_uint16),('interval',C.c_uint8),('refresh',C.c_uint8),('sync',C.c_uint8),('extra',C.c_void_p),('extra_length',C.c_int)]
class Alt(C.Structure):
 _fields_=[('length',C.c_uint8),('type',C.c_uint8),('interface',C.c_uint8),('alt',C.c_uint8),('endpoints',C.c_uint8),('cls',C.c_uint8),('sub',C.c_uint8),('proto',C.c_uint8),('string',C.c_uint8),('endpoint',C.POINTER(Endpoint)),('extra',C.c_void_p),('extra_length',C.c_int)]
class Interface(C.Structure):
 _fields_=[('alts',C.POINTER(Alt)),('count',C.c_int)]
class Config(C.Structure):
 _fields_=[('length',C.c_uint8),('type',C.c_uint8),('total',C.c_uint16),('interfaces',C.c_uint8),('value',C.c_uint8),('string',C.c_uint8),('attributes',C.c_uint8),('max_power',C.c_uint8),('interface',C.POINTER(Interface)),('extra',C.c_void_p),('extra_length',C.c_int)]
def bind(name,restype,args):
 f=getattr(u,name);f.restype=restype;f.argtypes=args;return f
ptr=C.c_void_p
bind('libusb_init',C.c_int,[C.POINTER(ptr)])
bind('libusb_get_device_list',C.c_ssize_t,[ptr,C.POINTER(C.POINTER(ptr))])
bind('libusb_get_device_descriptor',C.c_int,[ptr,C.POINTER(DeviceDescriptor)])
bind('libusb_get_config_descriptor',C.c_int,[ptr,C.c_uint8,C.POINTER(C.POINTER(Config))])
bind('libusb_free_config_descriptor',None,[C.POINTER(Config)])
bind('libusb_free_device_list',None,[C.POINTER(ptr),C.c_int])
bind('libusb_exit',None,[ptr])
def enumerate_devices():
 ctx=ptr();rc=u.libusb_init(C.byref(ctx));assert rc==0,rc
 lst=C.POINTER(ptr)();n=u.libusb_get_device_list(ctx,C.byref(lst));assert n>=0,n
 result=[]
 for i in range(n):
  d=DeviceDescriptor();rc=u.libusb_get_device_descriptor(lst[i],C.byref(d))
  if rc or d.vid!=0x04a9 or d.pid!=0x3302:continue
  item={'vid':hex(d.vid),'pid':hex(d.pid),'bcdDevice':hex(d.bcd),'configurations':[]}
  for ci in range(d.configs):
   cfg=C.POINTER(Config)();rc=u.libusb_get_config_descriptor(lst[i],ci,C.byref(cfg))
   if rc:item['error']=rc;continue
   cf=cfg.contents;entry={'value':cf.value,'interfaces':[]}
   for j in range(cf.interfaces):
    it=cf.interface[j]
    for k in range(it.count):
     a=it.alts[k]
     entry['interfaces'].append({'number':a.interface,'alt':a.alt,'class':hex(a.cls),'subclass':hex(a.sub),'protocol':hex(a.proto),'endpoints':[{'address':hex(a.endpoint[z].address),'attributes':a.endpoint[z].attributes,'max_packet':a.endpoint[z].max_packet} for z in range(a.endpoints)]})
   item['configurations'].append(entry);u.libusb_free_config_descriptor(cfg)
  result.append(item)
 u.libusb_free_device_list(lst,1);u.libusb_exit(ctx)
 return result

if __name__=='__main__':
 print(json.dumps(enumerate_devices(),indent=2))

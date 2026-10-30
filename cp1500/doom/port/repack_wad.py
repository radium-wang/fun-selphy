"""Strip unused audio while preserving4-byte alignment required by ARM typed loads."""
from pathlib import Path
import struct
p=Path(__file__).resolve().parent.parent
source=(p/'doom1.wad').read_bytes();count,directory=struct.unpack_from('<II',source,4)
out=bytearray(b'IWAD'+struct.pack('<II',count,0));records=[]
for i in range(count):
 off,size,name=struct.unpack_from('<II8s',source,directory+i*16)
 if name.rstrip(b'\0').startswith((b'DS',b'D_')):size=0
 out+=b'\0'*((-len(out))%4)
 records.append((len(out),size,name));out+=source[off:off+size]
out+=b'\0'*((-len(out))%4);struct.pack_into('<I',out,8,len(out))
for row in records:out+=struct.pack('<II8s',*row)
assert all(off%4==0 for off,size,name in records)
for i,(off,size,name) in enumerate(records):
 src_off,src_size,src_name=struct.unpack_from('<II8s',source,directory+i*16)
 assert name==src_name and out[off:off+size]==source[src_off:src_off+size]
(p/'doom1.nosound.wad').write_bytes(out)
print('Aligned repack:',len(out),'bytes; all non-audio lump payloads preserved by index')

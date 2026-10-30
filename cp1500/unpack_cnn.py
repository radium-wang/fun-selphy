#!/usr/bin/env python3
"""CP1500 1060/1070 offline extraction derived from the two supplied images.
No device access, target execution, or firmware modification. Python stdlib only.
The full translated view is NOT a flashable image: some source fields are plain.
"""
from pathlib import Path
import hashlib,json,re,struct,zlib
ROOT=Path(__file__).resolve().parent
TABLE=bytes([0]+list(range(255,0,-17))+[x for x in range(255,0,-1) if x%17])
assert len(TABLE)==len(set(TABLE))==256
INV=bytes(TABLE.index(x) for x in range(256))
def sha(b):return hashlib.sha256(b).hexdigest()
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
def write_strings(path,b):
    path.write_text(''.join(f'{m.start():08x} {m.group().decode("ascii")}\n' for m in re.finditer(rb'[ -~]{6,}',b)))
def unpack(version):
    src=ROOT/f'original/CP1500_{version}.cnn';raw=src.read_bytes();d=raw.translate(TABLE)
    assert d.translate(INV)==raw
    out=ROOT/f'unpacked/{version}';out.mkdir(parents=True,exist_ok=True)
    count=u32(d,0)
    assert u32(d,4)==count^0xffffffff
    h=8+count*5
    load,size,neg=struct.unpack_from('<III',d,h)
    assert size^neg==0xffffffff
    start=h+12;end=start+size
    assert end<=0xa0000
    boot=d[start:end]
    entry,entry_inv=struct.unpack_from('<II',d,end)
    assert entry^entry_inv==0xffffffff and load<=entry<load+size
    tab=0xa0000
    assert raw[tab:tab+4]==b'OART'
    assert u32(d,tab+0x1c)==len(raw)
    n=u32(d,tab+0xc)
    assert n==98 and 0x28+n*12==0x4c0
    sections=[]
    for idx in range(n):
        addr,length,flag=struct.unpack_from('<III',d,tab+0x28+idx*12)
        off=addr-0x80000000
        assert 0<=off<=len(raw) and off+length<=len(raw)
        sections.append({'index':idx,'stored_address':hex(addr),'file_offset':off,'length':length,'flag':flag})
    compressed=[s for s in sections if s['flag']==1]
    assert len(compressed)==1
    s=compressed[0];off=s['file_offset'];gz=d[off:off+s['length']]
    assert gz[:3]==b'\x1f\x8b\x08'
    dec=zlib.decompressobj(31);main=dec.decompress(gz,32*1024*1024)
    assert dec.eof and not dec.unused_data and not dec.unconsumed_tail
    crc,isize=struct.unpack('<II',gz[-8:])
    assert zlib.crc32(main)==crc and len(main)==isize
    files={'prefix-640KiB.decoded.bin':d[:tab],'boot.bin':boot,'main.gz':gz,'main.bin':main}
    for name,data in files.items():(out/name).write_bytes(data)
    write_strings(out/'boot.strings.txt',boot);write_strings(out/'main.strings.txt',main)
    manifest={'source':src.name,'source_sha256':sha(raw),'version':version,
      'method':'Empirically recovered fixed byte substitution; local static analysis, not REA Evidence',
      'decode_table_hex':TABLE.hex(),'encode_decode_roundtrip':True,
      'register_records_candidate':{'count':count,'record_size':5,'offset':8},
      'boot':{'source_offset':start,'size':size,'load_address':hex(load),'entry_candidate':hex(entry),
              'header_complements_valid':True,'date_string':d[0x2ac3e:0x2ac52].decode()},
      'rom_table':{'raw_magic':'OART','offset':tab,'count':n,'address_to_file_offset_subtract':'0x80000000','entries':sections},
      'gzip':{'source_offset':off,'compressed_size':len(gz),'uncompressed_size':len(main),
              'crc32':hex(crc),'crc32_verified':True,'isize_verified':True},
      'files':{name:{'size':len(data),'sha256':sha(data)} for name,data in files.items()},
      'limitations':['Decode table is verified for extracted boot and gzip payload; plain source magic/trailer fields exist.',
        'Header/section semantics are inferred from these two versions; parser intentionally rejects other layouts.',
        'CPU code inspected statically; no hardware execution, boot test or flash acceptance established.',
        'Gzip CRC is integrity validation, not authentication or proof of an unsigned update.']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
if __name__=='__main__':
    for v in ('1060','1070'):
        m=unpack(v);print(v,json.dumps({'boot':m['boot'],'gzip':m['gzip']},ensure_ascii=False))
    a=(ROOT/'unpacked/1060/boot.bin').read_bytes();b=(ROOT/'unpacked/1070/boot.bin').read_bytes()
    diff=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
    assert len(a)==len(b) and len(diff)==10 and all(0x2ac3e-0x762<=i<0x2ac52-0x762 for i in diff)
    print('Boot images identical except 10 bytes in the build timestamp.')

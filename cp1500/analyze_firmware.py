#!/usr/bin/env python3
"""Bounded, read-only CNN inspection; does not claim to decode Canon's format."""
from pathlib import Path
from collections import Counter
import hashlib, json, math, re, zlib
root = Path(__file__).resolve().parent
src = root / 'original/CP1500_1070.cnn'
out = root / 'analysis'
out.mkdir(exist_ok=True)
b = src.read_bytes()
def entropy(x):
    return -sum((n/len(x))*math.log2(n/len(x)) for n in Counter(x).values())
magic = {'gzip':'1f8b08','xz':'fd377a585a00','zip':'504b0304','elf':'7f454c46',
         'squashfs_le':'68737173','squashfs_be':'73717368','png':'89504e470d0a1a0a',
         'jpeg':'ffd8ff','bzip2':'425a68','7zip':'377abcaf271c','uimage':'27051956',
         'ubi':'55424923','ubifs':'31181006','cramfs_le':'453dcd28'}
hits={}
for name, hx in magic.items():
    sig=bytes.fromhex(hx)
    hits[name]=[m.start() for m in re.finditer(re.escape(sig),b)]
streams=[]
candidates=[i for i in range(len(b)-2) if (b[i]==0x78 and b[i+1] in (1,0x5e,0x9c,0xda)) or b[i:i+3]==b'\x1f\x8b\x08']
for off in candidates:
    try:
        dec=zlib.decompressobj(47)
        data=dec.decompress(b[off:],16*1024*1024)
        if dec.eof and len(data)>64:
            name=f'stream_{off:08x}.bin'
            (out/name).write_bytes(data)
            streams.append({'offset':off,'length':len(b)-off-len(dec.unused_data),'output_length':len(data),'file':name})
    except zlib.error:
        pass
report={'source':str(src),'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),
        'method':'Python standard-library static scan; not REA Evidence',
        'signature_hits_candidates_only':hits,'zlib_gzip_candidates_tested':len(candidates),
        'validated_zlib_gzip_streams':streams,
        'entropy_64KiB':[{'offset':off,'length':len(b[off:off+65536]),'bits_per_byte':entropy(b[off:off+65536])} for off in range(0,len(b),65536)],
        'constant_runs_at_least_4096':[{'offset':m.start(),'length':len(m.group()),'byte':m.group()[0]} for m in re.finditer(rb'(.)\1{4095,}',b,re.S)],
        'tail16':{'offset':len(b)-16,'hex':b[-16:].hex()},
        'limitations':['No proprietary format decoder available.','No decryption, signature verification, execution or flashing performed.','Missing standard magic does not exclude compression or a filesystem.','Input downloaded via HTTP after HTTPS transport failed; ZIP CRC and vendor-listed size are not authenticity verification.']}
(out/'scan.json').write_text(json.dumps(report,indent=2)+'\n')
(out/'strings_ascii.txt').write_text(''.join(f'{m.start():08x} {m.group().decode("ascii")}\n' for m in re.finditer(rb'[ -~]{8,}',b)))
(out/'header.hex.txt').write_text(''.join(f'{i:08x} {b[i:i+16].hex(" ")}\n' for i in range(0,512,16)))
(root/'original/SHA256SUMS').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted((root/'original').iterdir()) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:report[k] for k in ['size','sha256','signature_hits_candidates_only','zlib_gzip_candidates_tested','validated_zlib_gzip_streams','tail16']},indent=2))

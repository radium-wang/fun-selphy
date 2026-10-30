#!/usr/bin/env python3
from pathlib import Path
import struct,json,re,functools,hashlib
from unpack_cnn import TABLE
root=Path(__file__).resolve().parent
main=(root/'unpacked/1070/main.bin').read_bytes()
r={'scope':'Static inspection of CP1500 1060/1070; not a complete secure-boot audit.',
   'table_offset_in_main':main.find(TABLE),
   'code_offsets_in_main':{'byte_decoder':0xaa38,'decode_file_wrapper':0xab54,'validate_before_flash_call':0x2e68fc,'xor_validation_function':0x2e7b8c,'xor_accumulation':0x2e7ce8,'zero_test':0x2e7d00},
   'data_pointer_note':'Decoder uses literal 0x4b23bd; table resides at main file offset 0x4b243d. Observed +0x80 data mapping; main file offsets are not asserted runtime addresses.',
   'versions':{},'content_evidence':{}}
assert r['table_offset_in_main']==0x4b243d
for v in ['1060','1070']:
 raw=(root/f'original/CP1500_{v}.cnn').read_bytes();decoded=bytearray(raw.translate(TABLE))
 exempt=[(0xa0000,0xa0004),(0xa0024,0xa0028),(len(raw)-12,len(raw))]
 for s,e in exempt:decoded[s:e]=raw[s:e]
 data=decoded[0xa0000:]
 xor=functools.reduce(int.__xor__,struct.unpack(f'<{len(data)//4}I',data),0)
 assert xor==0
 r['versions'][v]={'source_sha256':hashlib.sha256(raw).hexdigest(),'plain_ranges_end_exclusive':exempt,'checksum_start':0xa0000,'checksum_end':len(raw),'xor32_le':xor}
terms={
 'OS':['ThreadX ARM9/RVDS','NetX BSD'],
 'print_engine':['LF MOTOR WAIT','HEAD_TEMP_INDEX','Could not found ribbon marker.','RIBBON JAM'],
 'image_and_display':['AIPL-JPG','AIPL-PNG','lcdapi_font_setup','PriSetBrightness','PriSetLayout'],
 'printing_protocols':['PROTO:CPNP','CMD:Raster3','CMD:URF','printer-firmware-version'],
 'web_and_tls':['Canon SELPHY CP1500 Network Configuration','make_SelfSignedCcertificate','rsa_check_keypair','SHA256'],
 'wireless':['SX-SD8801-THREADX-C698','WPA SHA256','moal_initialize_firmware'],
 'update':['%c:\\*.cnn','%c:\\*.rbn','FW_UPDATE_PROGRESS_VERIFY','Flash image check sum nonzero']}
for group,ts in terms.items():
 r['content_evidence'][group]=[{'text':s,'main_file_offset':main.find(s.encode())} for s in ts]
manifest=json.loads((root/'unpacked/1070/manifest.json').read_text())
raw=(root/'original/CP1500_1070.cnn').read_bytes().translate(TABLE)
r['bmp_sections']=[]
for s in manifest['rom_table']['entries']:
 off=s['file_offset'];n=s['length'];b=raw[off:off+n]
 if b[:2]==b'BM' and len(b)>=54:
  r['bmp_sections'].append({'index':s['index'],'source_offset':off,'section_size':n,'header_size':struct.unpack_from('<I',b,2)[0],'width':struct.unpack_from('<i',b,18)[0],'height':struct.unpack_from('<i',b,22)[0],'bits_per_pixel':struct.unpack_from('<H',b,28)[0]})
r['signature_conclusion']='Observed upgrade validation uses XOR32 and structural checks; no cryptographic firmware verification identified in inspected path. TLS crypto is not evidence of firmware signatures. Other paths, boot ROM, and hardware policy remain unverified.'
(root/'analysis/content-signature-audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'versions':r['versions'],'bmp_sections':r['bmp_sections'],'content_evidence':r['content_evidence']},ensure_ascii=False,indent=2))

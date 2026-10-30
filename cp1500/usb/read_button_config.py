from read_runtime_state import Session,ROOT
import struct,json
s=Session()
try:
 s.open();b=s.read(0x717f88,32);words=struct.unpack('<8I',b);print('button state',[hex(x) for x in words],flush=True)
 count=words[1];assert count<=32
 config=s.read(words[2],count*16);print('button config',config.hex(),flush=True)
 (ROOT/'button-config.bin').write_bytes(config)
 (ROOT/'button-state.json').write_text(json.dumps({'words':[hex(x) for x in words],'config_hex':config.hex()},indent=2)+'\n')
finally:s.close()

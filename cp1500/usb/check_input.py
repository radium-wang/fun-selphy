from read_runtime_state import Session,ROOT
import json,time
j=json.loads((ROOT/'doom-runtime.json').read_text());sy={k:int(v,16) for k,v in j['symbols'].items()};s=Session();rows=[]
try:
 s.open()
 for i in range(12):
  row={key:int.from_bytes(s.read(sy[key],4),'little') for key in ['cp_keymask','cp_keydowns','cp_keyups','cp_frames']};rows.append(row);print(row,flush=True);time.sleep(1)
 (ROOT/'input-live-check.json').write_text(json.dumps(rows,indent=2)+'\n')
finally:s.close()

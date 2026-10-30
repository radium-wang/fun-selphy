#!/usr/bin/env python3
from pathlib import Path
from collections import Counter
import hashlib,json
root=Path(__file__).resolve().parent
old=(root/'original/CP1500_1060.cnn').read_bytes()
new=(root/'original/CP1500_1070.cnn').read_bytes()
anchors=[]; intervals=[]
for i in range(0,len(old)-128,4096):
    chunk=old[i:i+128]
    if len(set(chunk))<32:continue
    j=new.find(chunk)
    if j<0 or new.find(chunk,j+1)>=0:continue
    anchors.append({'old_offset':i,'new_offset':j,'shift':j-i})
    lo=0;hi=128
    while i+lo>0 and j+lo>0 and old[i+lo-1]==new[j+lo-1]:lo-=1
    while i+hi<len(old) and j+hi<len(new) and old[i+hi]==new[j+hi]:hi+=1
    intervals.append((i+lo,i+hi))
merged=[]
for start,end in sorted(intervals):
    if merged and start<=merged[-1][1]:merged[-1][1]=max(end,merged[-1][1])
    else:merged.append([start,end])
prefix_changes=[{'offset':i,'old':old[i],'new':new[i]} for i in range(0xa0000) if old[i]!=new[i]]
allowed=set(b'\r\nS0123456789abcdefABCDEF')
key_counts=[sum(all(x^k in allowed for x in set(new[phase:65536:16])) for k in range(256)) for phase in range(16)]
r={'method':'Local Python static comparison; exact matches only, no REA Evidence',
   'old':{'version':'1.0.6.0','size':len(old),'sha256':hashlib.sha256(old).hexdigest()},
   'new':{'version':'1.0.7.0','size':len(new),'sha256':hashlib.sha256(new).hexdigest()},
   'size_delta':len(new)-len(old),'prefix_640KiB_changed_bytes':prefix_changes,
   'unique_128byte_anchor_stride':4096,'anchors':anchors,
   'anchor_shift_counts':dict(Counter(a['shift'] for a in anchors)),
   'old_exact_match_ranges_anchored':merged,
   'old_exact_match_bytes_lower_bound':sum(e-s for s,e in merged),
   'trailers':{'old':old[-16:].hex(),'new':new[-16:].hex()},
   'pixma_compatibility':{'xor16_srec_valid_key_counts_first64KiB':key_counts,
    'decompressor_signature_offset':new.find(bytes.fromhex('70b5054c05480649451a0e462a4631462046ff'))},
   'limitations':['Matched bytes include padding and data, not established code similarity.',
    'This anchor method is not an optimal alignment and reports a lower bound.',
    'PIXMA negative tests cover the examined public method, not all possible transformations.']}
(root/'analysis/comparison.json').write_text(json.dumps(r,indent=2)+'\n')
print({k:v for k,v in r.items() if k not in ['anchors','old_exact_match_ranges_anchored']})

from pathlib import Path
import subprocess,re,sys,os,shutil
p=Path(__file__).resolve().parent;root=p.parent
src=root/'doomgeneric-master'/'doomgeneric'
candidate=os.environ.get('ARM_CC') or shutil.which('arm-none-eabi-gcc')
if not candidate:
 local=list(root.glob('arm-gnu-toolchain-*/bin/arm-none-eabi-gcc'))
 if local:candidate=str(local[0])
if not candidate:raise SystemExit('Set ARM_CC or add arm-none-eabi-gcc to PATH')
tool=Path(candidate)
base=sys.argv[1] if len(sys.argv)>1 else '0x42000000'
out=p/'build';out.mkdir(exist_ok=True)
text=(src/'Makefile').read_text();names=re.search(r'SRC_DOOM = (.*)',text)[1].split()
files=[src/(n[:-2]+'.c') for n in names if n not in ['w_file_stdc.o','doomgeneric_xlib.o']]+[p/'platform.c',p/'w_file_memory.c']
flags=['-mcpu=arm926ej-s','-marm','-mfloat-abi=soft','-Os','-fno-strict-aliasing','-ffunction-sections','-fdata-sections','-DDOOMGENERIC_RESX=320','-DDOOMGENERIC_RESY=200','-DNORMALUNIX','-I'+str(src)]
objects=[]
for f in files:
 o=out/(f.stem+'.o');objects.append(str(o))
 if not o.exists() or o.stat().st_mtime<f.stat().st_mtime:
  r=subprocess.run([str(tool),*flags,'-c',str(f),'-o',str(o)],capture_output=True,text=True)
  if r.returncode:print(r.stderr);sys.exit(r.returncode)
link=p/'link.ld';link.write_text('ENTRY(cp_thread)\nSECTIONS { . = '+base+'; .text : { *(.text*) *(.rodata*) } .ARM.exidx : { *(.ARM.exidx*) } .data : { *(.data*) } . = ALIGN(8); __bss_start__ = .; .bss (NOLOAD) : { *(.bss*) *(COMMON) } __bss_end__ = .; _end = .; }\n')
subprocess.run([str(tool),*flags,'-nostartfiles','-Wl,--gc-sections','-Wl,-u,cp_init','-Wl,-u,cp_status','-Wl,-u,cp_frames','-Wl,-u,cp_log','-Wl,-u,cp_stop','-Wl,-u,cp_stage_limit','-Wl,-u,cp_keymask','-Wl,-u,cp_keydowns','-Wl,-u,cp_keyups','-T',str(link),*objects,'-Wl,--start-group','-lc','-lm','-lgcc','-Wl,--end-group','-o',str(out/'doom.elf')],check=True)
subprocess.run([str(tool).replace('gcc','objcopy'),'-O','binary',str(out/'doom.elf'),str(out/'doom.bin')],check=True)
with (out/'symbols.txt').open('w') as f:subprocess.run([str(tool).replace('gcc','nm'),'-n',str(out/'doom.elf')],stdout=f,check=True)
subprocess.run([str(tool).replace('gcc','size'),str(out/'doom.elf')],check=True)

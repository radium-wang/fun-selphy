#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <errno.h>
#include <stdio.h>
#include "doomgeneric.h"
#include "doomkeys.h"
#include "doomstat.h"
extern boolean menuactive;
unsigned char *cp_wad_data;
unsigned cp_wad_size;
volatile unsigned cp_status,cp_frames,cp_stop;
volatile unsigned cp_stage_limit=1; /* Loader overrides this; diagnostics default. */
unsigned cp_tick_hz=1000;
char cp_log[4096];unsigned cp_log_used;
static unsigned char lcd[640*240*3];
static unsigned char heap[5*1024*1024/2] __attribute__((aligned(8)));
static unsigned heap_used;
static unsigned ticks(void){return ((unsigned(*)(void))0x2c1720)();}
void DG_Init(void){cp_status=2;}
void DG_DrawFrame(void){
 for(unsigned y=0;y<240;y++){
  unsigned sy=y*200/240;
  for(unsigned x=0;x<320;x++){
   unsigned c=DG_ScreenBuffer[sy*320+x];
   unsigned char *d=lcd+(y*640+x*2)*3;
   d[0]=d[3]=(c>>16)&255;d[1]=d[4]=(c>>8)&255;d[2]=d[5]=c&255;
  }
 }
 ((int(*)(void*))0x673dc)(lcd);cp_frames++;cp_status=3;
}
void DG_SleepMs(uint32_t ms){unsigned t=(ms*cp_tick_hz+999)/1000;if(!t)t=1;((int(*)(unsigned))0x2c0f0c)(t);}
uint32_t DG_GetTicksMs(void){return (uint32_t)((uint64_t)ticks()*1000/cp_tick_hz);}
volatile unsigned cp_keymask,cp_keydowns,cp_keyups;
static unsigned key_delivered,key_snapshot,key_poll_tick;
static unsigned char held_key[8];
int DG_GetKey(int *pressed,unsigned char *key){
 unsigned changed=key_snapshot^key_delivered;
 if(!changed){
  unsigned now=ticks();
  if(now-key_poll_tick<10)return 0;
  key_poll_tick=now;
  ((void(*)(void))0x126c8c)(); /* refresh GPIO/ADC samples */
  ((void(*)(void))0x126f9c)(); /* decode configured voltage windows */
  cp_keymask=((unsigned(*)(void))0x127014)()&0xfe;
  key_snapshot=cp_keymask;changed=key_snapshot^key_delivered;
  if(!changed)return 0;
 }
 unsigned bit=0;while(!(changed&(1u<<bit)))bit++;
 unsigned mask=1u<<bit;int down=(key_snapshot&mask)!=0;
 if(down){
  unsigned char k=0;
  switch(mask){
   case 0x08:k=KEY_UPARROW;break;
   case 0x10:k=KEY_DOWNARROW;break;
   case 0x02:k=KEY_LEFTARROW;break;
   case 0x04:k=KEY_RIGHTARROW;break;
   case 0x40:k=(gamestate==GS_LEVEL&&!menuactive&&!demoplayback)?KEY_FIRE:KEY_ENTER;break;
   case 0x80:k=KEY_ESCAPE;break;
   case 0x20:k=(gamestate==GS_LEVEL&&!menuactive&&!demoplayback)?KEY_USE:KEY_ESCAPE;break;
  }
  held_key[bit]=k;key_delivered|=mask;cp_keydowns++;
 }else{key_delivered&=~mask;cp_keyups++;}
 *pressed=down;*key=held_key[bit];return 1;
}
void DG_SetWindowTitle(const char*t){(void)t;}
void *_sbrk(int n){if(n<0 || (unsigned)n>sizeof(heap)-heap_used){errno=ENOMEM;return (void*)-1;}void*p=heap+heap_used;heap_used+=n;return p;}
int _write(int fd,const void*b,size_t n){(void)fd;const char*p=b;for(size_t i=0;i<n;i++)cp_log[(cp_log_used++)%sizeof(cp_log)]=p[i];return n;}
extern int cp_wad_path_matches(const char*);
static unsigned file_offset;
int _open(const char*p,int flags,...){(void)flags;if(cp_wad_path_matches(p)){file_offset=0;return 3;}errno=ENOENT;return -1;}
int _close(int fd){(void)fd;return 0;}
int _read(int fd,void*b,size_t n){if(fd!=3)return 0;if(file_offset>cp_wad_size)return 0;if(n>cp_wad_size-file_offset)n=cp_wad_size-file_offset;memcpy(b,cp_wad_data+file_offset,n);file_offset+=n;return n;}
int _lseek(int fd,int off,int whence){if(fd!=3)return -1;int p=whence==0?off:whence==1?(int)file_offset+off:(int)cp_wad_size+off;if(p<0)return -1;file_offset=p;return p;}
int _fstat(int fd,struct stat*s){memset(s,0,sizeof(*s));s->st_mode=fd==3?S_IFREG:S_IFCHR;s->st_size=fd==3?cp_wad_size:0;return 0;}
int _stat(const char*p,struct stat*s){if(!cp_wad_path_matches(p)){errno=ENOENT;return -1;}return _fstat(3,s);}
int _isatty(int fd){return fd<3;}
int _getpid(void){return 1;}int _kill(int p,int sig){(void)p;(void)sig;return -1;}
int _gettimeofday(struct timeval*t,void*z){(void)z;unsigned ms=DG_GetTicksMs();t->tv_sec=ms/1000;t->tv_usec=(ms%1000)*1000;return 0;}
void _exit(int c){cp_status=0xdead0000|(c&65535);for(;;)DG_SleepMs(1000);}
extern unsigned char __bss_start__,__bss_end__;
/* Host calls initialization once before creating a dedicated ThreadX task. */
void cp_init(unsigned char*wad,unsigned size,unsigned hz){memset(&__bss_start__,0,&__bss_end__-&__bss_start__);cp_wad_data=wad;cp_wad_size=size;cp_tick_hz=hz;cp_status=1;}
void cp_thread(unsigned long ignored){
 (void)ignored;
 cp_status=0x10;
 if(cp_stage_limit==1){cp_frames=1;cp_status=0x11;return;}
 if(cp_stage_limit==2){
  cp_status=0x12;
  void *test=malloc(4096);
  cp_status=test?0x13:0xe1;
  if(test){memset(test,0x5a,4096);free(test);}
  printf("runtime probe passed\n");
  cp_status=0x14;return;
 }
 cp_status=0x20;
 static char*a[]={"doom","-iwad","doom1.wad","-nosound","-nomusic"};
 doomgeneric_Create(5,a);
 cp_status=0x21;
 if(cp_stage_limit<10)return;
 while(!cp_stop)doomgeneric_Tick();
 cp_status=4;
}
int mkdir(const char*p,mode_t m){(void)p;(void)m;return 0;}
int _unlink(const char*p){(void)p;errno=ENOENT;return -1;}
int _link(const char*a,const char*b){(void)a;(void)b;errno=ENOENT;return -1;}

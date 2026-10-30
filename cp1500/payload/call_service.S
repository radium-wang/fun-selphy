.syntax unified
.arch armv5te
.arm
.section .text,"ax",%progbits
.global call_service
.type call_service,%function
/* body: name[16], function u32, arguments[11]. */
call_service:
 push {r4-r6,lr}
 mov r4,r0
 mov r5,r2
 ldr r6,[r4,#16]
 sub sp,sp,#32
 add r3,r4,#36
 ldm r3,{r0-r2}
 stm sp,{r0-r2}
 add r3,r4,#48
 ldm r3,{r0-r2}
 add r3,sp,#12
 stm r3,{r0-r2}
 ldr r0,[r4,#60]
 str r0,[sp,#24]
 add r3,r4,#20
 ldm r3,{r0-r3}
 blx r6
 add sp,sp,#32
 str r0,[r4]
 mov r0,#4
 str r0,[r5]
 mov r0,#0
 pop {r4-r6,lr}
 bx lr
.size call_service,.-call_service

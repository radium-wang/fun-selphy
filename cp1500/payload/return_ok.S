.syntax unified
.arch armv5te
.arm
.section .text,"ax",%progbits
.global cp1500_return_ok
.type cp1500_return_ok,%function
/* r0=request/result buffer, r1=request length, r2=length word at buffer+0x400.
 * Leaf function: no stack, no absolute addresses, preserves r4-r11 and lr.
 * Reply bytes are written to r0, NOT to r2; r2 holds the reply length.
 */
cp1500_return_ok:
    mov r3, #79
    strb r3, [r0]
    mov r3, #75
    strb r3, [r0, #1]
    mov r3, #2
    str r3, [r2]
    mov r0, #0
    bx lr
.size cp1500_return_ok, .-cp1500_return_ok

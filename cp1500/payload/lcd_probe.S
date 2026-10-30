.syntax unified
.arch armv5te
.arm
.section .text,"ax",%progbits
.global lcd_probe
.type lcd_probe,%function
lcd_probe:
    push {r4-r10, lr}
    mov r4, r0
    mov r5, r2
    ldr r0, image_size
    ldr r3, malloc_address
    blx r3
    mov r6, r0
    mvn r10, #0
    cmp r6, #0
    beq report
    mov r9, r6
    mov r7, #240
row:
    mov r8, #0
pixel:
    mov r0, r8, lsr #7
    tst r0, #1
    movne r1, #255
    moveq r1, #0
    strb r1, [r9], #1
    tst r0, #2
    movne r1, #255
    moveq r1, #0
    strb r1, [r9], #1
    tst r0, #4
    movne r1, #255
    moveq r1, #0
    strb r1, [r9], #1
    add r8, r8, #1
    cmp r8, #640
    blt pixel
    subs r7, r7, #1
    bne row
    mov r0, r6
    ldr r3, display_address
    blx r3
    mov r10, r0
    ldr r0, arena_address
    mov r1, r6
    ldr r3, free_address
    blx r3
    mov r7, r0
    b report_ready
report:
    mvn r7, #0
report_ready:
    ldr r3, button_address
    blx r3
    str r0, [r4, #16]
    ldr r0, magic
    str r0, [r4]
    str r6, [r4, #4]
    str r10, [r4, #8]
    str r7, [r4, #12]
    mov r0, #20
    str r0, [r5]
    mov r0, #0
    pop {r4-r10, lr}
    bx lr
.align 2
malloc_address: .word 0x32d524
free_address: .word 0x31db84
arena_address: .word 0x70bae0
display_address: .word 0x673dc
button_address: .word 0x127014
image_size: .word 460800
magic: .ascii "LCD1"
.size lcd_probe, .-lcd_probe

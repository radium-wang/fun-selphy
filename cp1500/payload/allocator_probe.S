.syntax unified
.arch armv5te
.arm
.section .text,"ax",%progbits
.global allocator_probe
.type allocator_probe,%function
allocator_probe:
    push {r4-r8, lr}
    mov r4, r0
    mov r5, r2
    mov r0, #4096
    ldr r3, malloc_address
    blx r3
    mov r6, r0
    mov r7, #0
    mvn r8, #0
    cmp r6, #0
    beq report
    ldr r7, sentinel
    str r7, [r6]
    add r1, r6, #4096
    str r7, [r1, #-4]
    ldr r7, [r6]
    ldr r2, [r1, #-4]
    cmp r7, r2
    movne r7, #0
    ldr r0, arena_address
    mov r1, r6
    ldr r3, free_address
    blx r3
    mov r8, r0
report:
    ldr r0, magic
    str r0, [r4]
    str r6, [r4, #4]
    str r7, [r4, #8]
    str r8, [r4, #12]
    mov r0, #16
    str r0, [r5]
    mov r0, #0
    pop {r4-r8, lr}
    bx lr
.align 2
malloc_address: .word 0x32d524
free_address: .word 0x31db84
arena_address: .word 0x70bae0
sentinel: .word 0x1234abcd
magic: .ascii "MEM1"
.size allocator_probe, .-allocator_probe

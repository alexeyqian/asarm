A mini assembler:

Features:
- instruction encoding ✅
- control flow ✅
- memory model ✅
- calling convention ✅
- branching
- conditional

Simple arm64 introduction:
https://cybersandeep.gitbook.io/arm64basicguide/chapter-1-getting-to-know-arm64

ARM64 (also known as AArch64) uses a fixed-length 32-bit instruction encoding pattern. This means every instruction, regardless of its function, is exactly 4 bytes long, allowing for efficient decoding in high-performance processors.

General Encoding Structure
The 32 bits (31-0) are generally divided into several functional fields, though the exact layout varies based on the instruction type: 

sf (Bit 31): Scalar format. Determines if the operation is 64-bit (sf=1) or 32-bit (sf=0).

Opcode (Various bits): Determines the action (ADD, SUB, LDR, etc.).

Registers (Rn, Rm, Rd, Rt): 5-bit fields to select from the 31 general-purpose registers (X0-X30).

Immediate Values (Imm): Contiguous bits used for constants or offsets. 

Example:
  ADD Xd, Xn #imm
  | opcode | imm12 | Rn | Rd | (simplified)
  Rn - source, Rd - destination

Assembler as
ELF builder ld
Encoding LLVM backend

This ELF:
has no stack setup
no libc
no system calls
no .data section
no relocations

1. First Pass
Collect labels → address mapping
2. Second Pass
Encode instructions
Resolve label offsets
3. Encoding Layer
Each instruction → bit manipulation

| Category   | Instructions |
| ---------- | ------------ |
| Arithmetic | ADD, SUB     |
| Move       | MOV          |
| Control    | B            |
| Memory     | LDR, STR     |

Pre-index
LDR Xt, [Xn, #imm]!
STR Xt, [Xn, #imm]!
Update base register before access

Post-index
LDR Xt, [Xn], #imm
STR Xt, [Xn], #imm
Update base register after access

usecases
offset: struct/array access
pre-index stack push
post-index stack pop

Stack Frame Convention
func:
    STR X30, [SP, #-16]!   // save LR
    STR X29, [SP, #-16]!   // save FP

    MOV X29, SP            // set frame pointer

    ... body ...

    LDR X29, [SP], #16
    LDR X30, [SP], #16
    RET

Argument Passing
X0–X7 → arguments
X0 → return value

Local Variables - use stack
SUB SP, SP, #32
...
ADD SP, SP, #32

The core ABI rules (what actually matters)

| Purpose       | Registers                   |
| ------------- | --------------------------- |
| Arguments     | `X0–X7`                     |
| Return value  | `X0`                        |
| Caller-saved  | `X0–X18` (assume clobbered) |
| Callee-saved  | `X19–X28`                   |
| Frame pointer | `X29`                       |
| Link register | `X30`                       |
| Stack pointer | `SP`                        |

Stack rules
Stack grows downward
Must be 16-byte aligned at all calls
No “red zone” (unlike x86-64)

🧠 Function skeleton (canonical form)
func:
    STP X29, X30, [SP, #-16]!   // save FP + LR
    MOV X29, SP                 // set frame pointer

    // optionally save callee-saved regs
    STP X19, X20, [SP, #-16]!

    // allocate locals (must keep 16-byte alignment)
    SUB SP, SP, #32

    ... body ...

    ADD SP, SP, #32

    LDP X19, X20, [SP], #16
    LDP X29, X30, [SP], #16
    RET

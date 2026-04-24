# ARM64 (A64) Instruction Encoding Overview

In the ARM64 architecture (A64), instructions follow a **fixed-length encoding pattern** where every instruction is exactly **32 bits wide**. This consistency is a hallmark of its Reduced Instruction Set Computing (RISC) design, allowing for high-performance hardware decoding.

## Core Encoding Structure

The 32 bits are divided into functional fields. While layouts vary by instruction class, they generally follow these standards:

*   **Size Flag (sf):** Bit 31 typically determines the register width. 
    *   `0` = 32-bit registers ($Wn$)
    *   `1` = 64-bit registers ($Xn$)
*   **Opcode:** Specific bit ranges define the operation (e.g., ADD, SUB, LDR).
*   **Register Fields (5 bits each):** Specify one of the 31 general-purpose registers ($0$-$30$) or the zero register/SP ($31$).
    *   **Rd:** Destination register.
    *   **Rn, Rm:** Source registers.
*   **Immediates:** Constant values embedded directly in the instruction for arithmetic or memory offsets.

## Common Instruction Classes


| Instruction Class | Encoding Pattern Characteristics |
| :--- | :--- |
| **Data Processing (Immediate)** | Encodes operation type, immediate value, and source/destination. |
| **Data Processing (Register)** | Operates between registers; often includes a shift amount (`sh`). |
| **Loads and Stores** | Defines base register, destination register, and addressing mode/offset. |
| **Branches** | Encodes a target address offset relative to the Program Counter (PC). |

## Special Features

*   **Bitwise Immediates:** Uses a specialized pattern of rotated bit sequences to represent various constants within limited bits.
*   **System Instructions:** Controls CPU state using specific fields like `op1`, `CRn`, `CRm`, and `op2`.

---
*For precise bit-field diagrams of every instruction, refer to the [Arm A64 Instruction Set Architecture](https://arm.com) documentation.*

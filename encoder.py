# encoder.py

from dataclasses import dataclass
from typing import Optional


# ----------------------------
# Relocation model
# ----------------------------

@dataclass
class Relocation:
    symbol: str
    type: str   # "B", "BL", "ADR", "ADRP", "B.cond"
    addend: int = 0


@dataclass
class EncodedInstruction:
    value: int
    relocation: Optional[Relocation] = None


# ----------------------------
# Encoder (PURE)
# ----------------------------

class Encoder:

    # ----------------------------
    # Helpers
    # ----------------------------

    def reg(self, r: str) -> int:
        if r == "SP":
            return 31
        if r.startswith("X"):
            return int(r[1:])
        raise ValueError(f"Invalid register {r}")

    def imm(self, val: str) -> int:
        if val.startswith("#"):
            return int(val[1:], 0)
        raise ValueError(f"Invalid immediate {val}")

    # ----------------------------
    # Arithmetic
    # ----------------------------

    def add(self, rd, rn, imm) -> EncodedInstruction:
        instr = (
            (0b1001000100 << 22) |
            (imm << 10) |
            (rn << 5) |
            rd
        )
        return EncodedInstruction(instr)

    def sub(self, rd, rn, imm) -> EncodedInstruction:
        instr = (
            (0b1101000100 << 22) |
            (imm << 10) |
            (rn << 5) |
            rd
        )
        return EncodedInstruction(instr)

    def mov(self, rd, rn) -> EncodedInstruction:
        instr = (
            (0b10101010000 << 21) |
            (rn << 16) |
            (31 << 5) |
            rd
        )
        return EncodedInstruction(instr)

    # ----------------------------
    # Memory (unsigned offset)
    # ----------------------------

    def ldr(self, rt, rn, imm) -> EncodedInstruction:
        if imm % 8 != 0:
            raise ValueError("LDR imm must be multiple of 8")

        imm12 = imm // 8

        instr = (
            (0b1111100101 << 22) |
            (imm12 << 10) |
            (rn << 5) |
            rt
        )
        return EncodedInstruction(instr)

    def str(self, rt, rn, imm) -> EncodedInstruction:
        if imm % 8 != 0:
            raise ValueError("STR imm must be multiple of 8")

        imm12 = imm // 8

        instr = (
            (0b1111100001 << 22) |
            (imm12 << 10) |
            (rn << 5) |
            rt
        )
        return EncodedInstruction(instr)

    # ----------------------------
    # Branch (relocation)
    # ----------------------------

    def b(self, label: str) -> EncodedInstruction:
        return EncodedInstruction(
            value=0,
            relocation=Relocation(symbol=label, type="B")
        )

    def bl(self, label: str) -> EncodedInstruction:
        return EncodedInstruction(
            value=0,
            relocation=Relocation(symbol=label, type="BL")
        )

    # ----------------------------
    # Conditional branch
    # ----------------------------

    COND_MAP = {
        "EQ": 0,
        "NE": 1,
        "GE": 10,
        "LT": 11,
        "GT": 12,
        "LE": 13,
    }

    def b_cond(self, cond: str, label: str) -> EncodedInstruction:
        if cond not in self.COND_MAP:
            raise ValueError(f"Unknown condition {cond}")

        return EncodedInstruction(
            value=0,
            relocation=Relocation(symbol=label, type=f"B.{cond}")
        )

    # ----------------------------
    # RET
    # ----------------------------

    def ret(self, rn=30) -> EncodedInstruction:
        instr = (
            (0b1101011001011111000000 << 10) |
            (rn << 5)
        )
        return EncodedInstruction(instr)

    # ----------------------------
    # CMP
    # ----------------------------

    def cmp_reg(self, rn, rm) -> EncodedInstruction:
        instr = (
            (0b11101011000 << 21) |
            (rm << 16) |
            (rn << 5) |
            31
        )
        return EncodedInstruction(instr)

    def cmp_imm(self, rn, imm) -> EncodedInstruction:
        instr = (
            (0b1111000100 << 22) |
            (imm << 10) |
            (rn << 5) |
            31
        )
        return EncodedInstruction(instr)

    # ----------------------------
    # SVC
    # ----------------------------

    def svc(self, imm=0) -> EncodedInstruction:
        instr = (
            (0b11010100000 << 21) |
            (imm << 5) |
            0b00001
        )
        return EncodedInstruction(instr)

    # ----------------------------
    # ADR / ADRP (relocation)
    # ----------------------------

    def adr(self, rd, label: str) -> EncodedInstruction:
        return EncodedInstruction(
            value=0,
            relocation=Relocation(symbol=label, type="ADR")
        )

    def adrp(self, rd, label: str) -> EncodedInstruction:
        return EncodedInstruction(
            value=0,
            relocation=Relocation(symbol=label, type="ADRP")
        )

    # ----------------------------
    # STP / LDP (ABI)
    # ----------------------------

    def stp_pre(self, rt1, rt2, rn, imm) -> EncodedInstruction:
        if imm % 8 != 0:
            raise ValueError("STP imm must be multiple of 8")

        imm7 = (imm // 8) & 0x7F

        instr = (
            (0b1010100100 << 22) |
            (imm7 << 15) |
            (rt2 << 10) |
            (rn << 5) |
            rt1
        )
        return EncodedInstruction(instr)

    def ldp_post(self, rt1, rt2, rn, imm) -> EncodedInstruction:
        if imm % 8 != 0:
            raise ValueError("LDP imm must be multiple of 8")

        imm7 = (imm // 8) & 0x7F

        instr = (
            (0b1010100110 << 22) |
            (imm7 << 15) |
            (rt2 << 10) |
            (rn << 5) |
            rt1
        )
        return EncodedInstruction(instr)
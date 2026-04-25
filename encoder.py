"""Instruction encoders extracted from assembler.py

All encode_* functions are instance methods on Encoder.
"""
from typing import Any, List

from relocations import Relocation

class Encoder:
    def __init__(self):
        self.code = bytearray()
        self.relocations: List[Relocation] = []

    def emit32(self, value: int) -> None:
        self.code += value.to_bytes(4, byteorder='little')

    def emit_adr_reloc(self, rd, label) -> None:
        # Emit placeholder, add relocation entry
        offset = len(self.code)
        self.emit32(0)  # placeholder
        self.relocations.append(Relocation(offset, label, "ADR"))

    # -- Encoder instance methods --
    def encode_add(self, rd, rn, imm):
        # ADD (immediate) 64-bit
        return (
            (0b1001000100 << 22) |
            (imm << 10) |
            (rn << 5) |
            rd
        )

    def encode_sub(self, rd, rn, imm):
        return (
            (0b1101000100 << 22) |
            (imm << 10) |
            (rn << 5) |
            rd
        )

    def encode_mov(self, rd, rn):
        # MOV Xd, Xn → ORR Xd, XZR, Xn
        # XZR = 31
        return (
            (0b10101010000 << 21) |
            (rn << 16) |
            (31 << 5) |
            rd
        )

    def encode_b(self, offset):
        # B label (offset in instruction words)
        return (
            (0b000101 << 26) |
            (offset & 0x03FFFFFF)
        )

    def encode_ldr(self, rt, rn, imm):
        # LDR (unsigned immediate, 64-bit)
        if imm % 8 != 0:
            raise ValueError("LDR immediate must be multiple of 8")
        imm12 = imm // 8
        return (
            (0b1111100101 << 22) |
            (imm12 << 10) |
            (rn << 5) |
            rt
        )

    def encode_str(self, rt, rn, imm):
        # STR (unsigned immediate, 64-bit)
        if imm % 8 != 0:
            raise ValueError("STR immediate must be multiple of 8")
        imm12 = imm // 8
        return (
            (0b1111100001 << 22) |
            (imm12 << 10) |
            (rn << 5) |
            rt
        )

    def encode_ldr_pre(self, rt, rn, imm):
        if not -256 <= imm <= 255:
            raise ValueError("LDR pre-index immediate must be between -256 and 255")
        imm9 = imm & 0x1FF
        return (
            (0b11111000010 << 21) |
            (imm9 << 12) |
            (rn << 5) |
            rt
        )

    def encode_str_pre(self, rt, rn, imm):
        if not -256 <= imm <= 255:
            raise ValueError("imm out of range for pre-index")
        imm9 = imm & 0x1FF
        return (
            (0b11111000000 << 21) |
            (imm9 << 12) |
            (rn << 5) |
            rt
        )

    def encode_ldr_post(self, rt, rn, imm):
        if not -256 <= imm <= 255:
            raise ValueError("imm out of range for post-index")
        imm9 = imm & 0x1FF
        return (
            (0b11111000011 << 21) |
            (imm9 << 12) |
            (rn << 5) |
            rt
        )

    def encode_str_post(self, rt, rn, imm):
        if not -256 <= imm <= 255:
            raise ValueError("imm out of range for post-index")
        imm9 = imm & 0x1FF
        return (
            (0b11111000001 << 21) |
            (imm9 << 12) |
            (rn << 5) |
            rt
        )

    def encode_bl(self, offset):
        return (
            (0b100101 << 26) |
            (offset & 0x03FFFFFF)
        )

    def encode_ret(self, rn=30):
        return (
            (0b1101011001011111000000 << 10) |
            (rn << 5)
        )

    def encode_stp_pre(self, rt1, rt2, rn, imm):
        if imm % 8 != 0:
            raise ValueError("STP imm must be multiple of 8")
        imm7 = (imm // 8) & 0x7F
        return (
            (0b1010100100 << 22) |
            (imm7 << 15) |
            (rt2 << 10) |
            (rn << 5) |
            rt1
        )

    def encode_ldp_post(self, rt1, rt2, rn, imm):
        if imm % 8 != 0:
            raise ValueError("LDP imm must be multiple of 8")
        imm7 = (imm // 8) & 0x7F
        return (
            (0b1010100110 << 22) |
            (imm7 << 15) |
            (rt2 << 10) |
            (rn << 5) |
            rt1
        )

    def encode_cmp_reg(self, rn, rm):
        return (
            (0b11101011000 << 21) |
            (rm << 16) |
            (rn << 5) |
            31
        )

    def encode_cmp_imm(self, rn, imm):
        if not (0 <= imm < 4096):
            raise ValueError("imm out of range")
        return (
            (0b1111000100 << 22) |
            (imm << 10) |
            (rn << 5) |
            31
        )

    def encode_b_cond(self, cond, offset):
        return (
            (0b01010100 << 24) |
            ((offset & 0x7FFFF) << 5) |
            cond
        )

    def encode_svc(self, imm=0):
        if not (0 <= imm < (1 << 16)):
            raise ValueError("SVC immediate out of range")
        return (
            (0b11010100000 << 21) |
            (imm << 5) |
            0b00001
        )

    def encode_adr_not_used(self, rd, offset):
        immlo = (offset & 0x3)
        immhi = (offset >> 2) & 0x7FFFF
        return (
            (0b00010000 << 24) |
            (immlo << 29) |
            (immhi << 5) |
            rd
        )

    def encode_adrp(self, rd, offset):
        offset >>= 12
        immlo = offset & 0x3
        immhi = (offset >> 2) & 0x7FFFF
        return (
            (0b10010000 << 24) |
            (immlo << 29) |
            (immhi << 5) |
            rd
        )

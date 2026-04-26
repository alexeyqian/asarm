# relocations.py

from typing import List, Tuple
from encoder import Relocation


class RelocationError(Exception):
    pass


# ----------------------------
# Bit helpers
# ----------------------------

def write_u32_le(buf: bytearray, offset: int, value: int):
    buf[offset:offset+4] = value.to_bytes(4, "little")


# ----------------------------
# Encoding helpers (REAL AArch64)
# ----------------------------

def encode_b_imm(offset_bytes: int) -> int:
    # B / BL: 26-bit signed immediate (word aligned)
    if offset_bytes % 4 != 0:
        raise RelocationError("Branch target not 4-byte aligned")

    imm26 = offset_bytes >> 2

    if not -(1 << 25) <= imm26 < (1 << 25):
        raise RelocationError("Branch out of range")

    return imm26 & 0x03FFFFFF


def encode_b_cond_imm(offset_bytes: int) -> int:
    # B.cond: 19-bit signed immediate
    if offset_bytes % 4 != 0:
        raise RelocationError("Branch target not aligned")

    imm19 = offset_bytes >> 2

    if not -(1 << 18) <= imm19 < (1 << 18):
        raise RelocationError("Conditional branch out of range")

    return imm19 & 0x7FFFF


def encode_adr(offset_bytes: int) -> Tuple[int, int]:
    # ADR: 21-bit signed immediate (immhi:19, immlo:2)
    if not -(1 << 20) <= offset_bytes < (1 << 20):
        raise RelocationError("ADR out of range (±1MB)")

    imm = offset_bytes
    immlo = imm & 0x3
    immhi = (imm >> 2) & 0x7FFFF

    return immlo, immhi


def encode_adrp(pc: int, target: int) -> Tuple[int, int]:
    # ADRP: page-relative
    pc_page = pc & ~0xFFF
    target_page = target & ~0xFFF

    offset = (target_page - pc_page) >> 12

    if not -(1 << 20) <= offset < (1 << 20):
        raise RelocationError("ADRP out of range")

    immlo = offset & 0x3
    immhi = (offset >> 2) & 0x7FFFF

    return immlo, immhi


# ----------------------------
# Main relocation application
# ----------------------------
# "Patch instruction so it reaches target from here"
def apply_relocations(
    code: bytearray,
    relocations: List[Tuple[int, Relocation]],
    symtab: dict,
    text_base: int
):
    """
    code: bytearray of .text
    relocations: [(offset_in_code, Relocation)]
    symtab: {symbol: absolute_address}
    text_base: runtime base address of .text
    """

    for offset, reloc in relocations:

        if reloc.symbol not in symtab:
            raise RelocationError(f"Undefined symbol: {reloc.symbol}")

        target = symtab[reloc.symbol]
        # pc is = address of current instruction
        pc = text_base + offset

        # ----------------------------
        # B / BL
        # ----------------------------
        if reloc.type in ("B", "BL"):
            imm26 = encode_b_imm(target - pc)

            opcode = 0b000101 if reloc.type == "B" else 0b100101
            instr = (opcode << 26) | imm26

            write_u32_le(code, offset, instr)

        # ----------------------------
        # B.cond
        # ----------------------------
        elif reloc.type.startswith("B."):
            cond = reloc.type.split(".")[1]

            COND_MAP = {
                "EQ": 0, "NE": 1,
                "GE": 10, "LT": 11,
                "GT": 12, "LE": 13,
            }

            if cond not in COND_MAP:
                raise RelocationError(f"Unknown condition {cond}")

            imm19 = encode_b_cond_imm(target - pc)

            instr = (
                (0b01010100 << 24) |   # opcode
                (imm19 << 5) |
                COND_MAP[cond]
            )

            write_u32_le(code, offset, instr)

        # ----------------------------
        # ADR
        # ----------------------------
        elif reloc.type == "ADR":
            # need original rd from placeholder (lower 5 bits)
            original = int.from_bytes(code[offset:offset+4], "little")
            rd = original & 0x1F

            immlo, immhi = encode_adr(target - pc)

            instr = (
                (0b00010000 << 24) |
                (immlo << 29) |
                (immhi << 5) |
                rd
            )

            write_u32_le(code, offset, instr)

        # ----------------------------
        # ADRP
        # ----------------------------
        # page offset (4KB aligned) 
        elif reloc.type == "ADRP":
            original = int.from_bytes(code[offset:offset+4], "little")
            rd = original & 0x1F

            immlo, immhi = encode_adrp(pc, target)

            instr = (
                (0b10010000 << 24) |
                (immlo << 29) |
                (immhi << 5) |
                rd
            )

            write_u32_le(code, offset, instr)

        else:
            raise RelocationError(f"Unsupported relocation type: {reloc.type}")
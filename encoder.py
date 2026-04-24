"""Instruction encoders extracted from assembler.py

Contains functions named encode_*
"""
from typing import Any

# ADD, SUB, MOV, B, LDR/STR variants, BL, RET, STP/LDP, CMP, B.cond

def encode_add(rd, rn, imm):
    #ADD (immediate) 64-bit
    #opcode: 0b100100100 (fixed bits)
    return (
        (0b1001000100 << 22) |
        (imm << 10) |
        (rn << 5) |
        rd
    )
    
def encode_sub(rd, rn, imm):
    return (
        (0b1101000100 << 22) |
        (imm << 10) |
        (rn << 5) |
        rd
    )

def encode_mov(rd, rn):
    # MOV Xd, Xn → ORR Xd, XZR, Xn
    # XZR = 31
    return (
        (0b10101010000 << 21) |
        (rn << 16) |
        (31 << 5) |
        rd
    )

def encode_b(offset):
    # B label
    # offset is signed, in instructions (not bytes)
    return (
        (0b000101 << 26) |
        (offset & 0x03FFFFFF)
    )
    
def encode_ldr(rt, rn, imm):
    # LDR (unsigned immediate, 64-bit)
    # size=11 (64-bit), opc=01
    if imm % 8 != 0:
        raise ValueError("LDR immediate must be multiple of 8")

    imm12 = imm // 8

    return (
        (0b1111100101 << 22) |   # opcode
        (imm12 << 10) |
        (rn << 5) |
        rt
    )


def encode_str(rt, rn, imm):
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

# example: x = 10 #0b1010
# y = x << 2 # 0b101000 = 40
def encode_ldr_pre(rt, rn, imm):
    # LDR Xt, [Xn, #imm]!
    if not -256 <= imm <= 255:
        raise ValueError("LDR pre-index immediate must be between -256 and 255")
    imm9 = imm & 0x1FF  # 9-bit signed immediate
    return(
        (0b11111000010 << 21) |
        (imm9 << 12) |
        (rn << 5) |
        rt
    )

def encode_str_pre(rt, rn, imm):
    # STR Xt, [Xn, #imm]!
    if not -256 <= imm <= 255:
        raise ValueError("imm out of range for pre-index")

    imm9 = imm & 0x1FF

    return (
        (0b11111000000 << 21) |
        (imm9 << 12) |
        (rn << 5) |
        rt
    )

def encode_ldr_post(rt, rn, imm):
    if not -256 <= imm <= 255:
        raise ValueError("imm out of range for post-index")

    imm9 = imm & 0x1FF

    return (
        (0b11111000011 << 21) |
        (imm9 << 12) |
        (rn << 5) |
        rt
    )

def encode_str_post(rt, rn, imm):
    if not -256 <= imm <= 255:
        raise ValueError("imm out of range for post-index")

    imm9 = imm & 0x1FF

    return (
        (0b11111000001 << 21) |
        (imm9 << 12) |
        (rn << 5) |
        rt
    )

# writes return address into X30
# Execution flow
# BL func:
#    X30 = return address
#    jump to func
# RET:
#    jump to X30
def encode_bl(offset):
    # BL (branch with link)
    return (
        (0b100101 << 26) |
        (offset & 0x03FFFFFF)
    )

# default: RET = RET X30
# encoding is basically a special case of BR
def encode_ret(rn=30):
    # RET Xn
    return (
        (0b1101011001011111000000 << 10) |
        (rn << 5)
    )

# Pair load/store (critical for ABI)
# STP Xt1, Xt2, [SP, #-16]!
def encode_stp_pre(rt1, rt2, rn, imm):
    # imm must be multiple of 8, scaled by 8
    if imm % 8 != 0:
        raise ValueError("STP imm must be multiple of 8")

    imm7 = (imm // 8) & 0x7F

    return (
        (0b1010100100 << 22) |   # STP pre-index
        (imm7 << 15) |
        (rt2 << 10) |
        (rn << 5) |
        rt1
    )

# Pair load/store (critical for ABI)
# LDP Xt1, Xt2, [SP], #16
def encode_ldp_post(rt1, rt2, rn, imm):
    if imm % 8 != 0:
        raise ValueError("LDP imm must be multiple of 8")

    imm7 = (imm // 8) & 0x7F

    return (
        (0b1010100110 << 22) |   # LDP post-index
        (imm7 << 15) |
        (rt2 << 10) |
        (rn << 5) |
        rt1
    )

def encode_cmp_reg(rn, rm):
    # CMP Xn, Xm  == SUBS XZR, Xn, Xm
    return (
        (0b11101011000 << 21) |
        (rm << 16) |
        (rn << 5) |
        31  # XZR
    )

def encode_cmp_imm(rn, imm):
    if not (0 <= imm < 4096):
        raise ValueError("imm out of range")

    return (
        (0b1111000100 << 22) |
        (imm << 10) |
        (rn << 5) |
        31
    )
    
def encode_b_cond(cond, offset):
    return (
        (0b01010100 << 24) |
        ((offset & 0x7FFFF) << 5) |
        cond
    )

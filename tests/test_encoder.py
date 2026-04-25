import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from encoder import Encoder


def test_mov_add_sub_b_match_assembler():
    e = Encoder()
    # Values observed earlier from assembler sample
    assert e.encode_mov(0, 1) == 0xaa0103e0
    assert e.encode_add(2, 0, 10) == 0x91002802
    assert e.encode_sub(3, 2, 5) == 0xd1001443
    # branch with offset -4 (compute expected using same bit layout)
    expected_b = (0b000101 << 26) | ((-4) & 0x03FFFFFF)
    assert e.encode_b(-4) == expected_b


def test_ldr_str_alignment_and_scaling():
    e = Encoder()
    with pytest.raises(ValueError):
        e.encode_ldr(0, 1, 7)  # not multiple of 8
    with pytest.raises(ValueError):
        e.encode_str(0, 1, 3)

    # valid multiples
    val = e.encode_ldr(0, 1, 8)
    # imm12 should equal 1 (8/8)
    assert ((val >> 10) & 0xfff) == 1

    val2 = e.encode_str(5, 2, 16)
    assert ((val2 >> 10) & 0xfff) == 2


def test_pre_post_index_range():
    e = Encoder()
    with pytest.raises(ValueError):
        e.encode_ldr_pre(0, 1, 300)
    with pytest.raises(ValueError):
        e.encode_str_post(0, 1, -300)

    # within range
    v1 = e.encode_ldr_pre(0, 1, -256)
    # imm9 is stored as 9-bit two's complement; ensure returned is int
    assert isinstance(v1, int)

    v2 = e.encode_str_pre(1, 2, 255)
    assert isinstance(v2, int)


def test_cmp_and_svc_ranges():
    e = Encoder()
    with pytest.raises(ValueError):
        e.encode_cmp_imm(0, 5000)
    # valid
    assert isinstance(e.encode_cmp_imm(1, 4095), int)

    with pytest.raises(ValueError):
        e.encode_svc(1 << 20)
    assert isinstance(e.encode_svc(0), int)


def test_stp_ldp_alignment():
    e = Encoder()
    with pytest.raises(ValueError):
        e.encode_stp_pre(0, 1, 2, 7)
    with pytest.raises(ValueError):
        e.encode_ldp_post(0, 1, 2, 3)

    # valid
    assert isinstance(e.encode_stp_pre(0, 1, 2, 16), int)
    assert isinstance(e.encode_ldp_post(0, 1, 2, 8), int)


def test_b_cond_encoding_fields():
    e = Encoder()
    val = e.encode_b_cond(3, 5)
    # cond should occupy low 5 bits
    assert (val & 0x1f) == 3
    # offset field should be present
    assert ((val >> 5) & 0x7ffff) == (5 & 0x7ffff)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from encoder import Encoder, EncodedInstruction


def test_arithmetic_and_mov_and_cmp_svc():
    e = Encoder()

    mov = e.mov(0, 1)
    assert isinstance(mov, EncodedInstruction)
    assert mov.relocation is None
    v = mov.value
    # rd in low 5 bits
    assert (v & 0x1f) == 0
    # XZR encoded in bits [5:10]
    assert ((v >> 5) & 0x1f) == 31
    # rn in bits [16:??]
    assert ((v >> 16) & 0x1ff) == 1

    add = e.add(2, 0, 10)
    assert add.relocation is None
    av = add.value
    assert (av & 0x1f) == 2
    assert ((av >> 5) & 0x1f) == 0
    assert ((av >> 10) & 0xfff) == 10

    sub = e.sub(3, 2, 5)
    sv = sub.value
    assert (sv & 0x1f) == 3
    assert ((sv >> 5) & 0x1f) == 2
    assert ((sv >> 10) & 0xfff) == 5

    cmp_r = e.cmp_reg(1, 2)
    assert (cmp_r.value & 0x1f) == 31

    svc = e.svc(123)
    # low 5 bits are fixed low op (0b00001)
    assert (svc.value & 0x1f) == 0b00001
    assert ((svc.value >> 5) & 0xffff) == 123


def test_memory_encodings_and_alignment():
    e = Encoder()
    with pytest.raises(ValueError):
        e.ldr(0, 1, 7)
    with pytest.raises(ValueError):
        e.str(0, 1, 3)

    ld = e.ldr(0, 1, 8)
    assert ((ld.value >> 10) & 0xfff) == 1

    st = e.str(5, 2, 16)
    assert ((st.value >> 10) & 0xfff) == 2


def test_branch_and_relocations():
    e = Encoder()
    b = e.b('label1')
    assert b.value == 0
    assert b.relocation is not None
    assert b.relocation.symbol == 'label1'
    assert b.relocation.type == 'B'

    bl = e.bl('func')
    assert bl.relocation is not None and bl.relocation.type == 'BL'

    bc = e.b_cond('EQ', 'l')
    assert bc.relocation is not None
    assert bc.relocation.type == 'B.EQ'


def test_adr_adrp_relocations():
    e = Encoder()
    adr = e.adr(0, 'sym')
    assert adr.value == 0
    assert adr.relocation is not None and adr.relocation.type == 'ADR'

    adrp = e.adrp(1, 'page')
    assert adrp.value == 0
    assert adrp.relocation is not None and adrp.relocation.type == 'ADRP'


def test_stp_ldp_alignment_and_fields():
    e = Encoder()
    with pytest.raises(ValueError):
        e.stp_pre(0,1,2,7)
    with pytest.raises(ValueError):
        e.ldp_post(0,1,2,3)

    s = e.stp_pre(0,1,2,16)
    assert ((s.value >> 15) & 0x7f) == (16 // 8)

    l = e.ldp_post(0,1,2,8)
    assert ((l.value >> 15) & 0x7f) == (8 // 8)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from linker import Linker
import linker
from object_file import ObjectFile, Symbol, Relocation

class FakeBuilder:
    def __init__(self, b):
        self.b = b
    def build(self):
        return self.b


def test_link_merges_text_and_data_and_builds_elf():
    # Arrange
    obj1 = ObjectFile(text=b"\x01\x02", data=b"\x03", symbols={
        'foo': Symbol('foo', addr=0, section='text', global_=True)
    }, relocations=[])

    obj2 = ObjectFile(text=b"\x04", data=b"\x05\x06", symbols={
        'bar': Symbol('bar', addr=1, section='data', global_=True)
    }, relocations=[])

    # Make ELFBuilder return the raw bytes so we can inspect input
    linker.ELFBuilder = FakeBuilder

    l = Linker()

    # Act
    out = l.link([obj1, obj2])

    # Assert
    expected = b"\x01\x02\x04\x03\x05\x06"
    assert out == expected


def test_link_detects_duplicate_global_symbol():
    obj1 = ObjectFile(text=b"\x00", data=b"", symbols={
        'dup': Symbol('dup', addr=0, section='text', global_=True)
    }, relocations=[])

    obj2 = ObjectFile(text=b"\x00", data=b"", symbols={
        'dup': Symbol('dup', addr=0, section='text', global_=True)
    }, relocations=[])

    linker.ELFBuilder = FakeBuilder
    l = Linker()
    with pytest.raises(ValueError) as excinfo:
        l.link([obj1, obj2])
    assert 'Duplicate symbol dup' in str(excinfo.value)


def test_link_applies_relocations_with_remapped_bases():
    # Prepare two objects: first has a relocation referencing 'S'
    # second defines global symbol 'S' in text
    # Obj1 text 8 bytes, relocation at offset 4 in text
    obj1_text = bytearray(b"\x00" * 8)
    rel = Relocation(offset=4, symbol='S', type='B', section='text')
    obj1 = ObjectFile(text=bytes(obj1_text), data=b"", symbols={}, relocations=[rel])

    # Obj2 has symbol S at addr 0 in its text
    obj2 = ObjectFile(text=b"\xAA\xBB", data=b"", symbols={
        'S': Symbol('S', addr=0, section='text', global_=True)
    }, relocations=[])

    called = []
    class TestLinker(Linker):
        def apply_relocation(self, text, loc, target, rtype):
            # record call parameters
            called.append((loc, target, rtype))

    linker.ELFBuilder = FakeBuilder
    tl = TestLinker()
    out = tl.link([obj1, obj2])

    # The relocation base for obj1 is its text_base=0, so loc = base + r.offset = 0 + 4
    # The target is global_symtab['S'] which should be text_base of obj2 (len of obj1.text) + sym.addr
    expected_target = len(obj1.text) + obj2.symbols['S'].addr
    assert called == [(4, expected_target, 'B')]

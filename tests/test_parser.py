import pytest
from parser import parse
from ir import Instruction, Label, Directive


def test_parse_basic():
    lines = [
        "start:",
        '.ascii "Hi"',
        "ADD X1, X2, #5",
    ]

    nodes = parse(lines)

    assert isinstance(nodes[0], Label)
    assert nodes[0].name == "start"

    assert isinstance(nodes[1], Directive)
    assert nodes[1].name == ".ascii"
    assert nodes[1].args == ['"Hi"']

    assert isinstance(nodes[2], Instruction)
    assert nodes[2].op == "ADD"
    assert nodes[2].args == ["X1", "X2", "#5"]
    # line number should be the index in the input list
    assert nodes[2].line == 2


def test_parse_blank_and_whitespace():
    lines = ["", "  ", "LOOP:", "  MOV   X0  ,  X1", ".data", ".word 1 2 3"]
    nodes = parse(lines)

    # Should skip blank lines and parse label and instruction
    # First parsed node should be Label LOOp
    assert isinstance(nodes[0], Label)
    assert nodes[0].name == "LOOP"

    # Next should be MOV instruction
    assert isinstance(nodes[1], Instruction)
    assert nodes[1].op == "MOV"
    assert nodes[1].args == ["X0", "X1"]
    # The line index should correspond to its position in the original list
    assert nodes[1].line == 3

    # Directive parsing
    assert isinstance(nodes[2], Directive)
    assert nodes[2].name == ".data"
    assert nodes[2].args == []

    assert isinstance(nodes[3], Directive)
    assert nodes[3].name == ".word"
    assert nodes[3].args == ["1", "2", "3"]


def test_parse_commas_and_multargs():
    lines = ["LABEL:", "STR X0, [X1, #8]", "LDR X2, [X3],#16"]
    nodes = parse(lines)

    assert isinstance(nodes[0], Label)
    assert nodes[0].name == "LABEL"

    assert isinstance(nodes[1], Instruction)
    assert nodes[1].op == "STR"
    # args should be split on commas/whitespace
    assert nodes[1].args == ["X0", "[X1", "#8]"]

    assert isinstance(nodes[2], Instruction)
    assert nodes[2].op == "LDR"
    assert nodes[2].args == ["X2", "[X3]", "#16"]

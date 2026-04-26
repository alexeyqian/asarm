# parser.py

from dataclasses import dataclass
from typing import List, Optional, Union
from lexer import Token, TokenStream


# ----------------------------
# IR Nodes
# ----------------------------

@dataclass
class Instruction:
    op: str
    args: List["Operand"]
    line: int


@dataclass
class Label:
    name: str


@dataclass
class Directive:
    name: str
    args: List[str]


# ----------------------------
# Operands
# ----------------------------

@dataclass
class Register:
    name: str


@dataclass
class Immediate:
    value: int


@dataclass
class Identifier:
    name: str


@dataclass
class StringLiteral:
    value: str


@dataclass
class MemoryOperand:
    base: str
    offset: int = 0
    mode: str = "offset"   # "offset", "pre", "post"


Operand = Union[Register, Immediate, Identifier, StringLiteral, MemoryOperand]

"""
example source code:
.data
msg:
    .ascii "Hello\n"

.text
start:
    ADR X1, msg
    MOV X0, #1

example IR:
Directive(".data")
Label("msg")
Directive(".ascii", ["Hello\n"])
Directive(".text")

Label("start")

Instruction("ADR", [Register("X1"), Identifier("msg")])
Instruction("MOV", [Register("X0"), Immediate(1)])
"""


# ----------------------------
# Parser
# ----------------------------

class Parser:

    def __init__(self, tokens: List[Token]):
        self.stream = TokenStream(tokens)

    # ----------------------------
    # Entry
    # ----------------------------

    def parse(self) -> List[Union[Instruction, Label, Directive]]:
        nodes = []

        while self.stream.peek():
            tok = self.stream.peek()

            if tok.type == "LABEL":
                nodes.append(self.parse_label())

            elif tok.type == "DIRECTIVE":
                nodes.append(self.parse_directive())

            elif tok.type == "IDENT":
                nodes.append(self.parse_instruction())

            else:
                raise SyntaxError(f"Unexpected token {tok}")

        return nodes

    # ----------------------------
    # Label
    # ----------------------------

    def parse_label(self) -> Label:
        tok = self.stream.expect("LABEL")
        return Label(tok.value)

    # ----------------------------
    # Directive
    # ----------------------------

    def parse_directive(self) -> Directive:
        tok = self.stream.expect("DIRECTIVE")
        name = tok.value

        args = []

        while True:
            next_tok = self.stream.peek()
            if not next_tok or next_tok.type in ("LABEL", "DIRECTIVE", "IDENT"):
                break

            if next_tok.type == "STRING":
                args.append(self._parse_string(self.stream.next().value))
            else:
                args.append(self.stream.next().value)

        return Directive(name, args)

    # ----------------------------
    # Instruction
    # ----------------------------

    def parse_instruction(self) -> Instruction:
        op_tok = self.stream.expect("IDENT")
        op = op_tok.value.upper()

        args: List[Operand] = []

        while True:
            tok = self.stream.peek()
            if not tok or tok.type in ("LABEL", "DIRECTIVE"):
                break

            if tok.type == "COMMA":
                self.stream.next()
                continue

            args.append(self.parse_operand())

        return Instruction(op, args, op_tok.line)

    # ----------------------------
    # Operand parsing
    # ----------------------------

    def parse_operand(self) -> Operand:
        tok = self.stream.peek()

        if tok.type == "REGISTER":
            return Register(self.stream.next().value)

        elif tok.type == "IMMEDIATE":
            val = self._parse_imm(self.stream.next().value)
            return Immediate(val)

        elif tok.type == "IDENT":
            return Identifier(self.stream.next().value)

        elif tok.type == "STRING":
            return StringLiteral(self._parse_string(self.stream.next().value))

        elif tok.type == "LBRACKET":
            return self.parse_memory_operand()

        else:
            raise SyntaxError(f"Invalid operand {tok}")

    # ----------------------------
    # Memory operand
    # ----------------------------

    # STR X0, [SP, #-16]!
    # MemoryOperand(base="SP", offset=-16, mode="pre")
    def parse_memory_operand(self) -> MemoryOperand:
        # [Xn, #imm] / [Xn, #imm]! / [Xn], #imm

        self.stream.expect("LBRACKET")

        base_tok = self.stream.expect("REGISTER")
        base = base_tok.value

        offset = 0

        if self.stream.match("COMMA"):
            imm_tok = self.stream.expect("IMMEDIATE")
            offset = self._parse_imm(imm_tok.value)

        self.stream.expect("RBRACKET")

        # pre-index
        if self.stream.match("EXCL"):
            return MemoryOperand(base, offset, mode="pre")

        # post-index
        if self.stream.match("COMMA"):
            imm_tok = self.stream.expect("IMMEDIATE")
            post_offset = self._parse_imm(imm_tok.value)
            return MemoryOperand(base, post_offset, mode="post")

        return MemoryOperand(base, offset, mode="offset")

    # ----------------------------
    # Helpers
    # ----------------------------

    def _parse_imm(self, text: str) -> int:
        return int(text[1:], 0)

    def _parse_string(self, text: str) -> str:
        # remove quotes and decode escapes
        return bytes(text[1:-1], "utf-8").decode("unicode_escape")
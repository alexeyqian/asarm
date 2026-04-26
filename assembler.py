# assembler.py

from typing import List, Tuple, Dict

from lexer import Lexer
from parser import (
    Parser,
    Instruction,
    Label,
    Directive,
    Register,
    Immediate,
    Identifier,
    MemoryOperand,
)
from semantic import SemanticAnalyzer
from encoder import Encoder, EncodedInstruction, Relocation
from object_file import ObjectFile, Symbol


# ----------------------------
# Assembler
# ----------------------------

class Assembler:

    def __init__(self):
        self.reset()

    def reset(self):
        # sections
        self.section = "text"

        # buffers
        self.text = bytearray()
        self.data = bytearray()
        self.bss_size = 0

        # label offsets (section-relative)
        self.text_labels: Dict[str, int] = {}
        self.data_labels: Dict[str, int] = {}
        self.bss_labels: Dict[str, int] = {}

        # globals
        self.global_symbols = set()

        # relocations (offset, relocation)
        self.relocations: List[Tuple[int, Relocation]] = []

    # ----------------------------
    # Entry
    # ----------------------------

    def assemble_to_object(self, source: str) -> ObjectFile:
        self.reset()

        # 1. Lex + parse
        tokens = Lexer().tokenize(source)
        nodes = Parser(tokens).parse()

        # 2. Semantic validation
        SemanticAnalyzer().validate(nodes)

        # 3. First pass: collect labels
        self._first_pass(nodes)

        # 4. Second pass: encode
        self._second_pass(nodes)

        # 5. Build symbol table
        symbols = self._build_symbols()

        return ObjectFile(
            text=bytes(self.text),
            data=bytes(self.data),
            symbols=symbols,
            relocations=self.relocations,
        )

    # ----------------------------
    # First pass (label offsets)
    # ----------------------------

    def _first_pass(self, nodes):
        text_pc = 0

        for node in nodes:
            if isinstance(node, Directive):
                self._handle_directive_first(node)

            elif isinstance(node, Label):
                self._define_label(node.name, text_pc)

            elif isinstance(node, Instruction):
                if self.section == "text":
                    text_pc += 4

    def _handle_directive_first(self, d: Directive):
        if d.name == ".text":
            self.section = "text"

        elif d.name == ".data":
            self.section = "data"

        elif d.name == ".bss":
            self.section = "bss"

        elif d.name == ".zero":
            if self.section == "bss":
                size = int(d.args[0], 0)

                # align
                if self.bss_size % 8 != 0:
                    self.bss_size += 8 - (self.bss_size % 8)

                self.bss_size += size

        elif d.name == ".ascii":
            if self.section == "data":
                s = d.args[0]
                self.data.extend(s.encode("utf-8"))

        elif d.name == ".global":
            self.global_symbols.add(d.args[0])

    def _define_label(self, name, text_pc):
        if self.section == "text":
            self.text_labels[name] = text_pc

        elif self.section == "data":
            self.data_labels[name] = len(self.data)

        elif self.section == "bss":
            self.bss_labels[name] = self.bss_size

    # ----------------------------
    # Second pass (encode)
    # ----------------------------

    def _second_pass(self, nodes):
        encoder = Encoder()

        pc = 0

        for node in nodes:
            if isinstance(node, Directive):
                self._handle_directive_second(node)

            elif isinstance(node, Instruction):
                if self.section != "text":
                    continue

                enc = self._encode_instruction(node, encoder)

                offset = len(self.text)
                self.text += enc.value.to_bytes(4, "little")

                if enc.relocation:
                    self.relocations.append((offset, enc.relocation))

                pc += 4

            elif isinstance(node, Label):
                continue

    def _handle_directive_second(self, d: Directive):
        if d.name == ".text":
            self.section = "text"

        elif d.name == ".data":
            self.section = "data"

        elif d.name == ".bss":
            self.section = "bss"

        elif d.name == ".ascii":
            if self.section == "data":
                self.data.extend(d.args[0].encode("utf-8"))

        elif d.name == ".zero":
            # nothing to emit
            pass

    # ----------------------------
    # Instruction encoding
    # ----------------------------

    def _encode_instruction(self, inst: Instruction, encoder: Encoder) -> EncodedInstruction:
        op = inst.op
        args = inst.args

        def reg(x): return encoder.reg(x.name)
        def imm(x): return x.value

        # ----------------------------
        # Arithmetic
        # ----------------------------

        if op == "ADD":
            return encoder.add(reg(args[0]), reg(args[1]), imm(args[2]))

        elif op == "SUB":
            return encoder.sub(reg(args[0]), reg(args[1]), imm(args[2]))

        elif op == "MOV":
            return encoder.mov(reg(args[0]), reg(args[1]))

        # ----------------------------
        # Memory
        # ----------------------------

        elif op == "LDR":
            mem: MemoryOperand = args[1]
            return encoder.ldr(reg(args[0]), encoder.reg(mem.base), mem.offset)

        elif op == "STR":
            mem: MemoryOperand = args[1]
            return encoder.str(reg(args[0]), encoder.reg(mem.base), mem.offset)

        # ----------------------------
        # Branch
        # ----------------------------

        elif op == "B":
            return encoder.b(args[0].name)

        elif op == "BL":
            return encoder.bl(args[0].name)

        elif op.startswith("B."):
            cond = op.split(".")[1]
            return encoder.b_cond(cond, args[0].name)

        # ----------------------------
        # Compare
        # ----------------------------

        elif op == "CMP":
            if isinstance(args[1], Immediate):
                return encoder.cmp_imm(reg(args[0]), imm(args[1]))
            else:
                return encoder.cmp_reg(reg(args[0]), reg(args[1]))

        # ----------------------------
        # Return
        # ----------------------------

        elif op == "RET":
            if len(args) == 0:
                return encoder.ret()
            return encoder.ret(reg(args[0]))

        # ----------------------------
        # SVC
        # ----------------------------

        elif op == "SVC":
            if len(args) == 0:
                return encoder.svc(0)
            return encoder.svc(imm(args[0]))

        # ----------------------------
        # ADR / ADRP
        # ----------------------------

        elif op == "ADR":
            return encoder.adr(reg(args[0]), args[1].name)

        elif op == "ADRP":
            return encoder.adrp(reg(args[0]), args[1].name)

        # ----------------------------
        # STP / LDP
        # ----------------------------

        elif op == "STP":
            mem: MemoryOperand = args[2]
            return encoder.stp_pre(
                reg(args[0]),
                reg(args[1]),
                encoder.reg(mem.base),
                mem.offset
            )

        elif op == "LDP":
            mem: MemoryOperand = args[2]
            return encoder.ldp_post(
                reg(args[0]),
                reg(args[1]),
                encoder.reg(mem.base),
                mem.offset
            )

        else:
            raise Exception(f"Unsupported instruction: {op}")

    # ----------------------------
    # Symbol table
    # ----------------------------

    def _build_symbols(self):
        symbols = {}

        # section base offsets (relative for linker)
        text_base = 0
        data_base = len(self.text)
        bss_base = data_base + len(self.data)

        # text
        for name, offset in self.text_labels.items():
            symbols[name] = Symbol(
                name=name,
                addr=text_base + offset,
                section="text",
                global_=(name in self.global_symbols)
            )

        # data
        for name, offset in self.data_labels.items():
            symbols[name] = Symbol(
                name=name,
                addr=data_base + offset,
                section="data",
                global_=(name in self.global_symbols)
            )

        # bss
        for name, offset in self.bss_labels.items():
            symbols[name] = Symbol(
                name=name,
                addr=bss_base + offset,
                section="bss",
                global_=(name in self.global_symbols)
            )

        return symbols
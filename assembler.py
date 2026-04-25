import re
from typing import List, Dict

from ir import Label, Instruction
from symbols import SymbolTable
from encoder import Encoder
import parser

def reg_to_int(reg: str) -> int:
    if reg == "SP":
        return 31
    if not reg.startswith("X"):
        raise ValueError(f"Invalid register {reg}")
    return int(reg[1:])

def parse_imm(val: str) -> int:
    if val.startswith('#'):
        return int(val[1:], 0)
    raise ValueError(f"Invalid immediate {val}")

def parse_mem_operand(token_list):
    """
    Parses: [Xn, #imm]
    Returns: (rn, imm)
    """
    text = "".join(token_list)

    m = re.match(r"\[(X\d+)(?:,#(\d+))?\]", text)
    if not m:
        raise ValueError(f"Invalid memory operand: {text}")

    rn = reg_to_int(m.group(1))
    imm = int(m.group(2)) if m.group(2) else 0

    return rn, imm

def parse_mem_operand_full(tokens):
    """
    Supports:
      [Xn, #imm]
      [Xn, #imm]!
      [Xn], #imm
    Returns:
      (rn, imm, mode)
    mode ∈ {"offset", "pre", "post"}
    """
    text = "".join(tokens)
    # pre index
    m = re.match(r"\[(X\d+),#(-?\d+)\]!", text)
    if m:
        return reg_to_int(m.group(1)), int(m.group(2)), "pre"

    # Post-index
    m = re.match(r"\[(X\d+)\],#(-?\d+)", text)
    if m:
        return reg_to_int(m.group(1)), int(m.group(2)), "post"

    # Unsigned offset
    m = re.match(r"\[(X\d+)(?:,#(\d+))?\]", text)
    if m:
        imm = int(m.group(2)) if m.group(2) else 0
        return reg_to_int(m.group(1)), imm, "offset"

    raise ValueError(f"Invalid memory operand: {text}")

COND_MAP = {
    "EQ": 0,
    "NE": 1,
    "GE": 10,
    "LT": 11,
    "GT": 12,
    "LE": 13,
}

class Assembler:
    def __init__(self):
        self.labels: Dict[str, int] = {} # text_labels
        self.instructions: List[str] = [] # text_instructions
        self.data_labels = {}
        self.data_bytes = bytearray()
        
    def assemble(self, source: str):
        lines = source.splitlines()
        nodes = parser.parse(lines)
        symtab = SymbolTable()
        encoder = Encoder()
        pc = 0
        
        # pass 1: assign label offsets
        for node in nodes:
            if isinstance(node, Label):
                symtab.define(node.name, pc)
            elif isinstance(node, Instruction):
                pc += 4
        # pass 2: encode
        for node in nodes:
            if isinstance(node, Instruction):
                self.encode_instruction(node, encoder)
                
        # Layout
        layout = Layout().compute(len(encoder.code), 0)
        
        # Fix symbol addresses with base
        for name in symtab.symbols:
            symtab.symbols[name] += layout['text_base']
        
        # Apply relocations
        apply_relocations(encoder.code, encoder.relocations, symtab, layout)    

        # ELF
        elf = ELFBuilder(bytes(encoder.code)).build()
        
        return elf

    def preprocess(self, code: str):
        section = "text"

        lines = code.splitlines()
        for line in lines:
            line = line.split("//")[0].strip()
            if not line:
                continue
            
            if line == ".data":
                section = "data"
                continue
            elif line == ".text":
                section = "text"
                continue

            if section == "text":
                self.instructions.append(line)
            else:
                self.handle_data_line(line)


    def handle_data_line(self, line: str):
        if line.endswith(':'):
            label = line[:-1]
            self.data_labels[label] = len(self.data_bytes)
            return
        # Example:
        # msg:
        #     .ascii "Hello!"'
        # will add chars Hello! into data_bytes
        if line.startswith(".ascii"):
            # start from " and captures every character until it hits the closing ".
            s = re.findall(r'"(.*)"', line)[0]
            # encode: "Hello!" becomes: [72, 101, 108, 108, 111, 33]
            # utf-8 is 100% compatible with ascii for the first 128 chars, so this works for basic ascii.
            self.data_bytes.extend(s.encode('utf-8'))

    def resolve_label(self, label, pc):
        if label in self.labels:
            return self.labels[label]
        elif label in self.data_labels:
            return self.data_base + self.data_labels[label]
        else:
            raise ValueError(f"Undefined label {label}")

    def first_pass(self):
        pc = 0
        new_instructions = []
        
        for line in self.instructions:
            if line.endswith(":"):
                label = line[:-1]
                self.labels[label] = pc
            else:
                new_instructions.append(line)
                pc += 4  # each instruction is 4 bytes

        self.instructions = new_instructions

    def second_pass(self) -> List[int]:
        machine_code = []
        pc = 0
        
        for line in self.instructions:
            # \s: A special sequence that matches any whitespace character,
            # including spaces, tabs, and newlines.
            tokens = re.split(r'[,\s]+', line)
            op = tokens[0].upper()
            
            if op == "ADD":
                rd = reg_to_int(tokens[1])
                rn = reg_to_int(tokens[2])
                imm = parse_imm(tokens[3])
                mc = encode_add(rd, rn, imm)
            elif op == "SUB":
                rd = reg_to_int(tokens[1])
                rn = reg_to_int(tokens[2])
                imm = parse_imm(tokens[3])
                mc = encode_sub(rd, rn, imm)
            elif op == "MOV":
                rd = reg_to_int(tokens[1])
                rn = reg_to_int(tokens[2])
                mc = encode_mov(rd, rn)
            
            #Instruction | PC   | Address
            #start:      | 0x00 | (label stored as 0)
            #MOV X0, X1  | 0x | 0x0C |
            #B start     | 0x10 | (target = 0, offset = (0 - 0x10) // 4 = -4)
            elif op == "B":
                label = tokens[1]
                if label not in self.labels:
                    raise ValueError(f"Undefined label {label}")
                target = self.labels[label]
                offset = (target - pc) // 4
                mc = encode_b(offset)

            elif op == "BL":
                label = tokens[1]
                target = self.labels[label]
                # for full correctness, we can fix PC semantics globally later.
                offset = (target - pc) // 4 # real arm: target - (pc + 4)
                mc = encode_bl(offset)

            elif op == "RET":
                if len(tokens) == 1:
                    rn = 30  # default LR
                else:
                    rn = reg_to_int(tokens[1])
                mc = encode_ret(rn)

            elif op == "LDR":
                rt = reg_to_int(tokens[1])
                # tokens[2:] contains [Xn, #imm]
                rn, imm, mode = parse_mem_operand_full(tokens[2:])
                if mode == "offset":
                    mc = encode_ldr(rt, rn, imm)
                elif mode == "pre":
                    mc = encode_ldr_pre(rt, rn, imm)
                elif mode == "post":
                    mc = encode_ldr_post(rt, rn, imm)

            elif op == "STR":
                rt = reg_to_int(tokens[1])
                rn, imm, mode = parse_mem_operand_full(tokens[2:])
                if mode == "offset":
                    mc = encode_str(rt, rn, imm)
                elif mode == "pre":
                    mc = encode_str_pre(rt, rn, imm)
                elif mode == "post":
                    mc = encode_str_post(rt, rn, imm)
                    
            elif op == "STP":
                rt1 = reg_to_int(tokens[1])
                rt2 = reg_to_int(tokens[2])
                rn, imm, mode = parse_mem_operand_full(tokens[3:])
                if mode != "pre":
                    raise ValueError("STP must use pre-index in this ABI helper")
                mc = encode_stp_pre(rt1, rt2, rn, imm)

            elif op == "LDP":
                rt1 = reg_to_int(tokens[1])
                rt2 = reg_to_int(tokens[2])
                rn, imm, mode = parse_mem_operand_full(tokens[3:])
                if mode != "post":
                    raise ValueError("LDP must use post-index in this ABI helper")
                mc = encode_ldp_post(rt1, rt2, rn, imm)

            elif op == "CMP":
                rn = reg_to_int(tokens[1])

                if tokens[2].startswith("#"):
                    imm = parse_imm(tokens[2])
                    mc = encode_cmp_imm(rn, imm)
                else:
                    rm = reg_to_int(tokens[2])
                    mc = encode_cmp_reg(rn, rm)

            elif op.startswith("B."):
                cond_str = op.split(".")[1].upper()

                if cond_str not in COND_MAP:
                    raise ValueError(f"Unknown condition {cond_str}")
                cond = COND_MAP[cond_str]
                label = tokens[1]
                target = self.labels[label]
                offset = (target - pc) // 4
                mc = encode_b_cond(cond, offset)

            elif op == "SVC":
                if len(tokens) > 1:
                    imm = parse_imm(tokens[1])
                else:
                    imm = 0
                mc = encode_svc(imm)
            
            elif op == "ADR":
                rd = reg_to_int(tokens[1])
                label = tokens[2]
                target = self.resolve_label(label, pc)
                offset = target - pc
                mc = encode_adr(rd, offset)

            elif op == "ADRP":
                rd = reg_to_int(tokens[1])
                label = tokens[2]
                target = self.resolve_label(label, pc)
                pc_page = pc & ~0xFFF
                target_page = target & ~0xFFF
                offset = target_page - pc_page

                mc = encode_adrp(rd, offset)
    
            else:
                raise ValueError(f"Unknown instruction {op}")

            machine_code.append(mc)
            pc += 4

        return machine_code

    def assemble(self, code: str) -> List[int]:
        self.preprocess(code)
        self.first_pass()
        return self.second_pass()

# ----------------------------
# Example Usage
# ----------------------------

if __name__ == "__main__":
    asm = """
        start:
            MOV X0, X1
            ADD X2, X0, #10
            SUB X3, X2, #5
            B start
    """

    assembler = Assembler()
    machine_code = assembler.assemble(asm)

    for i, code in enumerate(machine_code):
        print(f"{i*4:04x}: {code:08x}")

from dataclasses import dataclass

@dataclass
#rename to RelocationEntry later
class Relocation:
    offset: int # where in code
    symbol: str #label name
    type: str # e.g. "B", "BL", "ADRP", "ADR"
    
def apply_relocations(code, relocs, symtab, layout):
    for r in relocs:
        target = symtab.resolve(r.symbol)
        if r.type == "ADR":
            pc = layout['text_base'] + r.offset
            offset = target - pc
            instr = encode_adr_fixed(offset)
            code[r.offset:r.offset + 4] = instr.to_bytes(4, byteorder='little') 
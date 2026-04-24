import struct

class ELFBuilder:
    def __init__(self, code_bytes: bytes):
        self.code = code_bytes
        
    def build(self)->bytes:
        BASE_ADDR = 0x400000
        # Offsets
        ELF_HEADER_SIZE = 64
        PHDR_SIZE = 56 # size of one program header

        code_offset = ELF_HEADER_SIZE + PHDR_SIZE
        entry_addr = BASE_ADDR + code_offset
        
        # ----------------------------
        # ELF Header
        # ----------------------------
        e_ident = b'\x7fELF'          # Magic
        e_ident += b'\x02'            # 64-bit
        e_ident += b'\x01'            # little endian
        e_ident += b'\x01'            # ELF version
        e_ident += b'\x00' * 9        # padding

        elf_header = struct.pack(
            "<16sHHIQQQIHHHHHH",
            e_ident,
            2,              # e_type (EXEC)
            183,            # e_machine (AArch64)
            1,              # e_version
            entry_addr,     # e_entry
            ELF_HEADER_SIZE, # e_phoff
            0,              # e_shoff
            0,              # e_flags
            ELF_HEADER_SIZE,
            PHDR_SIZE,
            1,              # number of program headers
            0,              # section headers
            0,
            0
        )
        
        # ----------------------------
        # Program Header
        # ----------------------------
        p_type = 1  # PT_LOAD
        p_flags = 5 # RX

        phdr = struct.pack(
            "<IIQQQQQQ",
            p_type,
            p_flags,
            0,                      # file offset
            BASE_ADDR,              # virtual addr
            BASE_ADDR,              # physical addr
            code_offset + len(self.code),
            code_offset + len(self.code),
            0x1000                  # alignment
        )
        
        # ----------------------------
        # Final Binary
        # ----------------------------
        padding = b'\x00' * (code_offset - len(elf_header) - len(phdr))

        return elf_header + phdr + padding + self.code

def to_bytes(machine_code):
    return b''.join(struct.pack("<I", instr) for instr in machine_code)

if __name__ == "__main__":
    asm = """
        start:
            MOV X0, X0
            B start
    """

    #assembler = Assembler()
    #machine_code = assembler.assemble(asm)

    #code_bytes = to_bytes(machine_code)

    #elf = ELFBuilder(code_bytes).build()

    #with open("program", "wb") as f:
    #    f.write(elf)

    #print("ELF binary written to 'program'")
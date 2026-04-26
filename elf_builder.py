# elf_writer.py

import struct

# ELF constants
ET_REL = 1
EM_AARCH64 = 183

SHT_NULL     = 0
SHT_PROGBITS = 1
SHT_SYMTAB   = 2
SHT_STRTAB   = 3
SHT_RELA     = 4
SHT_NOBITS   = 8

SHF_ALLOC = 0x2
SHF_EXECINSTR = 0x4
SHF_WRITE = 0x1

# Relocation types
R_AARCH64_CALL26 = 283
R_AARCH64_CONDBR19 = 280
R_AARCH64_ADR_PREL_LO21 = 274
R_AARCH64_ADR_PREL_PG_HI21 = 275
R_AARCH64_ADD_ABS_LO12_NC = 277


def align(x, a):
    return (x + a - 1) & ~(a - 1)


class ELFWriter:

    def __init__(self, obj):
        self.obj = obj

    def write(self, path):
        # ----------------------------
        # Build string tables
        # ----------------------------

        strtab = b"\x00"
        sym_index = {}

        def add_str(s):
            nonlocal strtab
            off = len(strtab)
            strtab += s.encode() + b"\x00"
            return off

        # ----------------------------
        # Symbols
        # ----------------------------

        symbols = []

        # first symbol = NULL
        symbols.append((0, 0, 0, 0, 0, 0))

        for i, (name, sym) in enumerate(self.obj.symbols.items(), start=1):
            name_off = add_str(name)

            shndx = {
                "text": 1,
                "data": 2,
                "bss": 3
            }[sym.section]

            info = 0x10 if sym.global_ else 0x0

            symbols.append((
                name_off,
                info,
                0,
                shndx,
                sym.addr,
                0
            ))

            sym_index[name] = i

        # ----------------------------
        # Relocations (.rela.text)
        # ----------------------------

        rela = b""

        for offset, reloc in self.obj.relocations:
            sym_i = sym_index[reloc.symbol]

            r_type = {
                "B": R_AARCH64_CALL26,
                "BL": R_AARCH64_CALL26,
                "B.EQ": R_AARCH64_CONDBR19,
                "ADR": R_AARCH64_ADR_PREL_LO21,
                "ADRP": R_AARCH64_ADR_PREL_PG_HI21,
                "ADD_PAGEOFF": R_AARCH64_ADD_ABS_LO12_NC
            }[reloc.type]

            r_info = (sym_i << 32) | r_type

            rela += struct.pack("<QQq", offset, r_info, 0)

        # ----------------------------
        # Section name table
        # ----------------------------

        shstrtab = b"\x00.text\x00.data\x00.bss\x00.rela.text\x00.symtab\x00.strtab\x00.shstrtab\x00"

        def shname(name):
            return shstrtab.index(name.encode())

        # ----------------------------
        # Layout
        # ----------------------------

        offset = 0x40  # after ELF header

        text_off = offset
        offset += len(self.obj.text)

        data_off = offset
        offset += len(self.obj.data)

        rela_off = align(offset, 8)
        offset = rela_off + len(rela)

        symtab_off = align(offset, 8)
        symtab_size = len(symbols) * 24
        offset = symtab_off + symtab_size

        strtab_off = offset
        offset += len(strtab)

        shstrtab_off = offset
        offset += len(shstrtab)

        shoff = align(offset, 8)

        # ----------------------------
        # Write file
        # ----------------------------

        with open(path, "wb") as f:

            # ELF header
            f.write(struct.pack(
                "<16sHHIQQQIHHHHHH",
                b"\x7fELF\x02\x01\x01\x00" + b"\x00"*8,
                ET_REL,
                EM_AARCH64,
                1,
                0,
                0,
                shoff,
                0,
                64,
                0,
                0,
                64,
                8,
                7
            ))

            # sections
            f.seek(text_off)
            f.write(self.obj.text)

            f.seek(data_off)
            f.write(self.obj.data)

            f.seek(rela_off)
            f.write(rela)

            f.seek(symtab_off)
            for s in symbols:
                f.write(struct.pack("<IBBHQQ", *s))

            f.seek(strtab_off)
            f.write(strtab)

            f.seek(shstrtab_off)
            f.write(shstrtab)

            # ----------------------------
            # Section headers
            # ----------------------------

            f.seek(shoff)

            def sh(name, type_, flags, addr, off, size, link, info, align_, entsize):
                f.write(struct.pack("<IIQQQQIIQQ",
                    shname(name), type_, flags, addr, off,
                    size, link, info, align_, entsize
                ))

            # NULL
            sh("", 0, 0, 0, 0, 0, 0, 0, 0, 0)

            # .text
            sh(".text", SHT_PROGBITS, SHF_ALLOC|SHF_EXECINSTR,
               0, text_off, len(self.obj.text), 0, 0, 4, 0)

            # .data
            sh(".data", SHT_PROGBITS, SHF_ALLOC|SHF_WRITE,
               0, data_off, len(self.obj.data), 0, 0, 8, 0)

            # .bss
            sh(".bss", SHT_NOBITS, SHF_ALLOC|SHF_WRITE,
               0, 0, self.obj.bss_size, 0, 0, 8, 0)

            # .rela.text
            sh(".rela.text", SHT_RELA, 0,
               0, rela_off, len(rela), 5, 1, 8, 24)

            # .symtab
            sh(".symtab", SHT_SYMTAB, 0,
               0, symtab_off, symtab_size, 6, 1, 8, 24)

            # .strtab
            sh(".strtab", SHT_STRTAB, 0,
               0, strtab_off, len(strtab), 0, 0, 1, 0)

            # .shstrtab
            sh(".shstrtab", SHT_STRTAB, 0,
               0, shstrtab_off, len(shstrtab), 0, 0, 1, 0)
# linker.py

class Linker:
    def link(self, objects):
        text = bytearray()
        data = bytearray()

        global_symtab = {}
        relocations = []

        text_offset = 0
        data_offset = 0

        # ----------------------------
        # Merge sections
        # ----------------------------
        for obj in objects:
            # merge text
            text_base = text_offset
            text.extend(obj.text)

            # merge data
            data_base = data_offset
            data.extend(obj.data)

            # remap symbols
            for name, sym in obj.symbols.items():
                if sym.section == "text":
                    addr = text_base + sym.addr
                else:
                    addr = len(text) + data_base + sym.addr

                if sym.global_:
                    if name in global_symtab:
                        raise ValueError(f"Duplicate symbol {name}")
                    global_symtab[name] = addr

            # remap relocations
            for r in obj.relocations:
                relocations.append((
                    r,
                    text_base if r.section == "text" else len(text) + data_base
                ))

            text_offset += len(obj.text)
            data_offset += len(obj.data)

        # ----------------------------
        # Apply relocations
        # ----------------------------
        for r, base in relocations:
            if r.symbol not in global_symtab:
                raise ValueError(f"Undefined symbol {r.symbol}")

            target = global_symtab[r.symbol]
            loc = base + r.offset

            self.apply_relocation(text, loc, target, r.type)

        # ----------------------------
        # Build final ELF
        # ----------------------------
        return ELFBuilder(bytes(text + data)).build()
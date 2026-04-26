class Layout:
    def __init__(self, base = 0x400000):
        self.base = base
        
    def compute(self, text_size, data_size):
        text_offset = 64 + 56
        data_offset = text_offset + text_size
        return {
            "text_offset": text_offset,
            "data_offset": data_offset,
            "text_base": self.base + text_offset,
            "data_base": self.base + data_offset,
            "bss_base": self.base + data_offset + len(data_size)
        }
from typing import Dict, List

class SymbolTable:
    def __init__(self):
        self.symbols: Dict[str, int] = {}
        
    def define(self, name, addr):
        if name in self.symbols:
            raise ValueError(f"Symbol {name} already defined")
        self.symbols[name] = addr
        
    def resolve(self, name):
        if name not in self.symbols:
            raise ValueError(f"Undefined symbol: {name}")
        return self.symbols[name]
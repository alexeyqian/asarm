# object_file.py

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class Symbol:
    name: str
    addr: int
    section: str   # "text" or "data"
    global_: bool

@dataclass
class Relocation:
    offset: int
    symbol: str
    type: str      # "B", "BL", "ADR"
    section: str   # where relocation lives

@dataclass
class ObjectFile:
    text: bytes
    data: bytes
    symbols: Dict[str, Symbol]
    relocations: List[Relocation]
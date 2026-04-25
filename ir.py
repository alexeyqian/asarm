# Intermediate Representation
from dataclasses import dataclass
from typing import List

@dataclass
class Instruction:
    op: str
    args: List[str]
    line: int
    
@dataclass
class Label:
    name: str
    
@dataclass
class Directive:
    name: str
    args: List[str]

from typing import Union
Node = Union[Instruction, Label, Directive]
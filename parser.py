import re
from ir import Label, Directive, Instruction

def parse(lines):
    nodes = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        if line.endswith(':'):
            nodes.append(Label(line[:-1]))
        elif line.startswith('.'):
            parts = line.split()
            nodes.append(Directive(parts[0], parts[1:]))
        else:
            parts = re.split(r"[,\s]+", line)
            nodes.append(Instruction(parts[0], parts[1:], i))

    return nodes

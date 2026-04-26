# semantic.py

from parser import (
    Instruction,
    Register,
    Immediate,
    Identifier,
    MemoryOperand
)


class SemanticError(Exception):
    pass


class SemanticAnalyzer:

    def validate(self, nodes):
        for node in nodes:
            if isinstance(node, Instruction):
                self._validate_instruction(node)

    # ----------------------------
    # Instruction validation
    # ----------------------------

    def _validate_instruction(self, inst: Instruction):
        op = inst.op
        args = inst.args

        if op in ("ADD", "SUB"):
            self._expect_len(inst, 3)
            self._expect_reg(args[0], inst)
            self._expect_reg(args[1], inst)
            self._expect_imm(args[2], inst)

        elif op == "MOV":
            self._expect_len(inst, 2)
            self._expect_reg(args[0], inst)

            if not isinstance(args[1], Register):
                raise SemanticError(f"{inst.line}: MOV requires register source")

        elif op in ("LDR", "STR"):
            self._expect_len(inst, 2)
            self._expect_reg(args[0], inst)
            self._expect_mem(args[1], inst)

        elif op in ("B", "BL"):
            self._expect_len(inst, 1)
            self._expect_label(args[0], inst)

        elif op.startswith("B."):
            self._expect_len(inst, 1)
            self._expect_label(args[0], inst)

        elif op == "CMP":
            self._expect_len(inst, 2)
            self._expect_reg(args[0], inst)

            if not isinstance(args[1], (Register, Immediate)):
                raise SemanticError(f"{inst.line}: CMP invalid operand")

        elif op == "RET":
            if len(args) > 1:
                raise SemanticError(f"{inst.line}: RET takes 0 or 1 operand")
            if len(args) == 1:
                self._expect_reg(args[0], inst)

        elif op == "SVC":
            if len(args) > 1:
                raise SemanticError(f"{inst.line}: SVC takes 0 or 1 operand")
            if len(args) == 1:
                self._expect_imm(args[0], inst)

        elif op in ("ADR", "ADRP"):
            self._expect_len(inst, 2)
            self._expect_reg(args[0], inst)
            self._expect_label(args[1], inst)

        elif op in ("STP", "LDP"):
            self._expect_len(inst, 3)
            self._expect_reg(args[0], inst)
            self._expect_reg(args[1], inst)
            self._expect_mem(args[2], inst)

        else:
            raise SemanticError(f"{inst.line}: Unknown instruction {op}")

    # ----------------------------
    # Helpers
    # ----------------------------

    def _expect_len(self, inst, n):
        if len(inst.args) != n:
            raise SemanticError(
                f"{inst.line}: {inst.op} expects {n} operands, got {len(inst.args)}"
            )

    def _expect_reg(self, arg, inst):
        if not isinstance(arg, Register):
            raise SemanticError(f"{inst.line}: Expected register")

    def _expect_imm(self, arg, inst):
        if not isinstance(arg, Immediate):
            raise SemanticError(f"{inst.line}: Expected immediate")

    def _expect_label(self, arg, inst):
        if not isinstance(arg, Identifier):
            raise SemanticError(f"{inst.line}: Expected label")

    def _expect_mem(self, arg, inst):
        if not isinstance(arg, MemoryOperand):
            raise SemanticError(f"{inst.line}: Expected memory operand")
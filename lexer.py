# lexer.py

from dataclasses import dataclass
from typing import List, Iterator, Optional
import re


# ----------------------------
# Token definition
# ----------------------------

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


# ----------------------------
# Lexer
# ----------------------------

class Lexer:

    TOKEN_SPEC = [
        ("COMMENT",   r"//.*"),
        ("STRING",    r'"([^"\\]|\\.)*"'),
        ("DIRECTIVE", r"\.[a-zA-Z_][a-zA-Z0-9_]*"),
        ("LABEL",     r"[a-zA-Z_][a-zA-Z0-9_]*:"),
        ("REGISTER",  r"\b(X[0-9]+|SP)\b"),
        ("IMMEDIATE", r"#-?(0x[0-9a-fA-F]+|\d+)"),
        ("IDENT",     r"[a-zA-Z_][a-zA-Z0-9_]*"),
        ("COMMA",     r","),
        ("LBRACKET",  r"\["),
        ("RBRACKET",  r"\]"),
        ("EXCL",      r"!"),
        ("COLON",     r":"),
        ("SKIP",      r"[ \t]+"),
        ("NEWLINE",   r"\n"),
    ]

    def __init__(self):
        self.regex = re.compile(
            "|".join(f"(?P<{name}>{pattern})" for name, pattern in self.TOKEN_SPEC)
        )

    # ----------------------------
    # Main tokenize function
    # ----------------------------

    def tokenize(self, code: str) -> List[Token]:
        tokens: List[Token] = []

        line_num = 1
        line_start = 0

        for match in self.regex.finditer(code):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start

            if kind == "NEWLINE":
                line_num += 1
                line_start = match.end()
                continue

            elif kind == "SKIP":
                continue

            elif kind == "COMMENT":
                continue

            elif kind == "LABEL":
                # strip trailing ':'
                value = value[:-1]
                tokens.append(Token("LABEL", value, line_num, column))

            else:
                tokens.append(Token(kind, value, line_num, column))

        return tokens


# ----------------------------
# Utility: stream interface
# ----------------------------

class TokenStream:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def next(self) -> Optional[Token]:
        tok = self.peek()
        if tok:
            self.pos += 1
        return tok

    def expect(self, token_type: str) -> Token:
        tok = self.next()
        if not tok or tok.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {tok}")
        return tok

    def match(self, token_type: str) -> Optional[Token]:
        tok = self.peek()
        if tok and tok.type == token_type:
            return self.next()
        return None
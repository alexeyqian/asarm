import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from lexer import Lexer, TokenStream, Token


def test_tokenize_basic_and_comments_and_labels():
    code = """start:
.data
MOV X0, X1 // this is a comment
"""
    lx = Lexer()
    toks = lx.tokenize(code)

    types = [t.type for t in toks]
    vals = [t.value for t in toks]
    lines = [t.line for t in toks]

    assert types[0] == "LABEL" and vals[0] == "start" and lines[0] == 1
    assert types[1] == "DIRECTIVE" and vals[1] == ".data" and lines[1] == 2
    # MOV X0 , X1 -> IDENT, REGISTER, COMMA, REGISTER
    assert types[2:] == ["IDENT", "REGISTER", "COMMA", "REGISTER"]
    assert vals[2] == "MOV" and vals[3] == "X0" and vals[4] == "," and vals[5] == "X1"


def test_string_and_immediate_tokens():
    code = 'msg: .ascii "Hello\\"World"\nLDR X2, [X3],#16\nSVC #0x10\n'
    lx = Lexer()
    toks = lx.tokenize(code)

    # find STRING token
    string_tokens = [t for t in toks if t.type == 'STRING']
    assert len(string_tokens) == 1
    assert 'Hello' in string_tokens[0].value

    imm_tokens = [t for t in toks if t.type == 'IMMEDIATE']
    # two immediates: #16 and #0x10
    assert any(t.value == '#16' for t in imm_tokens)
    assert any(t.value == '#0x10' for t in imm_tokens)


def test_brackets_excl_and_colon_and_newlines():
    code = "LABEL: STR X0, [X1, #8]!\n"
    toks = Lexer().tokenize(code)
    types = [t.type for t in toks]
    assert 'LBRACKET' in types and 'RBRACKET' in types and 'EXCL' in types
    # LABEL should appear as LABEL (without colon)
    assert toks[0].type == 'LABEL' and toks[0].value == 'LABEL'


def test_tokenstream_peek_next_expect_match():
    # create small token list
    tokens = [Token('A', 'a', 1, 0), Token('B', 'b', 1, 2)]
    ts = TokenStream(tokens)

    assert ts.peek() is tokens[0]
    assert ts.next() is tokens[0]
    assert ts.peek() is tokens[1]

    # match returns token if matches
    assert ts.match('B') is tokens[1]
    # now at end
    assert ts.peek() is None

    # expect should raise
    ts2 = TokenStream([Token('X','x',1,0)])
    with pytest.raises(SyntaxError):
        ts2.expect('Y')

    # expect returns token when correct
    ts3 = TokenStream([Token('Z','z',1,0)])
    t = ts3.expect('Z')
    assert t.type == 'Z'

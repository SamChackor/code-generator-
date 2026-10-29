"""
Lexer (Tokenizer) for Intermediate Code Generator
==================================================
Breaks raw source code strings into a sequence of strongly-typed tokens.
Handles comments, whitespace, arithmetic/relational/logical operators,
keywords, identifiers, and numeric constants.
"""

import re
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    KEYWORD_IF = auto()
    KEYWORD_ELSE = auto()
    KEYWORD_WHILE = auto()

    # Identifiers & Literals
    IDENTIFIER = auto()
    NUMBER = auto()

    # Assignment
    ASSIGN = auto()        # =

    # Arithmetic Operators
    PLUS = auto()          # +
    MINUS = auto()         # -
    MULTIPLY = auto()      # *
    DIVIDE = auto()        # /
    MODULO = auto()        # %

    # Relational Operators
    EQ = auto()            # ==
    NEQ = auto()           # !=
    LT = auto()            # <
    LTE = auto()           # <=
    GT = auto()            # >
    GTE = auto()           # >=

    # Logical Operators
    AND = auto()           # &&
    OR = auto()            # ||
    NOT = auto()           # !

    # Delimiters
    LPAREN = auto()        # (
    RPAREN = auto()        # )
    LBRACE = auto()        # {
    RBRACE = auto()        # }
    SEMICOLON = auto()     # ;

    # End of File
    EOF = auto()


class Token:
    """Represents a lexical token with its type, value, and position."""
    def __init__(self, token_type: TokenType, value, line: int, column: int):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"


class LexerError(Exception):
    """Raised when an unrecognized character or malformed token is encountered."""
    pass


class Lexer:
    """
    Lexical analyzer for the intermediate code generator language.
    Transforms raw source code text into a stream of Token objects.
    """

    KEYWORDS = {
        'if': TokenType.KEYWORD_IF,
        'else': TokenType.KEYWORD_ELSE,
        'while': TokenType.KEYWORD_WHILE
    }

    def __init__(self, source_code: str):
        self.source = source_code
        self.length = len(source_code)
        self.pos = 0
        self.line = 1
        self.col = 1

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return '\0'

    def _advance(self) -> str:
        char = self._peek()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return char

    def _skip_whitespace_and_comments(self):
        while self.pos < self.length:
            char = self._peek()

            # Skip Whitespace
            if char.isspace():
                self._advance()
                continue

            # Skip Single-line Comment: // ...
            if char == '/' and self._peek(1) == '/':
                self._advance()  # '/'
                self._advance()  # '/'
                while self.pos < self.length and self._peek() != '\n':
                    self._advance()
                continue

            # Skip Multi-line Comment: /* ... */
            if char == '/' and self._peek(1) == '*':
                self._advance()  # '/'
                self._advance()  # '*'
                while self.pos < self.length:
                    if self._peek() == '*' and self._peek(1) == '/':
                        self._advance()  # '*'
                        self._advance()  # '/'
                        break
                    self._advance()
                continue

            break

    def _tokenize_number(self) -> Token:
        start_col = self.col
        start_line = self.line
        num_str = ""
        has_dot = False

        while self.pos < self.length:
            ch = self._peek()
            if ch.isdigit():
                num_str += self._advance()
            elif ch == '.' and not has_dot and self._peek(1).isdigit():
                has_dot = True
                num_str += self._advance()
            else:
                break

        value = float(num_str) if has_dot else int(num_str)
        return Token(TokenType.NUMBER, value, start_line, start_col)

    def _tokenize_identifier_or_keyword(self) -> Token:
        start_col = self.col
        start_line = self.line
        ident_str = ""

        while self.pos < self.length:
            ch = self._peek()
            if ch.isalnum() or ch == '_':
                ident_str += self._advance()
            else:
                break

        token_type = self.KEYWORDS.get(ident_str, TokenType.IDENTIFIER)
        return Token(token_type, ident_str, start_line, start_col)

    def get_all_tokens(self):
        """Returns the full list of tokens ending with an EOF token."""
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens

    def next_token(self) -> Token:
        """Extracts and returns the next token from the input stream."""
        self._skip_whitespace_and_comments()

        if self.pos >= self.length:
            return Token(TokenType.EOF, None, self.line, self.col)

        char = self._peek()
        start_line = self.line
        start_col = self.col

        # Numbers
        if char.isdigit():
            return self._tokenize_number()

        # Identifiers & Keywords
        if char.isalpha() or char == '_':
            return self._tokenize_identifier_or_keyword()

        # Multi-character or single-character operators
        if char == '=':
            self._advance()
            if self._peek() == '=':
                self._advance()
                return Token(TokenType.EQ, "==", start_line, start_col)
            return Token(TokenType.ASSIGN, "=", start_line, start_col)

        if char == '!':
            self._advance()
            if self._peek() == '=':
                self._advance()
                return Token(TokenType.NEQ, "!=", start_line, start_col)
            return Token(TokenType.NOT, "!", start_line, start_col)

        if char == '<':
            self._advance()
            if self._peek() == '=':
                self._advance()
                return Token(TokenType.LTE, "<=", start_line, start_col)
            return Token(TokenType.LT, "<", start_line, start_col)

        if char == '>':
            self._advance()
            if self._peek() == '=':
                self._advance()
                return Token(TokenType.GTE, ">=", start_line, start_col)
            return Token(TokenType.GT, ">", start_line, start_col)

        if char == '&':
            self._advance()
            if self._peek() == '&':
                self._advance()
                return Token(TokenType.AND, "&&", start_line, start_col)
            raise LexerError(f"Unexpected character '&' at line {start_line}, col {start_col}. Did you mean '&&'?")

        if char == '|':
            self._advance()
            if self._peek() == '|':
                self._advance()
                return Token(TokenType.OR, "||", start_line, start_col)
            raise LexerError(f"Unexpected character '|' at line {start_line}, col {start_col}. Did you mean '||'?")

        # Single-character tokens
        single_char_map = {
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE,
            '%': TokenType.MODULO,
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '{': TokenType.LBRACE,
            '}': TokenType.RBRACE,
            ';': TokenType.SEMICOLON
        }

        if char in single_char_map:
            self._advance()
            return Token(single_char_map[char], char, start_line, start_col)

        # Unknown Character
        self._advance()
        raise LexerError(f"Invalid character '{char}' at line {start_line}, col {start_col}")

"""
Parser & Abstract Syntax Tree (AST) for Intermediate Code Generator
====================================================================
Builds an Abstract Syntax Tree (AST) from lexical tokens using
a standard Recursive Descent Parsing approach with precedence climbing.
"""

from lexer import Lexer, Token, TokenType, LexerError


# =====================================================================
# AST Node Definitions
# =====================================================================

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    pass


class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"ProgramNode(statements={self.statements})"


class BlockNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"BlockNode(statements={self.statements})"


class AssignNode(ASTNode):
    def __init__(self, var_name: str, expr: ASTNode):
        self.var_name = var_name
        self.expr = expr

    def __repr__(self):
        return f"AssignNode({self.var_name} = {self.expr})"


class BinOpNode(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinOpNode({self.left} {self.op} {self.right})"


class UnaryOpNode(ASTNode):
    def __init__(self, op: str, expr: ASTNode):
        self.op = op
        self.expr = expr

    def __repr__(self):
        return f"UnaryOpNode({self.op}{self.expr})"


class NumNode(ASTNode):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"NumNode({self.value})"


class VarNode(ASTNode):
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"VarNode({self.name})"


class IfNode(ASTNode):
    def __init__(self, condition: ASTNode, true_branch: ASTNode, false_branch: ASTNode = None):
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch

    def __repr__(self):
        return f"IfNode(cond={self.condition}, true={self.true_branch}, false={self.false_branch})"


class WhileNode(ASTNode):
    def __init__(self, condition: ASTNode, body: ASTNode):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return f"WhileNode(cond={self.condition}, body={self.body})"


# =====================================================================
# Parser Class
# =====================================================================

class ParserError(Exception):
    """Raised when source syntax does not conform to grammar rules."""
    pass


class Parser:
    """
    Recursive Descent Parser that parses tokens into an AST.
    Handles operator precedence:
      Logical OR -> Logical AND -> Equality -> Relational -> Additive -> Multiplicative -> Unary -> Primary
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _current_token(self) -> Token:
        return self.tokens[self.pos]

    def _peek_token(self, offset: int = 1) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def _match(self, *expected_types) -> bool:
        if self._current_token().type in expected_types:
            self.pos += 1
            return True
        return False

    def _consume(self, expected_type: TokenType, err_msg: str) -> Token:
        tok = self._current_token()
        if tok.type == expected_type:
            self.pos += 1
            return tok
        raise ParserError(f"Syntax Error at line {tok.line}, col {tok.column}: {err_msg} (got '{tok.value}')")

    def parse(self) -> ProgramNode:
        """Entry point: parses an entire program into a ProgramNode."""
        statements = []
        while self._current_token().type != TokenType.EOF:
            stmt = self._statement()
            if stmt:
                statements.append(stmt)
        return ProgramNode(statements)

    def _statement(self) -> ASTNode:
        tok = self._current_token()

        if tok.type == TokenType.SEMICOLON:
            self.pos += 1
            return None

        if tok.type == TokenType.LBRACE:
            return self._block_statement()

        if tok.type == TokenType.KEYWORD_IF:
            return self._if_statement()

        if tok.type == TokenType.KEYWORD_WHILE:
            return self._while_statement()

        if tok.type == TokenType.IDENTIFIER and self._peek_token().type == TokenType.ASSIGN:
            return self._assignment_statement()

        raise ParserError(
            f"Syntax Error at line {tok.line}, col {tok.column}: "
            f"Unexpected token '{tok.value}' where a statement was expected."
        )

    def _block_statement(self) -> BlockNode:
        self._consume(TokenType.LBRACE, "Expected '{' to start code block")
        stmts = []
        while self._current_token().type != TokenType.RBRACE and self._current_token().type != TokenType.EOF:
            stmt = self._statement()
            if stmt:
                stmts.append(stmt)
        self._consume(TokenType.RBRACE, "Expected '}' to close code block")
        return BlockNode(stmts)

    def _assignment_statement(self) -> AssignNode:
        id_tok = self._consume(TokenType.IDENTIFIER, "Expected identifier for assignment target")
        self._consume(TokenType.ASSIGN, "Expected '=' in assignment")
        expr = self._expression()

        # Semicolon is optional if right brace or EOF follows, but consumed if present
        if self._current_token().type == TokenType.SEMICOLON:
            self._consume(TokenType.SEMICOLON, "Expected ';' after assignment")

        return AssignNode(id_tok.value, expr)

    def _if_statement(self) -> IfNode:
        self._consume(TokenType.KEYWORD_IF, "Expected 'if'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after if-condition")

        true_branch = self._statement()
        false_branch = None

        if self._match(TokenType.KEYWORD_ELSE):
            false_branch = self._statement()

        return IfNode(condition, true_branch, false_branch)

    def _while_statement(self) -> WhileNode:
        self._consume(TokenType.KEYWORD_WHILE, "Expected 'while'")
        self._consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._expression()
        self._consume(TokenType.RPAREN, "Expected ')' after while-condition")

        body = self._statement()
        return WhileNode(condition, body)

    # -------------------------------------------------------------
    # Expression Grammar with Precedence Hierarchy
    # -------------------------------------------------------------

    def _expression(self) -> ASTNode:
        return self._logical_or()

    def _logical_or(self) -> ASTNode:
        node = self._logical_and()
        while self._match(TokenType.OR):
            op = "||"
            right = self._logical_and()
            node = BinOpNode(node, op, right)
        return node

    def _logical_and(self) -> ASTNode:
        node = self._equality()
        while self._match(TokenType.AND):
            op = "&&"
            right = self._equality()
            node = BinOpNode(node, op, right)
        return node

    def _equality(self) -> ASTNode:
        node = self._relational()
        while self._current_token().type in (TokenType.EQ, TokenType.NEQ):
            op_tok = self._current_token()
            self.pos += 1
            right = self._relational()
            node = BinOpNode(node, op_tok.value, right)
        return node

    def _relational(self) -> ASTNode:
        node = self._additive()
        rel_types = (TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE)
        while self._current_token().type in rel_types:
            op_tok = self._current_token()
            self.pos += 1
            right = self._additive()
            node = BinOpNode(node, op_tok.value, right)
        return node

    def _additive(self) -> ASTNode:
        node = self._multiplicative()
        while self._current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._current_token()
            self.pos += 1
            right = self._multiplicative()
            node = BinOpNode(node, op_tok.value, right)
        return node

    def _multiplicative(self) -> ASTNode:
        node = self._unary()
        while self._current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op_tok = self._current_token()
            self.pos += 1
            right = self._unary()
            node = BinOpNode(node, op_tok.value, right)
        return node

    def _unary(self) -> ASTNode:
        if self._current_token().type in (TokenType.MINUS, TokenType.NOT):
            op_tok = self._current_token()
            self.pos += 1
            operand = self._unary()
            return UnaryOpNode(op_tok.value, operand)
        return self._primary()

    def _primary(self) -> ASTNode:
        tok = self._current_token()

        if self._match(TokenType.NUMBER):
            return NumNode(tok.value)

        if self._match(TokenType.IDENTIFIER):
            return VarNode(tok.value)

        if self._match(TokenType.LPAREN):
            node = self._expression()
            self._consume(TokenType.RPAREN, "Expected ')' to close grouped expression")
            return node

        raise ParserError(f"Syntax Error at line {tok.line}, col {tok.column}: Unexpected expression term '{tok.value}'")


# =====================================================================
# AST Visualizer / Tree Printer
# =====================================================================

def format_ast(node: ASTNode, prefix: str = "", is_last: bool = True) -> str:
    """Renders the AST as an ASCII/Unicode hierarchy tree."""
    connector = "└── " if is_last else "├── "
    next_prefix = prefix + ("    " if is_last else "│   ")

    if isinstance(node, ProgramNode):
        lines = ["Program"]
        for i, stmt in enumerate(node.statements):
            last = (i == len(node.statements) - 1)
            lines.append(format_ast(stmt, prefix, last))
        return "\n".join(lines)

    elif isinstance(node, BlockNode):
        lines = [f"{prefix}{connector}Block"]
        for i, stmt in enumerate(node.statements):
            last = (i == len(node.statements) - 1)
            lines.append(format_ast(stmt, next_prefix, last))
        return "\n".join(lines)

    elif isinstance(node, AssignNode):
        lines = [f"{prefix}{connector}Assign ({node.var_name})"]
        lines.append(format_ast(node.expr, next_prefix, True))
        return "\n".join(lines)

    elif isinstance(node, BinOpNode):
        lines = [f"{prefix}{connector}BinaryOp ({node.op})"]
        lines.append(format_ast(node.left, next_prefix, False))
        lines.append(format_ast(node.right, next_prefix, True))
        return "\n".join(lines)

    elif isinstance(node, UnaryOpNode):
        lines = [f"{prefix}{connector}UnaryOp ({node.op})"]
        lines.append(format_ast(node.expr, next_prefix, True))
        return "\n".join(lines)

    elif isinstance(node, NumNode):
        return f"{prefix}{connector}Num ({node.value})"

    elif isinstance(node, VarNode):
        return f"{prefix}{connector}Var ({node.name})"

    elif isinstance(node, IfNode):
        lines = [f"{prefix}{connector}If-Statement"]
        lines.append(f"{next_prefix}├── Condition:")
        lines.append(format_ast(node.condition, next_prefix + "│   ", True))
        has_else = node.false_branch is not None
        lines.append(f"{next_prefix}{'├──' if has_else else '└──'} Then:")
        lines.append(format_ast(node.true_branch, next_prefix + ("│   " if has_else else "    "), True))
        if has_else:
            lines.append(f"{next_prefix}└── Else:")
            lines.append(format_ast(node.false_branch, next_prefix + "    ", True))
        return "\n".join(lines)

    elif isinstance(node, WhileNode):
        lines = [f"{prefix}{connector}While-Loop"]
        lines.append(f"{next_prefix}├── Condition:")
        lines.append(format_ast(node.condition, next_prefix + "│   ", True))
        lines.append(f"{next_prefix}└── Body:")
        lines.append(format_ast(node.body, next_prefix + "    ", True))
        return "\n".join(lines)

    return f"{prefix}{connector}{str(node)}"

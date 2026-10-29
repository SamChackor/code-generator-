"""
Intermediate Code Generator (3-Address Code, Quadruples, Triples & Optimizer)
=============================================================================
Translates an Abstract Syntax Tree (AST) into:
1. Standard Three-Address Code (3AC) with temporary variables (t1, t2...) and labels (L1, L2...)
2. Quadruple Table: (op, arg1, arg2, result)
3. Triple Table: (op, arg1, arg2) referencing instruction indices
4. Optimization: Constant folding, algebraic identities, and copy propagation
"""

from parser import (
    ASTNode, ProgramNode, BlockNode, AssignNode,
    BinOpNode, UnaryOpNode, NumNode, VarNode,
    IfNode, WhileNode
)


# =====================================================================
# Three-Address Code Instruction Representation
# =====================================================================

class Instruction3AC:
    """Represents a single Three-Address Code instruction."""
    def __init__(self, op: str, arg1=None, arg2=None, result=None):
        self.op = op          # '+', '-', '*', '/', '=', 'ifFalse', 'goto', 'label', etc.
        self.arg1 = arg1      # First operand or condition
        self.arg2 = arg2      # Second operand (if binary)
        self.result = result  # Target variable or jump label

    def __str__(self):
        if self.op == 'label':
            return f"{self.result}:"
        elif self.op == 'goto':
            return f"goto {self.result}"
        elif self.op == 'ifFalse':
            return f"ifFalse {self.arg1} goto {self.result}"
        elif self.op == 'if':
            return f"if {self.arg1} goto {self.result}"
        elif self.op == '=':
            return f"{self.result} = {self.arg1}"
        elif self.arg2 is not None:
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        else:
            return f"{self.result} = {self.op} {self.arg1}"

    def to_quadruple(self):
        """Returns (op, arg1, arg2, result) for quadruple table."""
        return (
            self.op,
            str(self.arg1) if self.arg1 is not None else "",
            str(self.arg2) if self.arg2 is not None else "",
            str(self.result) if self.result is not None else ""
        )


# =====================================================================
# Code Generator
# =====================================================================

class CodeGenerator:
    """
    Traverses the AST and emits 3-Address Code instructions.
    Manages temporary variable and label allocation.
    """

    def __init__(self):
        self.temp_counter = 0
        self.label_counter = 0
        self.instructions = []

    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self) -> str:
        self.label_counter += 1
        return f"L{self.label_counter}"

    def emit(self, op: str, arg1=None, arg2=None, result=None) -> Instruction3AC:
        instr = Instruction3AC(op, arg1, arg2, result)
        self.instructions.append(instr)
        return instr

    def generate(self, node: ASTNode):
        """Main driver to generate intermediate code for any AST root node."""
        if isinstance(node, ProgramNode):
            for stmt in node.statements:
                self.generate(stmt)

        elif isinstance(node, BlockNode):
            for stmt in node.statements:
                self.generate(stmt)

        elif isinstance(node, AssignNode):
            expr_res = self._generate_expr(node.expr)
            self.emit('=', arg1=expr_res, result=node.var_name)

        elif isinstance(node, IfNode):
            cond_res = self._generate_expr(node.condition)
            label_else = self.new_label()
            label_end = self.new_label() if node.false_branch else label_else

            # If condition is false, jump to else/end
            self.emit('ifFalse', arg1=cond_res, result=label_else)

            # Generate Then-branch
            self.generate(node.true_branch)

            if node.false_branch:
                self.emit('goto', result=label_end)
                self.emit('label', result=label_else)
                self.generate(node.false_branch)
                self.emit('label', result=label_end)
            else:
                self.emit('label', result=label_else)

        elif isinstance(node, WhileNode):
            label_start = self.new_label()
            label_end = self.new_label()

            self.emit('label', result=label_start)
            cond_res = self._generate_expr(node.condition)
            self.emit('ifFalse', arg1=cond_res, result=label_end)

            self.generate(node.body)
            self.emit('goto', result=label_start)
            self.emit('label', result=label_end)

    def _generate_expr(self, node: ASTNode) -> str:
        """Evaluates an expression and returns the variable or literal name holding the result."""
        if isinstance(node, NumNode):
            return str(node.value)

        elif isinstance(node, VarNode):
            return node.name

        elif isinstance(node, UnaryOpNode):
            sub_res = self._generate_expr(node.expr)
            temp = self.new_temp()
            self.emit(node.op, arg1=sub_res, result=temp)
            return temp

        elif isinstance(node, BinOpNode):
            left_res = self._generate_expr(node.left)
            right_res = self._generate_expr(node.right)
            temp = self.new_temp()
            self.emit(node.op, arg1=left_res, arg2=right_res, result=temp)
            return temp

        raise ValueError(f"Unknown expression node type: {type(node)}")

    # -------------------------------------------------------------
    # Quadruple and Triple Representation Builders
    # -------------------------------------------------------------

    def get_quadruples(self):
        """
        Returns list of (index, op, arg1, arg2, result)
        Format: (Index, Operator, Operand 1, Operand 2, Result)
        """
        quads = []
        for idx, instr in enumerate(self.instructions):
            op, a1, a2, res = instr.to_quadruple()
            quads.append((idx, op, a1, a2, res))
        return quads

    def get_triples(self):
        """
        Returns list of (index, op, arg1, arg2)
        In Triples, temporary names (t1, t2...) are replaced by pointer references
        to the instruction row index that produced them, e.g. (0), (1).
        """
        triples = []
        temp_to_index = {}

        for idx, instr in enumerate(self.instructions):
            arg1_str = str(instr.arg1) if instr.arg1 is not None else ""
            arg2_str = str(instr.arg2) if instr.arg2 is not None else ""

            # Substitute temporary references with (row_index)
            if arg1_str in temp_to_index:
                arg1_str = f"({temp_to_index[arg1_str]})"
            if arg2_str in temp_to_index:
                arg2_str = f"({temp_to_index[arg2_str]})"

            if instr.op == 'label':
                triples.append((idx, 'label', instr.result, ""))
            elif instr.op == 'goto':
                triples.append((idx, 'goto', instr.result, ""))
            elif instr.op == 'ifFalse':
                triples.append((idx, 'ifFalse', arg1_str, instr.result))
            elif instr.op == '=':
                triples.append((idx, '=', instr.result, arg1_str))
            else:
                triples.append((idx, instr.op, arg1_str, arg2_str))

            # Record if this instruction produced a temporary variable
            if instr.result and instr.result.startswith('t') and instr.result[1:].isdigit():
                temp_to_index[instr.result] = idx

        return triples


# =====================================================================
# AST-Level Optimizer (Constant Folding & Algebraic Identities)
# =====================================================================

class ASTOptimizer:
    """
    Performs compile-time Constant Folding and Algebraic Simplification
    on the Abstract Syntax Tree before code generation.
    """

    def __init__(self):
        self.optimization_log = []

    def optimize(self, node: ASTNode) -> ASTNode:
        if isinstance(node, ProgramNode):
            new_stmts = [self.optimize(s) for s in node.statements]
            return ProgramNode(new_stmts)

        elif isinstance(node, BlockNode):
            new_stmts = [self.optimize(s) for s in node.statements]
            return BlockNode(new_stmts)

        elif isinstance(node, AssignNode):
            new_expr = self._optimize_expr(node.expr)
            return AssignNode(node.var_name, new_expr)

        elif isinstance(node, IfNode):
            new_cond = self._optimize_expr(node.condition)
            new_true = self.optimize(node.true_branch)
            new_false = self.optimize(node.false_branch) if node.false_branch else None
            return IfNode(new_cond, new_true, new_false)

        elif isinstance(node, WhileNode):
            new_cond = self._optimize_expr(node.condition)
            new_body = self.optimize(node.body)
            return WhileNode(new_cond, new_body)

        return node

    def _optimize_expr(self, node: ASTNode) -> ASTNode:
        if isinstance(node, (NumNode, VarNode)):
            return node

        if isinstance(node, UnaryOpNode):
            sub = self._optimize_expr(node.expr)
            if isinstance(sub, NumNode):
                if node.op == '-':
                    val = -sub.value
                    self.optimization_log.append(f"Constant Folding: -{sub.value}  =>  {val}")
                    return NumNode(val)
                elif node.op == '!':
                    val = 1 if sub.value == 0 else 0
                    self.optimization_log.append(f"Constant Folding: !{sub.value}  =>  {val}")
                    return NumNode(val)
            return UnaryOpNode(node.op, sub)

        if isinstance(node, BinOpNode):
            left = self._optimize_expr(node.left)
            right = self._optimize_expr(node.right)

            # Both operands are numeric constants: Pure Constant Folding
            if isinstance(left, NumNode) and isinstance(right, NumNode):
                val = self._eval_const(left.value, node.op, right.value)
                if val is not None:
                    self.optimization_log.append(
                        f"Constant Folding: {left.value} {node.op} {right.value}  =>  {val}"
                    )
                    return NumNode(val)

            # Algebraic Identities (x + 0, x * 1, x * 0, x - 0, etc.)
            # Addition: x + 0 => x, 0 + x => x
            if node.op == '+':
                if isinstance(right, NumNode) and right.value == 0:
                    self.optimization_log.append(f"Algebraic Simplification: expr + 0  =>  expr")
                    return left
                if isinstance(left, NumNode) and left.value == 0:
                    self.optimization_log.append(f"Algebraic Simplification: 0 + expr  =>  expr")
                    return right

            # Subtraction: x - 0 => x
            if node.op == '-':
                if isinstance(right, NumNode) and right.value == 0:
                    self.optimization_log.append(f"Algebraic Simplification: expr - 0  =>  expr")
                    return left

            # Multiplication: x * 0 => 0, 0 * x => 0, x * 1 => x, 1 * x => x
            if node.op == '*':
                if (isinstance(left, NumNode) and left.value == 0) or (isinstance(right, NumNode) and right.value == 0):
                    self.optimization_log.append(f"Algebraic Simplification: expr * 0  =>  0")
                    return NumNode(0)
                if isinstance(right, NumNode) and right.value == 1:
                    self.optimization_log.append(f"Algebraic Simplification: expr * 1  =>  expr")
                    return left
                if isinstance(left, NumNode) and left.value == 1:
                    self.optimization_log.append(f"Algebraic Simplification: 1 * expr  =>  expr")
                    return right

            # Division: x / 1 => x
            if node.op == '/':
                if isinstance(right, NumNode) and right.value == 1:
                    self.optimization_log.append(f"Algebraic Simplification: expr / 1  =>  expr")
                    return left

            return BinOpNode(left, node.op, right)

        return node

    def _eval_const(self, a, op, b):
        try:
            if op == '+': return a + b
            if op == '-': return a - b
            if op == '*': return a * b
            if op == '/': return (a // b) if (isinstance(a, int) and isinstance(b, int) and b != 0 and a % b == 0) else (a / b)
            if op == '%': return a % b
            if op == '==': return 1 if a == b else 0
            if op == '!=': return 1 if a != b else 0
            if op == '<':  return 1 if a < b else 0
            if op == '<=': return 1 if a <= b else 0
            if op == '>':  return 1 if a > b else 0
            if op == '>=': return 1 if a >= b else 0
            if op == '&&': return 1 if (a and b) else 0
            if op == '||': return 1 if (a or b) else 0
        except ZeroDivisionError:
            return None
        return None

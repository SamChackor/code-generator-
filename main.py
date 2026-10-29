"""
Intermediate Code Generator (3AC, Quadruples, Triples & Optimizer)
===================================================================
Main Driver / CLI Application for college project viva & presentation.
"""

import sys
import os
import argparse
from lexer import Lexer, LexerError
from parser import Parser, ParserError, format_ast
from generator import CodeGenerator, ASTOptimizer


# =====================================================================
# Pretty Table Printing Utilities
# =====================================================================

def print_banner():
    banner = """
===========================================================================
      COMPILER DESIGN: INTERMEDIATE CODE GENERATOR (3AC & TABLES)
===========================================================================
  * Generates: 3-Address Code (3AC), Quadruples, Triples & AST
  * Optimizations: Constant Folding & Algebraic Simplification
===========================================================================
"""
    print(banner)


def format_quadruples_table(quads) -> str:
    """Renders a clean ASCII table for Quadruples: (Index, Op, Arg1, Arg2, Result)."""
    header = f"{'Idx':<5} | {'Op':<10} | {'Arg1':<12} | {'Arg2':<12} | {'Result':<10}"
    divider = "-" * len(header)
    rows = [header, divider]
    for idx, op, a1, a2, res in quads:
        rows.append(f"{idx:<5} | {op:<10} | {a1:<12} | {a2:<12} | {res:<10}")
    return "\n".join(rows)


def format_triples_table(triples) -> str:
    """Renders a clean ASCII table for Triples: (Index, Op, Arg1, Arg2)."""
    header = f"{'Idx':<5} | {'Op':<10} | {'Arg1':<14} | {'Arg2':<14}"
    divider = "-" * len(header)
    rows = [header, divider]
    for idx, op, a1, a2 in triples:
        rows.append(f"{idx:<5} | {op:<10} | {a1:<14} | {a2:<14}")
    return "\n".join(rows)


# =====================================================================
# Core Pipeline Processing Function
# =====================================================================

def compile_and_generate(source_code: str, title: str = "Source Code Snippet", save_file: str = None) -> dict:
    """
    Executes the entire compiler front-end and intermediate representation phases:
    Lexer -> Parser -> AST -> Unoptimized 3AC -> Quadruples -> Triples -> Optimizer -> Optimized 3AC
    """
    output_lines = []

    def log(msg=""):
        print(msg)
        output_lines.append(msg)

    log("=" * 75)
    log(f"  TARGET: {title}")
    log("=" * 75)
    log("[1] SOURCE CODE:")
    for line in source_code.strip().splitlines():
        log(f"    {line}")
    log()

    # Step 1: Lexical Analysis
    try:
        lexer = Lexer(source_code)
        tokens = lexer.get_all_tokens()
    except LexerError as le:
        log(f"[!] Lexical Error: {le}")
        return {"error": str(le)}

    # Step 2: Syntax Analysis & AST Construction
    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except ParserError as pe:
        log(f"[!] Syntax Error: {pe}")
        return {"error": str(pe)}

    log("[2] ABSTRACT SYNTAX TREE (AST):")
    ast_str = format_ast(ast)
    log(ast_str)
    log()

    # Step 3: Intermediate Code Generation (Unoptimized 3AC)
    gen = CodeGenerator()
    gen.generate(ast)
    instructions_3ac = gen.instructions
    quads = gen.get_quadruples()
    triples = gen.get_triples()

    log("[3] THREE-ADDRESS CODE (3AC):")
    for idx, instr in enumerate(instructions_3ac):
        log(f"    {str(instr):<30}  // ({idx})")
    log()

    # Step 4: Quadruple Representation
    log("[4] QUADRUPLES TABLE:")
    log(format_quadruples_table(quads))
    log()

    # Step 5: Triple Representation
    log("[5] TRIPLES TABLE:")
    log(format_triples_table(triples))
    log()

    # Step 6: Code Optimization (Constant Folding & Algebraic Identities)
    optimizer = ASTOptimizer()
    opt_ast = optimizer.optimize(ast)
    gen_opt = CodeGenerator()
    gen_opt.generate(opt_ast)
    opt_instructions = gen_opt.instructions

    log("[6] OPTIMIZATION PASS (Constant Folding & Simplification):")
    if optimizer.optimization_log:
        for opt_entry in optimizer.optimization_log:
            log(f"    - {opt_entry}")
    else:
        log("    - No constant folding opportunities identified.")
    log()

    log("[7] OPTIMIZED THREE-ADDRESS CODE (3AC):")
    for idx, instr in enumerate(opt_instructions):
        log(f"    {str(instr):<30}  // ({idx})")
    log()

    instr_diff = len(instructions_3ac) - len(opt_instructions)
    if instr_diff > 0:
        log(f"[*] Performance Gain: Reduced {instr_diff} instruction(s) ({len(instructions_3ac)} -> {len(opt_instructions)}).")
    else:
        log(f"[*] Instructions: {len(opt_instructions)} (no dead instructions).")
    log("=" * 75)
    log()

    result_text = "\n".join(output_lines)
    if save_file:
        try:
            with open(save_file, "a", encoding="utf-8") as f:
                f.write(result_text + "\n\n")
            print(f"[+] Output appended to file: {os.path.abspath(save_file)}")
        except Exception as e:
            print(f"[!] Failed to write output file: {e}")

    return {
        "tokens": tokens,
        "ast": ast,
        "3ac": instructions_3ac,
        "quads": quads,
        "triples": triples,
        "opt_3ac": opt_instructions,
        "text": result_text
    }


# =====================================================================
# Built-In Demonstration Test Cases
# =====================================================================

SAMPLE_CASES = [
    {
        "title": "Arithmetic Expression with Precedence",
        "code": """
// Calculate polynomial term with operator precedence
x = a + b * c - (d / e + 2);
"""
    },
    {
        "title": "Multiple Assignment & Relational Expression",
        "code": """
a = 15;
b = 20;
c = a * b + 50;
flag = (c > 300) && (a != b);
"""
    },
    {
        "title": "If-Else Conditional Branching",
        "code": """
if (x > y) {
    max = x;
    diff = x - y;
} else {
    max = y;
    diff = y - x;
}
"""
    },
    {
        "title": "While Loop (Accumulator / Summation)",
        "code": """
sum = 0;
i = 1;
while (i <= 10) {
    sum = sum + i;
    i = i + 1;
}
"""
    },
    {
        "title": "Constant Folding & Algebraic Identities Demonstration",
        "code": """
// All constant operations will be folded at compile-time!
val = 10 + 20 * 2;
simplified = (x * 0) + (y * 1) + (z + 0);
scaled = val * 2 - (40 / 4);
"""
    }
]


# =====================================================================
# Interactive Console Menu
# =====================================================================

def run_interactive_menu():
    output_filename = "output_ir.txt"

    # Reset output file at start of session
    if os.path.exists(output_filename):
        try:
            open(output_filename, 'w').close()
        except Exception:
            pass

    while True:
        print_banner()
        print("Select an option:")
        print("  1. Run All Built-In Sample Test Cases")
        print("  2. Run a Specific Built-In Sample Case")
        print("  3. Load and Run Code from 'input_samples.txt'")
        print("  4. Enter Custom Code Interactively")
        print("  5. Exit")
        print("-" * 75)

        choice = input("Enter choice (1-5): ").strip()

        if choice == '1':
            for case in SAMPLE_CASES:
                compile_and_generate(case["code"], title=case["title"], save_file=output_filename)
            input("\n[Press Enter to continue...]")

        elif choice == '2':
            print("\nAvailable Built-In Cases:")
            for i, case in enumerate(SAMPLE_CASES, 1):
                print(f"  {i}. {case['title']}")
            sub_choice = input(f"Select test case (1-{len(SAMPLE_CASES)}): ").strip()
            if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(SAMPLE_CASES):
                case = SAMPLE_CASES[int(sub_choice) - 1]
                compile_and_generate(case["code"], title=case["title"], save_file=output_filename)
            else:
                print("[!] Invalid sample selection.")
            input("\n[Press Enter to continue...]")

        elif choice == '3':
            sample_file = "input_samples.txt"
            if not os.path.exists(sample_file):
                print(f"[!] File '{sample_file}' not found in current directory.")
            else:
                with open(sample_file, "r", encoding="utf-8") as f:
                    content = f.read()
                compile_and_generate(content, title=f"File: {sample_file}", save_file=output_filename)
            input("\n[Press Enter to continue...]")

        elif choice == '4':
            print("\nType or paste your code snippet below.")
            print("(Type a blank line or 'END' on a new line to finish input):")
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip() == "END":
                        break
                    if not line and lines and lines[-1] == "":
                        # Two consecutive blank lines end input
                        break
                    lines.append(line)
                except EOFError:
                    break
            user_code = "\n".join(lines).strip()
            if user_code:
                compile_and_generate(user_code, title="User Custom Snippet", save_file=output_filename)
            else:
                print("[!] No code entered.")
            input("\n[Press Enter to continue...]")

        elif choice == '5':
            print("\nExiting Intermediate Code Generator. Good luck with your presentation!")
            sys.exit(0)

        else:
            print("[!] Invalid choice. Please enter 1 to 5.")


def main():
    arg_parser = argparse.ArgumentParser(description="Intermediate Code Generator (3AC, Quadruples, Triples)")
    arg_parser.add_argument("--file", "-f", help="Source file to compile to Intermediate Code", default=None)
    arg_parser.add_argument("--all", "-a", action="store_true", help="Run all built-in test samples")
    arg_parser.add_argument("--out", "-o", help="Output text file to store results", default="output_ir.txt")
    args = arg_parser.parse_args()

    if args.all:
        print_banner()
        for case in SAMPLE_CASES:
            compile_and_generate(case["code"], title=case["title"], save_file=args.out)
        return

    if args.file:
        print_banner()
        if not os.path.exists(args.file):
            print(f"[!] Error: File '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()
        compile_and_generate(code, title=f"File: {args.file}", save_file=args.out)
        return

    run_interactive_menu()


if __name__ == "__main__":
    main()

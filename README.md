# Intermediate Code Generator

A Python implementation of an intermediate code generator, built as a micro project for the Compiler Construction course.

## Overview

This project takes a source program as input and generates intermediate code (three-address code) from it. It covers the front-end phases of a compiler:

1. **Lexical analysis:** splits the source code into tokens
2. **Syntax analysis:** checks the token stream against the grammar
3. **Intermediate code generation:** produces three-address code

## Features

- Arithmetic expressions
- Assignment statements
- Conditional statements (if / else)
- Loops (while / for)
- Automatic temporary variable and label generation

*(Edit this list to match what your project supports.)*

## Project Structure

```
code-generator/
├── main.py            # Entry point
├── lexer.py           # Tokenizer
├── parser.py          # Parser
├── codegen.py         # Intermediate code generation
├── README.md
└── examples/          # Sample inputs
```

*(Replace with your actual file tree.)*

## Requirements

- Python 3.8 or higher
- No external libraries required

## How to Run

```bash
git clone https://github.com/palakdugad22-hub/code-generator-.git
cd code-generator-
python main.py
```

## Example

**Input**

```
a = b + c * d
```

**Output (three-address code)**

```
t1 = c * d
t2 = b + t1
a = t2
```

*(Replace with a real input and output from your program.)*

## How It Works

Source code → Lexer → Tokens → Parser → Intermediate Code Generator → Three-address code

## Author

Palak Dugad
Compiler Construction Micro Project

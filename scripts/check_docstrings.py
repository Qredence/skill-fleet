#!/usr/bin/env python3
"""
Script to find public functions missing docstrings in Python files.
"""

import ast
import os
from pathlib import Path
from typing import List, Set, Tuple


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.functions: List[Tuple[str, int, bool]] = []  # (name, line, has_docstring)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        # Skip private functions (starting with underscore)
        if not node.name.startswith('_'):
            has_docstring = ast.get_docstring(node) is not None
            self.functions.append((node.name, node.lineno, has_docstring))
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        # Handle async functions the same way
        if not node.name.startswith('_'):
            has_docstring = ast.get_docstring(node) is not None
            self.functions.append((node.name, node.lineno, has_docstring))
        self.generic_visit(node)


def check_file_for_missing_docstrings(filepath: Path) -> List[Tuple[str, int, str]]:
    """Check a Python file for public functions missing docstrings."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        visitor = FunctionVisitor()
        visitor.visit(tree)
        
        missing_docs = []
        for func_name, line_num, has_docstring in visitor.functions:
            if not has_docstring:
                missing_docs.append((func_name, line_num, filepath.name))
        
        return missing_docs
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return []


def main():
    src_dir = Path("src/skill_fleet")
    all_missing = []
    
    # Check all Python files
    for py_file in src_dir.rglob("*.py"):
        missing = check_file_for_missing_docstrings(py_file)
        if missing:
            all_missing.append((py_file, missing))
    
    # Print results
    if all_missing:
        print("Functions missing docstrings:")
        print("=" * 60)
        for filepath, functions in all_missing:
            print(f"\n{filepath}:")
            for func_name, line_num, filename in functions:
                print(f"  - {func_name} (line {line_num})")
    else:
        print("No public functions missing docstrings found!")
    
    # Summary
    total_missing = sum(len(functions) for _, functions in all_missing)
    print(f"\nTotal: {total_missing} functions missing docstrings")


if __name__ == "__main__":
    main()
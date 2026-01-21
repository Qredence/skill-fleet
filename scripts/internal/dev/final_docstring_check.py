#!/usr/bin/env python3
"""
Final comprehensive check for public functions missing docstrings.
"""

import ast
from pathlib import Path


class ComprehensiveFunctionVisitor(ast.NodeVisitor):
    """Comprehensive AST visitor to find functions and check for docstrings."""

    def __init__(self):
        self.functions: list[dict] = []
        self.current_class = None

    def visit_FunctionDef(self, node):
        """Visit function definition nodes and collect metadata."""
        # Skip private functions (starting with underscore)
        if not node.name.startswith("_"):
            has_docstring = ast.get_docstring(node) is not None
            is_async = False
            self.functions.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": has_docstring,
                    "is_async": is_async,
                    "is_method": self.current_class is not None,
                    "class_name": self.current_class,
                }
            )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definition nodes and collect metadata."""
        # Handle async functions the same way
        if not node.name.startswith("_"):
            has_docstring = ast.get_docstring(node) is not None
            is_async = True
            self.functions.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": has_docstring,
                    "is_async": is_async,
                    "is_method": self.current_class is not None,
                    "class_name": self.current_class,
                }
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definition nodes and set current class context."""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class


def check_file_for_missing_docstrings(filepath: Path) -> list[dict]:
    """Check a Python file for public functions missing docstrings."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        visitor = ComprehensiveFunctionVisitor()
        visitor.visit(tree)

        missing_docs = []
        for func_info in visitor.functions:
            if not func_info["has_docstring"]:
                missing_docs.append(func_info)

        return missing_docs
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return []


def main():
    """Find and report public functions missing docstrings with detailed breakdown."""
    src_dir = Path("src/skill_fleet")
    all_missing = []

    # Check all Python files
    for py_file in src_dir.rglob("*.py"):
        missing = check_file_for_missing_docstrings(py_file)
        if missing:
            all_missing.append((py_file, missing))

    # Print results with detailed information
    if all_missing:
        print("Functions missing docstrings:")
        print("=" * 80)

        # Group by file for better readability
        for filepath, functions in sorted(all_missing):
            print(f"\n📁 {filepath}:")
            for func in functions:
                func_type = "async " if func["is_async"] else ""
                location = f"class {func['class_name']}" if func["is_method"] else "module"
                print(f"  - {func_type}{func['name']} (line {func['line']}, {location})")
    else:
        print("✅ No public functions missing docstrings found!")

    # Summary statistics
    total_missing = sum(len(functions) for _, functions in all_missing)
    print("\n📊 Summary:")
    print(f"  Total files with missing docstrings: {len(all_missing)}")
    print(f"  Total functions missing docstrings: {total_missing}")

    # Detailed breakdown
    if all_missing:
        print("\n🔍 Detailed breakdown:")
        for filepath, functions in sorted(all_missing):
            print(f"\n{filepath}:")
            for func in functions:
                func_type = "async " if func["is_async"] else ""
                print(f"  def {func_type}{func['name']}(...)  # line {func['line']}")


if __name__ == "__main__":
    main()

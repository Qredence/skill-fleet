---
name: python-decorators
description: Ability to design, implement, and apply higher-order functions to extend
  or modify the behavior of functions and classes in Python.
metadata:
  skill_id: technical_skills/programming/languages/python/decorators
  version: 1.0.0
---

# Python Decorators: Functional and Metaprogramming Patterns

## Overview
Python decorators are a powerful form of metaprogramming used to modify or enhance the behavior of functions or classes without permanently modifying their source code. They rely on Python's first-class function support and closure mechanics.

## Core Concepts
- **Closures**: Functions that "remember" the environment in which they were created.
- **First-Class Citizens**: The ability to pass functions as arguments, return them from other functions, and assign them to variables.
- **Syntactic Sugar**: The `@decorator` syntax is equivalent to `func = decorator(func)`.

## Modules

### 1. Basic Function Decorators
Focuses on the standard wrapper pattern.
- **Simple Logger**: Intercepting calls to log arguments and return values.
- **Metadata Preservation**: Critical use of `functools.wraps` to prevent losing the original function's identity (`__name__`, `__doc__`).

### 2. Parameterized Decorators (Decorator Factories)
Moving beyond simple wrappers to "factories" that return decorators.
- Implementation of the triple-nested function structure: `outer_params(actual_decorator(wrapped_func))`.
- Use cases: `@retry(times=3)`, `@access_level("admin")`.

### 3. Class-Based Decorators
Utilizing the `__call__` dunder method to treat an object instance as a decorator.
- Maintaining state within instance attributes rather than closures.

### 4. Stateful & Memoization
Advanced patterns for performance and tracking.
- **Call Counting**: Monitoring execution frequency.
- **Memoization**: Caching expensive computation results based on input arguments (e.g., implementing a custom LRU cache).

### 5. Composition and Order
Understanding the "Onion" model of execution.
- Order of application: Bottom-to-top.
- Order of execution: Top-to-bottom.
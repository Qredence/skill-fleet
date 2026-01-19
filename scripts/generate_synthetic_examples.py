#!/usr/bin/env python3
"""Generate synthetic training examples for underrepresented categories.

This script creates diverse, realistic training examples based on common
patterns in software development to reach the recommended 50-100 examples.
"""

from __future__ import annotations

import json
from pathlib import Path


# Synthetic training examples across diverse categories
SYNTHETIC_EXAMPLES = [
    # Python category
    {
        "task_description": "Create a python async patterns skill: Master asynchronous programming in Python with async/await, event loops, and concurrent execution patterns. Use when building async APIs, handling concurrent I/O, or optimizing performance with asyncio.",
        "expected_taxonomy_path": "python/async-patterns",
        "expected_name": "async-patterns",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "guides"],
        "expected_keywords": ["python", "async", "await", "asyncio", "concurrent"],
        "expected_description": "Master asynchronous programming in Python with async/await, event loops, and concurrent execution patterns. Use when building async APIs or handling concurrent I/O operations.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a python error handling skill: Implement robust error handling with try/except blocks, custom exceptions, and error recovery strategies. Use when building production Python applications requiring reliability and graceful degradation.",
        "expected_taxonomy_path": "python/error-handling",
        "expected_name": "error-handling",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides"],
        "expected_keywords": ["python", "error", "exception", "try", "except"],
        "expected_description": "Implement robust error handling with try/except blocks, custom exceptions, and error recovery strategies for production applications.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a python dataclasses skill: Use Python dataclasses for clean data modeling with automatic __init__, __repr__, and comparison methods. Use when defining data structures, DTOs, or configuration objects.",
        "expected_taxonomy_path": "python/dataclasses",
        "expected_name": "dataclasses",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": [],
        "expected_keywords": ["python", "dataclass", "model", "dto"],
        "expected_description": "Use Python dataclasses for clean data modeling with automatic methods. Use when defining data structures or configuration objects.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a python logging best practices skill: Configure Python logging with handlers, formatters, and log levels for production applications. Use when implementing structured logging, log aggregation, or debugging workflows.",
        "expected_taxonomy_path": "python/logging",
        "expected_name": "logging",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides", "templates"],
        "expected_keywords": ["python", "logging", "debug", "monitor"],
        "expected_description": "Configure Python logging with handlers, formatters, and log levels for production. Use for structured logging or debugging workflows.",
        "source": "synthetic",
    },
    
    # Testing category
    {
        "task_description": "Create a testing pytest fixtures skill: Master pytest fixtures for test setup, teardown, and dependency injection. Use when writing maintainable tests with reusable test components and complex test scenarios.",
        "expected_taxonomy_path": "testing/pytest-fixtures",
        "expected_name": "pytest-fixtures",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "examples"],
        "expected_keywords": ["pytest", "fixtures", "testing", "setup"],
        "expected_description": "Master pytest fixtures for test setup, teardown, and dependency injection. Use for maintainable tests with reusable components.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a testing mocking strategies skill: Implement effective test mocking with unittest.mock, pytest-mock, and dependency injection. Use when isolating units under test, mocking external services, or testing edge cases.",
        "expected_taxonomy_path": "testing/mocking",
        "expected_name": "mocking",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides"],
        "expected_keywords": ["testing", "mock", "unittest", "pytest"],
        "expected_description": "Implement effective test mocking with unittest.mock and pytest-mock. Use when isolating units under test or mocking external services.",
        "source": "synthetic",
    },
    
    # Web category
    {
        "task_description": "Create a web react hooks patterns skill: Master React hooks (useState, useEffect, useContext, custom hooks) for functional components. Use when building modern React applications with state management and side effects.",
        "expected_taxonomy_path": "web/react-hooks",
        "expected_name": "react-hooks",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "examples"],
        "expected_keywords": ["react", "hooks", "useState", "useEffect"],
        "expected_description": "Master React hooks for functional components. Use when building modern React applications with state management and side effects.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a web api design patterns skill: Design RESTful APIs with proper resource modeling, HTTP methods, status codes, and versioning strategies. Use when architecting backend APIs or defining API contracts.",
        "expected_taxonomy_path": "web/api-design",
        "expected_name": "api-design",
        "expected_skill_style": "navigation_hub",
        "expected_subdirectories": ["references", "guides", "examples"],
        "expected_keywords": ["api", "rest", "http", "design"],
        "expected_description": "Design RESTful APIs with proper resource modeling, HTTP methods, and status codes. Use when architecting backend APIs.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a web authentication jwt skill: Implement JWT-based authentication with token generation, validation, and refresh strategies. Use when adding authentication to web APIs or SPAs.",
        "expected_taxonomy_path": "web/auth-jwt",
        "expected_name": "auth-jwt",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides", "templates"],
        "expected_keywords": ["auth", "jwt", "token", "security"],
        "expected_description": "Implement JWT-based authentication with token generation and validation. Use when adding authentication to web APIs or SPAs.",
        "source": "synthetic",
    },
    
    # DevOps category
    {
        "task_description": "Create a devops docker compose skill: Orchestrate multi-container applications with Docker Compose including service dependencies, networking, and volumes. Use when setting up development environments or deploying multi-service applications.",
        "expected_taxonomy_path": "devops/docker-compose",
        "expected_name": "docker-compose",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["examples", "templates"],
        "expected_keywords": ["docker", "compose", "container", "devops"],
        "expected_description": "Orchestrate multi-container applications with Docker Compose. Use when setting up development environments or deploying applications.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a devops github actions skill: Automate CI/CD workflows with GitHub Actions including testing, building, and deployment pipelines. Use when implementing continuous integration or automated deployments.",
        "expected_taxonomy_path": "devops/github-actions",
        "expected_name": "github-actions",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["examples", "templates"],
        "expected_keywords": ["github", "actions", "ci", "cd", "automation"],
        "expected_description": "Automate CI/CD workflows with GitHub Actions. Use when implementing continuous integration or automated deployments.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a devops environment variables skill: Manage environment-specific configuration with .env files, environment variables, and secrets management. Use when configuring applications for different environments or handling sensitive data.",
        "expected_taxonomy_path": "devops/env-config",
        "expected_name": "env-config",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides"],
        "expected_keywords": ["env", "config", "secrets", "security"],
        "expected_description": "Manage environment-specific configuration with .env files and secrets. Use when configuring applications for different environments.",
        "source": "synthetic",
    },
    
    # Database category
    {
        "task_description": "Create a database sql query optimization skill: Optimize SQL queries with indexes, query planning, and performance analysis. Use when diagnosing slow queries, improving database performance, or scaling data access.",
        "expected_taxonomy_path": "database/sql-optimization",
        "expected_name": "sql-optimization",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "guides"],
        "expected_keywords": ["sql", "optimization", "index", "performance"],
        "expected_description": "Optimize SQL queries with indexes and query planning. Use when diagnosing slow queries or improving database performance.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a database migrations skill: Manage database schema changes with migration tools (Alembic, Flyway, Prisma Migrate). Use when evolving database schemas, deploying schema changes, or maintaining version control of database structure.",
        "expected_taxonomy_path": "database/migrations",
        "expected_name": "migrations",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides", "examples"],
        "expected_keywords": ["database", "migration", "schema", "alembic"],
        "expected_description": "Manage database schema changes with migration tools. Use when evolving database schemas or deploying schema changes.",
        "source": "synthetic",
    },
    
    # Architecture category
    {
        "task_description": "Create an architecture dependency injection skill: Implement dependency injection patterns for loose coupling and testability. Use when building modular applications, improving testability, or managing object lifecycles.",
        "expected_taxonomy_path": "architecture/dependency-injection",
        "expected_name": "dependency-injection",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "examples"],
        "expected_keywords": ["architecture", "di", "injection", "pattern"],
        "expected_description": "Implement dependency injection patterns for loose coupling. Use when building modular applications or improving testability.",
        "source": "synthetic",
    },
    {
        "task_description": "Create an architecture event driven skill: Design event-driven architectures with message queues, event buses, and asynchronous communication. Use when building scalable distributed systems or decoupling microservices.",
        "expected_taxonomy_path": "architecture/event-driven",
        "expected_name": "event-driven",
        "expected_skill_style": "navigation_hub",
        "expected_subdirectories": ["references", "guides", "examples"],
        "expected_keywords": ["architecture", "event", "message", "async"],
        "expected_description": "Design event-driven architectures with message queues and event buses. Use when building scalable distributed systems.",
        "source": "synthetic",
    },
    
    # API category
    {
        "task_description": "Create an api error responses skill: Design consistent API error responses with proper status codes, error messages, and error details. Use when building production APIs requiring clear error communication.",
        "expected_taxonomy_path": "api/error-responses",
        "expected_name": "error-responses",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "examples"],
        "expected_keywords": ["api", "error", "response", "http"],
        "expected_description": "Design consistent API error responses with proper status codes and messages. Use when building production APIs.",
        "source": "synthetic",
    },
    {
        "task_description": "Create an api pagination skill: Implement API pagination with cursor-based, offset-based, and page-based strategies. Use when designing APIs that return large datasets or implementing efficient data fetching.",
        "expected_taxonomy_path": "api/pagination",
        "expected_name": "pagination",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["examples"],
        "expected_keywords": ["api", "pagination", "cursor", "offset"],
        "expected_description": "Implement API pagination with cursor-based and offset-based strategies. Use when designing APIs returning large datasets.",
        "source": "synthetic",
    },
    {
        "task_description": "Create an api versioning skill: Implement API versioning strategies including URL versioning, header versioning, and content negotiation. Use when evolving APIs while maintaining backward compatibility.",
        "expected_taxonomy_path": "api/versioning",
        "expected_name": "versioning",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides"],
        "expected_keywords": ["api", "version", "compatibility", "migration"],
        "expected_description": "Implement API versioning strategies including URL and header versioning. Use when evolving APIs while maintaining compatibility.",
        "source": "synthetic",
    },
    
    # Practices category
    {
        "task_description": "Create a practices code review skill: Conduct effective code reviews with checklists, best practices, and constructive feedback techniques. Use when establishing code review processes or improving code quality through peer review.",
        "expected_taxonomy_path": "practices/code-review",
        "expected_name": "code-review",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references"],
        "expected_keywords": ["review", "quality", "feedback", "pr"],
        "expected_description": "Conduct effective code reviews with checklists and best practices. Use when establishing review processes or improving code quality.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a practices git workflow skill: Implement Git workflows (Gitflow, trunk-based, GitHub Flow) with branching strategies and merge conventions. Use when establishing team Git practices or managing code collaboration.",
        "expected_taxonomy_path": "practices/git-workflow",
        "expected_name": "git-workflow",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides"],
        "expected_keywords": ["git", "workflow", "branch", "merge"],
        "expected_description": "Implement Git workflows with branching strategies. Use when establishing team Git practices or managing collaboration.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a practices documentation skill: Write effective technical documentation with clear structure, code examples, and usage guides. Use when documenting APIs, creating onboarding materials, or maintaining project documentation.",
        "expected_taxonomy_path": "practices/documentation",
        "expected_name": "documentation",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "templates"],
        "expected_keywords": ["docs", "documentation", "readme", "guide"],
        "expected_description": "Write effective technical documentation with structure and examples. Use when documenting APIs or creating onboarding materials.",
        "source": "synthetic",
    },
    
    # Domain category
    {
        "task_description": "Create a domain machine learning basics skill: Understand ML fundamentals including supervised learning, model training, and evaluation metrics. Use when starting ML projects, understanding model behavior, or implementing basic ML workflows.",
        "expected_taxonomy_path": "domain/ml-basics",
        "expected_name": "ml-basics",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["references", "examples"],
        "expected_keywords": ["ml", "machine-learning", "model", "training"],
        "expected_description": "Understand ML fundamentals including supervised learning and model training. Use when starting ML projects or understanding model behavior.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a domain data validation skill: Implement data validation with Pydantic, JSON Schema, and custom validators. Use when processing user input, validating API requests, or ensuring data integrity.",
        "expected_taxonomy_path": "domain/data-validation",
        "expected_name": "data-validation",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["examples"],
        "expected_keywords": ["validation", "pydantic", "schema", "data"],
        "expected_description": "Implement data validation with Pydantic and JSON Schema. Use when processing user input or validating API requests.",
        "source": "synthetic",
    },
    {
        "task_description": "Create a domain observability skill: Implement observability with metrics, logging, and tracing for production systems. Use when monitoring application health, debugging production issues, or implementing SRE practices.",
        "expected_taxonomy_path": "domain/observability",
        "expected_name": "observability",
        "expected_skill_style": "navigation_hub",
        "expected_subdirectories": ["references", "guides"],
        "expected_keywords": ["observability", "metrics", "tracing", "monitoring"],
        "expected_description": "Implement observability with metrics, logging, and tracing. Use when monitoring application health or debugging production issues.",
        "source": "synthetic",
    },
    
    # Memory category
    {
        "task_description": "Create a memory caching strategies skill: Implement caching with Redis, in-memory caches, and cache invalidation strategies. Use when optimizing performance, reducing database load, or implementing distributed caching.",
        "expected_taxonomy_path": "memory/caching",
        "expected_name": "caching",
        "expected_skill_style": "comprehensive",
        "expected_subdirectories": ["guides", "examples"],
        "expected_keywords": ["cache", "redis", "performance", "optimization"],
        "expected_description": "Implement caching with Redis and cache invalidation strategies. Use when optimizing performance or reducing database load.",
        "source": "synthetic",
    },
]


def main():
    # Load existing trainset_v3.json
    trainset_path = Path("config/training/trainset_v3.json")
    
    if not trainset_path.exists():
        print(f"❌ {trainset_path} not found. Run expand_training_data.py first.")
        return
    
    with trainset_path.open("r", encoding="utf-8") as f:
        existing_examples = json.load(f)
    
    print("=" * 60)
    print("Synthetic Training Examples Generator")
    print("=" * 60)
    print(f"\n📦 Loaded {len(existing_examples)} existing examples")
    print(f"📝 Generating {len(SYNTHETIC_EXAMPLES)} synthetic examples")
    
    # Combine existing and synthetic
    all_examples = existing_examples + SYNTHETIC_EXAMPLES
    
    # Deduplicate by name
    seen_names = set()
    unique_examples = []
    for example in all_examples:
        name = example.get("expected_name")
        if name and name not in seen_names:
            seen_names.add(name)
            unique_examples.append(example)
    
    print(f"🔧 After deduplication: {len(unique_examples)} total examples")
    
    # Save updated trainset
    output_path = Path("config/training/trainset_v4.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(unique_examples, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(unique_examples)} training examples to {output_path}")
    
    # Print statistics
    print("\n" + "=" * 60)
    print("Final Training Set Statistics")
    print("=" * 60)
    
    sources = {}
    categories = {}
    styles = {}
    
    for example in unique_examples:
        source = example.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1
        
        category = example.get("expected_taxonomy_path", "").split("/")[0]
        categories[category] = categories.get(category, 0) + 1
        
        style = example.get("expected_skill_style", "unknown")
        styles[style] = styles.get(style, 0) + 1
    
    print(f"\nTotal: {len(unique_examples)} examples")
    print(f"By source: {dict(sorted(sources.items()))}")
    print(f"By style: {dict(sorted(styles.items()))}")
    print(f"By category: {dict(sorted(categories.items()))}")
    
    # DSPy readiness
    print("\n" + "=" * 60)
    print("DSPy Optimization Readiness")
    print("=" * 60)
    
    if len(unique_examples) >= 50:
        print(f"✅ Excellent! {len(unique_examples)} examples meets DSPy best practices (50-100)")
        print("   Recommended: MIPROv2 with auto='medium' or auto='heavy'")
    else:
        print(f"⚠️  {len(unique_examples)} examples - close but below 50 threshold")
        print(f"   Need {50 - len(unique_examples)} more examples for optimal results")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

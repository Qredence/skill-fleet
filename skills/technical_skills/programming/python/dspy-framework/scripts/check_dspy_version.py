"""Print installed DSPy package and version for quick validation."""

import importlib.metadata


def main() -> int:
    candidates = ("dspy-ai", "dspy")
    for name in candidates:
        try:
            version = importlib.metadata.version(name)
            print(f"{name}=={version}")
            return 0
        except importlib.metadata.PackageNotFoundError:
            continue

    print("DSPy not installed (tried: dspy-ai, dspy)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

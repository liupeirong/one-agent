---
applyTo: "**/*.py"
---

# Python Coding Standards

## Readability & Style

* Use Python naming: `PascalCase` classes, `snake_case` functions/variables, `UPPER_SNAKE_CASE` constants, `_` private members.
* Group imports: stdlib → third-party → local (blank line between groups, no trailing whitespace).

## Pythonic Idioms

* Prefer comprehensions for simple transforms; use explicit loops for complex logic/side-effects.
* Always use `with` for files, locks, DB connections.
* Prefer `dataclass` / `NamedTuple` / `Enum` for data holders.
* Use `pathlib` over `os.path`; timezone-aware `datetime` when relevant.
* Use `*` keyword-only arguments for multi-optional functions.
* Never use mutable defaults or `global`/`nonlocal` unless strictly required.

## Function & Class Design

* Keep functions small and single-responsibility.
* Add docstrings to all public APIs (follow repo style).
* Document unavoidable side-effects.
* Follow codebase’s class-member ordering (if defined).

## Type Safety Foundations

* Add type hints to all public APIs, module vars, and class attributes.
* Use PEP 695 (3.12+) or `TypeVar` for generics.
* Avoid `Any` except in thin wrappers.

## Error Handling

* Raise specific exceptions; never bare `except:` (broad `except Exception:` only at app boundaries with logging).
* No silent failures or generic error messages.
* Provide context, expected state, and guidance in every exception.

## Anti-Patterns to Avoid

* Never use `eval`, `exec`, or `pickle` on untrusted data.
* Never hard-code secrets.

## Maintainability

* Prefer self-documenting code; comments only for "why".
* Use structured logging instead of `print`.
* Flag overly long/complex functions that resist testing.

## Design Principles

* Eliminate duplication: extract repeated logic into a shared helper so fixes propagate automatically.
* Prefer the simplest implementation that satisfies current requirements. Introduce abstractions only when a second concrete use case appears.
* Before flagging seemingly unused code, verify it is not a protocol implementation, framework hook, public API, or entry point invoked externally.
* Match solution complexity to problem complexity. A duplicated function warrants a shared helper, not an event-driven architecture.
* Align with existing patterns; do not re-implement shared functionality or bypass established layers.

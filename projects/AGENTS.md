# Project Engineering Rules

These rules apply to every project below `projects/`, including projects with
their own Git repository. A nested project with its own `AGENTS.md` may add
stricter rules, but must not weaken these requirements.

## General

- Keep changes narrowly scoped and preserve existing project conventions.
- Never commit secrets, credentials, member/customer data, databases,
  spreadsheets, CSV exports, caches, generated outputs, or evidence artifacts.
- Add or update tests for every behavior change, including at least one boundary
  or failure case.
- Before handing work off, run the relevant format, lint, type, and test checks.
  State clearly if a check could not be run and why.
- When generating code in a response, first explain the core design in one or
  two sentences. After the code, include a `pytest` unit test that covers a
  boundary condition.

## Python

- Target Python 3.11 or newer and keep every line at 88 characters or fewer.
- Add explicit type annotations to every function parameter and return value.
  Avoid `Any`; narrow external or untyped values at system boundaries.
- Public functions and classes must have Google-style docstrings with a short
  summary and applicable `Args`, `Returns`, and `Raises` sections.
- Follow PEP 8. Group imports as standard library, third-party packages, then
  local modules; prefer absolute imports.
- Model structured data with `dataclasses` or Pydantic models. Do not pass
  complex domain data as untyped dictionaries.
- Use `async`/`await` for asynchronous I/O. Do not call blocking I/O from async
  code; move unavoidable blocking work to a thread or process executor.
- Catch the narrowest useful exception and log failures with context. Bare
  `except` and silent `except Exception` handlers are forbidden.
- Define important numbers and strings as named constants or `Enum` members.
- Never use mutable default arguments. Use `None` and initialize inside the
  function, or use a dataclass `default_factory`.
- Use `pytest` for tests and cover normal, boundary, and expected failure paths.
- Run `uvx ruff format --check <files>`, `uvx ruff check <files>`,
  `uvx mypy <files>`, and the relevant `pytest` suite.

## Frontend

- Use TypeScript in strict mode. Do not introduce `any`, unchecked type casts,
  floating promises, or promises used as booleans.
- Follow React Hooks rules and keep effects limited to synchronization with
  external systems. Prefer small, testable components and pure functions.
- Build accessible interfaces: semantic elements, keyboard operation, visible
  focus, associated labels, and meaningful loading, empty, and error states.
- Format with Prettier and lint with the shared ESLint configuration in
  `standards/frontend/`.
- Use Vitest for unit and component tests. Use Playwright for critical user
  journeys that cross pages or depend on browser behavior.

## Legacy Code

The repository contains code written before these rules. Do not perform broad,
unrelated rewrites solely to clear historical findings. New files must comply
fully; touched legacy files should be improved within the scope of the change.
Any temporary exemption must be narrow, documented beside the tool setting,
and include a clear removal condition.

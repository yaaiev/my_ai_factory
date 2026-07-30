# Shared Engineering Standards

The repository applies one lightweight quality gate to all root-managed
projects. The policy is defined in `projects/AGENTS.md` and enforced by the root
tool configuration, pre-commit hooks, and GitHub Actions.

## Local Setup

Install `uv`, Node.js 22 or newer, and pre-commit. Then enable the hooks:

```bash
pre-commit install
```

For Python files:

```bash
uvx ruff format --check path/to/files
uvx ruff check path/to/files
uvx mypy path/to/files
uvx pytest path/to/tests
```

For a frontend project, install its dependencies plus the packages declared in
`standards/frontend/package.json`, extend `tsconfig.strict.json`, and import the
shared ESLint and Prettier configurations. The project remains responsible for
its own build and test commands because framework requirements differ.

## Adoption Model

New and changed files are checked strictly. Existing code is not reformatted or
rewritten wholesale: it becomes compliant as normal work touches it. This keeps
the quality bar enforceable without mixing unrelated changes into feature work.

After the workflow is merged, configure the `main` branch in GitHub to require
the `Changed code quality` check before merging and require pull requests.

# Contributing

Keep changes small and focused on one issue. Check the [GitHub issues](https://github.com/PRNovoa/software-engineering-database-udit/issues) before starting, and comment on the relevant issue so we avoid duplicate work. Discuss larger design decisions there first.

See the [README](README.md) for setup instructions.

## Making changes

- Create a branch named `<type>/<issue>-<short-description>`, for example `docs/5-contributing` or `fix/1-create-dictionary`.
- If there's no issue related to what you're going to do add it first.
- Work and push changes on that branch. Never push directly to `main`; changes must go through a pull request.
- Use clear English names and `snake_case` for Python functions and variables. Follow the surrounding code and avoid unrelated refactoring.
- Implement the database logic ourselves and use Python's standard library where possible. Avoid external libraries unless they are necessary, and explain why in the PR.
- Write commits as `<type>: <short description>`. Use `feat`, `fix`, `docs`, `test`, or `chore`, for example `docs: add contributing guide`.
- Keep local environments, generated database files, and credentials out of commits.

## Pull requests

Open a PR with a short description of what changed, why, and how you tested it. Link the issue with `Closes #5` if the PR fully resolves it, or `Related to #5` if it only covers part of the work.

- Keep `main` production-ready. Merge only completed, tested changes with all automated tests passing.
- All four members must approve the final changes. The PR author confirms approval in a comment; the other three submit approving reviews. If the code changes afterward, everyone must approve again.
- The test and branch-protection setup must run tests on every branch push and pull request, require passing tests and the three other members' reviews before merging, and block direct pushes to `main`, including bypasses.

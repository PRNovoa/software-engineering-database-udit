# Contributing

Keep changes small and focused on one issue. Check the [GitHub issues](https://github.com/PRNovoa/software-engineering-database-udit/issues) before starting, and comment on the relevant issue so we avoid duplicate work.

Larger design decisions can be discussed in [Discussions](https://github.com/PRNovoa/software-engineering-database-udit/discussions) first. It's optional, but useful when the team needs to agree on something before opening an issue for the work.

Follow the design decisions in [docs/design.md](docs/design.md). When a new one is agreed, add it there.

See the [README](README.md) for setup instructions.

## Making changes

- Pick issues by priority: `Must` first, then `Should`, then `Could`.
- Create a branch named `<type>/<issue>-<short-description>`, for example `docs/5-contributing` or `fix/1-create-dictionary`.
- If there's no issue related to what you're going to do add it first.
- Work and push changes on that branch. Never push directly to `main`; changes must go through a pull request.
- Use clear English names and `snake_case` for Python functions and variables. Follow the surrounding code and avoid unrelated refactoring.
- Implement the database logic ourselves and use Python's standard library where possible. Avoid external libraries unless they are necessary, and explain why in the PR.
- Write commits as `<type>: <short description>`. Use `feat`, `fix`, `docs`, `test`, or `chore`, for example `docs: add contributing guide`.
- Keep local environments, generated database files, and credentials out of commits.

## Issues and labels

Every open issue gets exactly one priority label, following the MoSCoW method:

- `Must`: required for the project to work. Do these first.
- `Should`: important, but the project still works without it. Do these after the `Must` issues.
- `Could`: nice to have. Do these only once the `Must` and `Should` issues are covered.

Add the label when you open the issue. If you think a priority is wrong, say so in the issue before you change it.

## Pull requests

Open a PR with a short description of what changed, why, and how you tested it.

Every PR description must reference its issue using `#` followed by the actual issue number. For example:

- `Closes #31` if the PR fully resolves the issue.
- `Related to #31` if the PR only covers part of the work or is related to the issue.

An issue reference only in the title, branch name, commit message, or comments does not satisfy this requirement.

- Keep `main` production-ready. Merge only completed, tested changes with all automated tests passing.
- All four members must approve the final changes. The PR author confirms approval in a comment; the other three submit approving reviews. If the code changes afterward, everyone must approve again.
- The test and branch-protection setup must run tests on every branch push and pull request, require passing tests and the three other members' reviews before merging, and block direct pushes to `main`, including bypasses.

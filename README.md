# Database Exercise

Database exercise for the Software Engineering course. The project currently
contains the initial scaffolding for a file-backed key-value database written in
Python.

> [!NOTE]
> See [docs/design.md](docs/design.md) for how the database works and why.

## Requirements

| | |
|---|---|
| **Python** | `>=3.14,<3.16` |
| **Dependencies** | No runtime dependencies beyond the Python standard library |

## Setup

```sh
git clone https://github.com/PRNovoa/software-engineering-database-udit.git
cd software-engineering-database-udit
python3 -m venv .venv
source .venv/bin/activate
```

> [!TIP]
> On Windows, activate with `.venv\Scripts\activate` instead.

Install the project and its development dependencies, including `pytest`, in
editable mode:

```sh
python -m pip install --editable ".[dev]"
```

## Testing

Run the test suite with `pytest`:

```sh
pytest
```

The test suite is configured to run with pytest.

## Project structure

```text
docs/
└── design.md
src/
├── __init__.py
├── database.py
└── entries.py
tests/
└── test_entries.py
pyproject.toml
```

> [!IMPORTANT]
> See [CONTRIBUTING.md](CONTRIBUTING.md) for branch, test, and approval
> requirements.

## Authors

| |
|---|
| Iván Herrera |
| Pablo Novoa |
| Carlos Parra |
| Gonzalo Pérez Fernández-Corugedo |

---

<sub>The formatting of this document was made with AI help. The content, the design decisions and the code are our own work.</sub>
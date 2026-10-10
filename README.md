# Database Exercise

Database exercise for the Software Engineering course. The project currently
contains the initial scaffolding for a file-backed key-value database written in
Python.

## Requirements

- Python 3.9 or newer
- No runtime dependencies beyond the Python standard library

## Setup

```sh
git clone https://github.com/PRNovoa/software-engineering-database-udit.git
cd software-engineering-database-udit
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate with `.venv\Scripts\activate` instead.

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

The current setup test verifies that the CRUD module can be imported.

## Project structure

```text
src/
└── crud.py
tests/
└── test_crud.py
pyproject.toml
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch, test, and approval
requirements.

## Authors

- Iván Herrera
- Pablo Novoa
- Carlos Parra
- Gonzalo Pérez Fernández-Corugedo

# Contributing to fastmcp-production-template

First off, thank you for considering contributing to `fastmcp-production-template`! It's people like you that make open-source such a great community.

## 1. Where do I go from here?

If you've noticed a bug or have a feature request, please make sure to check our [issue tracker](https://github.com/ManjunathGovindaraju/fastmcp-production-template/issues) to see if someone else has already created a ticket. If not, go ahead and [create one](https://github.com/ManjunathGovindaraju/fastmcp-production-template/issues/new/choose)!

## 2. Setting up your environment

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone https://github.com/ManjunathGovindaraju/fastmcp-production-template.git
cd fastmcp-production-template

# Install dependencies
make install
# Alternatively: uv sync
```

## 3. Development Workflow

We use a `Makefile` to simplify common development tasks:

- `make dev`: Run the MCP server locally.
- `make test`: Run the test suite using `pytest`.
- `make lint`: Run the linter (`ruff`).
- `make format`: Format the code using `ruff format`.

Please ensure that your code passes `make lint` and `make test` before submitting a pull request.

## 4. Submitting a Pull Request

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature-name`).
3. Make your changes.
4. Run tests and linting (`make test` and `make lint`).
5. Commit your changes (`git commit -m 'Add some feature'`).
6. Push to the branch (`git push origin feature/your-feature-name`).
7. Open a Pull Request.

Please fill out the provided Pull Request template when opening your PR.

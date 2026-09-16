# Contributing to SEEM

Thank you for your interest in contributing to **SEEM (Simulation of Equitable Emergency Mobility)**.

We welcome contributions that improve the quality, reproducibility, maintainability, and scientific value of the
project.

---

# Ways to Contribute

Contributions may include:

* Bug fixes
* Performance improvements
* Documentation enhancements
* New analysis notebooks
* Additional datasets
* Simulation features
* Validation experiments
* Test coverage
* Code refactoring that preserves behavior

Before starting a major feature or architectural change, please open an issue to discuss the proposal.

---

# Development Principles

SEEM is a research-oriented simulation framework.

Contributors should prioritize:

* correctness
* reproducibility
* readability
* maintainability

Avoid introducing unnecessary complexity.

Whenever possible, preserve backwards compatibility.

---

# Repository Structure

The repository is organized into logical components:

* `simulation/` — core simulation framework
* `analysis/` — analysis scripts and notebooks
* `data/` — datasets and map resources
* `outputs/` — generated simulation results
* `scripts/` — project entry points
* `archive/` — historical research artifacts

Please keep new files within the appropriate directory.

---

# Coding Standards

Please follow these guidelines:

* Follow PEP 8.
* Use descriptive snake_case names for modules, functions, and variables.
* Keep functions focused and reasonably small.
* Add docstrings to public classes and functions.
* Prefer explicit imports.
* Remove unused imports and dead code.
* Avoid hardcoded absolute paths.

---

# Documentation

If your contribution changes:

* repository structure,
* public APIs,
* configuration,
* scripts,
* notebooks,

please update the relevant documentation.

Documentation should always reflect the current repository state.

---

# Testing

Before submitting a pull request, verify that:

* imports succeed,
* modified scripts execute successfully,
* configuration paths remain valid,
* no existing functionality has been broken.

If adding new functionality, include appropriate tests whenever practical.

---

# Pull Requests

Each pull request should:

* have a clear title,
* explain the motivation,
* summarize the implementation,
* describe any behavioral changes,
* update documentation if necessary.

Keep pull requests focused on a single logical change.

---

# Commit Messages

Use clear, descriptive commit messages.

Examples:

* Refactor simulation initialization
* Fix GTFS graph loading
* Improve evacuation analytics documentation
* Add accessibility metrics

Avoid generic messages such as "Update" or "Fix."

---

# Reporting Issues

When reporting a bug, include:

* operating system
* Python version
* dependency versions
* reproduction steps
* expected behavior
* observed behavior
* relevant logs or error messages

Minimal reproducible examples are highly appreciated.

---

# Code of Conduct

Please communicate respectfully and constructively.

We strive to maintain a welcoming, collaborative, and inclusive research environment.

---

# Citation

If this repository contributes to your research, please cite the software using the metadata provided in `CITATION.cff`.

If an accompanying publication is available, please cite both the software and the publication.

---

Thank you for helping improve SEEM and supporting open, reproducible research.

Title: requirements.txt

Overview
- Purpose: Python dependency list for optional CV workflows and testing.
- Scope: The core game runs on the standard library; CV and test tooling are
  listed here for convenience.

Contents
- `numpy<2`: numerical dependency for some CV tooling.
- `pytest`: test runner for unit tests.
- `ultralytics`: YOLO model runtime used by calibration and inference scripts.

---

Title: pyproject.toml

Overview
- Purpose: Project metadata and tool configuration.
- Scope: Used by Python tooling and packaging.

What to look for
- Tooling configuration for linters/formatters (if present).
- Build system settings (if configured).

Why it matters
- A single configuration file keeps developer tooling consistent.

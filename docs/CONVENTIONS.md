# Coding Conventions

This document outlines the coding standards and conventions to be followed when contributing to the SubTracker project.

## File Naming

- Python module files: Use snake_case (lowercase with underscores) for all module filenames (e.g., `subscription_service.py`, `date_utils.py`)
- Test files: Prefix with `Test` followed by the name of the module being tested (e.g., `TestSubscriptionService.py`)
- Documentation files: Use UPPER_CASE for documentation files (e.g., `README.md`, `CONVENTIONS.md`)

## Directory Structure

- Source code: All application code should be in the `src` directory
- Tests: All tests should be in the `tests` directory, mirroring the structure of `src`
- Documentation: All documentation should be in the `docs` directory
- Configuration: Project-wide configuration files should be in the `config` directory

## Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines
- Maximum line length: 100 characters
- Use 4 spaces for indentation, not tabs
- Use docstrings for all modules, classes, and functions

### Import Statements

- Group imports in the following order, with a blank line between each group:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library-specific imports
- Prefer absolute imports over relative imports for clarity

```python
# Standard library imports
import os
import json
from datetime import date

# Third-party imports
import pytest
from dateutil.relativedelta import relativedelta

# Local application imports
from src.models.subscription import Subscription
from src.utils.date_utils import calculate_next_renewal_date
```

### Docstrings

- Use the Google docstring format for all docstrings
- Include type annotations in function signatures
- Document parameters, return values, and exceptions

```python
def calculate_next_renewal_date(start_date: date, cycle: BillingCycle) -> date:
    """
    Calculate the next renewal date from a start date.

    Args:
        start_date: The initial start date of the subscription
        cycle: The billing cycle

    Returns:
        The calculated next renewal date

    Raises:
        ValueError: If the billing cycle is invalid or cannot be calculated
    """
```

## Commenting

- Use comments sparingly and only to explain complex logic or reasoning
- Do not use comments to explain what the code does (that should be clear from the code itself)
- Use TODOs with a GitHub issue number for code that needs to be revisited

```python
# TODO(#123): Refactor this method to handle edge cases
```

## Error Handling

- Use logging instead of print statements for error reporting
- Use specific exceptions rather than generic ones
- Handle exceptions at the appropriate level of abstraction

```python
try:
    # Some operation that might fail
except SpecificException as e:
    logger.error(f"Specific operation failed: {e}")
    # Handle or re-raise as appropriate
```

## Testing

- Write tests for all new features
- Maintain high test coverage (aim for at least 80%)
- Use pytest fixtures where appropriate
- Use descriptive test names that explain what is being tested

```python
def test_monthly_renewal_date_is_calculated_correctly():
    # Test implementation
```

## Version Control

- Use clear, descriptive commit messages
- Prefix commit messages with the type of change (e.g., "fix:", "feat:", "docs:")
- Reference issue numbers in commit messages when applicable

## Miscellaneous

- Avoid magic numbers and strings; use constants or configuration values
- Use type annotations for all function definitions
- Prefer composition over inheritance
- Keep functions small and focused on a single responsibility

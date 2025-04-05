# Coding Conventions

This document outlines the coding style and naming conventions to be followed throughout the SubTracker project to ensure consistency and readability.

## 1. Naming Conventions

*   **Files and Directories:**
    *   Python files use `snake_case.py` for utility and service files
    *   Use `PascalCase.py` for classes, especially UI components (e.g., `MainScreen.py`)
    *   Directories are always lowercase with underscores (e.g., `utils/`, `services/`)
*   **Python Variables:**
    *   Use `snake_case` for regular variables and function names (e.g., `user_data`, `get_subscription_details()`).
*   **Python Functions:**
    *   Use `snake_case` for function names (e.g., `get_user_data()`).
    *   Prefix private/helper functions with underscore (e.g., `_load_data()`).
*   **Python Classes/Components:**
    *   Use `PascalCase` (e.g., `Subscription`, `MainScreen`).
*   **Constants:**
    *   Use `UPPER_SNAKE_CASE` for constants (e.g., `API_BASE_URL`, `DEFAULT_CURRENCY`).
*   **GUI/TUI Widgets:**
    *   For PyQt6: Use `PascalCase` for class names, `camelCase` for method names (Qt convention)
    *   For Textual: Use `PascalCase` for widget classes, `snake_case` for methods

## 2. Code Formatting

*   **Style Guide:** We adhere to the [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/).
*   **Line Length:** Maximum line length is 88 characters.
*   **Imports:**
    *   Group imports in the following order: standard library imports, related third-party imports, local application/library specific imports.
    *   Separate groups with a blank line.
    *   Avoid wildcard imports (`from module import *`).
*   **Indentation:** Use 4 spaces for indentation, not tabs.
*   **String Quotes:** Use single quotes for short strings, double quotes for docstrings and longer strings.

## 3. Documentation

*   **Docstrings:** All modules, classes, functions, and methods have docstrings explaining their purpose, arguments, and return values. We use Google-style docstrings:

```python
def function_name(param1, param2):
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.

    Raises:
        ExceptionType: When and why this exception is raised.
    """
```

*   **Comments:**
    *   Use inline comments (`#`) to explain complex or non-obvious sections of code
    *   Keep comments up-to-date with code changes
    *   Comments should explain "why", not "what" (the code should be clear enough to explain "what")

## 4. Project Structure Conventions

*   **Module Organization:**
    *   Place related functionality in the same module or package
    *   Organize code by feature rather than by type
    *   Follow the structure outlined in `ARCHITECTURE.md`
*   **Code Structure:**
    *   Keep functions and methods focused on a single responsibility
    *   Limit function/method size to maintain readability
    *   Extract complex logic into helper functions/methods

## 5. UI Specific Conventions

### GUI (PyQt6)

*   Widget naming:
    *   Suffix widgets with their type (e.g., `nameLabel`, `saveButton`)
    *   Consistent naming for actions and slots
*   Layout:
    *   Use layouts instead of fixed positioning
    *   Follow Qt's parent-child relationships consistently

### TUI (Textual)

*   Component design:
    *   Custom TUI components inherit from appropriate Textual base classes
    *   Use Textual's message system for component communication
*   Styling:
    *   Use TCSS (Textual CSS) for styling TUI components
    *   Keep styling separate from logic when possible

## 6. Testing

*   Tests are placed in the `/tests` directory, mirroring the structure of the `/src` directory.
*   Use descriptive names for test files and functions:
    *   `test_[module_name].py` for test files
    *   `test_[function_name]_[scenario]` for test functions
*   Each test should focus on a single functionality or case.
*   Use fixtures to set up common test data.

## 7. Error Handling

*   Use specific exception types instead of generic `Exception`
*   Handle exceptions at appropriate levels
*   Provide informative error messages
*   Log errors for debugging while providing user-friendly messages to the UI

## 8. Version Control

*   Commit messages follow a consistent format:
    *   Start with a type: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, etc.
    *   Use present tense, imperative style (e.g., "Add feature" not "Added feature")
    *   Keep the first line under 50 characters
    *   Provide details in the commit body if necessary

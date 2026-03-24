# Coding Conventions

**Analysis Date:** 2024-07-29

## Naming Patterns

**Files:**
- `snake_case.py` for Python modules.

**Functions:**
- `snake_case` for all function names (e.g., `start`, `set_language`, `get_model_candidates`). This applies to both synchronous and asynchronous functions.

**Variables:**
- `snake_case` for local variables (e.g., `user_id`, `conn`, `today`).
- `UPPER_SNAKE_CASE` for global constants and configuration values (e.g., `TELEGRAM_TOKEN`, `AUTHORIZED_USER_ID`, `WEEKDAYS_PTBR_SHORT`).

**Types:**
- Type hints are used for some function parameters, specifically `Update` and `ContextTypes.DEFAULT_TYPE` in Telegram handler functions (e.g., `update: Update`, `context: ContextTypes.DEFAULT_TYPE`). Full type hinting is not consistently adopted throughout the codebase.

## Code Style

**Formatting:**
- No explicit code formatter (e.g., Black, autopep8) is configured or detected.
- Formatting appears to be manual, leading to some inconsistencies (e.g., variable blank lines between function definitions in `core/handlers.py`).

**Linting:**
- No explicit linter (e.g., Pylint, Flake8) is configured or detected.

## Import Organization

**Order:**
1. Standard library imports (e.g., `os`, `logging`, `datetime`).
2. Third-party package imports (e.g., `telegram`, `dotenv`, `google.genai`).
3. Local/relative imports (e.g., `.config`, `.database`, `.i18n`).

**Path Aliases:**
- Not detected.

## Error Handling

**Patterns:**
- `try...except Exception` blocks are used for broad error catching, especially around external interactions or potentially failing operations (e.g., API calls, database operations in `core/handlers.py`).
- `RuntimeError` is raised for critical missing configuration values during application startup (e.g., `TELEGRAM_TOKEN` in `core/config.py`).
- `logger.exception` is used to log errors along with their full traceback, indicating a problem (e.g., "A extração do Gemini falhou" in `core/handlers.py`).

## Logging

**Framework:** Standard Python `logging` module.

**Patterns:**
- Logging is configured in `core/config.py` with `logging.basicConfig` set to `INFO` level.
- `logger.info()` is used for general informational messages.
- `logger.warning()` is used for non-critical issues (e.g., missing `GEMINI_API_KEY` in `core/config.py`).
- `logger.exception()` is used when an unhandled exception occurs in an `except` block.

## Comments

**When to Comment:**
- No consistent pattern for comments or docstrings is observed.
- Most functions and modules lack docstrings.

**JSDoc/TSDoc:**
- Not applicable (Python project).

## Function Design

**Size:**
- Functions generally appear to be of moderate size, focusing on a single logical responsibility (e.g., handling a specific Telegram command).

**Parameters:**
- Parameters typically use `snake_case`.
- Type hints for `telegram.Update` and `ContextTypes.DEFAULT_TYPE` are present in handler functions.

**Return Values:**
- Return values vary based on function purpose; no single dominant pattern is evident.

## Module Design

**Exports:**
- Python modules implicitly "export" all top-level definitions. Imports are explicit.

**Barrel Files:**
- Not applicable.

---

*Convention analysis: 2024-07-29*

# AGENTS.md - Agentic Coding Guidelines

## Build/Lint/Test Commands

### Dependencies Installation
```bash
pip install -r requirements.txt  # Python dependencies
chmod +x cleanup               # Make Bash script executable
brew install sqlite3 fdupes rmlint fd ripgrep  # System tools
```

### Testing
```bash
python3 run_tests.py            # Run all tests (requires python3 in PATH)
/usr/local/bin/python3 -m pytest tests/ -v  # Run with pytest directly
/usr/local/bin/python3 -m pytest tests/test_app.py::TestClass::test_method  # Single test
```

### Linting & Code Quality
```bash
python3 -m py_compile app.py ai_analyzer.py  # Syntax check
# No formal linter configured - use py_compile for basic checks
# Note: Some tests require AI/ML dependencies (torch, transformers) to be installed
```

## Code Style Guidelines

### Python
- **Imports**: Standard library → third-party → local (alphabetical within groups)
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: try/except with specific exceptions, meaningful messages
- **Database**: Use context managers (`with get_db_connection() as conn:`)
- **API**: JSON responses with proper HTTP status codes, consistent format
- **Types**: No formal type hints required, but use descriptive variable names

### Bash (cleanup script)
- **Safety**: `set -euo pipefail` at script start
- **Variables**: UPPERCASE for constants, lowercase for locals, always quote `"$var"`
- **Functions**: Clear names, document complex logic
- **Logging**: Use `log()` function for all user messages
- **Colors**: Use predefined color variables for consistent output

### Database Schema
- **Naming**: snake_case for tables/columns
- **Constraints**: Foreign keys for data integrity, indexes on queried columns
- **Types**: TEXT, INTEGER, REAL, DATETIME as appropriate

### General
- **Security**: Never expose sensitive data, extensive exclusion patterns
- **Modularity**: Single responsibility per function
- **Configuration**: Use config.json for adjustable parameters
- **Documentation**: Comments for complex logic only
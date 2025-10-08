# TidyMe - Advanced macOS System Cleanup Service

## Project Overview

This project implements an Advanced macOS System Cleanup Service designed to help macOS users maintain a clean and optimized system. It provides comprehensive tools for:

- Finding and removing duplicate files using advanced hashing algorithms
- Cleaning cache files, temporary files, and development artifacts
- Providing detailed reporting on space usage and cleanup activities
- Running as a background daemon for continuous monitoring
- Storing all activities in a SQLite database for analytics

The service is implemented as a Bash script with a CLI interface that offers both interactive and command-line modes.

## Project Structure

```
.
├── system-cleanup-service.md    # Main documentation and implementation
├── QWEN.md                      # This file
└── logs/
    └── openai/                  # OpenAI API logs (likely from Qwen Code sessions)
```

## Key Components

### Main Service Script
The core functionality is contained in `system-cleanup-service.md`, which includes:
- A comprehensive Bash script for system cleanup operations
- Database schema for logging activities
- Installation instructions
- CLI interface with interactive menu

### Features
1. **Advanced Duplicate Detection**: Uses multiple hashing algorithms (quick, content-based, semantic) to identify duplicates
2. **Smart Cleanup Functions**:
   - Cache cleanup (system and application caches)
   - Temporary file cleanup (downloads, trash, temp directories)
   - Development file cleanup (node_modules, __pycache__, build directories)
3. **Background Daemon**: Continuous monitoring with hourly scans
4. **Database Logging**: SQLite database storage for all operations
5. **Safety Measures**: 
   - Excludes critical system files
   - Automatically protects active development projects
   - Comprehensive error handling

## Installation

The service can be installed by following the instructions in `system-cleanup-service.md`:

1. Create service directories:
   ```bash
   sudo mkdir -p /usr/local/bin/cleanup-service
   sudo mkdir -p /usr/local/var/cleanup-service
   sudo mkdir -p /var/log/cleanup-service
   ```

2. Install dependencies:
   ```bash
   brew install sqlite3 fdupes rmlint fd ripgrep
   ```

3. Set up the database with the provided schema

4. Install the service script and create a symlink for easy access

## Usage

### Interactive Mode
Run `cleanup` to access the interactive menu with options for:
1. Quick Scan & Report
2. Find Duplicates (Advanced)
3. Clean Caches
4. Clean Temporary Files
5. Clean Development Files
6. System Analysis
7. Generate Report
8. Start Background Daemon
9. Stop Background Daemon
10. Complete Cleanup (All)

### Command Line Mode
```bash
# Quick scan and report
cleanup scan

# Clean specific areas
cleanup clean-cache
cleanup clean-temp
cleanup clean-dev

# Full cleanup
cleanup clean-all

# Generate report
cleanup report

# Background service
cleanup daemon-start
cleanup daemon-stop
```

### System Service
The service can be installed as a macOS system service using launchd:
```bash
sudo launchctl load /Library/LaunchDaemons/com.cleanup.service.plist
```

## Development Notes

This project is a Bash-based macOS system utility. Key implementation details include:

- Uses SQLite for data persistence
- Implements multiple file hashing algorithms for duplicate detection
- Employs smart exclusion patterns to protect important files
- Automatically detects active development projects to avoid cleaning them
- Provides detailed logging and reporting capabilities

## Dependencies

- sqlite3: Database operations
- fdupes: Duplicate file detection
- rmlint: File cleanup
- fd: File finding
- ripgrep: Text searching

## Safety Features

- Active project detection prevents cleaning of recently used development directories
- Critical system files are excluded from all operations
- All operations are logged to database and log files
- Database stores full history for audit trails
- Background daemon runs with minimal system impact
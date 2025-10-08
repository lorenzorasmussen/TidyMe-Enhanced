# TidyMe - Advanced macOS System Cleanup Service

## Project Overview

TidyMe is an intelligent, automated system cleanup service designed for macOS. Its primary purpose is to reclaim disk space by efficiently identifying and removing duplicate files, clearing system and application caches, and cleaning temporary and development-related files.

The project is implemented as a comprehensive bash script (`cleanup`) that serves as both a command-line interface (CLI) and the core logic for the cleanup operations. It leverages standard macOS utilities and external tools (like `sqlite3`, `fdupes`, `rmlint`, `fd`, `ripgrep`) for its functionality.

Key architectural aspects include:
*   **Modular Bash Script:** The `cleanup` script is well-structured with functions for different cleanup tasks, database interactions, and daemon control.
*   **Configuration-driven:** Behavior is highly customizable via `config.json`, allowing users to define directories, daemon intervals, and exclusion patterns.
*   **Background Daemon:** Can run as a persistent background service using macOS `launchd` (configured via `launchd/com.tidyme.service.plist`) to perform periodic scans and cleanups.
*   **SQLite Database:** Utilizes an SQLite database (`cleanup.db`) for logging all operations, scan results, and cleanup actions, providing detailed analytics and audit trails.
*   **Advanced Duplicate Detection:** Employs multiple hashing algorithms (quick, content-based, semantic) to accurately identify duplicate files.
*   **Safety Features:** Includes mechanisms to exclude critical system files and protect active development projects based on recent activity.

## Building and Running

TidyMe is primarily a bash script, so "building" involves making the script executable.

### Prerequisites

*   macOS 10.12 or later
*   [Homebrew](https://brew.sh/) package manager

### Installation

1.  **Make the CLI script executable:**
    ```bash
    chmod +x cleanup
    ```

2.  **Install dependencies using Homebrew:**
    ```bash
    brew install sqlite3 fdupes rmlint fd ripgrep
    ```

3.  **(Optional) Install as a system service:**
    To run TidyMe as a background daemon, copy the `cleanup` script to a system location and load the `launchd` plist.
    ```bash
    sudo cp cleanup /usr/local/bin/tidyme
    sudo cp launchd/com.tidyme.service.plist /Library/LaunchDaemons/
    sudo launchctl load -w /Library/LaunchDaemons/com.tidyme.service.plist
    ```

### Usage

The `cleanup` script can be run directly from the project directory or from `/usr/local/bin/tidyme` if installed as a system service.

**Command-Line Interface (CLI) Usage:**

```bash
# Show help
./cleanup --help

# Quick scan and report (finds duplicates and generates a report)
./cleanup scan

# Clean specific areas
./cleanup clean-cache       # Clean caches
./cleanup clean-temp        # Clean temporary files
./cleanup clean-dev         # Clean development files

# Full cleanup (runs all cleanups)
./cleanup clean-all

# Generate report
./cleanup report

# Daemon control
./cleanup daemon-start      # Start background daemon
./cleanup daemon-stop       # Stop background daemon
# Note: Daemon status can be checked via `launchctl list | grep tidyme` if installed as a service.
```

**Interactive Mode:**

Run `./cleanup` without any arguments to access the interactive menu:

```bash
./cleanup
```

## Configuration

The service's behavior is controlled by the `config.json` file. This file allows customization of various parameters:

*   **`directories`**: Defines paths for data and logs.
*   **`daemon`**: Configures the background daemon's `scan_interval` (in seconds) and `pid_file` location.
*   **`exclusions`**: Specifies glob patterns for files and directories to be excluded from general, cache, and temporary file cleanups. This is crucial for protecting important data.
*   **`cleanup`**: Detailed settings for each cleanup category:
    *   `cache`: `min_age_days` and specific `patterns` for cache files.
    *   `temp`: `min_age_days` and `patterns` for temporary files.
    *   `dev`: `min_age_days`, `active_project_days` (for protecting recently active git projects), and `patterns` for development artifacts (e.g., `node_modules`, `__pycache__`).
*   **`duplicate_detection`**: Parameters for duplicate finding, including `min_file_size` and `semantic_similarity_threshold`.

Example `config.json` structure:

```json
{
  "directories": {
    "data": "/usr/local/var/tidyme",
    "logs": "/var/log/tidyme"
  },
  "daemon": {
    "scan_interval": 3600,
    "pid_file": "/var/run/tidyme.pid"
  },
  "exclusions": {
    "patterns": [
      "*/Library/Caches/com.apple.*",
      "*/.git/*",
      "*/.ssh/*"
    ],
    "cache_exclusions": [],
    "temp_exclusions": []
  },
  "cleanup": {
    "cache": {
      "min_age_days": 3,
      "patterns": []
    },
    "temp": {
      "min_age_days": 1,
      "patterns": []
    },
    "dev": {
      "min_age_days": 14,
      "active_project_days": 7,
      "patterns": []
    }
  },
  "duplicate_detection": {
    "min_file_size": 1024,
    "semantic_similarity_threshold": 0.8
  }
}
```

## Development Conventions

*   **Bash Scripting:** The core logic is implemented in bash, emphasizing shell scripting best practices.
*   **SQLite for Data Persistence:** All operational logs, scan results, and cleanup actions are stored in an SQLite database, allowing for detailed reporting and analysis.
*   **Modular Design:** Functions are used extensively within the `cleanup` script to separate concerns and improve readability.
*   **Error Handling:** Basic error handling is present using `set -euo pipefail` and `2>/dev/null` for suppressing errors.
*   **Logging:** Operations are logged to a file (`cleanup.log`) and the SQLite database.
*   **External Tool Integration:** Relies on external command-line tools like `find`, `stat`, `shasum`, `sqlite3`, `du`, `rm`, `uuidgen`, and potentially `fdupes`, `rmlint`, `fd`, `ripgrep` for specific tasks.
*   **No explicit testing framework:** The project does not appear to have a dedicated testing framework. Testing would likely involve manual execution and verification of logs and file system changes.

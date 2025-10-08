# TECHNICAL DATA EXTRACTION FROM SYSTEM CLEANUP SERVICE

## TECHNICAL DATA EXTRACTION

### File Paths and Directory Structures
- `/usr/local/bin/cleanup-service/` - Main service directory
- `/usr/local/var/cleanup-service/` - Data storage directory
- `/var/log/cleanup-service/` - Log directory
- `/usr/local/bin/cleanup-service/cleanup-service.sh` - Main service script
- `/usr/local/bin/cleanup-service/install.sh` - Installation script
- `/usr/local/var/cleanup-service/cleanup.db` - SQLite database file
- `/var/log/cleanup-service/cleanup.log` - Log file
- `/var/log/cleanup-service/daemon.log` - Daemon stdout log
- `/var/log/cleanup-service/daemon.error.log` - Daemon stderr log
- `/Library/LaunchDaemons/com.cleanup.service.plist` - macOS launch daemon configuration

### URLs and API Endpoints
- `https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh` - Homebrew installation script

### Configuration Examples
```xml
<!-- Launch Daemon Configuration -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cleanup.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cleanup-service/cleanup-service.sh</string>
        <string>daemon-start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/cleanup-service/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/cleanup-service/daemon.error.log</string>
</dict>
</plist>
```

### Security Protocols and Authentication
- Uses `sudo` for privileged operations
- Exclusion patterns to protect critical system files:
  - `*/Library/Caches/com.apple.*`
  - `*/.ssh/*`
  - `*/.aws/*`
  - `*/.kube/*`
- File permission checking with `-r` flag before operations
- Active project detection to prevent cleaning recently used directories

### Validation Procedures
- File readability checks before processing
- Error handling with try/catch equivalent patterns
- Database transaction logging for all operations
- Size validation before file operations

### Transport Methods
- Direct file system operations via Bash commands
- SQLite database for data persistence
- Standard output/error redirection for logging
- macOS launchd for service management

## CONVERSATION DATA MAPPING

### Technical Transitions and Catalysts
1. From manual cleanup to automated service
2. From basic duplicate detection to advanced multi-algorithm approach
3. From single-run scripts to background daemon service
4. From simple file deletion to intelligent exclusion patterns

### Problem-Solving Sequences
1. **Duplicate Detection Optimization**:
   - Phase 1: Size-based grouping for efficiency
   - Phase 2: Hash-based exact duplicate detection
   - Phase 3: Semantic similarity for text files
   
2. **Safety Implementation**:
   - Exclusion pattern development
   - Active project detection
   - Error handling implementation

3. **System Integration**:
   - CLI interface development
   - Database logging implementation
   - Launchd daemon configuration

### Framework Developments
- Modular function design for different cleanup types
- Database schema for persistent logging
- Interactive menu system for user experience
- Command-line interface for automation

### Technical Constraints and Solutions
- **Constraint**: Large file processing efficiency
  - **Solution**: Quick hash algorithm sampling first/middle/last chunks
- **Constraint**: System file protection
  - **Solution**: Comprehensive exclusion patterns
- **Constraint**: Active project preservation
  - **Solution**: Git repository detection with recent activity checking

## IMPLEMENTATION DATA HARVEST

### Critical Commands and Scripts
```bash
# Directory creation
sudo mkdir -p /usr/local/bin/cleanup-service
sudo mkdir -p /usr/local/var/cleanup-service
sudo mkdir -p /var/log/cleanup-service

# Dependency installation
brew install sqlite3 fdupes rmlint fd ripgrep

# Service installation
sudo cp cleanup-service.sh /usr/local/bin/cleanup-service/
sudo chmod +x /usr/local/bin/cleanup-service/cleanup-service.sh
sudo ln -sf /usr/local/bin/cleanup-service/cleanup-service.sh /usr/local/bin/cleanup

# Daemon management
sudo launchctl load /Library/LaunchDaemons/com.cleanup.service.plist
sudo launchctl start com.cleanup.service
```

### JSON Configurations
```json
{
  "Label": "com.cleanup.service",
  "ProgramArguments": [
    "/usr/local/bin/cleanup-service/cleanup-service.sh",
    "daemon-start"
  ],
  "RunAtLoad": true,
  "KeepAlive": true,
  "StandardOutPath": "/var/log/cleanup-service/daemon.log",
  "StandardErrorPath": "/var/log/cleanup-service/daemon.error.log"
}
```

### Function Call Protocols
- `find_duplicates_advanced` - Main duplicate detection function
- `cleanup_caches_advanced` - Cache cleanup function
- `cleanup_temp_advanced` - Temporary file cleanup function
- `cleanup_development_advanced` - Development artifact cleanup function
- `db_execute` - Database query execution wrapper
- `calculate_file_hash` - Multi-algorithm file hashing

### System Integration Points
- SQLite database for data persistence
- macOS launchd for daemon management
- Homebrew for dependency management
- Standard filesystem APIs for file operations

## PATTERN DATA SYNTHESIS

### Established Frameworks
1. **Modular Cleanup Architecture**:
   - Separate functions for different cleanup types
   - Common database logging interface
   - Shared configuration and utility functions

2. **Database Schema Pattern**:
   - Scans table for operation tracking
   - Files table for file metadata
   - Duplicates table for duplicate tracking
   - Cleanup_log table for action logging

3. **Safety Pattern**:
   - Pre-operation validation
   - Exclusion pattern matching
   - Error logging and handling
   - Active project protection

### Best Practices
- Use of `set -euo pipefail` for strict error handling
- Temporary file management with process-specific directories
- Comprehensive logging for all operations
- User-friendly colored output with emoji indicators
- Dry-run capability through function modularity

### Technical Patterns
- Multi-phase processing for efficiency
- Pattern-based file exclusion
- Size-based pre-filtering for duplicate detection
- Semantic similarity checking for text files
- Database transaction logging for all operations

### Compliance Requirements
- SQLite database schema compliance
- macOS launchd plist format compliance
- POSIX shell scripting compliance
- File system permission model compliance

## ACTIONABLE DATA COMPILATION

### Implementation Instructions

1. **Service Installation**:
   ```bash
   # Create directories
   sudo mkdir -p /usr/local/bin/cleanup-service
   sudo mkdir -p /usr/local/var/cleanup-service
   sudo mkdir -p /var/log/cleanup-service
   
   # Install dependencies
   brew install sqlite3 fdupes rmlint fd ripgrep
   
   # Initialize database with schema
   sqlite3 /usr/local/var/cleanup-service/cleanup.db < schema.sql
   ```

2. **Database Schema Setup**:
   ```sql
   CREATE TABLE IF NOT EXISTS scans (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
       scan_type TEXT,
       files_found INTEGER,
       total_size INTEGER,
       status TEXT
   );
   
   CREATE TABLE IF NOT EXISTS files (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       path TEXT UNIQUE,
       size INTEGER,
       hash TEXT,
       file_type TEXT,
       last_access DATETIME,
       last_modified DATETIME,
       is_duplicate INTEGER DEFAULT 0,
       duplicate_group TEXT,
       confidence_score REAL,
       scan_id INTEGER,
       FOREIGN KEY (scan_id) REFERENCES scans (id)
   );
   
   CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash);
   CREATE INDEX IF NOT EXISTS idx_files_size ON files(size);
   ```

3. **Daemon Configuration**:
   ```bash
   # Create launchd plist
   sudo tee /Library/LaunchDaemons/com.cleanup.service.plist > /dev/null << 'EOF'
   [PLIST CONTENT]
   EOF
   
   # Load and start daemon
   sudo launchctl load /Library/LaunchDaemons/com.cleanup.service.plist
   sudo launchctl start com.cleanup.service
   ```

### Critical Dependencies
1. sqlite3 - Database operations
2. fdupes - Duplicate file detection
3. rmlint - File cleanup operations
4. fd - Fast file finding
5. ripgrep - Text searching capabilities
6. Homebrew - Package management
7. macOS launchd - Service management

### Initialization Sequences
1. Directory structure creation
2. Database initialization
3. Dependency installation
4. Script deployment
5. Daemon registration
6. Service activation

### Troubleshooting Patterns
1. **Database Issues**:
   - Check database file permissions
   - Verify schema integrity
   - Review database logs

2. **Daemon Problems**:
   - Check launchd plist syntax
   - Verify service permissions
   - Review daemon logs

3. **File Operation Failures**:
   - Check file permissions
   - Verify exclusion patterns
   - Review error logs

### Integration Guidelines
1. **Database Integration**:
   - Use consistent table schemas
   - Implement proper indexing
   - Follow transaction logging patterns

2. **Service Integration**:
   - Follow macOS launchd conventions
   - Implement proper logging paths
   - Use standard exit codes

3. **File System Integration**:
   - Implement comprehensive exclusion patterns
   - Use safe file operation practices
   - Follow POSIX compliance standards
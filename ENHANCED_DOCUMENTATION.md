# 🧹 Enhanced TidyMe - Advanced macOS System Cleanup Service

An intelligent, automated system cleanup service for macOS that helps you reclaim disk space by finding and removing duplicate files, clearing caches, and cleaning temporary files. Built with advanced algorithms, safety features, and AI-powered analysis to ensure your system stays clean without risking important data.

## 🌟 Enhanced Features

### Advanced Duplicate Detection
- **Size-based grouping** for efficiency
- **Hash-based exact duplicate detection** using multiple algorithms
- **Semantic similarity checking** for text files
- **AI-powered pattern recognition** for near-duplicates

### Smart Cleanup Functions
- **Cache cleanup** (system and application caches)
- **Temporary file cleanup** (downloads, trash, temp directories)
- **Development file cleanup** (node_modules, __pycache__, build directories)
- **System file analysis** (safe system cache cleanup)

### Safety Measures
- **Enhanced Safety Classification System**:
  - 🟢 **SAFE** - No risk, files regenerate automatically
  - 🟡 **CAUTION** - Low risk, may require app restart
  - 🟠 **WARNING** - Medium risk, backup recommended
  - 🔴 **DANGER** - High risk, expert review required
- **Active Project Protection** - Automatically detects git repositories with recent activity
- **Comprehensive Exclusion System** - Protects critical system files and user data
- **Interactive Confirmation** - User must approve all destructive operations
- **Automatic Backup Creation** - Creates backups before destructive operations
- **Self-Healing Restore Scripts** - Generates restore scripts for recovered data

### Advanced Features
- **Background Daemon** - Continuous monitoring with configurable scan intervals
- **Database Logging** - SQLite database storage for all operations with detailed analytics
- **CLI Interface** - Both interactive menu and command-line modes for flexibility
- **Web Interface** - Flask-based web server with real-time dashboard
- **Detailed Reporting** - Space usage analysis and cleanup reports
- **AI Analysis** - Intelligent insights and recommendations
- **Modular Design** - Easily configurable parameters and extensible architecture

## 🛡️ Safety Classification System

### 🟢 SAFE - No Risk
Operations that pose no risk to system functionality or user data:
- Cache file deletion (older than configured retention period)
- Temporary file deletion
- Log file cleanup (older than configured retention period)

### 🟡 CAUTION - Low Risk
Operations that may require application restart or have minor impact:
- Development artifact cleanup (node_modules, __pycache__, etc.)
- Browser cache cleanup
- Application support cache cleanup

### 🟠 WARNING - Medium Risk
Operations that require backup and careful consideration:
- Large directory cleanup
- Duplicate file removal
- Configuration cache cleanup

### 🔴 DANGER - High Risk
Operations that require expert review and extreme caution:
- System file modification
- Critical application data cleanup
- Root-level directory operations

## 📁 Project Structure

```
.
├── cleanup                   # Main executable CLI interface
├── app.py                    # Web interface Flask application
├── ai_analyzer.py            # AI-powered analysis engine
├── config.json               # Configuration file for adjustable parameters
├── launchd/                  # Launchd plist files (macOS)
├── systemd/                  # Systemd service files (Linux) - placeholder
├── data/                     # Data directory for database and logs
│   ├── cleanup.db            # SQLite database for operations tracking
│   └── cleanup.log           # Log file for operations
├── README.md                 # This file
├── ENHANCED_DOCUMENTATION.md # Enhanced documentation
├── agents.md                 # Context for AI agents
├── system-cleanup-service.md # Original implementation documentation
└── logs/
    └── openai/               # OpenAI API logs (Qwen Code sessions)
```

## 🔧 Configuration

The service can be configured through the `config.json` file with enhanced retention policies:

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
  "safety_levels": {
    "safe": "No risk, files regenerate automatically",
    "caution": "Low risk, may require app restart",
    "warning": "Medium risk, backup recommended",
    "danger": "High risk, expert review required"
  },
  "exclusions": {
    "patterns": [
      "*/Library/Caches/com.apple.*",
      "*/.git/*",
      "*/.svn/*",
      "*/node_modules/*",
      "*/.Trash/*"
    ],
    "security_patterns": [
      "*.key",
      "*.pem",
      "*.p12",
      "*.crt",
      "*.cer"
    ],
    "config_patterns": [
      "*.env",
      ".env.*",
      "config",
      "*.conf"
    ]
  },
  "cleanup": {
    "cache": {
      "min_age_days": 3
    },
    "temp": {
      "min_age_days": 1
    },
    "dev": {
      "min_age_days": 14,
      "active_project_days": 7
    }
  },
  "retention_policies": {
    "npm_cache": 3,
    "yarn_cache": 3,
    "pip_cache": 7,
    "python_cache": 7,
    "vscode_cache": 7,
    "chrome_cache": 3,
    "safari_cache": 7,
    "xcode_derived_data": 7,
    "jetbrains_cache": 7,
    "docker_cache": 7,
    "spotify_cache": 7,
    "slack_cache": 7,
    "zoom_cache": 7,
    "teams_cache": 7,
    "discord_cache": 7,
    "go_build_cache": 1,
    "uv_cache": 1,
    "puppeteer_cache": 1,
    "electron_cache": 1,
    "node_gyp_cache": 1,
    "homebrew_cache": 1,
    "podman_updater_cache": 1,
    "pnpm_cache": 1,
    "trash_contents": 1,
    "qwen_history": 30,
    "pnpm_store": 30,
    "rustup_toolchains": 30,
    "downloads_dmg": 30,
    "downloads_zip": 7,
    "downloads_archives": 7
  },
  "duplicate_detection": {
    "min_file_size": 1024,
    "semantic_similarity_threshold": 0.8
  }
}
```

## 🚀 Usage

### Web Interface (Recommended)

The easiest way to use TidyMe is through the web interface:

```bash
# Start the web server
./start_server.sh

# Open your browser to http://127.0.0.1:5000
```

The web interface provides:
- **Real-time statistics** dashboard
- **One-click cleanup** operations
- **AI-powered insights** and recommendations
- **Interactive reports** and analytics
- **Background job monitoring**

### Local CLI Usage

You can also use the command-line interface directly:

```bash
# Show help
./cleanup --help

# Quick scan and report
./cleanup scan

# Clean specific areas
./cleanup clean-cache       # Clean caches
./cleanup clean-temp        # Clean temporary files
./cleanup clean-dev         # Clean development files

# Full cleanup (with interactive confirmation)
./cleanup clean-all

# Generate report
./cleanup report

# Daemon control
./cleanup daemon start       # Start background daemon
./cleanup daemon stop        # Stop background daemon
./cleanup daemon status      # Check daemon status
```

### Interactive Mode

Run `./cleanup` to access the interactive menu:

```
╔══════════════════════════════════════════════════════════════╗
║                Advanced macOS System Cleanup                ║
╠══════════════════════════════════════════════════════════════╣
║  1. Quick Scan & Report                                      ║
║  2. Find Duplicates (Advanced)                               ║
║  3. Clean Caches                                             ║
║  4. Clean Temporary Files                                    ║
║  5. Clean Development Files                                  ║
║  6. System Analysis                                          ║
║  7. Generate Report                                          ║
║  8. Start Background Daemon                                  ║
║  9. Stop Background Daemon                                   ║
║  10. Complete Cleanup (All)                                  ║
║  0. Exit                                                     ║
╚══════════════════════════════════════════════════════════════╝
```

### REST API

TidyMe also provides a REST API for integration:

```bash
# Get statistics
curl http://127.0.0.1:5000/api/stats

# Run cleanup operation
curl -X POST http://127.0.0.1:5000/api/cleanup/scan

# Get AI insights
curl http://127.0.0.1:5000/api/ai/insights

# Get cleanup report
curl http://127.0.0.1:5000/api/ai/report
```

### AI Features

TidyMe includes AI-powered analysis:

- **Smart Recommendations**: AI suggests optimal cleanup schedules
- **Pattern Analysis**: Identifies cleanup trends and anomalies
- **Predictive Insights**: Forecasts future cleanup needs
- **Intelligent Reporting**: Generates detailed analysis reports

## 🔧 How It Works

### Duplicate Detection Process

1. **Phase 1**: Size-based grouping for efficiency
2. **Phase 2**: Hash-based exact duplicate detection using multiple algorithms
3. **Phase 3**: Semantic similarity checking for text files

### Safety Features

- **Active Project Protection**: Automatically detects git repositories with recent activity (within 7 days) and excludes them from cleanup
- **Critical File Exclusion**: Built-in patterns to protect system files:
  - Apple system caches
  - SSH keys and configurations
  - Cloud credentials (AWS, Kubernetes)
  - Version control directories
- **Interactive Confirmation**: All destructive operations require user approval
- **Backup Creation**: Automatic backup creation before destructive operations
- **Comprehensive Logging**: All operations are logged to both file and database for audit trails

### Cleanup Categories

1. **Cache Files**: System and application caches older than configured retention period
2. **Temporary Files**: Download fragments, trash contents, and temporary directories
3. **Development Artifacts**: node_modules, build directories, Python cache files, etc.

## 📊 Database Schema

The service uses SQLite for data persistence with the following tables:

- `scans`: Operation tracking
- `files`: File metadata and duplicate information
- `duplicates`: Detailed duplicate file tracking
- `cleanup_log`: Action logging for all operations

## 🔒 Security

- No personal data collection
- All operations are local to your machine
- Explicit sudo prompts for privileged operations
- Comprehensive exclusion patterns to protect important files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Thanks to all the open-source tools that make this project possible
- Inspired by the need for intelligent system maintenance on macOS

## 🆘 Support

For issues, feature requests, or questions, please open an issue on the GitHub repository.
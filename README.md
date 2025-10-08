# 🧹 TidyMe - Enhanced macOS System Cleanup Service

An intelligent, automated system cleanup service for macOS with **enhanced safety features** that helps you reclaim disk space by finding and removing duplicate files, clearing caches, and cleaning temporary files. Built with advanced algorithms, comprehensive safety protocols, and AI-powered analysis to ensure your system stays clean without risking important data.

> **NEW: Enhanced Safety Features Implemented!** TidyMe now includes a comprehensive safety classification system, interactive confirmations, automatic backups, and enhanced exclusion patterns.

## 🌟 Enhanced Features

### Enhanced Safety Measures
- **Safety Classification System**:
  - 🟢 **SAFE** - No risk, files regenerate automatically
  - 🟡 **CAUTION** - Low risk, may require app restart
  - 🟠 **WARNING** - Medium risk, backup recommended
  - 🔴 **DANGER** - High risk, expert review required
- **Interactive Confirmation Steps** for all cleanup operations
- **Automatic Backup Creation** before destructive operations
- **Self-Healing Restore Scripts** for recovered data
- **Granular Retention Policies** based on file types and ages

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

### Modern Features
- **Background Daemon** - Continuous monitoring with configurable scan intervals
- **Database Logging** - SQLite database storage for all operations with detailed analytics
- **CLI Interface** - Both interactive menu and command-line modes for flexibility
- **Web Interface** - Flask-based web server with real-time dashboard
- **Detailed Reporting** - Space usage analysis and cleanup reports
- **AI Analysis** - Intelligent insights and recommendations
- **Modular Design** - Easily configurable parameters and extensible architecture

## 📚 Documentation

### 📘 [Enhanced Documentation](ENHANCED_DOCUMENTATION.md)
Complete documentation covering all enhanced features, safety measures, and usage instructions.

### 📗 [Original Documentation](system-cleanup-service.md)
Original implementation documentation for reference.

### 📕 [AI Agent Context](agents.md)
Context information for AI agents working with this project.

## 📁 Project Structure

```
.
├── cleanup                   # Main executable CLI interface
├── app.py                    # Web interface Flask application
├── ai_analyzer.py            # AI-powered analysis engine
├── config.json               # Configuration file for adjustable parameters
├── launchd/                 # Launchd plist files (macOS)
├── systemd/                  # Systemd service files (Linux) - placeholder
├── data/                     # Data directory for database and logs
│   ├── cleanup.db            # SQLite database for operations tracking
│   └── cleanup.log           # Log file for operations
├── README.md                 # This file
├── ENHANCED_DOCUMENTATION.md # Enhanced documentation
├── agents.md                # Context for AI agents
├── system-cleanup-service.md # Original implementation documentation
└── logs/
    └── openai/               # OpenAI API logs (Qwen Code sessions)
```

## 🚀 Quick Start

### Prerequisites

- macOS 10.12 or later
- [Homebrew](https://brew.sh/) package manager

### Installation

1. Make the CLI script executable:
   ```bash
   chmod +x cleanup
   ```

2. Install dependencies:
   ```bash
   brew install sqlite3 fdupes rmlint fd ripgrep
   ```

3. (Optional) Install as system service:
   ```bash
   # Copy to system location
   sudo cp cleanup /usr/local/bin/tidyme
   ```

## 🛡️ Enhanced Safety Features

### Safety Classification System
Every operation is classified by risk level:

- 🟢 **SAFE**: No risk, files regenerate automatically
- 🟡 **CAUTION**: Low risk, may require app restart
- 🟠 **WARNING**: Medium risk, backup recommended
- 🔴 **DANGER**: High risk, expert review required

### Interactive Confirmations
All cleanup operations require explicit user confirmation:

```bash
⚠️  Proceed with cache cleanup? This will delete cache files older than 3 days (y/N): 
```

### Automatic Backups
Before any destructive operation, TidyMe creates automatic backups:
```bash
💾 Creating backup of Caches...
✅ Caches backup successful: /Users/username/backups/tidyme-backup-20231015-143022
```

### Self-Healing Restore Scripts
Each backup includes a restore script:
```bash
🔧 Restore script created: /Users/username/backups/tidyme-backup-20231015-143022/restore.sh
```

## 🧪 Usage Examples

### Web Interface (Recommended)
```bash
# Start the web server
./start_server.sh

# Open your browser to http://127.0.0.1:5000
```

### CLI Interface
```bash
# Show help
./cleanup --help

# Quick scan and report
./cleanup scan

# Clean specific areas (with safety confirmations)
./cleanup clean-cache       # Clean caches
./cleanup clean-temp        # Clean temporary files
./cleanup clean-dev         # Clean development files

# Full cleanup (with safety confirmations)
./cleanup clean-all

# Generate report
./cleanup report
```

## ⚙️ Enhanced Configuration

TidyMe now includes granular retention policies and enhanced exclusion patterns:

```json
{
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
      "*/.Trash/*",
      "*/Library/Application Support/Code/User/*",
      "*/.ssh/*",
      "*/.aws/*",
      "*/.kube/*",
      "*/Desktop/*",
      "*/Documents/*",
      "*/Downloads/*",
      "*/Pictures/*",
      "*/Movies/*",
      "*/Music/*"
    ],
    "security_patterns": [
      "*.key",
      "*.pem",
      "*.p12",
      "*.crt",
      "*.cer",
      "*.der",
      "*.pfx",
      "*.p7b",
      "*.p7c",
      "*.p7s",
      "*.sst"
    ],
    "config_patterns": [
      "*.env",
      ".env.*",
      "config",
      "*.conf",
      "*.ini",
      "*.cfg",
      "*.plist"
    ]
  }
}
```

## 🔧 How It Works

### Enhanced Duplicate Detection Process

1. **Phase 1**: Size-based grouping for efficiency
2. **Phase 2**: Hash-based exact duplicate detection using multiple algorithms
3. **Phase 3**: Semantic similarity checking for text files
4. **Phase 4**: AI-powered pattern recognition for near-duplicates

### Enhanced Safety Features

- **Active Project Protection**: Automatically detects git repositories with recent activity (within 7 days) and excludes them from cleanup
- **Comprehensive Exclusion System**: Enhanced patterns to protect critical files:
  - Security files (*.key, *.pem, *.p12, etc.)
  - Configuration files (*.env, config, *.conf, etc.)
  - Database files (*.sqlite, *.db, etc.)
  - Development files (*.sln, *.csproj, etc.)
  - Documentation files (README*, CHANGELOG*, etc.)
  - Media files (*.jpg, *.png, *.mp4, etc.)
- **Interactive Confirmation**: All destructive operations require user approval
- **Automatic Backup Creation**: Creates backups before destructive operations
- **Self-Healing Restore Scripts**: Generates restore scripts for recovered data
- **Comprehensive Logging**: All operations are logged to both file and database for audit trails

## 📊 Enhanced Database Schema

The service uses SQLite for data persistence with enhanced tables:

- `scans`: Operation tracking with safety levels
- `files`: File metadata and duplicate information
- `duplicates`: Detailed duplicate file tracking with similarity scores
- `cleanup_log`: Action logging for all operations with success/failure status

## 🔒 Security

- No personal data collection
- All operations are local to your machine
- Explicit sudo prompts for privileged operations
- Comprehensive exclusion patterns to protect important files
- Granular retention policies to prevent accidental deletion of important data

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
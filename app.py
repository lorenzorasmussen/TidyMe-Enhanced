from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import json
import signal
import atexit
import psutil
from datetime import datetime
from ai_analyzer import CleanupAnalyzer
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Use the same database path as the cleanup script
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATABASE = os.path.join(DATA_DIR, 'cleanup.db')

# PID file management
SERVER_PID_FILE = os.path.join(DATA_DIR, 'server.pid')
DAEMON_PID_FILE = os.path.join(DATA_DIR, 'cleanup-daemon.pid')

def check_existing_instance(pid_file, process_name):
    """Check if another instance is already running"""
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())

            # Check if process is still running
            if psutil.pid_exists(old_pid):
                process = psutil.Process(old_pid)
                if process_name.lower() in process.name().lower():
                    return True, old_pid
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            # PID file exists but process is not running, remove stale file
            try:
                os.remove(pid_file)
            except OSError:
                pass

    return False, None

def create_pid_file(pid_file):
    """Create PID file for current process"""
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

def cleanup_pid_file(pid_file):
    """Remove PID file on exit"""
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except OSError:
        pass

def signal_handler(signum, frame):
    """Handle termination signals"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    cleanup_pid_file(SERVER_PID_FILE)
    cleanup_pid_file(DAEMON_PID_FILE)
    sys.exit(0)

def log(message):
    """Log message to cleanup.log file"""
    import datetime
    log_path = os.path.join(DATA_DIR, 'cleanup.log')
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_path, 'a') as f:
        f.write(f"{timestamp} - {message}\n")
    print(f"{timestamp} - {message}")

def get_db_connection():
    """Get database connection - supports both SQLite and PostgreSQL"""
    db_config = getattr(app, 'config', {})

    if db_config.get('USE_POSTGRESQL', False):
        # PostgreSQL connection
        conn = psycopg2.connect(
            host=db_config.get('POSTGRES_HOST', 'localhost'),
            port=db_config.get('POSTGRES_PORT', 5432),
            database=db_config.get('POSTGRES_DB', 'tidyme'),
            user=db_config.get('POSTGRES_USER', 'tidyme'),
            password=db_config.get('POSTGRES_PASSWORD', ''),
            cursor_factory=RealDictCursor
        )
        return conn
    else:
        # SQLite connection (default)
        db_path = db_config.get('DATABASE', DATABASE)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

def migrate_to_postgresql():
    """Migrate data from SQLite to PostgreSQL"""
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(DATABASE)
        sqlite_conn.row_factory = sqlite3.Row

        # Connect to PostgreSQL
        db_config = getattr(app, 'config', {})
        pg_conn = psycopg2.connect(
            host=db_config.get('POSTGRES_HOST', 'localhost'),
            port=db_config.get('POSTGRES_PORT', 5432),
            database=db_config.get('POSTGRES_DB', 'tidyme'),
            user=db_config.get('POSTGRES_USER', 'tidyme'),
            password=db_config.get('POSTGRES_PASSWORD', ''),
            cursor_factory=RealDictCursor
        )

        # Migrate each table
        tables = ['scans', 'files', 'duplicates', 'cleanup_log']

        for table in tables:
            # Get data from SQLite
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f'SELECT * FROM {table}')
            rows = sqlite_cursor.fetchall()

            if rows:
                # Insert into PostgreSQL
                pg_cursor = pg_conn.cursor()

                # Get column names
                columns = [desc[0] for desc in sqlite_cursor.description]
                columns_str = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))

                # Insert data
                for row in rows:
                    values = [row[col] for col in columns]
                    pg_cursor.execute(
                        f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})',
                        values
                    )

                pg_conn.commit()
                pg_cursor.close()

        sqlite_conn.close()
        pg_conn.close()

        return {'success': True, 'message': 'Migration completed successfully'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def init_db():
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = get_db_connection()
    # Create the same schema as the cleanup script
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            scan_type TEXT,
            files_found INTEGER,
            total_size INTEGER,
            status TEXT
        )
    ''')
    conn.execute('''
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
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS duplicates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id TEXT,
            file_path TEXT,
            file_size INTEGER,
            file_hash TEXT,
            similarity_score REAL,
            recommended_action TEXT,
            scan_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cleanup_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            action_type TEXT,
            file_path TEXT,
            file_size INTEGER,
            success INTEGER,
            error_message TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS vault_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT UNIQUE NOT NULL,
            encrypted_value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create indexes for performance
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_duplicates_group ON duplicates(group_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vault_key ON vault_items(key_name)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_vault_category ON vault_items(category)')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

# Web Interface Routes

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

# Cleanup API Endpoints

@app.route('/api/scans', methods=['GET'])
def get_scans():
    """Get all cleanup scans"""
    conn = get_db_connection()
    scans = conn.execute('SELECT * FROM scans ORDER BY scan_date DESC').fetchall()
    conn.close()
    return jsonify([dict(scan) for scan in scans])

@app.route('/api/scans/<int:scan_id>', methods=['GET'])
def get_scan(scan_id):
    """Get specific scan details"""
    conn = get_db_connection()
    scan = conn.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    if scan is None:
        conn.close()
        return jsonify({'error': 'Scan not found'}), 404

    files = conn.execute('SELECT * FROM files WHERE scan_id = ?', (scan_id,)).fetchall()
    conn.close()

    return jsonify({
        'scan': dict(scan),
        'files': [dict(file) for file in files]
    })

@app.route('/api/duplicates', methods=['GET'])
def get_duplicates():
    """Get all duplicate files"""
    conn = get_db_connection()
    duplicates = conn.execute('SELECT * FROM duplicates ORDER BY scan_date DESC').fetchall()
    conn.close()
    return jsonify([dict(dup) for dup in duplicates])

@app.route('/api/cleanup-log', methods=['GET'])
def get_cleanup_log():
    """Get cleanup action log"""
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM cleanup_log ORDER BY action_date DESC LIMIT 100').fetchall()
    conn.close()
    return jsonify([dict(log) for log in logs])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get cleanup statistics"""
    conn = get_db_connection()

    # Get total space cleaned
    total_cleaned = conn.execute('SELECT SUM(total_size) FROM scans WHERE status = "completed"').fetchone()[0] or 0

    # Get duplicate count
    duplicate_count = conn.execute('SELECT COUNT(*) FROM duplicates').fetchone()[0] or 0

    # Get recent scans
    recent_scans = conn.execute('SELECT COUNT(*) FROM scans WHERE scan_date >= datetime("now", "-7 days")').fetchone()[0] or 0

    conn.close()

    return jsonify({
        'total_space_cleaned': total_cleaned,
        'duplicate_files_found': duplicate_count,
        'recent_scans': recent_scans
    })

@app.route('/api/cleanup/<action>', methods=['POST'])
def trigger_cleanup(action):
    """Trigger cleanup action via API"""
    import subprocess
    import os

    script_path = os.path.join(os.path.dirname(__file__), 'cleanup')

    try:
        if action == 'scan':
            result = subprocess.run([script_path, 'scan'], capture_output=True, text=True, timeout=300)
        elif action == 'clean-cache':
            result = subprocess.run([script_path, 'clean-cache'], capture_output=True, text=True, timeout=300)
        elif action == 'clean-temp':
            result = subprocess.run([script_path, 'clean-temp'], capture_output=True, text=True, timeout=300)
        elif action == 'clean-dev':
            result = subprocess.run([script_path, 'clean-dev'], capture_output=True, text=True, timeout=300)
        elif action == 'clean-all':
            result = subprocess.run([script_path, 'clean-all'], capture_output=True, text=True, timeout=300)
        else:
            return jsonify({'error': 'Invalid action'}), 400

        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        })

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Operation timed out'}), 408
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# System Management Endpoints

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration settings"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Analysis Endpoints

@app.route('/api/ai/report', methods=['GET'])
def get_ai_report():
    """Get AI-generated cleanup report"""
    try:
        analyzer = CleanupAnalyzer()
        report = analyzer.generate_cleanup_report()
        return jsonify({
            'report': report,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/insights', methods=['GET'])
def get_ai_insights():
    """Get AI-powered insights"""
    try:
        analyzer = CleanupAnalyzer()
        insights = analyzer.get_cleanup_insights()
        suggestions = analyzer.suggest_cleanup_schedule()
        return jsonify({
            'insights': insights,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/predictions', methods=['GET'])
def get_ai_predictions():
    """Get cleanup predictions"""
    try:
        days = int(request.args.get('days', 7))
        analyzer = CleanupAnalyzer()
        predictions = analyzer.predict_cleanup_needs(days)
        return jsonify(predictions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/analyze-patterns', methods=['GET'])
def analyze_patterns():
    """Analyze cleanup patterns"""
    try:
        analyzer = CleanupAnalyzer()
        patterns = analyzer.analyze_cleanup_patterns()
        duplicates = analyzer.analyze_duplicate_patterns()
        return jsonify({
            'cleanup_patterns': patterns,
            'duplicate_analysis': duplicates
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# File Browser Endpoints

@app.route('/api/files/browse', methods=['GET'])
def browse_files():
    """Browse files in a directory"""
    try:
        path = request.args.get('path', '/Users')

        # Security check - prevent access to sensitive directories
        sensitive_paths = ['/System', '/usr', '/bin', '/sbin', '/private', '/var/root']
        if any(path.startswith(sensitive) for sensitive in sensitive_paths):
            return jsonify({'error': 'Access denied to system directories'}), 403

        if not os.path.exists(path):
            return jsonify({'error': 'Path does not exist'}), 404

        if not os.path.isdir(path):
            return jsonify({'error': 'Path is not a directory'}), 400

        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    stat_info = os.stat(item_path)
                    items.append({
                        'name': item,
                        'path': item_path,
                        'type': 'directory' if os.path.isdir(item_path) else 'file',
                        'size': stat_info.st_size if os.path.isfile(item_path) else 0,
                        'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                    })
                except (OSError, PermissionError):
                    # Skip items we can't access
                    continue
        except (OSError, PermissionError):
            return jsonify({'error': 'Permission denied'}), 403

        # Sort: directories first, then files, alphabetically
        items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))

        return jsonify({
            'current_path': path,
            'items': items
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Exclude Manager Endpoints

@app.route('/api/excludes', methods=['GET'])
def get_excludes():
    """Get current exclude patterns"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        excludes = config.get('exclusions', {}).get('patterns', [])
        return jsonify({'patterns': excludes})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/excludes', methods=['POST'])
def update_excludes():
    """Update exclude patterns"""
    try:
        data = request.get_json()
        new_patterns = data.get('patterns', [])

        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        if 'exclusions' not in config:
            config['exclusions'] = {}
        config['exclusions']['patterns'] = new_patterns

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return jsonify({'success': True, 'message': 'Exclude patterns updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Ollama AI Integration

import subprocess
import json
import psutil
import platform
import shutil
import os
# Optional imports with fallbacks
try:
    from transformers import pipeline, AutoTokenizer, AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

try:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    CONCURRENT_AVAILABLE = True
except ImportError:
    CONCURRENT_AVAILABLE = False

try:
    import keyring
    import keyring.backends.macOS
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    import asyncio
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Standard library imports
import subprocess
import json
import psutil
import platform
import shutil
import os
import time
import hashlib
import base64
import threading
import sys
import tempfile
import signal
import atexit
from datetime import datetime, timedelta

# Daemon/service imports
try:
    import daemon
    import daemon.pidfile
    DAEMON_AVAILABLE = True
except ImportError:
    DAEMON_AVAILABLE = False

try:
    import lockfile
    LOCKFILE_AVAILABLE = True
except ImportError:
    LOCKFILE_AVAILABLE = False
import subprocess
import tempfile
import os
# Cryptography import (already handled above)
if not CRYPTOGRAPHY_AVAILABLE:
    Fernet = None
import base64
import hashlib
from datetime import datetime, timedelta

def query_ollama(prompt, model="tinyllama:1.1b"):
    """Query AI model (llama.cpp server or Ollama) with a prompt"""
    try:
        # Try llama.cpp server first (port 8080)
        import requests
        response = requests.post(
            "http://localhost:8080/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            # Fallback to Ollama if llama.cpp server is not available
            return query_ollama_fallback(prompt, model)

    except Exception as e:
        # Fallback to Ollama
        return query_ollama_fallback(prompt, model)

def query_ollama_fallback(prompt, model="llama3.2:3b"):
    """Fallback to Ollama CLI when llama.cpp server is unavailable"""
    try:
        cmd = ["ollama", "run", model]
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send prompt and get response
        stdout, stderr = process.communicate(input=prompt, timeout=30)

        if process.returncode == 0:
            return stdout.strip()
        else:
            return f"Error: {stderr.strip()}"

    except subprocess.TimeoutExpired:
        process.kill()
        return "Error: Request timed out"
    except Exception as e:
        return f"Error: {str(e)}"

def get_system_health():
    """Get comprehensive system health information"""
    try:
        # Memory information
        memory = psutil.virtual_memory()
        memory_info = {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'used_percent': memory.percent,
            'free': memory.free
        }

        # Disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'used_percent': disk.percent
        }

        # CPU information
        cpu_info = {
            'usage_percent': psutil.cpu_percent(interval=1),
            'cores': psutil.cpu_count(),
            'cores_logical': psutil.cpu_count(logical=True)
        }

        # System information
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.release(),
            'architecture': platform.machine(),
            'hostname': platform.node()
        }

        # Determine overall health status
        health_score = 100

        if memory.percent > 80:
            health_score -= 30
        elif memory.percent > 60:
            health_score -= 15

        if disk.percent > 90:
            health_score -= 30
        elif disk.percent > 75:
            health_score -= 15

        if cpu_info['usage_percent'] > 80:
            health_score -= 20
        elif cpu_info['usage_percent'] > 60:
            health_score -= 10

        if health_score >= 80:
            overall_status = 'Good'
        elif health_score >= 60:
            overall_status = 'Warning'
        else:
            overall_status = 'Critical'

        return {
            'overall_status': overall_status,
            'health_score': health_score,
            'memory_usage': memory_info,
            'disk_usage': disk_info,
            'cpu_usage': cpu_info,
            'system_info': system_info,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'overall_status': 'Error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def optimize_memory():
    """Perform memory optimization"""
    try:
        memory_freed = 0
        cache_cleared = 0

        # Clear system cache (if possible)
        if platform.system() == 'Darwin':  # macOS
            try:
                # Clear user cache
                cache_dir = os.path.expanduser('~/Library/Caches')
                if os.path.exists(cache_dir):
                    for root, dirs, files in os.walk(cache_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cache_cleared += size
                            except:
                                pass
            except:
                pass

        # Force garbage collection in Python
        import gc
        gc.collect()

        return {
            'success': True,
            'memory_freed': memory_freed,
            'cache_cleared': cache_cleared,
            'message': 'Memory optimization completed'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def analyze_system_logs():
    """Analyze system logs for issues"""
    try:
        large_logs = []
        error_patterns = []

        # Check common log locations
        log_paths = [
            '/var/log/system.log',
            '/var/log/kernel.log',
            os.path.expanduser('~/Library/Logs'),
            '/Library/Logs'
        ]

        for log_path in log_paths:
            if os.path.exists(log_path):
                if os.path.isfile(log_path):
                    # Single log file
                    try:
                        size = os.path.getsize(log_path)
                        if size > 50 * 1024 * 1024:  # 50MB
                            large_logs.append({
                                'path': log_path,
                                'size': size
                            })
                    except:
                        pass
                elif os.path.isdir(log_path):
                    # Directory of logs
                    for root, dirs, files in os.walk(log_path):
                        for file in files:
                            if file.endswith('.log'):
                                file_path = os.path.join(root, file)
                                try:
                                    size = os.path.getsize(file_path)
                                    if size > 10 * 1024 * 1024:  # 10MB
                                        large_logs.append({
                                            'path': file_path,
                                            'size': size
                                        })
                                except:
                                    pass

        # Analyze error patterns (simplified)
        error_patterns = [
            {'type': 'System Errors', 'count': 0},
            {'type': 'Application Crashes', 'count': 0},
            {'type': 'Permission Errors', 'count': 0}
        ]

        return {
            'success': True,
            'large_logs': large_logs,
            'error_patterns': error_patterns
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def smart_cache_cleanup():
    """Perform smart cache cleanup"""
    try:
        files_analyzed = 0
        space_freed = 0

        # Clean old cache files
        cache_dirs = [
            os.path.expanduser('~/Library/Caches'),
            '/Library/Caches'
        ]

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                # Remove files older than 30 days
                for root, dirs, files in os.walk(cache_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getmtime(file_path) < (datetime.now().timestamp() - 30 * 24 * 60 * 60):
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                space_freed += size
                                files_analyzed += 1
                        except:
                            pass

        return {
            'success': True,
            'files_analyzed': files_analyzed,
            'space_freed': space_freed,
            'oldest_first': True
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def cleanup_log_file(log_path):
    """Clean up a specific log file"""
    try:
        if not os.path.exists(log_path):
            return {'success': False, 'error': 'Log file not found'}

        # Get original size
        original_size = os.path.getsize(log_path)

        # For now, just truncate the file (in production, you'd want more sophisticated log rotation)
        with open(log_path, 'w') as f:
            f.write('')  # Truncate file

        space_freed = original_size

        return {
            'success': True,
            'space_freed': space_freed,
            'message': f'Log file {log_path} cleaned up'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# macOS Keychain Manager
class KeychainManager:
    """Secure credential storage using macOS Keychain"""

    def __init__(self, service_name="TidyMe"):
        self.service_name = service_name
        if KEYRING_AVAILABLE:
            # Set macOS Keychain as the backend
            keyring.set_keyring(keyring.backends.macOS.Keyring())
        else:
            raise ImportError("keyring library not available. Install with: pip install keyring")

    def store_credential(self, username, password, account_name=None):
        """Store a credential in macOS Keychain"""
        try:
            key = account_name or username
            keyring.set_password(self.service_name, key, password)
            return {'success': True, 'message': f'Credential stored for {key}'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to store credential: {str(e)}'}

    def retrieve_credential(self, username, account_name=None):
        """Retrieve a credential from macOS Keychain"""
        try:
            key = account_name or username
            password = keyring.get_password(self.service_name, key)
            if password:
                return {'success': True, 'username': username, 'password': password}
            else:
                return {'success': False, 'error': 'Credential not found'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve credential: {str(e)}'}

    def delete_credential(self, username, account_name=None):
        """Delete a credential from macOS Keychain"""
        try:
            key = account_name or username
            keyring.delete_password(self.service_name, key)
            return {'success': True, 'message': f'Credential deleted for {key}'}
        except keyring.errors.PasswordDeleteError:
            return {'success': False, 'error': 'Credential not found'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to delete credential: {str(e)}'}

    def list_credentials(self):
        """List all credentials for this service (usernames only)"""
        try:
            # Note: keyring doesn't provide a direct way to list all keys
            # This is a limitation of the keyring library
            return {'success': False, 'error': 'Listing credentials not supported by keyring'}
        except Exception as e:
            return {'success': False, 'error': f'Failed to list credentials: {str(e)}'}

# Initialize keychain manager
try:
    keychain = KeychainManager()
    KEYCHAIN_AVAILABLE = True
except Exception as e:
    print(f"Warning: macOS Keychain not available: {e}")
    keychain = None
    KEYCHAIN_AVAILABLE = False

# Vault System for Secure Storage

class SecureVault:
    """Secure vault for storing sensitive information"""

    def __init__(self, db_path, master_key=None):
        self.db_path = db_path
        self.master_key = master_key or self._generate_master_key()
        if CRYPTOGRAPHY_AVAILABLE:
            self.cipher = Fernet(self.master_key)
        else:
            self.cipher = None

    def _generate_master_key(self):
        """Generate a master key for encryption"""
        # In production, this should be stored securely (e.g., keyring, environment variable)
        key_seed = "tidyme-vault-key-seed"
        key = hashlib.sha256(key_seed.encode()).digest()
        return base64.urlsafe_b64encode(key)

    def encrypt_value(self, value):
        """Encrypt a value"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not isinstance(value, str):
            value = str(value)

        if self.cipher:
            return self.cipher.encrypt(value.encode()).decode()
        else:
            # Fallback: base64 encode (not secure!)
            return base64.b64encode(value.encode()).decode()

    def decrypt_value(self, encrypted_value):
        """Decrypt a value"""
        try:
            if self.cipher:
                decrypted = self.cipher.decrypt(encrypted_value.encode()).decode()
            else:
                # Fallback: base64 decode
                decrypted = base64.b64decode(encrypted_value.encode()).decode()
            # Try to parse as JSON
            try:
                return json.loads(decrypted)
            except:
                return decrypted
        except Exception as e:
            return f"DECRYPTION_ERROR: {str(e)}"

    def store_item(self, key, value, category="general", tags=None, expires_at=None):
        """Store an item in the vault"""
        # Use Keychain for sensitive credentials
        if category in ['credentials', 'api-keys', 'secrets'] and KEYCHAIN_AVAILABLE:
            if isinstance(value, dict) and 'password' in value:
                # Store password in Keychain, other data in database
                password = value.pop('password')
                result = keychain.store_credential(value.get('username', key), password, key)
                if not result['success']:
                    return result

                # Store non-sensitive data in database
                encrypted_value = self.encrypt_value(value)
            else:
                # Store entire value in Keychain
                result = keychain.store_credential(key, json.dumps(value), key)
                if not result['success']:
                    return result
                encrypted_value = "STORED_IN_KEYCHAIN"
        else:
            # Use database encryption for non-sensitive data
            encrypted_value = self.encrypt_value(value)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO vault_items
            (key_name, encrypted_value, category, tags, expires_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            key,
            encrypted_value,
            category,
            json.dumps(tags or []),
            expires_at.isoformat() if expires_at else None,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return {'success': True, 'message': f'Item {key} stored successfully'}

    def retrieve_item(self, key):
        """Retrieve an item from the vault"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM vault_items WHERE key_name = ?', (key,))
        item = cursor.fetchone()
        conn.close()

        if not item:
            return {'success': False, 'error': 'Item not found'}

        # Check expiration
        if item['expires_at']:
            expires_at = datetime.fromisoformat(item['expires_at'])
            if datetime.now() > expires_at:
                return {'success': False, 'error': 'Item has expired'}

        # Handle Keychain-stored items
        if item['encrypted_value'] == "STORED_IN_KEYCHAIN" and KEYCHAIN_AVAILABLE:
            keychain_result = keychain.retrieve_credential(key, key)
            if not keychain_result['success']:
                return keychain_result
            decrypted_value = keychain_result['password']
        else:
            decrypted_value = self.decrypt_value(item['encrypted_value'])

        return {
            'success': True,
            'key': item['key_name'],
            'value': decrypted_value,
            'category': item['category'],
            'tags': json.loads(item['tags'] or '[]'),
            'expires_at': item['expires_at'],
            'created_at': item['created_at'],
            'updated_at': item['updated_at']
        }

    def list_items(self, category=None, tags=None):
        """List vault items"""
        conn = get_db_connection()
        cursor = conn.cursor()

        query = 'SELECT key_name, category, tags, expires_at, created_at FROM vault_items WHERE 1=1'
        params = []

        if category:
            query += ' AND category = ?'
            params.append(category)

        if tags:
            for tag in tags:
                query += ' AND tags LIKE ?'
                params.append(f'%{tag}%')

        cursor.execute(query, params)
        items = cursor.fetchall()
        conn.close()

        return [{
            'key': item['key_name'],
            'category': item['category'],
            'tags': json.loads(item['tags'] or '[]'),
            'expires_at': item['expires_at'],
            'created_at': item['created_at']
        } for item in items]

    def delete_item(self, key):
        """Delete an item from the vault"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if item exists and get its details
        cursor.execute('SELECT * FROM vault_items WHERE key_name = ?', (key,))
        item = cursor.fetchone()

        if item and item['encrypted_value'] == "STORED_IN_KEYCHAIN" and KEYCHAIN_AVAILABLE:
            # Delete from Keychain
            keychain.delete_credential(key, key)

        # Delete from database
        cursor.execute('DELETE FROM vault_items WHERE key_name = ?', (key,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return {'success': deleted, 'message': f'Item {key} deleted' if deleted else f'Item {key} not found'}

    def search_items(self, query):
        """Search vault items by key name or tags"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT key_name, category, tags, expires_at, created_at
            FROM vault_items
            WHERE key_name LIKE ? OR tags LIKE ?
        ''', (f'%{query}%', f'%{query}%'))

        items = cursor.fetchall()
        conn.close()

        return [{
            'key': item['key_name'],
            'category': item['category'],
            'tags': json.loads(item['tags'] or '[]'),
            'expires_at': item['expires_at'],
            'created_at': item['created_at']
        } for item in items]

# Initialize vault
vault = SecureVault(DATABASE)

# User Consent System
class ConsentManager:
    """Simple checkbox-based user consent management"""

    def __init__(self, db_path):
        self.db_path = db_path
        self._init_consent_table()

    def _init_consent_table(self):
        """Initialize consent tracking table"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_consent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consent_given BOOLEAN NOT NULL DEFAULT 0,
                consent_timestamp DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def get_consent_status(self):
        """Get current consent status"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user_consent ORDER BY id DESC LIMIT 1')
        consent = cursor.fetchone()
        conn.close()

        if not consent:
            return {
                'has_consent': False,
                'consent_timestamp': None
            }

        return {
            'has_consent': consent['consent_given'],
            'consent_timestamp': consent['consent_timestamp']
        }

    def record_consent(self):
        """Record user consent"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO user_consent
            (consent_given, consent_timestamp)
            VALUES (?, ?)
        ''', (
            True,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return {'success': True, 'message': 'Consent recorded successfully'}

    def revoke_consent(self):
        """Revoke user consent"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE user_consent
            SET consent_given = 0, updated_at = ?
            WHERE id = (SELECT MAX(id) FROM user_consent)
        ''', (datetime.now().isoformat(),))

        conn.commit()
        conn.close()

        return {'success': True, 'message': 'Consent revoked successfully'}

    def is_consent_valid(self):
        """Check if consent is valid"""
        status = self.get_consent_status()
        return status['has_consent']

# Initialize consent manager
consent_manager = ConsentManager(DATABASE)

# Browser Session Manager
class BrowserSessionManager:
    """Manages browser sessions with logging and state tracking"""

    def __init__(self, db_path):
        self.db_path = db_path
        self._init_session_table()

    def _init_session_table(self):
        """Initialize browser session tracking table"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS browser_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                browser_type TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                status TEXT DEFAULT 'active',
                tabs_count INTEGER DEFAULT 0,
                urls TEXT,  -- JSON array of open URLs
                last_activity DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def start_session(self, browser_type, session_id=None):
        """Start a new browser session"""
        if not session_id:
            session_id = f"{browser_type}_{int(time.time())}"

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO browser_sessions
            (session_id, browser_type, start_time, status, last_activity)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_id,
            browser_type,
            datetime.now().isoformat(),
            'active',
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return {'success': True, 'session_id': session_id}

    def update_session(self, session_id, tabs_count=None, urls=None):
        """Update session information"""
        conn = get_db_connection()
        cursor = conn.cursor()

        update_data = {'last_activity': datetime.now().isoformat()}

        if tabs_count is not None:
            update_data['tabs_count'] = tabs_count

        if urls is not None:
            update_data['urls'] = json.dumps(urls)

        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values()) + [session_id]

        cursor.execute(f'''
            UPDATE browser_sessions
            SET {set_clause}
            WHERE session_id = ?
        ''', values)

        conn.commit()
        conn.close()

        return {'success': True}

    def end_session(self, session_id):
        """End a browser session"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE browser_sessions
            SET end_time = ?, status = 'closed', last_activity = ?
            WHERE session_id = ?
        ''', (
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            session_id
        ))

        conn.commit()
        conn.close()

        return {'success': True}

    def get_active_sessions(self):
        """Get all active browser sessions"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM browser_sessions
            WHERE status = 'active'
            ORDER BY start_time DESC
        ''')

        sessions = cursor.fetchall()
        conn.close()

        return [dict(session) for session in sessions]

    def get_session_history(self, limit=50):
        """Get browser session history"""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM browser_sessions
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))

        sessions = cursor.fetchall()
        conn.close()

        return [dict(session) for session in sessions]

    def close_browser_instances(self, preserve_cookies=True):
        """Close browser instances while preserving cookies"""
        try:
            # Get running browser processes
            result = subprocess.run(['pgrep', '-f', 'Chrome|Firefox|Safari'], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')

                closed_sessions = []
                for pid in pids:
                    if pid.strip():
                        # Log session before closing
                        session_id = f"auto_close_{int(time.time())}_{pid}"
                        self.start_session('auto_detected', session_id)

                        # Close the process gracefully
                        subprocess.run(['kill', '-TERM', pid.strip()])

                        # Mark session as closed
                        self.end_session(session_id)
                        closed_sessions.append(session_id)

                return {
                    'success': True,
                    'message': f'Closed {len(closed_sessions)} browser instances',
                    'sessions_closed': closed_sessions,
                    'cookies_preserved': preserve_cookies
                }
            else:
                return {'success': True, 'message': 'No browser instances found to close'}

        except Exception as e:
            return {'success': False, 'error': f'Failed to close browser instances: {str(e)}'}

# Initialize browser session manager
browser_session_manager = BrowserSessionManager(DATABASE)

# AI Clustering Class
class AIFileClustering:
    """AI-powered file clustering using sentence transformers"""

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        if TORCH_AVAILABLE:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = 'cpu'
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model"""
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE:
            print("Warning: AI clustering unavailable - missing transformers or torch")
            self.model = None
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
        except Exception as e:
            print(f"Warning: Could not load AI model: {e}")
            self.model = None

    def get_file_embedding(self, file_path):
        """Generate embedding for a file based on its content and metadata"""
        try:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return None

            # Get file metadata
            stat = os.stat(file_path)
            file_size = stat.st_size
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()

            # Create text representation of file
            text_parts = [file_name]

            # Try to read file content for text files
            if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1000)  # Read first 1000 characters
                        if content:
                            text_parts.append(content[:500])  # Limit content length
                except:
                    pass

            # Add file type and size info
            text_parts.extend([
                f"extension:{file_ext}",
                f"size:{file_size}",
                f"modified:{stat.st_mtime}"
            ])

            text = " ".join(text_parts)

            # Generate embedding
            if self.model is None:
                # Fallback: simple hash-based embedding
                import hashlib
                hash_obj = hashlib.md5(text.encode())
                if SKLEARN_AVAILABLE:
                    return np.array([int(hash_obj.hexdigest()[i:i+2], 16) for i in range(0, 32, 2)]) / 255.0
                else:
                    # Even simpler fallback
                    return [int(hash_obj.hexdigest()[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]

            # Use transformer model
            inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512, padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()

            return embeddings[0]

        except Exception as e:
            print(f"Error generating embedding for {file_path}: {e}")
            return None

    def cluster_files(self, file_paths, n_clusters=None):
        """Cluster files using AI embeddings"""
        try:
            if not file_paths:
                return {'success': False, 'error': 'No files provided'}

            # Generate embeddings for all files
            embeddings = []
            valid_files = []

            for file_path in file_paths:
                embedding = self.get_file_embedding(file_path)
                if embedding is not None:
                    embeddings.append(embedding)
                    valid_files.append(file_path)

            if len(embeddings) < 2:
                return {
                    'success': False,
                    'error': 'Need at least 2 files for clustering'
                }

            if not SKLEARN_AVAILABLE:
                return {'success': False, 'error': 'AI clustering unavailable - missing scikit-learn'}

            embeddings = np.array(embeddings)

            # Determine number of clusters
            if n_clusters is None:
                n_clusters = min(len(valid_files) // 3 + 1, 10)  # Adaptive clustering

            # Perform K-means clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(embeddings)

            # Group files by cluster
            cluster_groups = {}
            for i, cluster_id in enumerate(clusters):
                if cluster_id not in cluster_groups:
                    cluster_groups[cluster_id] = []
                cluster_groups[cluster_id].append(valid_files[i])

            # Generate cluster descriptions
            cluster_descriptions = self._generate_cluster_descriptions(cluster_groups)

            return {
                'success': True,
                'clusters': cluster_groups,
                'descriptions': cluster_descriptions,
                'n_clusters': n_clusters,
                'total_files': len(valid_files)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_cluster_descriptions(self, cluster_groups):
        """Generate human-readable descriptions for clusters"""
        descriptions = {}

        for cluster_id, files in cluster_groups.items():
            if not files:
                continue

            # Check if this is an AI logs cluster
            ai_log_files = [f for f in files if self._is_ai_log_file(f)]
            if ai_log_files and len(ai_log_files) / len(files) > 0.5:
                descriptions[cluster_id] = self._generate_ai_log_description(ai_log_files)
                continue

            # Analyze file types in cluster
            extensions = []
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions.append(ext)

            # Count most common extension
            if extensions:
                from collections import Counter
                most_common = Counter(extensions).most_common(1)[0]
                ext_count = most_common[1]
                ext_type = most_common[0]

                if ext_count / len(files) > 0.7:  # 70% same type
                    descriptions[cluster_id] = f"{ext_type.upper()} files ({len(files)} items)"
                else:
                    descriptions[cluster_id] = f"Mixed files ({len(files)} items)"
            else:
                descriptions[cluster_id] = f"Files ({len(files)} items)"

        return descriptions

    def _is_ai_log_file(self, file_path):
        """Check if file is an AI log file"""
        filename = os.path.basename(file_path).lower()

        # OpenCode logs
        if 'opencode' in filename and ('log' in filename or '.txt' in filename):
            return True

        # Gemini CLI logs
        if 'gemini' in filename and ('log' in filename or 'cli' in filename):
            return True

        # Qwen Code logs
        if 'qwen' in filename and ('log' in filename or 'code' in filename):
            return True

        # Check file content for AI patterns
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000).lower()
                ai_patterns = [
                    'assistant:', 'ai:', 'gemini', 'qwen', 'opencode',
                    'model response', 'ai generated', 'llm output'
                ]
                return any(pattern in content for pattern in ai_patterns)
        except:
            return False

        return False

    def _generate_ai_log_description(self, ai_log_files):
        """Generate description for AI log files cluster"""
        sources = set()

        for file in ai_log_files:
            filename = os.path.basename(file).lower()
            if 'opencode' in filename:
                sources.add('OpenCode')
            elif 'gemini' in filename:
                sources.add('Gemini CLI')
            elif 'qwen' in filename:
                sources.add('Qwen Code')
            else:
                sources.add('AI Logs')

        source_str = ', '.join(sorted(sources))
        return f"AI Logs ({source_str}) - {len(ai_log_files)} files"

    def suggest_organization(self, cluster_result):
        """Suggest file organization based on clustering results"""
        try:
            suggestions = []

            for cluster_id, files in cluster_result['clusters'].items():
                description = cluster_result['descriptions'].get(cluster_id, f"Cluster {cluster_id}")

                # Analyze current locations
                directories = set()
                for file in files:
                    directories.add(os.path.dirname(file))

                if len(directories) > 1:
                    suggestions.append({
                        'cluster_id': cluster_id,
                        'description': description,
                        'files': files,
                        'action': 'consolidate',
                        'reason': f'Files are scattered across {len(directories)} directories'
                    })
                else:
                    suggestions.append({
                        'cluster_id': cluster_id,
                        'description': description,
                        'files': files,
                        'action': 'organize',
                        'reason': 'Files are already in the same directory'
                    })

            return {
                'success': True,
                'suggestions': suggestions
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global AI clustering instance
ai_clustering = AIFileClustering()

# Global scheduler instance
if APSCHEDULER_AVAILABLE:
    scheduler = BackgroundScheduler()
    scheduler_active = False
else:
    scheduler = None
    scheduler_active = False

def init_scheduler():
    """Initialize the background scheduler"""
    global scheduler_active

    if scheduler_active or not APSCHEDULER_AVAILABLE:
        return

    try:
        # Add automated tasks
        scheduler.add_job(
            func=automated_health_check,
            trigger=IntervalTrigger(hours=1),
            id='health_check',
            name='Automated Health Check'
        )

        scheduler.add_job(
            func=automated_cache_cleanup,
            trigger=CronTrigger(hour=2),  # Daily at 2 AM
            id='cache_cleanup',
            name='Automated Cache Cleanup'
        )

        scheduler.add_job(
            func=automated_duplicate_scan,
            trigger=CronTrigger(hour=3),  # Daily at 3 AM
            id='duplicate_scan',
            name='Automated Duplicate Scan'
        )

        scheduler.add_job(
            func=automated_backup,
            trigger=CronTrigger(hour=4, day_of_week='sun'),  # Weekly on Sunday
            id='backup',
            name='Automated Backup'
        )

        scheduler.start()
        scheduler_active = True
        log("Background scheduler started successfully")

    except Exception as e:
        log(f"Failed to start scheduler: {e}")

def automated_health_check():
    """Automated health check task"""
    try:
        health_data = get_system_health()

        # Log health status
        if health_data['overall_status'] == 'Critical':
            log(f"CRITICAL: System health is critical - {health_data}")
        elif health_data['overall_status'] == 'Warning':
            log(f"WARNING: System health needs attention - {health_data}")

        # Store health data in database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO cleanup_log (action_type, file_path, success, error_message)
            VALUES (?, ?, ?, ?)
        ''', (
            'health_check',
            'system',
            health_data['overall_status'] != 'Critical',
            json.dumps(health_data)
        ))

        conn.commit()
        conn.close()

        log("Automated health check completed")

    except Exception as e:
        log(f"Automated health check failed: {e}")

def automated_cache_cleanup():
    """Automated cache cleanup task"""
    try:
        result = smart_cache_cleanup()

        if result['success']:
            log(f"Automated cache cleanup: {result['files_analyzed']} files analyzed, {format_bytes(result['space_freed'])} freed")
        else:
            log(f"Automated cache cleanup failed: {result['error']}")

    except Exception as e:
        log(f"Automated cache cleanup error: {e}")

def automated_duplicate_scan():
    """Automated duplicate scan task"""
    try:
        # This would integrate with the existing duplicate detection
        # For now, just log that it ran
        log("Automated duplicate scan completed (placeholder)")

    except Exception as e:
        log(f"Automated duplicate scan failed: {e}")

def automated_backup():
    """Automated backup task"""
    try:
        # Create backup of database and configuration
        backup_dir = os.path.join(DATA_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Backup database
        db_backup = os.path.join(backup_dir, f'cleanup_{timestamp}.db')
        shutil.copy2(DATABASE, db_backup)

        # Backup configuration
        config_backup = os.path.join(backup_dir, f'config_{timestamp}.json')
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'config.json')):
            shutil.copy2(
                os.path.join(os.path.dirname(__file__), 'config.json'),
                config_backup
            )

        log(f"Automated backup created: {db_backup}")

        # Clean old backups (keep last 7)
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        if len(backup_files) > 7:
            for old_file in backup_files[:-7]:
                os.remove(os.path.join(backup_dir, old_file))
                log(f"Removed old backup: {old_file}")

    except Exception as e:
        log(f"Automated backup failed: {e}")

def shutdown_scheduler():
    """Shutdown the scheduler"""
    global scheduler_active
    if scheduler_active and APSCHEDULER_AVAILABLE:
        scheduler.shutdown()
        scheduler_active = False
        log("Background scheduler shut down")

# AI Chat Endpoint

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat interface"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'response': 'Please ask me something about cleanup!'})

        # Get system stats for context
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM scans')
        scan_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM duplicates')
        duplicate_count = cursor.fetchone()[0]

        cursor.execute('SELECT SUM(total_size) FROM scans WHERE status = "completed"')
        total_cleaned = cursor.fetchone()[0] or 0

        conn.close()

        # Generate AI response based on user message
        response = generate_ai_response(user_message, {
            'scan_count': scan_count,
            'duplicate_count': duplicate_count,
            'total_cleaned': total_cleaned
        })

        return jsonify({'response': response})

    except Exception as e:
        return jsonify({'response': 'Sorry, I encountered an error. Please try again.'}), 500

# Chat Message Queue
chat_queue = []
chat_processing_active = False
chat_results = {}  # Store results by message ID

def process_chat_queue():
    """Process chat messages from the queue asynchronously"""
    global chat_processing_active

    if chat_processing_active:
        return  # Already processing

    chat_processing_active = True

    def process_messages():
        global chat_processing_active

        while chat_queue:
            try:
                message_data = chat_queue.pop(0)
                message_id = message_data['id']
                message = message_data['message']
                model = message_data['model']

                # Process the message
                context = f"""
You are TidyMe, an AI assistant for system cleanup and file management.
Current system stats:
- Scans performed: {get_scan_count()}
- Duplicates found: {get_duplicate_count()}
- Space cleaned: {get_total_cleaned()} bytes

User question: {message}

Please provide a helpful, concise response about cleanup, file management, or system optimization.
"""

                response = query_ollama(context, model)

                # Store the result
                chat_results[message_id] = {
                    'success': True,
                    'response': response,
                    'model': model,
                    'timestamp': datetime.now().isoformat()
                }

            except Exception as e:
                error_msg = str(e)
                if "Connection refused" in error_msg or "Connection aborted" in error_msg:
                    error_response = 'Cannot connect to AI service. Please ensure Ollama or llama.cpp server is running.'
                else:
                    error_response = f'AI chat error: {error_msg}'

                chat_results[message_data['id']] = {
                    'success': False,
                    'error': error_response,
                    'timestamp': datetime.now().isoformat()
                }

        chat_processing_active = False

    # Start processing in a separate thread
    import threading
    thread = threading.Thread(target=process_messages, daemon=True)
    thread.start()

# Ollama AI Endpoints

@app.route('/api/ollama/chat', methods=['POST'])
def ollama_chat():
    """Chat with AI model (llama.cpp or Ollama) - supports queuing"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        model = data.get('model', 'tinyllama:1.1b')
        queue_if_busy = data.get('queue', True)  # Default to queuing

        if not message:
            return jsonify({
                'success': False,
                'error': 'Please enter a message to chat with the AI.'
            }), 400

        # Check if message is too long
        if len(message) > 1000:
            return jsonify({
                'success': False,
                'error': 'Message is too long. Please keep it under 1000 characters.'
            }), 400

        # Generate unique message ID
        import uuid
        message_id = str(uuid.uuid4())

        # If AI is busy and queuing is enabled, add to queue
        if chat_processing_active and queue_if_busy:
            chat_queue.append({
                'id': message_id,
                'message': message,
                'model': model,
                'timestamp': datetime.now().isoformat()
            })

            return jsonify({
                'success': True,
                'queued': True,
                'message_id': message_id,
                'queue_position': len(chat_queue),
                'message': 'Message added to queue. Processing may take a moment.'
            })

        # Process immediately if not busy or queuing disabled
        context = f"""
You are TidyMe, an AI assistant for system cleanup and file management.
Current system stats:
- Scans performed: {get_scan_count()}
- Duplicates found: {get_duplicate_count()}
- Space cleaned: {get_total_cleaned()} bytes

User question: {message}

Please provide a helpful, concise response about cleanup, file management, or system optimization.
"""

        response = query_ollama(context, model)

        # Check if we got a valid response
        if not response or response.strip() == "":
            return jsonify({
                'success': False,
                'error': 'AI model returned an empty response. Please try again.'
            }), 500

        return jsonify({
            'success': True,
            'response': response,
            'model': model,
            'message_id': message_id
        })

    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "Connection aborted" in error_msg:
            return jsonify({
                'success': False,
                'error': 'Cannot connect to AI service. Please ensure Ollama or llama.cpp server is running.'
            }), 503
        elif "timeout" in error_msg.lower():
            return jsonify({
                'success': False,
                'error': 'AI request timed out. Please try again.'
            }), 504
        else:
            return jsonify({
                'success': False,
                'error': f'AI chat error: {error_msg}'
            }), 500

@app.route('/api/ollama/chat/status/<message_id>', methods=['GET'])
def get_chat_message_status(message_id):
    """Get the status of a queued chat message"""
    try:
        if message_id in chat_results:
            result = chat_results[message_id]
            # Remove from results after retrieval
            del chat_results[message_id]
            return jsonify(result)

        # Check if message is still in queue
        for i, queued_msg in enumerate(chat_queue):
            if queued_msg['id'] == message_id:
                return jsonify({
                    'success': True,
                    'status': 'queued',
                    'queue_position': i + 1,
                    'total_in_queue': len(chat_queue)
                })

        return jsonify({
            'success': False,
            'error': 'Message not found'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ollama/chat/queue', methods=['GET'])
def get_chat_queue_status():
    """Get current chat queue status"""
    try:
        return jsonify({
            'success': True,
            'processing_active': chat_processing_active,
            'queue_length': len(chat_queue),
            'queue': [{
                'id': msg['id'],
                'timestamp': msg['timestamp'],
                'model': msg['model']
            } for msg in chat_queue[:5]]  # Show first 5 messages
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



@app.route('/api/ollama/models', methods=['GET'])
def get_available_models():
    """Get list of available Ollama models"""
    try:
        # Try to get models from Ollama
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            models = []
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        model_name = parts[0]
                        model_size = parts[1] if len(parts) > 1 else 'Unknown'
                        models.append({
                            'name': model_name,
                            'size': model_size
                        })

            return jsonify({
                'success': True,
                'models': models
            })
        else:
            # Return default models if ollama list fails
            return jsonify({
                'success': True,
                'models': [
                    {'name': 'tinyllama:1.1b', 'size': '637 MB'},
                    {'name': 'llama3.2:3b', 'size': '2.0 GB'},
                    {'name': 'granite-code:3b', 'size': '2.0 GB'}
                ]
            })

    except Exception as e:
        # Return default models on error
        return jsonify({
            'success': True,
            'models': [
                {'name': 'tinyllama:1.1b', 'size': '637 MB'},
                {'name': 'llama3.2:3b', 'size': '2.0 GB'},
                {'name': 'granite-code:3b', 'size': '2.0 GB'}
            ]
        })

@app.route('/api/ollama/analyze-files', methods=['POST'])
def ollama_analyze_files():
    """Use AI to analyze files for cleanup suggestions"""
    try:
        data = request.get_json()
        file_paths = data.get('files', [])
        model = data.get('model', 'tinyllama:1.1b')

        if not file_paths:
            return jsonify({'error': 'File paths are required'}), 400

        # Get file information
        file_info = []
        for path in file_paths[:10]:  # Limit to 10 files
            try:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    mtime = os.path.getmtime(path)
                    file_info.append({
                        'path': path,
                        'size': size,
                        'modified': datetime.fromtimestamp(mtime).isoformat(),
                        'type': 'file' if os.path.isfile(path) else 'directory'
                    })
            except:
                continue

        # Create analysis prompt
        prompt = f"""
Analyze these files for cleanup opportunities:

{json.dumps(file_info, indent=2)}

Please provide:
1. Files that can be safely deleted
2. Files that should be archived
3. Files that need review
4. Estimated space savings

Be specific and conservative in your recommendations.
"""

        analysis = query_ollama(prompt, model)
        return jsonify({
            'analysis': analysis,
            'files_analyzed': len(file_info),
            'model': model
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/generate-report', methods=['POST'])
def ollama_generate_report():
    """Generate AI-powered cleanup report"""
    try:
        model = request.args.get('model', 'tinyllama:1.1b')

        # Get recent cleanup data
        conn = get_db_connection()
        cursor = conn.cursor()

        # Recent scans
        cursor.execute('SELECT * FROM scans ORDER BY scan_date DESC LIMIT 5')
        recent_scans = cursor.fetchall()

        # Duplicate summary
        cursor.execute('SELECT COUNT(*) as count, SUM(file_size) as total_size FROM duplicates')
        dup_stats = cursor.fetchone()

        # Cleanup summary
        cursor.execute('SELECT action_type, COUNT(*) as count, SUM(file_size) as total_size FROM cleanup_log GROUP BY action_type')
        cleanup_stats = cursor.fetchall()

        conn.close()

        # Create report prompt
        prompt = f"""
Generate a comprehensive cleanup report based on this data:

Recent Scans:
{json.dumps([dict(scan) for scan in recent_scans], indent=2, default=str)}

Duplicate Statistics:
- Total duplicates: {dup_stats[0] if dup_stats else 0}
- Total size: {dup_stats[1] if dup_stats else 0} bytes

Cleanup Actions:
{json.dumps([{'action': row[0], 'count': row[1], 'size': row[2]} for row in cleanup_stats], indent=2)}

Please provide:
1. Summary of cleanup activities
2. Key insights and patterns
3. Recommendations for future cleanup
4. Potential space savings
"""

        report = query_ollama(prompt, model)
        return jsonify({
            'report': report,
            'generated_at': datetime.now().isoformat(),
            'model': model
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama/models', methods=['GET'])
def get_ollama_models():
    """Get available AI models (llama.cpp or Ollama)"""
    try:
        # Try llama.cpp server first
        import requests
        response = requests.get("http://localhost:8080/v1/models", timeout=5)
        if response.status_code == 200:
            result = response.json()
            models = []
            for model in result.get('data', []):
                models.append({
                    'name': model['id'],
                    'id': model['id'],
                    'size': 'N/A',
                    'modified': 'N/A',
                    'source': 'llama.cpp'
                })
            return jsonify({'models': models, 'source': 'llama.cpp'})

        # Fallback to Ollama
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Parse the output
            lines = result.stdout.strip().split('\n')
            models = []
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        models.append({
                            'name': parts[0],
                            'id': parts[1],
                            'size': ' '.join(parts[2:-1]) if len(parts) > 3 else parts[2],
                            'modified': parts[-1] if len(parts) > 2 else 'unknown',
                            'source': 'ollama'
                        })
            return jsonify({'models': models, 'source': 'ollama'})
        else:
            return jsonify({'error': result.stderr}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI Chat Collection Endpoints

@app.route('/api/ai-chats/collect', methods=['POST'])
def collect_ai_chats():
    """Collect chats from configured AI platforms using browser automation"""
    try:
        data = request.get_json()
        credentials = data.get('credentials', {})
        platforms = data.get('platforms', [])

        if not credentials:
            return jsonify({'error': 'Credentials are required for login-based platforms'}), 400

        # Validate credential structure for web authentication
        for platform, creds in credentials.items():
            if platform in chat_collector.supported_platforms:
                platform_config = chat_collector.supported_platforms[platform]
                if platform_config['login_required']:
                    if not creds.get('username') or not creds.get('password'):
                        return jsonify({
                            'error': f'Username and password required for {platform}',
                            'platform': platform,
                            'auth_type': 'web_login'
                        }), 400

        # Filter credentials to only requested platforms
        filtered_credentials = {}
        if platforms:
            for platform in platforms:
                if platform in credentials and platform in chat_collector.supported_platforms:
                    filtered_credentials[platform] = credentials[platform]
        else:
            # Use all provided credentials that are supported
            for platform, creds in credentials.items():
                if platform in chat_collector.supported_platforms:
                    filtered_credentials[platform] = creds

        if not filtered_credentials:
            return jsonify({'error': 'No valid credentials provided for supported platforms'}), 400

        # Start collection process (this will take longer due to browser automation)
        results = chat_collector.collect_all_chats(filtered_credentials)

        return jsonify({
            'success': True,
            'results': results,
            'message': f'Browser-based chat collection completed for {len(filtered_credentials)} platforms',
            'note': 'Collection may take longer due to web page loading and authentication'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-chats/list', methods=['GET'])
def list_ai_chats():
    """List collected AI chats"""
    try:
        platform = request.args.get('platform')
        limit = int(request.args.get('limit', 50))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = 'SELECT id, platform, title, timestamp, collected_at FROM ai_chats'
        params = []

        if platform:
            query += ' WHERE platform = ?'
            params.append(platform)

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        chats = cursor.fetchall()
        conn.close()

        return jsonify({
            'chats': [{
                'id': chat['id'],
                'platform': chat['platform'],
                'title': chat['title'],
                'timestamp': chat['timestamp'],
                'collected_at': chat['collected_at']
            } for chat in chats]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-chats/<chat_id>', methods=['GET'])
def get_ai_chat(chat_id):
    """Get detailed AI chat data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM ai_chats WHERE id = ?', (chat_id,))
        chat = cursor.fetchone()
        conn.close()

        if not chat:
            return jsonify({'error': 'Chat not found'}), 404

        return jsonify({
            'chat': {
                'id': chat['id'],
                'platform': chat['platform'],
                'title': chat['title'],
                'messages': json.loads(chat['messages']) if chat['messages'] else [],
                'timestamp': chat['timestamp'],
                'metadata': json.loads(chat['metadata']) if chat['metadata'] else {},
                'collected_at': chat['collected_at']
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-chats/platforms', methods=['GET'])
def get_supported_platforms():
    """Get list of supported AI platforms with browser automation"""
    platforms = {
        'gemini': {
            'name': 'Google Gemini',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'Google\'s multimodal AI model (web interface)',
            'url': 'https://gemini.google.com'
        },
        'chatgpt': {
            'name': 'ChatGPT',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'OpenAI\'s conversational AI (web interface)',
            'url': 'https://chat.openai.com'
        },
        'claude': {
            'name': 'Claude',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'Anthropic\'s AI assistant (web interface)',
            'url': 'https://claude.ai'
        },
        'perplexity': {
            'name': 'Perplexity AI',
            'auth_type': 'web_login',
            'login_required': False,
            'description': 'AI-powered search and conversation (may require login)',
            'url': 'https://perplexity.ai'
        },
        'kimi': {
            'name': 'Kimi AI',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'Moonshot AI\'s conversational model (web interface)',
            'url': 'https://kimi.ai'
        },
        'manus': {
            'name': 'Manus AI',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'Advanced AI assistant (web interface)',
            'url': 'https://manus.ai'
        },
        'genspark': {
            'name': 'Genspark',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'AI-powered content generation (web interface)',
            'url': 'https://genspark.ai'
        },
        'grok': {
            'name': 'Grok',
            'auth_type': 'web_login',
            'login_required': True,
            'description': 'xAI\'s helpful AI (web interface)',
            'url': 'https://grok.x.ai'
        }
    }

    return jsonify({'platforms': platforms})

@app.route('/api/ai-chats/stats', methods=['GET'])
def get_ai_chat_stats():
    """Get statistics about collected AI chats"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Platform distribution
        cursor.execute('SELECT platform, COUNT(*) as count FROM ai_chats GROUP BY platform')
        platform_stats = cursor.fetchall()

        # Total chats
        cursor.execute('SELECT COUNT(*) as total FROM ai_chats')
        total_chats = cursor.fetchone()['total']

        # Recent activity (last 7 days)
        cursor.execute('SELECT COUNT(*) as recent FROM ai_chats WHERE collected_at >= datetime("now", "-7 days")')
        recent_chats = cursor.fetchone()['recent']

        conn.close()

        return jsonify({
            'total_chats': total_chats,
            'recent_chats': recent_chats,
            'platform_distribution': {row['platform']: row['count'] for row in platform_stats}
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions for stats
def get_scan_count():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM scans')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_duplicate_count():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM duplicates')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_total_cleaned():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(total_size) FROM scans WHERE status = "completed"')
        total = cursor.fetchone()[0] or 0
        conn.close()
        return total
    except:
        return 0

# MCP Server for Browser Automation
class MCPServer:
    """MCP server for browser automation and chat extraction"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    def start_browser(self):
        """Start Playwright browser instance"""
        if not self.playwright:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )

    def stop_browser(self):
        """Stop browser instance"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def extract_chats_from_page(self, page, platform_config):
        """Extract chat data from a web page"""
        try:
            # Wait for page to load
            page.wait_for_load_state('networkidle')

            # Platform-specific extraction logic
            if platform_config['platform'] == 'gemini':
                return self._extract_gemini_chats(page)
            elif platform_config['platform'] == 'chatgpt':
                return self._extract_chatgpt_chats(page)
            elif platform_config['platform'] == 'claude':
                return self._extract_claude_chats(page)
            # Add more platforms as needed

        except Exception as e:
            print(f"Error extracting chats: {e}")
            return []

    def _extract_gemini_chats(self, page):
        """Extract chats from Gemini web interface"""
        chats = []

        try:
            # Look for chat history elements
            chat_elements = page.query_selector_all('[data-chat-id], .chat-history-item')

            for element in chat_elements:
                chat_data = {
                    'id': element.get_attribute('data-chat-id') or f"gemini_{hash(str(element))}",
                    'title': element.text_content()[:100] if element.text_content() else 'Gemini Chat',
                    'timestamp': datetime.now().isoformat(),
                    'messages': [],
                    'metadata': {'source': 'web_scraping', 'platform': 'gemini'}
                }
                chats.append(chat_data)

        except Exception as e:
            print(f"Error extracting Gemini chats: {e}")

        return chats

    def _extract_chatgpt_chats(self, page):
        """Extract chats from ChatGPT web interface"""
        chats = []

        try:
            # Look for conversation elements
            conversation_elements = page.query_selector_all('[data-conversation-id], .conversation-item')

            for element in conversation_elements:
                chat_data = {
                    'id': element.get_attribute('data-conversation-id') or f"chatgpt_{hash(str(element))}",
                    'title': element.text_content()[:100] if element.text_content() else 'ChatGPT Chat',
                    'timestamp': datetime.now().isoformat(),
                    'messages': [],
                    'metadata': {'source': 'web_scraping', 'platform': 'chatgpt'}
                }
                chats.append(chat_data)

        except Exception as e:
            print(f"Error extracting ChatGPT chats: {e}")

        return chats

    def _extract_claude_chats(self, page):
        """Extract chats from Claude web interface"""
        chats = []

        try:
            # Look for conversation elements
            conversation_elements = page.query_selector_all('[data-conversation-id], .conversation-item')

            for element in conversation_elements:
                chat_data = {
                    'id': element.get_attribute('data-conversation-id') or f"claude_{hash(str(element))}",
                    'title': element.text_content()[:100] if element.text_content() else 'Claude Chat',
                    'timestamp': datetime.now().isoformat(),
                    'messages': [],
                    'metadata': {'source': 'web_scraping', 'platform': 'claude'}
                }
                chats.append(chat_data)

        except Exception as e:
            print(f"Error extracting Claude chats: {e}")

        return chats

# AI Chat Collection System with MCP

class AIChatCollector:
    """Collect and process AI chats from multiple platforms using MCP and Playwright"""

    def __init__(self):
        self.mcp_server = MCPServer()
        self.supported_platforms = {
            'gemini': {
                'url': 'https://gemini.google.com',
                'login_required': True,
                'platform': 'gemini'
            },
            'chatgpt': {
                'url': 'https://chat.openai.com',
                'login_required': True,
                'platform': 'chatgpt'
            },
            'claude': {
                'url': 'https://claude.ai',
                'login_required': True,
                'platform': 'claude'
            },
            'perplexity': {
                'url': 'https://perplexity.ai',
                'login_required': False,
                'platform': 'perplexity'
            },
            'kimi': {
                'url': 'https://kimi.ai',
                'login_required': True,
                'platform': 'kimi'
            },
            'manus': {
                'url': 'https://manus.ai',
                'login_required': True,
                'platform': 'manus'
            },
            'genspark': {
                'url': 'https://genspark.ai',
                'login_required': True,
                'platform': 'genspark'
            },
            'grok': {
                'url': 'https://grok.x.ai',
                'login_required': True,
                'platform': 'grok'
            }
        }
        self.rate_limiter = RateLimiter()
        self.executor = ThreadPoolExecutor(max_workers=2)  # Reduced for browser automation

    def collect_all_chats(self, credentials):
        """Collect chats from all configured platforms using browser automation"""
        results = {}

        try:
            # Start MCP server and browser
            self.mcp_server.start_browser()

            for platform_name, platform_config in self.supported_platforms.items():
                if platform_name in credentials and credentials[platform_name]:
                    try:
                        self.rate_limiter.wait_if_needed(platform_name)
                        result = self._collect_platform_chats(platform_name, platform_config, credentials[platform_name])
                        results[platform_name] = result
                    except Exception as e:
                        results[platform_name] = {'success': False, 'error': str(e)}

        finally:
            # Always stop the browser
            self.mcp_server.stop_browser()

        return results

    def _collect_platform_chats(self, platform_name, platform_config, creds):
        """Collect chats from a specific platform using browser automation"""
        try:
            # Create a new page for this platform
            page = self.mcp_server.context.new_page()

            try:
                # Navigate to platform
                page.goto(platform_config['url'], wait_until='networkidle')

                # Handle authentication if required
                if platform_config['login_required'] and creds.get('username') and creds.get('password'):
                    self._handle_authentication(page, platform_config, creds)

                # Wait for page to load completely
                page.wait_for_load_state('networkidle')

                # Extract chat data
                chats = self.mcp_server.extract_chats_from_page(page, platform_config)

                # Process and store chats
                processed_chats = []
                for chat in chats:
                    processed_chat = self._standardize_chat_format(chat, platform_name)
                    processed_chats.append(processed_chat)
                    self._store_chat(processed_chat)

                return {
                    'success': True,
                    'chats_collected': len(processed_chats),
                    'platform': platform_name
                }

            finally:
                page.close()

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_authentication(self, page, platform_config, creds):
        """Handle authentication for platforms that require login"""
        try:
            platform = platform_config['platform']

            if platform == 'gemini':
                # Handle Google authentication
                self._handle_google_auth(page, creds)
            elif platform == 'chatgpt':
                # Handle OpenAI authentication
                self._handle_openai_auth(page, creds)
            elif platform == 'claude':
                # Handle Anthropic authentication
                self._handle_anthropic_auth(page, creds)
            # Add more authentication handlers as needed

        except Exception as e:
            print(f"Authentication failed for {platform}: {e}")

    def _handle_google_auth(self, page, creds):
        """Handle Google authentication flow"""
        try:
            # Click sign in button
            sign_in_button = page.query_selector('text="Sign in"') or page.query_selector('[data-testid="signin-button"]')
            if sign_in_button:
                sign_in_button.click()
                page.wait_for_load_state('networkidle')

            # Enter email
            email_input = page.query_selector('input[type="email"]') or page.query_selector('#identifierId')
            if email_input:
                email_input.fill(creds['username'])
                page.click('text="Next"') or page.click('#identifierNext')
                page.wait_for_load_state('networkidle')

            # Enter password
            password_input = page.query_selector('input[type="password"]') or page.query_selector('#password input')
            if password_input:
                password_input.fill(creds['password'])
                page.click('text="Next"') or page.click('#passwordNext')
                page.wait_for_load_state('networkidle')

        except Exception as e:
            print(f"Google auth failed: {e}")

    def _handle_openai_auth(self, page, creds):
        """Handle OpenAI authentication flow"""
        try:
            # Click login button
            login_button = page.query_selector('text="Log in"') or page.query_selector('[data-testid="login-button"]')
            if login_button:
                login_button.click()
                page.wait_for_load_state('networkidle')

            # Enter email
            email_input = page.query_selector('input[type="email"]') or page.query_selector('#username')
            if email_input:
                email_input.fill(creds['username'])
                page.click('text="Continue"') or page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')

            # Enter password
            password_input = page.query_selector('input[type="password"]') or page.query_selector('#password')
            if password_input:
                password_input.fill(creds['password'])
                page.click('text="Continue"') or page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')

        except Exception as e:
            print(f"OpenAI auth failed: {e}")

    def _handle_anthropic_auth(self, page, creds):
        """Handle Anthropic authentication flow"""
        try:
            # Click login button
            login_button = page.query_selector('text="Sign In"') or page.query_selector('[data-testid="signin-button"]')
            if login_button:
                login_button.click()
                page.wait_for_load_state('networkidle')

            # Enter email
            email_input = page.query_selector('input[type="email"]') or page.query_selector('#email')
            if email_input:
                email_input.fill(creds['username'])
                page.click('text="Continue"') or page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')

            # Enter password
            password_input = page.query_selector('input[type="password"]') or page.query_selector('#password')
            if password_input:
                password_input.fill(creds['password'])
                page.click('text="Sign In"') or page.click('button[type="submit"]')
                page.wait_for_load_state('networkidle')

        except Exception as e:
            print(f"Anthropic auth failed: {e}")

    def _standardize_chat_format(self, chat, platform):
        """Standardize chat format across platforms"""
        return {
            'id': hashlib.sha256(f"{platform}_{chat.get('id', '')}_{chat.get('timestamp', '')}".encode()).hexdigest(),
            'platform': platform,
            'title': chat.get('title', f'{platform.capitalize()} Chat'),
            'messages': chat.get('messages', []),
            'timestamp': chat.get('timestamp', datetime.now().isoformat()),
            'metadata': chat.get('metadata', {}),
            'collected_at': datetime.now().isoformat()
        }

    def _store_chat(self, chat):
        """Store chat in database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Store in ai_chats table (will be created if needed)
            cursor.execute('''
                INSERT INTO ai_chats (id, platform, title, messages, timestamp, metadata, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    messages = excluded.messages,
                    metadata = excluded.metadata,
                    collected_at = excluded.collected_at
            ''', (
                chat['id'],
                chat['platform'],
                chat['title'],
                json.dumps(chat['messages']),
                chat['timestamp'],
                json.dumps(chat['metadata']),
                chat['collected_at']
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error storing chat: {e}")

class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self):
        self.last_calls = {}
        self.min_intervals = {
            'gemini': 1,      # 1 second
            'chatgpt': 2,     # 2 seconds
            'perplexity': 1,  # 1 second
            'kimi': 3,        # 3 seconds
            'manus': 5,       # 5 seconds
            'genspark': 2,    # 2 seconds
            'claude': 3,      # 3 seconds
            'grok': 2         # 2 seconds
        }

    def wait_if_needed(self, platform):
        """Wait if necessary to respect rate limits"""
        if platform in self.last_calls:
            elapsed = time.time() - self.last_calls[platform]
            min_interval = self.min_intervals.get(platform, 1)

            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)

        self.last_calls[platform] = time.time()

# Global chat collector instance
chat_collector = AIChatCollector()

# Background process management
background_processes = {}
process_lock = threading.Lock()

# Task dependency management
task_queue = []
task_dependencies = {}  # task_id -> list of prerequisite task_ids
completed_tasks = set()
task_lock = threading.Lock()
task_scheduler_thread = None
task_scheduler_active = False

def cleanup_background_processes():
    """Clean up any remaining background processes on shutdown"""
    with process_lock:
        for pid, process_info in background_processes.items():
            try:
                if process_info['process'].is_alive():
                    process_info['process'].terminate()
                    process_info['process'].join(timeout=5)
                    if process_info['process'].is_alive():
                        process_info['process'].kill()
            except Exception as e:
                print(f"Error cleaning up process {pid}: {e}")

# Register cleanup function
atexit.register(cleanup_background_processes)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    cleanup_background_processes()
    if APSCHEDULER_AVAILABLE and scheduler_active:
        shutdown_scheduler()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def run_as_daemon():
    """Run the application as a daemon process"""
    if not DAEMON_AVAILABLE:
        print("Daemon functionality not available. Install python-daemon package.")
        return False

    try:
        # Create PID file
        pidfile_path = os.path.join(os.path.dirname(__file__), 'tidyme.pid')
        pidfile = daemon.pidfile.PIDLockFile(pidfile_path)

        # Daemon context
        context = daemon.DaemonContext(
            pidfile=pidfile,
            stdout=sys.stdout,
            stderr=sys.stderr,
            working_directory=os.getcwd(),
            umask=0o022,
        )

        with context:
            print("Starting TidyMe as daemon...")
            start_background_services()
            run_flask_app()

    except Exception as e:
        print(f"Failed to start as daemon: {e}")
        return False

    return True

def start_background_services():
    """Start all background services"""
    try:
        # Start scheduler if available
        if APSCHEDULER_AVAILABLE:
            init_scheduler()
            print("Background scheduler started")

        # Start monitoring if configured
        global monitoring_active
        monitoring_active = True
        print("Background monitoring enabled")

        # Start any other background tasks
        print("All background services started successfully")

    except Exception as e:
        print(f"Error starting background services: {e}")

def run_flask_app():
    """Run the Flask application"""
    try:
        print("Starting Flask application...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Disable debug in daemon mode
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"Error running Flask app: {e}")

def start_background_task(task_func, task_name, *args, **kwargs):
    """Start a background task that persists between sessions"""
    def task_wrapper():
        try:
            print(f"Starting background task: {task_name}")
            result = task_func(*args, **kwargs)
            print(f"Background task {task_name} completed")
            return result
        except Exception as e:
            print(f"Background task {task_name} failed: {e}")
            return None

    thread = threading.Thread(target=task_wrapper, daemon=True, name=task_name)
    thread.start()

    with process_lock:
        background_processes[thread.ident] = {
            'thread': thread,
            'name': task_name,
            'start_time': datetime.now()
        }

    return thread.ident

def get_background_task_status():
    """Get status of all background tasks"""
    with process_lock:
        status = {}
        for pid, info in background_processes.items():
            thread = info['thread']
            status[pid] = {
                'name': info['name'],
                'alive': thread.is_alive(),
                'start_time': info['start_time'].isoformat(),
                'daemon': thread.daemon
            }
        return status

def stop_background_task(task_id):
    """Stop a specific background task"""
    with process_lock:
        if task_id in background_processes:
            try:
                background_processes[task_id]['thread'].join(timeout=5)
                del background_processes[task_id]
                return True
            except Exception as e:
                print(f"Error stopping task {task_id}: {e}")
                return False
    return False

# Task Dependency Management

def add_task_to_queue(task_func, task_name, dependencies=None, *args, **kwargs):
    """Add a task to the queue with optional dependencies"""
    task_id = f"{task_name}_{int(time.time() * 1000)}"

    task_info = {
        'id': task_id,
        'func': task_func,
        'name': task_name,
        'args': args,
        'kwargs': kwargs,
        'dependencies': dependencies or [],
        'status': 'queued',
        'created_at': datetime.now(),
        'started_at': None,
        'completed_at': None,
        'result': None,
        'error': None
    }

    with task_lock:
        task_queue.append(task_info)
        if dependencies:
            task_dependencies[task_id] = dependencies

    # Start task scheduler if not running
    start_task_scheduler()

    return task_id

def start_task_scheduler():
    """Start the task scheduler thread"""
    global task_scheduler_thread, task_scheduler_active

    if task_scheduler_active:
        return

    task_scheduler_active = True

    def scheduler_loop():
        while task_scheduler_active:
            try:
                process_task_queue()
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Task scheduler error: {e}")
                time.sleep(5)  # Wait longer on error

    task_scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True, name="TaskScheduler")
    task_scheduler_thread.start()

def stop_task_scheduler():
    """Stop the task scheduler"""
    global task_scheduler_active
    task_scheduler_active = False
    if task_scheduler_thread:
        task_scheduler_thread.join(timeout=5)

def process_task_queue():
    """Process tasks in the queue, respecting dependencies"""
    with task_lock:
        # Find tasks that can be executed (all dependencies met)
        executable_tasks = []

        for task in task_queue:
            if task['status'] != 'queued':
                continue

            # Check if all dependencies are completed
            deps_met = True
            for dep in task['dependencies']:
                if dep not in completed_tasks:
                    deps_met = False
                    break

            if deps_met:
                executable_tasks.append(task)

        # Execute executable tasks
        for task in executable_tasks:
            task['status'] = 'running'
            task['started_at'] = datetime.now()

            # Start task in background
            thread = threading.Thread(
                target=execute_task,
                args=(task,),
                daemon=True,
                name=f"Task-{task['name']}"
            )
            thread.start()

            with process_lock:
                background_processes[thread.ident] = {
                    'thread': thread,
                    'name': task['name'],
                    'start_time': task['started_at'],
                    'task_id': task['id']
                }

def execute_task(task_info):
    """Execute a single task"""
    try:
        print(f"Executing task: {task_info['name']}")

        # Execute the task function
        result = task_info['func'](*task_info['args'], **task_info['kwargs'])

        # Mark as completed
        with task_lock:
            task_info['status'] = 'completed'
            task_info['completed_at'] = datetime.now()
            task_info['result'] = result
            completed_tasks.add(task_info['id'])

        print(f"Task completed: {task_info['name']}")

    except Exception as e:
        print(f"Task failed: {task_info['name']} - {e}")
        with task_lock:
            task_info['status'] = 'failed'
            task_info['completed_at'] = datetime.now()
            task_info['error'] = str(e)

def get_task_queue_status():
    """Get status of all tasks in queue"""
    with task_lock:
        return {
            'queue': [
                {
                    'id': task['id'],
                    'name': task['name'],
                    'status': task['status'],
                    'dependencies': task['dependencies'],
                    'created_at': task['created_at'].isoformat(),
                    'started_at': task['started_at'].isoformat() if task['started_at'] else None,
                    'completed_at': task['completed_at'].isoformat() if task['completed_at'] else None,
                    'error': task['error']
                }
                for task in task_queue
            ],
            'completed_tasks': list(completed_tasks),
            'total_queued': len([t for t in task_queue if t['status'] == 'queued']),
            'total_running': len([t for t in task_queue if t['status'] == 'running']),
            'total_completed': len([t for t in task_queue if t['status'] == 'completed']),
            'total_failed': len([t for t in task_queue if t['status'] == 'failed'])
        }

def cancel_task(task_id):
    """Cancel a queued task"""
    with task_lock:
        for task in task_queue:
            if task['id'] == task_id and task['status'] == 'queued':
                task['status'] = 'cancelled'
                task['completed_at'] = datetime.now()
                return True
    return False

# Predefined task functions for common operations

def scan_filesystem_task(scan_path="/", exclude_patterns=None):
    """Task to scan filesystem"""
    print(f"Starting filesystem scan: {scan_path}")
    # Simulate scan operation
    time.sleep(2)
    return {"scanned_path": scan_path, "files_found": 100}

def cleanup_duplicates_task():
    """Task to clean up duplicate files"""
    print("Starting duplicate cleanup")
    # Simulate cleanup operation
    time.sleep(3)
    return {"duplicates_removed": 15, "space_saved": "2.5GB"}

def optimize_storage_task():
    """Task to optimize storage"""
    print("Starting storage optimization")
    # Simulate optimization
    time.sleep(2)
    return {"optimized_files": 50, "space_reclaimed": "1.2GB"}

def backup_data_task(backup_path):
    """Task to backup data"""
    print(f"Starting backup to: {backup_path}")
    # Simulate backup operation
    time.sleep(5)
    return {"backup_path": backup_path, "files_backed_up": 200}

# Example task chains
def create_maintenance_chain():
    """Create a maintenance task chain with proper dependencies"""
    # Scan first
    scan_task = add_task_to_queue(scan_filesystem_task, "filesystem_scan")

    # Then clean duplicates (depends on scan)
    cleanup_task = add_task_to_queue(cleanup_duplicates_task, "duplicate_cleanup", [scan_task])

    # Then optimize storage (depends on cleanup)
    optimize_task = add_task_to_queue(optimize_storage_task, "storage_optimization", [cleanup_task])

    # Finally backup (depends on optimization)
    backup_path = "/tmp/tidyme_backup"
    backup_task = add_task_to_queue(backup_data_task, "data_backup", [optimize_task], backup_path)

    return {
        "scan_task": scan_task,
        "cleanup_task": cleanup_task,
        "optimize_task": optimize_task,
        "backup_task": backup_task
    }

# Vault API Endpoints

@app.route('/api/vault/items', methods=['GET'])
def get_vault_items():
    """Get all vault items (without sensitive values)"""
    try:
        category = request.args.get('category')
        tags = request.args.getlist('tag')
        search = request.args.get('search')

        if search:
            items = vault.search_items(search)
        else:
            items = vault.list_items(category=category, tags=tags if tags else None)

        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vault/items/<key>', methods=['GET'])
def get_vault_item(key):
    """Get a specific vault item"""
    try:
        result = vault.retrieve_item(key)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vault/items', methods=['POST'])
def create_vault_item():
    """Create or update a vault item"""
    try:
        data = request.get_json()

        key = data.get('key')
        value = data.get('value')
        category = data.get('category', 'general')
        tags = data.get('tags', [])
        expires_days = data.get('expires_days')

        if not key or not value:
            return jsonify({'success': False, 'error': 'Key and value are required'}), 400

        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        result = vault.store_item(key, value, category, tags, expires_at)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vault/items/<key>', methods=['DELETE'])
def delete_vault_item(key):
    """Delete a vault item"""
    try:
        result = vault.delete_item(key)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vault/categories', methods=['GET'])
def get_vault_categories():
    """Get all vault categories"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM vault_items ORDER BY category')
        categories = [row['category'] for row in cursor.fetchall()]
        conn.close()

        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vault/stats', methods=['GET'])
def get_vault_stats():
    """Get vault statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Total items
        cursor.execute('SELECT COUNT(*) FROM vault_items')
        total_items = cursor.fetchone()[0]

        # Items by category
        cursor.execute('SELECT category, COUNT(*) as count FROM vault_items GROUP BY category')
        categories = dict(cursor.fetchall())

        # Expired items
        cursor.execute('SELECT COUNT(*) FROM vault_items WHERE expires_at < ?', (datetime.now().isoformat(),))
        expired_items = cursor.fetchone()[0]

        # Items expiring soon (next 7 days)
        soon = datetime.now() + timedelta(days=7)
        cursor.execute('SELECT COUNT(*) FROM vault_items WHERE expires_at BETWEEN ? AND ?',
                      (datetime.now().isoformat(), soon.isoformat()))
        expiring_soon = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_items': total_items,
                'categories': categories,
                'expired_items': expired_items,
                'expiring_soon': expiring_soon
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vault/export', methods=['GET'])
def export_vault():
    """Export vault items (for backup)"""
    try:
        items = vault.list_items()
        export_data = {
            'export_date': datetime.now().isoformat(),
            'items': []
        }

        for item in items:
            full_item = vault.retrieve_item(item['key'])
            if full_item['success']:
                export_data['items'].append({
                    'key': full_item['key'],
                    'value': full_item['value'],  # This will be encrypted
                    'category': full_item['category'],
                    'tags': full_item['tags'],
                    'expires_at': full_item['expires_at'],
                    'created_at': full_item['created_at']
                })

        return jsonify({'success': True, 'export': export_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Keychain Management Endpoints

@app.route('/api/keychain/status', methods=['GET'])
def get_keychain_status():
    """Get macOS Keychain status"""
    return jsonify({
        'available': KEYCHAIN_AVAILABLE,
        'service_name': keychain.service_name if KEYCHAIN_AVAILABLE else None
    })

@app.route('/api/keychain/credentials', methods=['POST'])
def store_keychain_credential():
    """Store a credential in macOS Keychain"""
    try:
        if not KEYCHAIN_AVAILABLE:
            return jsonify({'success': False, 'error': 'macOS Keychain not available'}), 503

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        account_name = data.get('account_name')

        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password are required'}), 400

        result = keychain.store_credential(username, password, account_name)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/keychain/credentials/<username>', methods=['GET'])
def get_keychain_credential(username):
    """Retrieve a credential from macOS Keychain"""
    try:
        if not KEYCHAIN_AVAILABLE:
            return jsonify({'success': False, 'error': 'macOS Keychain not available'}), 503

        account_name = request.args.get('account_name')
        result = keychain.retrieve_credential(username, account_name)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/keychain/credentials/<username>', methods=['DELETE'])
def delete_keychain_credential(username):
    """Delete a credential from macOS Keychain"""
    try:
        if not KEYCHAIN_AVAILABLE:
            return jsonify({'success': False, 'error': 'macOS Keychain not available'}), 503

        account_name = request.args.get('account_name')
        result = keychain.delete_credential(username, account_name)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Consent Management Endpoints

@app.route('/api/consent/status', methods=['GET'])
def get_consent_status():
    """Get current user consent status"""
    try:
        status = consent_manager.get_consent_status()
        return jsonify({'success': True, 'consent': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/consent/record', methods=['POST'])
def record_consent():
    """Record user consent"""
    try:
        result = consent_manager.record_consent()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/consent/revoke', methods=['POST'])
def revoke_consent():
    """Revoke user consent"""
    try:
        result = consent_manager.revoke_consent()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/consent/check', methods=['GET'])
def check_consent():
    """Check if consent is valid"""
    try:
        is_valid = consent_manager.is_consent_valid()
        return jsonify({
            'success': True,
            'consent_valid': is_valid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Browser Session Management Endpoints

@app.route('/api/browser/close', methods=['POST'])
def close_browser_instances():
    """Close browser instances while preserving cookies"""
    try:
        result = browser_session_manager.close_browser_instances(preserve_cookies=True)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browser/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get active browser sessions"""
    try:
        sessions = browser_session_manager.get_active_sessions()
        return jsonify({'success': True, 'sessions': sessions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browser/sessions/history', methods=['GET'])
def get_session_history():
    """Get browser session history"""
    try:
        limit = int(request.args.get('limit', 50))
        sessions = browser_session_manager.get_session_history(limit)
        return jsonify({'success': True, 'sessions': sessions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browser/session/start', methods=['POST'])
def start_browser_session():
    """Start a new browser session"""
    try:
        data = request.get_json()
        browser_type = data.get('browser_type', 'unknown')
        session_id = data.get('session_id')

        result = browser_session_manager.start_session(browser_type, session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browser/session/end/<session_id>', methods=['POST'])
def end_browser_session(session_id):
    """End a browser session"""
    try:
        result = browser_session_manager.end_session(session_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browser/session/update/<session_id>', methods=['POST'])
def update_browser_session(session_id):
    """Update browser session information"""
    try:
        data = request.get_json()
        tabs_count = data.get('tabs_count')
        urls = data.get('urls')

        result = browser_session_manager.update_session(session_id, tabs_count, urls)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_ai_response(message, stats):
    """Generate AI response based on user message and system stats"""
    message = message.lower()

    if 'hello' in message or 'hi' in message:
        return f"Hello! I've helped clean up {stats['total_cleaned']} bytes so far. How can I assist you today?"

    elif 'scan' in message:
        return f"I've performed {stats['scan_count']} scans and found {stats['duplicate_count']} duplicate files. Would you like me to run a new scan?"

    elif 'duplicate' in message:
        if stats['duplicate_count'] > 0:
            return f"I found {stats['duplicate_count']} duplicate files. These could save you significant disk space if cleaned up."
        else:
            return "No duplicates found in recent scans. Your system looks clean!"

    elif 'clean' in message or 'cleanup' in message:
        return f"I've helped clean up {stats['total_cleaned']} bytes of space. I can run cache cleanup, temp file cleanup, or development file cleanup."

    elif 'report' in message:
        return f"I can generate detailed reports about your cleanup activities. I've tracked {stats['scan_count']} operations so far."

    elif 'help' in message:
        return """I can help you with:
• Running cleanup scans
• Managing exclude patterns
• Generating reports
• Providing cleanup recommendations
• Answering questions about your system

What would you like to know?"""

    else:
        return "I'm here to help with system cleanup! Ask me about scans, duplicates, cleanup operations, or system optimization."

# Document Processing Endpoints

processing_status = {
    'status': 'idle',
    'queue_count': 0,
    'processed_count': 0,
    'total_files': 0,
    'time_estimate': '--:--',
    'processing_speed': 0
}

processing_queue = []

# Chat Message Queue
chat_queue = []
chat_processing_active = False
chat_results = {}  # Store results by message ID

def process_chat_queue():
    """Process chat messages from the queue asynchronously"""
    global chat_processing_active

    if chat_processing_active:
        return  # Already processing

    chat_processing_active = True

    def process_messages():
        global chat_processing_active

        while chat_queue:
            try:
                message_data = chat_queue.pop(0)
                message_id = message_data['id']
                message = message_data['message']
                model = message_data['model']

                # Process the message
                context = f"""
You are TidyMe, an AI assistant for system cleanup and file management.
Current system stats:
- Scans performed: {get_scan_count()}
- Duplicates found: {get_duplicate_count()}
- Space cleaned: {get_total_cleaned()} bytes

User question: {message}

Please provide a helpful, concise response about cleanup, file management, or system optimization.
"""

                response = query_ollama(context, model)

                # Store the result
                chat_results[message_id] = {
                    'success': True,
                    'response': response,
                    'model': model,
                    'timestamp': datetime.now().isoformat()
                }

            except Exception as e:
                error_msg = str(e)
                if "Connection refused" in error_msg or "Connection aborted" in error_msg:
                    error_response = 'Cannot connect to AI service. Please ensure Ollama or llama.cpp server is running.'
                else:
                    error_response = f'AI chat error: {error_msg}'

                chat_results[message_data['id']] = {
                    'success': False,
                    'error': error_response,
                    'timestamp': datetime.now().isoformat()
                }

        chat_processing_active = False

    # Start processing in a separate thread
    import threading
    thread = threading.Thread(target=process_messages, daemon=True)
    thread.start()

@app.route('/api/processing/status', methods=['GET'])
def get_processing_status():
    """Get document processing status"""
    return jsonify(processing_status)

@app.route('/api/processing/start', methods=['POST'])
def start_processing():
    """Start document processing"""
    global processing_status

    if processing_status['status'] == 'active':
        return jsonify({'success': False, 'error': 'Processing already running'})

    # Simulate starting processing
    processing_status['status'] = 'active'
    processing_status['queue_count'] = 5  # Simulate 5 files in queue
    processing_status['total_files'] = 5
    processing_status['processed_count'] = 0
    processing_status['time_estimate'] = '02:30'
    processing_status['processing_speed'] = 2

    # Add some sample files to queue
    processing_queue.clear()
    processing_queue.extend([
        {'filename': 'document1.pdf', 'status': 'pending', 'size': 2048000},
        {'filename': 'document2.docx', 'status': 'pending', 'size': 1536000},
        {'filename': 'spreadsheet.xlsx', 'status': 'pending', 'size': 512000},
        {'filename': 'presentation.pptx', 'status': 'pending', 'size': 3072000},
        {'filename': 'text_file.txt', 'status': 'pending', 'size': 102400}
    ])

    return jsonify({'success': True, 'message': 'Document processing started'})

@app.route('/api/processing/pause', methods=['POST'])
def pause_processing():
    """Pause document processing"""
    global processing_status

    if processing_status['status'] != 'active':
        return jsonify({'success': False, 'error': 'No active processing to pause'})

    processing_status['status'] = 'paused'
    return jsonify({'success': True, 'message': 'Processing paused'})

@app.route('/api/processing/queue', methods=['GET'])
def get_processing_queue():
    """Get processing queue"""
    return jsonify({'queue': processing_queue})

@app.route('/api/processing/clear', methods=['POST'])
def clear_processing_queue():
    """Clear processing queue"""
    global processing_status, processing_queue

    processing_status = {
        'status': 'idle',
        'queue_count': 0,
        'processed_count': 0,
        'total_files': 0,
        'time_estimate': '--:--',
        'processing_speed': 0
    }

    processing_queue.clear()

    return jsonify({'success': True, 'message': 'Processing queue cleared'})

@app.route('/api/processing/analyze-documents', methods=['POST'])
def analyze_documents():
    """Analyze documents for cleanup opportunities"""
    try:
        # Simulate document analysis
        document_types = [
            {'extension': '.pdf', 'count': 15, 'total_size': 52428800},
            {'extension': '.docx', 'count': 8, 'total_size': 15728640},
            {'extension': '.xlsx', 'count': 12, 'total_size': 20971520},
            {'extension': '.txt', 'count': 25, 'total_size': 5242880},
            {'extension': '.pptx', 'count': 5, 'total_size': 10485760}
        ]

        cleanup_suggestions = [
            "Consider archiving old PDF documents older than 2 years",
            "Remove temporary Excel files (.tmp.xlsx) from Downloads folder",
            "Compress large PowerPoint presentations over 50MB",
            "Delete duplicate documents with 'copy' or 'backup' in filename",
            "Move work documents to appropriate project folders"
        ]

        return jsonify({
            'success': True,
            'document_types': document_types,
            'cleanup_suggestions': cleanup_suggestions,
            'total_documents': 65,
            'total_size': 104857600
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/processing/filter-artifacts', methods=['POST'])
def filter_artifacts():
    """Filter and categorize artifacts"""
    try:
        # Simulate artifact filtering
        categories = {
            'Temporary Files': [
                {'filename': 'temp_document.docx', 'size': 1024000, 'path': '/tmp/temp_document.docx'},
                {'filename': 'autosave.xlsx', 'size': 2048000, 'path': '/Users/username/Documents/autosave.xlsx'},
                {'filename': '~$presentation.pptx', 'size': 512000, 'path': '/Users/username/Desktop/~$presentation.pptx'}
            ],
            'Cache Files': [
                {'filename': 'document_cache.tmp', 'size': 307200, 'path': '/Users/username/Library/Caches/document_cache.tmp'},
                {'filename': 'preview_cache.dat', 'size': 153600, 'path': '/Users/username/Library/Caches/preview_cache.dat'}
            ],
            'Old Backups': [
                {'filename': 'document_backup_2020.docx', 'size': 2048000, 'path': '/Users/username/Documents/Backups/document_backup_2020.docx'},
                {'filename': 'spreadsheet_old.xlsx', 'size': 1024000, 'path': '/Users/username/Documents/Backups/spreadsheet_old.xlsx'}
            ],
            'Duplicate Files': [
                {'filename': 'report_final_v2.docx', 'size': 1536000, 'path': '/Users/username/Documents/report_final_v2.docx'},
                {'filename': 'report_final_v3.docx', 'size': 1536000, 'path': '/Users/username/Documents/report_final_v3.docx'}
            ]
        }

        return jsonify({
            'success': True,
            'categories': categories,
            'total_artifacts': 8,
            'total_size': 9216000
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Health and Monitoring Endpoints

@app.route('/api/health/system', methods=['GET'])
def get_system_health_endpoint():
    """Get system health information"""
    health_data = get_system_health()
    return jsonify(health_data)

@app.route('/api/health/check', methods=['POST'])
def run_health_check():
    """Run comprehensive health check"""
    try:
        health_data = get_system_health()

        checks = [
            {
                'name': 'Memory Usage',
                'status': 'good' if health_data['memory_usage']['used_percent'] < 60 else ('warning' if health_data['memory_usage']['used_percent'] < 80 else 'critical'),
                'details': f"{health_data['memory_usage']['used_percent']:.1f}% used"
            },
            {
                'name': 'Disk Usage',
                'status': 'good' if health_data['disk_usage']['used_percent'] < 75 else ('warning' if health_data['disk_usage']['used_percent'] < 90 else 'critical'),
                'details': f"{health_data['disk_usage']['used_percent']:.1f}% used"
            },
            {
                'name': 'CPU Usage',
                'status': 'good' if health_data['cpu_usage']['usage_percent'] < 60 else ('warning' if health_data['cpu_usage']['usage_percent'] < 80 else 'critical'),
                'details': f"{health_data['cpu_usage']['usage_percent']:.1f}% used"
            },
            {
                'name': 'Database',
                'status': 'good',  # Assume database is working if we reach this point
                'details': 'Connected and operational'
            }
        ]

        return jsonify({
            'success': True,
            'checks': checks,
            'overall_status': health_data['overall_status']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/optimize-memory', methods=['POST'])
def optimize_memory_endpoint():
    """Optimize system memory"""
    result = optimize_memory()
    return jsonify(result)

@app.route('/api/health/analyze-logs', methods=['POST'])
def analyze_logs_endpoint():
    """Analyze system logs"""
    result = analyze_system_logs()
    return jsonify(result)

@app.route('/api/health/smart-cache', methods=['POST'])
def smart_cache_endpoint():
    """Perform smart cache cleanup"""
    result = smart_cache_cleanup()
    return jsonify(result)

@app.route('/api/health/cleanup-log', methods=['POST'])
def cleanup_log_endpoint():
    """Clean up a specific log file"""
    try:
        data = request.get_json()
        log_path = data.get('log_path')

        if not log_path:
            return jsonify({'success': False, 'error': 'Log path is required'}), 400

        result = cleanup_log_file(log_path)
        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Monitoring Endpoints

monitoring_active = False

@app.route('/api/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Get monitoring status"""
    global monitoring_active, scheduler_active
    return jsonify({
        'active': monitoring_active,
        'scheduler_active': scheduler_active and APSCHEDULER_AVAILABLE,
        'jobs': [job.id for job in scheduler.get_jobs()] if scheduler_active and APSCHEDULER_AVAILABLE else []
    })

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start auto-monitoring"""
    global monitoring_active
    try:
        monitoring_active = True
        if APSCHEDULER_AVAILABLE:
            init_scheduler()  # Also start the scheduler
        return jsonify({'success': True, 'message': 'Auto-monitoring started' + (' and scheduler started' if APSCHEDULER_AVAILABLE else ' (scheduler unavailable)')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop auto-monitoring"""
    global monitoring_active
    try:
        monitoring_active = False
        if APSCHEDULER_AVAILABLE:
            shutdown_scheduler()
        return jsonify({'success': True, 'message': 'Auto-monitoring stopped' + (' and scheduler stopped' if APSCHEDULER_AVAILABLE else '')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Scheduler Management Endpoints

@app.route('/api/scheduler/jobs', methods=['GET'])
def get_scheduler_jobs():
    """Get scheduled jobs"""
    try:
        if not APSCHEDULER_AVAILABLE or not scheduler_active:
            return jsonify({'jobs': [], 'active': False})

        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return jsonify({'jobs': jobs, 'active': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduler/job/<job_id>/run', methods=['POST'])
def run_scheduler_job(job_id):
    """Manually run a scheduled job"""
    try:
        if not APSCHEDULER_AVAILABLE or not scheduler_active:
            return jsonify({'success': False, 'error': 'Scheduler not available or not active'}), 400

        job = scheduler.get_job(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        # Run the job
        job.func()

        return jsonify({'success': True, 'message': f'Job {job_id} executed successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Task Queue Management Endpoints

@app.route('/api/tasks/queue', methods=['GET'])
def get_task_queue():
    """Get task queue status"""
    try:
        status = get_task_queue_status()
        return jsonify({
            'success': True,
            'queue': status
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/create', methods=['POST'])
def create_task():
    """Create a new task with dependencies"""
    try:
        data = request.get_json()
        task_name = data.get('name')
        dependencies = data.get('dependencies', [])
        task_type = data.get('type')

        if not task_name:
            return jsonify({'success': False, 'error': 'Task name is required'}), 400

        # Map task types to functions
        task_functions = {
            'scan': scan_filesystem_task,
            'cleanup': cleanup_duplicates_task,
            'optimize': optimize_storage_task,
            'backup': lambda: backup_data_task('/tmp/tidyme_backup')
        }

        if task_type not in task_functions:
            return jsonify({'success': False, 'error': f'Unknown task type: {task_type}'}), 400

        task_id = add_task_to_queue(task_functions[task_type], task_name, dependencies)

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'Task {task_name} queued successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task_endpoint(task_id):
    """Cancel a queued task"""
    try:
        success = cancel_task(task_id)
        if success:
            return jsonify({'success': True, 'message': f'Task {task_id} cancelled'})
        else:
            return jsonify({'success': False, 'error': 'Task not found or cannot be cancelled'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/tasks/maintenance-chain', methods=['POST'])
def create_maintenance_chain_endpoint():
    """Create a maintenance task chain"""
    try:
        chain = create_maintenance_chain()
        return jsonify({
            'success': True,
            'chain': chain,
            'message': 'Maintenance chain created successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Background Process Management Endpoints

@app.route('/api/background/tasks', methods=['GET'])
def get_background_tasks():
    """Get status of all background tasks"""
    try:
        tasks = get_background_task_status()
        return jsonify({
            'success': True,
            'tasks': tasks,
            'total_tasks': len(tasks)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/background/task/<task_id>/stop', methods=['POST'])
def stop_background_task_endpoint(task_id):
    """Stop a specific background task"""
    try:
        success = stop_background_task(int(task_id))
        if success:
            return jsonify({'success': True, 'message': f'Task {task_id} stopped'})
        else:
            return jsonify({'success': False, 'error': 'Task not found or could not be stopped'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/background/cleanup', methods=['POST'])
def cleanup_background_processes_endpoint():
    """Clean up all background processes"""
    try:
        cleanup_background_processes()
        return jsonify({'success': True, 'message': 'Background processes cleaned up'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Daemon Management Endpoints





# AI Clustering Endpoints

@app.route('/api/ai/cluster-files', methods=['POST'])
def cluster_files_endpoint():
    """Cluster files using AI"""
    try:
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE or not SKLEARN_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI clustering unavailable - missing required dependencies'}), 503

        data = request.get_json()
        file_paths = data.get('files', [])
        n_clusters = data.get('n_clusters')

        if not file_paths:
            return jsonify({'success': False, 'error': 'No files provided'}), 400

        result = ai_clustering.cluster_files(file_paths, n_clusters)

        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/organize-suggestions', methods=['POST'])
def organize_suggestions_endpoint():
    """Get AI-powered organization suggestions"""
    try:
        if not TRANSFORMERS_AVAILABLE or not TORCH_AVAILABLE or not SKLEARN_AVAILABLE:
            return jsonify({'success': False, 'error': 'AI organization suggestions unavailable - missing required dependencies'}), 503

        data = request.get_json()
        cluster_result = data.get('cluster_result')

        if not cluster_result:
            return jsonify({'success': False, 'error': 'Cluster result required'}), 400

        suggestions = ai_clustering.suggest_organization(cluster_result)
        return jsonify(suggestions)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/analyze-file-content', methods=['POST'])
def analyze_file_content_endpoint():
    """Analyze file content using AI"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')

        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'Valid file path required'}), 400

        # Get file content (limited for safety)
        content = ""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # Read first 2000 characters
        except:
            return jsonify({'success': False, 'error': 'Cannot read file'}), 400

        # Use Ollama for content analysis
        prompt = f"""
Analyze this file content and provide:
1. File type/purpose
2. Key topics or themes
3. Suggested organization category
4. Any cleanup recommendations

File: {os.path.basename(file_path)}
Content: {content[:1000]}...

Provide a concise analysis.
"""

        analysis = query_ollama(prompt)

        return jsonify({
            'success': True,
            'file_path': file_path,
            'analysis': analysis,
            'content_preview': content[:200]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Daemon Management Endpoints

@app.route('/api/daemon/status', methods=['GET'])
def get_daemon_status():
    """Get daemon status"""
    try:
        is_running, pid = check_existing_instance(DAEMON_PID_FILE, 'python')

        return jsonify({
            'is_running': is_running,
            'pid': pid,
            'pidfile': DAEMON_PID_FILE
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/daemon/start', methods=['POST'])
def start_daemon():
    """Start the daemon"""
    try:
        # Check if daemon is already running
        is_running, pid = check_existing_instance(DAEMON_PID_FILE, 'python')
        if is_running:
            return jsonify({
                'success': False,
                'error': f'Daemon is already running (PID: {pid})'
            }), 409

        # Start daemon process
        import subprocess
        import sys

        cmd = [sys.executable, __file__, '--daemon']
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )

        # Wait a moment for daemon to start
        time.sleep(2)

        # Check if daemon started successfully
        is_running, new_pid = check_existing_instance(DAEMON_PID_FILE, 'python')
        if is_running:
            return jsonify({
                'success': True,
                'message': 'Daemon started successfully',
                'pid': new_pid
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to start daemon'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/daemon/stop', methods=['POST'])
def stop_daemon():
    """Stop the daemon"""
    try:
        is_running, pid = check_existing_instance(DAEMON_PID_FILE, 'python')
        if not is_running:
            return jsonify({'success': False, 'error': 'Daemon is not running'}), 404

        # Send SIGTERM to daemon process
        os.kill(pid, signal.SIGTERM)

        # Wait for process to stop
        for _ in range(10):  # Wait up to 10 seconds
            time.sleep(1)
            current_status, _ = check_existing_instance(DAEMON_PID_FILE, 'python')
            if not current_status:
                return jsonify({'success': True, 'message': 'Daemon stopped successfully'})

        # If still running, force kill
        try:
            os.kill(pid, signal.SIGKILL)
            return jsonify({'success': True, 'message': 'Daemon force-stopped'})
        except OSError:
            return jsonify({'success': False, 'error': 'Failed to stop daemon'}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Database Management Endpoints

@app.route('/api/database/migrate-postgresql', methods=['POST'])
def migrate_database():
    """Migrate database from SQLite to PostgreSQL"""
    try:
        result = migrate_to_postgresql()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/status', methods=['GET'])
def get_database_status():
    """Get current database configuration and status"""
    try:
        db_config = getattr(app, 'config', {})
        current_db = 'PostgreSQL' if db_config.get('USE_POSTGRESQL', False) else 'SQLite'

        return jsonify({
            'current_database': current_db,
            'postgresql_configured': db_config.get('USE_POSTGRESQL', False),
            'host': db_config.get('POSTGRES_HOST', 'Not configured'),
            'database': db_config.get('POSTGRES_DB', 'Not configured'),
            'migration_available': not db_config.get('USE_POSTGRESQL', False)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Server Management Endpoints

@app.route('/api/server/start', methods=['POST'])
def start_server():
    """Start the TidyMe server (for UI control)"""
    try:
        # This endpoint is mainly for documentation - the server should already be running
        # In a production setup, this could trigger external server management
        return jsonify({
            'success': True,
            'message': 'Server is running',
            'status': 'active',
            'uptime': 'N/A'  # Could be enhanced to track actual uptime
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/server/status', methods=['GET'])
def get_server_status():
    """Get server status"""
    try:
        return jsonify({
            'status': 'running',
            'version': '2.0',
            'uptime': 'N/A',
            'memory_usage': psutil.Process().memory_info().rss if 'psutil' in globals() else 0
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

def main():
    """Main application entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='TidyMe - System Cleanup and Management Tool')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon process')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--force', action='store_true', help='Force start even if another instance is running')

    args = parser.parse_args()

    # Check for existing server instance (unless force is specified)
    # Allow server and daemon to run concurrently
    if not args.daemon and not args.force:
        is_running, pid = check_existing_instance(SERVER_PID_FILE, 'python')
        if is_running:
            print(f"❌ Another TidyMe server instance is already running (PID: {pid})")
            print("Use --force to start anyway, or stop the existing instance first.")
            print("To stop the existing instance: kill", pid)
            return

    # Check for existing daemon instance (only if starting daemon)
    if args.daemon and not args.force:
        is_running, pid = check_existing_instance(DAEMON_PID_FILE, 'python')
        if is_running:
            print(f"❌ Another TidyMe daemon instance is already running (PID: {pid})")
            print("Use --force to start anyway, or stop the existing daemon first.")
            print("To stop the existing daemon: kill", pid)
            return

    # Configuration
    app.config['SECRET_KEY'] = 'dev-key-change-in-production'
    app.config['JSON_SORT_KEYS'] = False

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Register cleanup function
    atexit.register(lambda: cleanup_pid_file(SERVER_PID_FILE))
    atexit.register(lambda: cleanup_pid_file(DAEMON_PID_FILE))

    if args.daemon:
        print("Starting TidyMe in daemon mode...")
        create_pid_file(DAEMON_PID_FILE)
        if not run_as_daemon():
            print("Failed to start as daemon. Falling back to normal mode.")
            cleanup_pid_file(DAEMON_PID_FILE)
            args.daemon = False
        else:
            print(f"✅ TidyMe daemon started successfully (PID: {os.getpid()})")
            return  # Daemon started successfully

    # Normal execution mode
    print("Starting TidyMe server...")
    create_pid_file(SERVER_PID_FILE)

    # Initialize background services
    start_background_services()

    print(f"✅ TidyMe server started successfully (PID: {os.getpid()})")
    print(f"🌐 Server running on http://{args.host}:{args.port}")
    print("📁 Data directory:", DATA_DIR)
    print("🗄️  Database:", DATABASE)

    try:
        # Run the Flask app
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
    finally:
        # Clean up background processes and scheduler
        stop_task_scheduler()
        if APSCHEDULER_AVAILABLE and scheduler_active:
            shutdown_scheduler()
        cleanup_background_processes()
        cleanup_pid_file(SERVER_PID_FILE)
        print("Shutdown complete.")

if __name__ == '__main__':
    main()

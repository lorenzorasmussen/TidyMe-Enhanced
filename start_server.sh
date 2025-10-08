#!/bin/bash
# TidyMe Server Startup Script

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
LOG_DIR="$SCRIPT_DIR/logs"
DATA_DIR="$SCRIPT_DIR/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_DIR/server.log"
}

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    log "ERROR: $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
    log "WARNING: $1"
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
    log "SUCCESS: $1"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    success "Directories created"
}

# Setup Python virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv "$VENV_DIR" || error "Failed to create virtual environment"
        success "Virtual environment created"
    fi

    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate" || error "Failed to activate virtual environment"

    log "Installing/updating dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt || error "Failed to install dependencies"
    success "Dependencies installed"
}

# Check if server is already running
check_server_running() {
    local pid_file="$DATA_DIR/tidyme.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            warning "Server appears to be already running (PID: $pid)"
            echo "Use './stop_server.sh' to stop it first, or remove $pid_file if it's stale"
            exit 1
        else
            warning "Removing stale PID file"
            rm -f "$pid_file"
        fi
    fi
}

# Start the server
start_server() {
    log "Starting TidyMe server..."

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export FLASK_APP=app.py
    export FLASK_ENV=production

    # Start with Gunicorn if available, otherwise Flask
    if command -v gunicorn >/dev/null 2>&1; then
        log "Starting with Gunicorn..."
        gunicorn --config gunicorn.conf.py app:app &
        echo $! > "$DATA_DIR/tidyme.pid"
    else
        warning "Gunicorn not found, starting with Flask development server"
        python -m flask run --host=127.0.0.1 --port=5000 &
        echo $! > "$DATA_DIR/tidyme.pid"
    fi

    sleep 2

    # Verify server started
    if kill -0 $(cat "$DATA_DIR/tidyme.pid") 2>/dev/null; then
        success "Server started successfully (PID: $(cat "$DATA_DIR/tidyme.pid"))"
        echo "Server is running at http://127.0.0.1:5000"
        echo "Web interface: http://127.0.0.1:5000/"
        echo "API endpoints: http://127.0.0.1:5000/api/"
    else
        error "Failed to start server"
    fi
}

# Main execution
main() {
    echo "🧹 TidyMe Server Startup"
    echo "========================"

    create_directories
    setup_venv
    check_server_running
    start_server

    echo ""
    echo "Server startup complete!"
    echo "Logs are available in: $LOG_DIR/"
    echo "PID file: $DATA_DIR/tidyme.pid"
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "TidyMe Server Startup Script"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --dev         Start in development mode"
        echo ""
        exit 0
        ;;
    "--dev")
        warning "Starting in development mode"
        export FLASK_ENV=development
        ;;
esac

main
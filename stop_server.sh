#!/bin/bash
# TidyMe Server Stop Script

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Stop the server
stop_server() {
    local pid_file="$DATA_DIR/tidyme.pid"

    if [ ! -f "$pid_file" ]; then
        warning "PID file not found: $pid_file"
        echo "Server may not be running"
        return
    fi

    local pid=$(cat "$pid_file")
    log "Stopping server (PID: $pid)"

    if kill "$pid" 2>/dev/null; then
        # Wait for process to stop
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            ((count++))
        done

        if kill -0 "$pid" 2>/dev/null; then
            warning "Server didn't stop gracefully, forcing stop..."
            kill -9 "$pid" 2>/dev/null || true
        fi

        success "Server stopped"
    else
        warning "Process $pid not found or already stopped"
    fi

    # Clean up PID file
    rm -f "$pid_file"
}

# Main execution
main() {
    echo "🧹 TidyMe Server Stop"
    echo "====================="

    stop_server

    echo ""
    echo "Server stop complete!"
}

main
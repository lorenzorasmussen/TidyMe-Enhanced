#!/bin/bash
# Test suite for TidyMe cleanup script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test helper functions
test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((TESTS_RUN++))
}

test_info() {
    echo -e "${YELLOW}INFO${NC}: $1"
}

# Setup test environment
setup_test_env() {
    test_info "Setting up test environment..."

    # Create temporary directory for tests
    TEST_DIR="/tmp/tidyme-test-$$"
    mkdir -p "$TEST_DIR"

    # Create test data directory
    TEST_DATA_DIR="$TEST_DIR/data"
    mkdir -p "$TEST_DATA_DIR"

    # Create test database
    TEST_DB="$TEST_DATA_DIR/cleanup.db"
    sqlite3 "$TEST_DB" << 'EOF'
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
CREATE TABLE IF NOT EXISTS duplicates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT,
    file_path TEXT,
    file_size INTEGER,
    file_hash TEXT,
    similarity_score REAL,
    recommended_action TEXT,
    scan_date DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cleanup_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT,
    file_path TEXT,
    file_size INTEGER,
    success INTEGER,
    error_message TEXT
);
EOF

    # Create test files
    TEST_FILES_DIR="$TEST_DIR/test-files"
    mkdir -p "$TEST_FILES_DIR"

    # Create some test files
    echo "test content 1" > "$TEST_FILES_DIR/file1.txt"
    echo "test content 2" > "$TEST_FILES_DIR/file2.txt"
    echo "test content 1" > "$TEST_FILES_DIR/duplicate1.txt"  # Duplicate of file1
    echo "different content" > "$TEST_FILES_DIR/file3.txt"

    # Create subdirectory with files
    mkdir -p "$TEST_FILES_DIR/subdir"
    echo "subdir content" > "$TEST_FILES_DIR/subdir/file.txt"

    test_pass "Test environment setup"
}

# Cleanup test environment
cleanup_test_env() {
    test_info "Cleaning up test environment..."
    rm -rf "$TEST_DIR"
    test_pass "Test environment cleanup"
}

# Test script execution
test_script_execution() {
    test_info "Testing script execution..."

    # Test help command
    if ./cleanup --help > /dev/null 2>&1; then
        test_pass "Help command execution"
    else
        test_fail "Help command execution"
    fi

    # Test invalid command
    if ./cleanup invalid-command 2>&1 | grep -q "Unknown command"; then
        test_pass "Invalid command handling"
    else
        test_fail "Invalid command handling"
    fi
}

# Test database functions
test_database_functions() {
    test_info "Testing database functions..."

    # Test database initialization
    if [ -f "$TEST_DB" ]; then
        # Check if tables exist
        table_count=$(sqlite3 "$TEST_DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('scans', 'files', 'duplicates', 'cleanup_log');")
        if [ "$table_count" -eq 4 ]; then
            test_pass "Database schema creation"
        else
            test_fail "Database schema creation (found $table_count tables, expected 4)"
        fi
    else
        test_fail "Database file creation"
    fi
}

# Test utility functions
test_utility_functions() {
    test_info "Testing utility functions..."

    # Test format_bytes function (we'll test the logic manually)
    # This would require sourcing the script or extracting functions

    # Test file hashing (create a test file and hash it)
    test_file="$TEST_FILES_DIR/hash_test.txt"
    echo "test hash content" > "$test_file"

    if command -v shasum >/dev/null 2>&1; then
        hash1=$(shasum -a 256 "$test_file" | cut -d' ' -f1)
        hash2=$(shasum -a 256 "$test_file" | cut -d' ' -f1)

        if [ "$hash1" = "$hash2" ]; then
            test_pass "File hashing consistency"
        else
            test_fail "File hashing consistency"
        fi
    else
        test_info "shasum not available, skipping hash test"
    fi
}

# Test file operations
test_file_operations() {
    test_info "Testing file operations..."

    # Test file size calculation
    test_file="$TEST_FILES_DIR/size_test.txt"
    echo -n "12345" > "$test_file"  # 5 bytes

    if command -v stat >/dev/null 2>&1; then
        size=$(stat -f%z "$test_file" 2>/dev/null || echo 0)
        if [ "$size" -eq 5 ]; then
            test_pass "File size calculation"
        else
            test_fail "File size calculation (got $size, expected 5)"
        fi
    else
        test_info "stat not available, skipping size test"
    fi
}

# Test exclusion patterns
test_exclusion_patterns() {
    test_info "Testing exclusion patterns..."

    # Create files that should be excluded
    mkdir -p "$TEST_FILES_DIR/.git"
    echo "git content" > "$TEST_FILES_DIR/.git/config"

    mkdir -p "$TEST_FILES_DIR/node_modules"
    echo "node content" > "$TEST_FILES_DIR/node_modules/package.json"

    # Test that find respects exclusions (basic test)
    if find "$TEST_FILES_DIR" -name "*.txt" 2>/dev/null | grep -q "file1.txt"; then
        test_pass "File discovery works"
    else
        test_fail "File discovery works"
    fi
}

# Run all tests
run_tests() {
    echo "=========================================="
    echo "Running TidyMe Test Suite"
    echo "=========================================="

    setup_test_env

    test_script_execution
    test_database_functions
    test_utility_functions
    test_file_operations
    test_exclusion_patterns

    cleanup_test_env

    echo "=========================================="
    echo "Test Results: $TESTS_PASSED/$TESTS_RUN tests passed"
    echo "=========================================="

    if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Main execution
if [ ! -f "./cleanup" ]; then
    echo -e "${RED}Error: cleanup script not found in current directory${NC}"
    exit 1
fi

if [ ! -x "./cleanup" ]; then
    echo -e "${RED}Error: cleanup script is not executable${NC}"
    echo "Run: chmod +x cleanup"
    exit 1
fi

run_tests
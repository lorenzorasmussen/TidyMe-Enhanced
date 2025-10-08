#!/usr/bin/env python3
"""
Integration test for TidyMe application
Tests the full application stack including Flask app, database, and AI features
"""

import unittest
import tempfile
import os
import sqlite3
import subprocess
import time
from app import app, init_db, get_db_connection
from ai_analyzer import CleanupAnalyzer


class TestTidyMeIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['DATABASE'] = self.db_path
        app.config['TESTING'] = True
        self.app = app.test_client()

        with app.app_context():
            init_db()

    def tearDown(self):
        """Clean up test environment"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_full_application_stack(self):
        """Test the complete application stack"""
        # Test Flask app initialization
        self.assertIsNotNone(app)

        # Test database connection
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        conn.close()

        # Test web interface
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TidyMe', response.data)

        # Test API endpoints
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_space_cleaned', data)

        # Test AI analyzer
        analyzer = CleanupAnalyzer(self.db_path)
        self.assertIsNotNone(analyzer)

        # Test AI insights
        insights = analyzer.get_cleanup_insights()
        self.assertIsInstance(insights, list)

        # Test AI suggestions
        suggestions = analyzer.suggest_cleanup_schedule()
        self.assertIsInstance(suggestions, list)

        print("✅ Full application stack test passed!")

    def test_database_operations(self):
        """Test database operations work correctly"""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Test inserting a scan record
        cursor.execute('''
            INSERT INTO scans (scan_type, files_found, total_size, status)
            VALUES (?, ?, ?, ?)
        ''', ('test_scan', 5, 1024, 'completed'))

        scan_id = cursor.lastrowid

        # Test retrieving the record
        cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,))
        scan = cursor.fetchone()
        self.assertIsNotNone(scan)
        self.assertEqual(scan['scan_type'], 'test_scan')

        conn.commit()
        conn.close()

        print("✅ Database operations test passed!")

    def test_ai_analysis(self):
        """Test AI analysis functionality"""
        # Insert some test data
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO scans (scan_type, files_found, total_size, status)
            VALUES (?, ?, ?, ?)
        ''', ('cache_cleanup', 10, 2048, 'completed'))

        cursor.execute('''
            INSERT INTO cleanup_log (action_type, file_path, file_size, success)
            VALUES (?, ?, ?, ?)
        ''', ('cache_delete', '/tmp/test.txt', 1024, 1))

        conn.commit()
        conn.close()

        # Test AI analyzer with data
        analyzer = CleanupAnalyzer(self.db_path)

        patterns = analyzer.analyze_cleanup_patterns()
        self.assertIn('cache_delete', patterns)

        insights = analyzer.get_cleanup_insights()
        self.assertIsInstance(insights, list)

        print("✅ AI analysis test passed!")

    def test_web_ui_components(self):
        """Test that web UI components are properly served"""
        # Test CSS file
        response = self.app.get('/static/css/style.css')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'body', response.data)

        # Test JavaScript file
        response = self.app.get('/static/js/app.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'loadStats', response.data)

        print("✅ Web UI components test passed!")


def run_cli_test():
    """Test CLI functionality"""
    print("\n🧹 Testing CLI functionality...")

    try:
        # Test help command
        result = subprocess.run(['./cleanup', '--help'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and 'TidyMe' in result.stdout:
            print("✅ CLI help command works")
        else:
            print("❌ CLI help command failed")

        # Test report command (should work even with empty database)
        result = subprocess.run(['./cleanup', 'report'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ CLI report command works")
        else:
            print("❌ CLI report command failed")

    except subprocess.TimeoutExpired:
        print("❌ CLI test timed out")
    except FileNotFoundError:
        print("❌ CLI script not found")


if __name__ == '__main__':
    print("🚀 Running TidyMe Integration Tests")
    print("=" * 50)

    # Run unit tests
    unittest.main(verbosity=2, exit=False)

    # Run CLI tests
    run_cli_test()

    print("\n" + "=" * 50)
    print("🎉 Integration testing complete!")
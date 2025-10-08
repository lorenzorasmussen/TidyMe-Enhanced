#!/usr/bin/env python3
"""
Test suite for TidyMe Flask API
"""

import unittest
import tempfile
import os
import sqlite3
from app import app, init_db, get_db_connection


class TestTidyMeAPI(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['DATABASE'] = self.db_path
        app.config['TESTING'] = True
        self.app = app.test_client()

        with app.app_context():
            init_db()

    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_get_scans_empty(self):
        """Test getting scans when database is empty"""
        response = self.app.get('/api/scans')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, [])

    def test_get_duplicates_empty(self):
        """Test getting duplicates when database is empty"""
        response = self.app.get('/api/duplicates')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, [])

    def test_get_cleanup_log_empty(self):
        """Test getting cleanup log when database is empty"""
        response = self.app.get('/api/cleanup-log')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data, [])

    def test_get_stats_empty(self):
        """Test getting stats when database is empty"""
        response = self.app.get('/api/stats')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['total_space_cleaned'], 0)
        self.assertEqual(data['duplicate_files_found'], 0)
        self.assertEqual(data['recent_scans'], 0)

    def test_invalid_cleanup_action(self):
        """Test invalid cleanup action"""
        response = self.app.post('/api/cleanup/invalid-action')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_scan_not_found(self):
        """Test getting non-existent scan"""
        response = self.app.get('/api/scans/999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)

    def test_web_interface_route(self):
        """Test web interface route"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TidyMe', response.data)


class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['DATABASE'] = self.db_path

        with app.app_context():
            init_db()

    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_schema(self):
        """Test that database schema is created correctly"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ['scans', 'files', 'duplicates', 'cleanup_log']
        for table in expected_tables:
            self.assertIn(table, tables)

        # Check indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = ['idx_files_hash', 'idx_files_size', 'idx_duplicates_group']
        for index in expected_indexes:
            self.assertIn(index, indexes)

        conn.close()


if __name__ == '__main__':
    unittest.main()
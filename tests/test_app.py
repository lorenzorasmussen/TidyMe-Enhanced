import pytest
import os
import tempfile
import json
from app import app, get_db_connection, ai_clustering


@pytest.fixture
def client():
    """Test client for Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_db():
    """Temporary database for testing"""
    db_fd, db_path = tempfile.mkstemp()
    app.config['DATABASE'] = db_path

    with app.app_context():
        # Initialize test database
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                scan_type TEXT,
                files_found INTEGER,
                total_size INTEGER,
                status TEXT
            )
        ''')
        conn.commit()
        conn.close()

    yield db_path

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health/system')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'overall_status' in data
    assert 'memory_usage' in data


def test_stats_endpoint(client, temp_db):
    """Test stats endpoint"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_space_cleaned' in data
    assert 'duplicate_files_found' in data


def test_ai_clustering():
    """Test AI clustering functionality"""
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_files = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f'test_file_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'This is test file {i} with some content.')
            test_files.append(file_path)

        # Test clustering
        result = ai_clustering.cluster_files(test_files, n_clusters=2)

        # Should succeed with basic clustering
        assert result['success'] is True or result['error'] == 'Need at least 2 files for clustering'


def test_file_embedding():
    """Test file embedding generation"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test file
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('This is a test file for embedding.')

        # Generate embedding
        embedding = ai_clustering.get_file_embedding(test_file)

        # Should return an embedding (numpy array)
        assert embedding is not None
        assert len(embedding) > 0


def test_ollama_chat_endpoint(client):
    """Test Ollama chat endpoint"""
    test_data = {
        'message': 'Hello, test message',
        'model': 'llama3.2:3b'
    }

    response = client.post('/api/ollama/chat',
                          data=json.dumps(test_data),
                          content_type='application/json')

    # Should return 200 even if Ollama is not available
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'response' in data


def test_processing_status(client):
    """Test document processing status endpoint"""
    response = client.get('/api/processing/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'queue_count' in data


def test_daemon_status(client):
    """Test daemon status endpoint"""
    response = client.get('/api/daemon/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'running' in data


def test_config_endpoint(client):
    """Test configuration endpoint"""
    response = client.get('/api/config')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)


def test_invalid_cleanup_action(client):
    """Test invalid cleanup action"""
    response = client.post('/api/cleanup/invalid-action')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'Invalid action' in data['error']


def test_file_browser_endpoint(client):
    """Test file browser endpoint"""
    response = client.get('/api/files/browse?path=/tmp')
    assert response.status_code in [200, 403, 404]  # Various responses possible based on permissions


if __name__ == '__main__':
    pytest.main([__file__])
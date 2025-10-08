#!/usr/bin/env python3
"""
Test AI features with sample data
"""

import os
import tempfile
import shutil
from app import ai_clustering, query_ollama

def create_sample_files():
    """Create sample files for testing"""
    temp_dir = tempfile.mkdtemp()

    # Create various types of files
    sample_files = [
        ('document1.txt', 'This is a text document about project planning and development.'),
        ('document2.txt', 'Another text file discussing software architecture and design patterns.'),
        ('script1.py', 'def hello_world():\n    print("Hello, World!")\n    return True'),
        ('script2.py', 'import os\n\ndef get_files():\n    return os.listdir(".")'),
        ('readme.md', '# Project README\n\nThis project is about file management and cleanup.'),
        ('config.json', '{"database": "sqlite", "debug": true, "port": 5000}'),
        ('image.jpg', 'Fake image file content'),  # Simulate binary file
        ('video.mp4', 'Fake video file content'),  # Simulate binary file
    ]

    file_paths = []
    for filename, content in sample_files:
        file_path = os.path.join(temp_dir, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            file_paths.append(file_path)
        except:
            # Skip files that can't be written
            pass

    return temp_dir, file_paths

def test_ai_clustering():
    """Test AI clustering functionality"""
    print("🧠 Testing AI Clustering...")

    temp_dir, file_paths = create_sample_files()

    try:
        # Test clustering
        result = ai_clustering.cluster_files(file_paths, n_clusters=3)

        if result['success']:
            print(f"✅ Clustering successful!")
            print(f"   - Files analyzed: {result['total_files']}")
            print(f"   - Clusters created: {result['n_clusters']}")

            for cluster_id, files in result['clusters'].items():
                description = result['descriptions'].get(cluster_id, f"Cluster {cluster_id}")
                print(f"   - {description}: {len(files)} files")
                for file in files[:2]:  # Show first 2 files
                    print(f"     * {os.path.basename(file)}")

            # Test organization suggestions
            suggestions = ai_clustering.suggest_organization(result)
            if suggestions['success']:
                print(f"   - Organization suggestions: {len(suggestions['suggestions'])}")

        else:
            print(f"❌ Clustering failed: {result['error']}")

    except Exception as e:
        print(f"❌ Clustering error: {e}")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

def test_file_embeddings():
    """Test file embedding generation"""
    print("\n📊 Testing File Embeddings...")

    temp_dir, file_paths = create_sample_files()

    try:
        for file_path in file_paths[:3]:  # Test first 3 files
            embedding = ai_clustering.get_file_embedding(file_path)
            if embedding is not None:
                print(f"✅ Embedding generated for {os.path.basename(file_path)} (size: {len(embedding)})")
            else:
                print(f"❌ Failed to generate embedding for {os.path.basename(file_path)}")

    except Exception as e:
        print(f"❌ Embedding error: {e}")

    finally:
        shutil.rmtree(temp_dir)

def test_ollama_integration():
    """Test Ollama integration"""
    print("\n🤖 Testing Ollama Integration...")

    try:
        # Test simple query
        prompt = "Hello! Can you help me with file organization? Please respond with a short message."
        response = query_ollama(prompt)

        if response and not response.startswith("Error"):
            print("✅ Ollama query successful!")
            print(f"   Response: {response[:100]}...")
        else:
            print(f"❌ Ollama query failed: {response}")

    except Exception as e:
        print(f"❌ Ollama error: {e}")

def test_ai_file_analysis():
    """Test AI file content analysis"""
    print("\n🔍 Testing AI File Analysis...")

    temp_dir, file_paths = create_sample_files()

    try:
        # Test analysis on a text file
        text_file = None
        for file_path in file_paths:
            if file_path.endswith('.txt'):
                text_file = file_path
                break

        if text_file:
            from app import analyze_file_content_endpoint
            # This would need to be adapted for testing
            print(f"✅ Would analyze: {os.path.basename(text_file)}")
        else:
            print("❌ No suitable text file found for analysis")

    except Exception as e:
        print(f"❌ Analysis error: {e}")

    finally:
        shutil.rmtree(temp_dir)

def main():
    """Run all AI feature tests"""
    print("🚀 Starting AI Features Test Suite")
    print("=" * 50)

    test_ai_clustering()
    test_file_embeddings()
    test_ollama_integration()
    test_ai_file_analysis()

    print("\n" + "=" * 50)
    print("🏁 AI Features Test Suite Complete")

if __name__ == "__main__":
    main()
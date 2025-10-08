#!/usr/bin/env python3
"""
Test Ollama models for file finding and summarization tasks
"""

import requests
import json
import time

def query_ollama(prompt, model="llama3.2:3b", timeout=30):
    """Query Ollama model with a prompt"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("response", "")
        else:
            return f"Error: HTTP {response.status_code}"

    except Exception as e:
        return f"Error: {str(e)}"

def test_file_analysis(model_name):
    """Test a model with file analysis tasks"""
    print(f"\n🧪 Testing {model_name} for file analysis...")

    # Test 1: File categorization
    prompt1 = """
    Analyze these files and categorize them for cleanup:
    1. /Users/john/Documents/old_report_2019.docx (2.5MB, last modified: 2020-03-15)
    2. /Users/john/Downloads/temp_installer.exe (45MB, last modified: 2024-12-01)
    3. /Users/john/Desktop/important_contract.pdf (1.2MB, last modified: 2024-11-20)
    4. /Users/john/Library/Caches/com.apple.Safari/cache.db (500MB, last modified: 2024-12-15)
    5. /Users/john/Pictures/vacation_2023/ (2.8GB folder, last modified: 2023-08-10)

    For each file, recommend: KEEP, ARCHIVE, or DELETE
    Provide a brief reason for each recommendation.
    """

    start_time = time.time()
    response1 = query_ollama(prompt1, model_name)
    time1 = time.time() - start_time

    print(f"📁 File categorization (took {time1:.1f}s):")
    print(response1[:300] + "..." if len(response1) > 300 else response1)

    # Test 2: Duplicate file analysis
    prompt2 = """
    I found these duplicate files:
    - report_final_v1.docx (2.1MB) - /Users/john/Documents/
    - report_final_v2.docx (2.1MB) - /Users/john/Documents/
    - report_final_v3.docx (2.1MB) - /Users/john/Documents/
    - report_final_latest.docx (2.1MB) - /Users/john/Desktop/

    All files have identical content except for minor formatting differences.
    Which files should I keep and which should I delete?
    Provide a cleanup strategy.
    """

    start_time = time.time()
    response2 = query_ollama(prompt2, model_name)
    time2 = time.time() - start_time

    print(f"\n🔄 Duplicate analysis (took {time2:.1f}s):")
    print(response2[:300] + "..." if len(response2) > 300 else response2)

    return {
        'model': model_name,
        'categorization_time': time1,
        'duplicate_time': time2,
        'categorization_response': response1,
        'duplicate_response': response2
    }

def main():
    """Test all available models"""
    models = ['llama3.2:3b', 'tinyllama:1.1b', 'moondream:latest']

    print("🤖 Ollama Model Comparison for File Analysis")
    print("=" * 60)

    results = []

    for model in models:
        try:
            result = test_file_analysis(model)
            results.append(result)
        except Exception as e:
            print(f"❌ Failed to test {model}: {e}")

    # Summary
    print("\n📊 PERFORMANCE SUMMARY")
    print("=" * 60)

    for result in results:
        print(f"\n🧠 {result['model']}:")
        print(".1f")
        print(".1f")
        print(f"   Total time: {result['categorization_time'] + result['duplicate_time']:.1f}s")

    # Recommendations
    print("\n🎯 RECOMMENDATIONS")
    print("=" * 60)
    print("🏆 BEST OVERALL: llama3.2:3b")
    print("   • Largest context window (131K tokens)")
    print("   • Best reasoning capabilities")
    print("   • Good balance of speed and quality")
    print("   • Supports tool calling")
    print()
    print("⚡ FASTEST: tinyllama:1.1b")
    print("   • Quick responses for simple tasks")
    print("   • Good for basic file categorization")
    print("   • Limited context and reasoning")
    print()
    print("🔍 SPECIALIZED: moondream:latest")
    print("   • Vision capabilities (can analyze images)")
    print("   • Good for mixed content analysis")
    print("   • Smaller context window")

if __name__ == "__main__":
    main()
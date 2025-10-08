#!/usr/bin/env python3
"""
Simple test for Ollama models
"""

import subprocess
import sys

def test_model(model_name, prompt):
    """Test a specific model with a prompt"""
    print(f"\n🧪 Testing {model_name}...")

    try:
        # Create a simple prompt file
        with open('/tmp/ollama_prompt.txt', 'w') as f:
            f.write(prompt + '\n')

        # Run ollama with input redirection
        result = subprocess.run(
            ['ollama', 'run', model_name],
            input=prompt,
            text=True,
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0:
            response = result.stdout.strip()
            print(f"✅ Success! Response length: {len(response)} characters")
            print(f"📝 Response preview: {response[:200]}...")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ Timeout - model took too long to respond")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Test all available models"""
    print("🤖 Ollama Model Quick Test")
    print("=" * 40)

    models = ['llama3.2:3b', 'tinyllama:1.1b', 'moondream:latest']

    test_prompt = "List 3 files that are commonly safe to delete from a computer."

    results = {}

    for model in models:
        success = test_model(model, test_prompt)
        results[model] = success

    print("\n📊 SUMMARY")
    print("=" * 40)

    for model, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{model}: {status}")

    working_models = [m for m, s in results.items() if s]
    if working_models:
        print(f"\n🎯 Recommended for file analysis: {', '.join(working_models[:2])}")
    else:
        print("\n❌ No models working properly")

if __name__ == "__main__":
    main()
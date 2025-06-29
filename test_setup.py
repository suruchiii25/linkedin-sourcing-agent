#!/usr/bin/env python3
"""
Test script to verify our development environment is set up correctly.
"""

import sys
import os
from dotenv import load_dotenv

def test_python_version():
    """Test if Python version is compatible."""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version OK")
    return True

def test_imports():
    """Test if all required packages are installed."""
    try:
        import requests
        import bs4
        import pandas as pd
        import fastapi
        import groq
        from googlesearch import search
        print("✅ All packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_environment():
    """Test if environment variables are loaded."""
    load_dotenv()
    
    groq_key = os.getenv('GROQ_API_KEY')
    if not groq_key or groq_key == 'your_groq_api_key_here':
        print("❌ GROQ_API_KEY not set properly")
        return False
    
    print("✅ Environment variables loaded")
    return True

def test_groq_connection():
    """Test if we can connect to Groq API."""
    try:
        load_dotenv()
        from groq import Groq
        
        # Create client without proxies parameter
        client = Groq(
            api_key=os.getenv('GROQ_API_KEY')
        )
        
        # Simple test call
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say hello"}],
            model="llama3-8b-8192",
            max_tokens=10
        )
        
        print("✅ Groq API connection successful")
        print(f"Test response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Groq API connection failed: {e}")
        print("💡 This might be OK - we can proceed with building the agent")
        return False

def main():
    """Run all tests."""
    print("🔧 Testing LinkedIn Sourcing Agent Setup...")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_imports,
        test_environment,
        test_groq_connection
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 Setup complete! Ready to build the agent.")
    else:
        print("❌ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main()
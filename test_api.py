#!/usr/bin/env python3
"""
Test script for the LLM API
Run this after deploying to test your API endpoints
"""

import requests
import json
import time
import sys

def test_api(base_url):
    """Test the LLM API endpoints"""
    print(f"Testing LLM API at: {base_url}")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed")
            print(f"   Model: {health_data.get('model')}")
            print(f"   Device: {health_data.get('device')}")
            print(f"   GPU Available: {health_data.get('gpu_available')}")
            if health_data.get('gpu_name'):
                print(f"   GPU: {health_data.get('gpu_name')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test metrics endpoint
    print("\n3. Testing metrics endpoint...")
    try:
        response = requests.get(f"{base_url}/metrics", timeout=10)
        if response.status_code == 200:
            metrics = response.json()
            print("✅ Metrics endpoint working")
            print(f"   Device: {metrics.get('device')}")
            if 'gpu_memory_used' in metrics:
                print(f"   GPU Memory: {metrics.get('gpu_memory_used')}")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
    
    # Test text generation
    print("\n4. Testing text generation...")
    test_prompts = [
        {
            "prompt": "The future of artificial intelligence is",
            "max_new_tokens": 30,
            "temperature": 0.7
        },
        {
            "prompt": "Hello, how are you?",
            "max_new_tokens": 20,
            "temperature": 0.8
        },
        {
            "prompt": "Write a short poem about the ocean:",
            "max_new_tokens": 50,
            "temperature": 1.0
        }
    ]
    
    for i, test_case in enumerate(test_prompts, 1):
        print(f"\n   Test {i}: '{test_case['prompt'][:30]}...'")
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/generate",
                json=test_case,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Generation successful ({elapsed_time:.2f}s)")
                print(f"   📝 Generated: {result.get('generated_text', '')[:100]}...")
                print(f"   🔧 Device: {result.get('device_used')}")
                print(f"   🎯 Tokens: {result.get('tokens_generated')}")
                print(f"   💾 Cached: {result.get('cached')}")
            else:
                print(f"   ❌ Generation failed: {response.status_code}")
                print(f"   Error: {response.text}")
        except requests.exceptions.Timeout:
            print(f"   ⏰ Request timed out after 60 seconds")
        except Exception as e:
            print(f"   ❌ Generation error: {e}")
    
    # Test caching (run same request twice)
    print("\n5. Testing response caching...")
    cache_test = {
        "prompt": "Testing cache functionality",
        "max_new_tokens": 25,
        "temperature": 0.7
    }
    
    try:
        # First request
        print("   Making first request...")
        response1 = requests.post(
            f"{base_url}/generate",
            json=cache_test,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"   First request: {result1.get('processing_time', 0):.2f}s")
            
            # Second request (should be cached)
            print("   Making second request (should be cached)...")
            time.sleep(1)  # Brief pause
            response2 = requests.post(
                f"{base_url}/generate",
                json=cache_test,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response2.status_code == 200:
                result2 = response2.json()
                print(f"   Second request: {result2.get('processing_time', 0):.2f}s")
                print(f"   ✅ Cache working: {result2.get('cached', False)}")
            else:
                print(f"   ❌ Second request failed: {response2.status_code}")
        else:
            print(f"   ❌ First request failed: {response1.status_code}")
    
    except Exception as e:
        print(f"   ❌ Cache test error: {e}")
    
    print("\n🎉 API testing completed!")
    return True

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_api.py <API_URL>")
        print("Example: python test_api.py https://api.llm-api.0a1b2c3d4e5f.convox.cloud")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    
    # Validate URL format
    if not api_url.startswith(('http://', 'https://')):
        print("❌ URL must start with http:// or https://")
        sys.exit(1)
    
    test_api(api_url)

if __name__ == "__main__":
    main()
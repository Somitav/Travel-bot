#!/usr/bin/env python3
"""
Simple API Test Script for Travel Bot Backend

This script tests all the API endpoints to ensure they're working correctly.
Run this script while the backend server is running.
"""

import requests
import json
import time
import sys
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = "test_session_123"


def print_separator(title):
    """Print a formatted separator with title"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_response(response, title="Response"):
    """Print formatted response"""
    print(f"\n--- {title} ---")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")

    if response.headers.get('content-type', '').startswith('application/json'):
        try:
            print(f"JSON Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
    else:
        print(f"Raw Response: {response.text}")


def test_health_endpoint():
    """Test the health endpoint"""
    print_separator("Testing Health Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing health endpoint: {e}")
        return False


def test_root_endpoint():
    """Test the root endpoint"""
    print_separator("Testing Root Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing root endpoint: {e}")
        return False


def test_chat_endpoint_greeting():
    """Test chat endpoint with greeting"""
    print_separator("Testing Chat Endpoint - Greeting")

    try:
        data = {"message": "Hello"}
        response = requests.post(
            f"{BASE_URL}/chat/{TEST_SESSION_ID}",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True
        )

        print(f"Status Code: {response.status_code}")
        print("Server-Side Events Stream:")

        # Read SSE stream
        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                try:
                    parsed = json.loads(data)
                    event_count += 1
                    print(f"  Event {event_count}: {json.dumps(parsed, indent=4)}")

                    # Check if this is the done event
                    if parsed.get('type') == 'done':
                        print("  Stream completed successfully")
                        break
                except json.JSONDecodeError:
                    event_count += 1
                    print(f"  Event {event_count}: {data}")

            # Safety limit to prevent infinite loops
            if event_count > 20:
                print("  ... (truncated - too many events)")
                break

        return response.status_code == 200
    except Exception as e:
        print(f"Error testing chat endpoint: {e}")
        return False


def test_chat_endpoint_travel_request():
    """Test chat endpoint with travel request"""
    print_separator("Testing Chat Endpoint - Travel Request")

    try:
        data = {"message": "I want to plan a 3-day trip to Paris starting from New York on 2024-12-01"}
        response = requests.post(
            f"{BASE_URL}/chat/{TEST_SESSION_ID}",
            json=data,
            headers={"Content-Type": "application/json"},
            stream=True
        )

        print(f"Status Code: {response.status_code}")
        print("Server-Side Events Stream:")

        # Read SSE stream
        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                data = line[6:]  # Remove 'data: ' prefix
                try:
                    parsed = json.loads(data)
                    event_count += 1
                    print(f"  Event {event_count}: {json.dumps(parsed, indent=4)}")

                    # Check if this is the done event
                    if parsed.get('type') == 'done':
                        print("  Stream completed successfully")
                        break
                except json.JSONDecodeError:
                    event_count += 1
                    print(f"  Event {event_count}: {data}")

            # Safety limit to prevent infinite loops
            if event_count > 30:
                print("  ... (truncated - too many events)")
                break

        return response.status_code == 200
    except Exception as e:
        print(f"Error testing chat endpoint: {e}")
        return False


def test_get_session():
    """Test get session endpoint"""
    print_separator("Testing Get Session Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/session/{TEST_SESSION_ID}")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing get session: {e}")
        return False


def test_missing_message_error():
    """Test error handling for missing message"""
    print_separator("Testing Error Handling - Missing Message")

    try:
        data = {}  # Empty data
        response = requests.post(
            f"{BASE_URL}/chat/{TEST_SESSION_ID}",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print_response(response)
        return response.status_code == 422 or 'error' in response.json()
    except Exception as e:
        print(f"Error testing missing message: {e}")
        return False


def test_delete_session():
    """Test delete session endpoint"""
    print_separator("Testing Delete Session Endpoint")

    try:
        response = requests.delete(f"{BASE_URL}/session/{TEST_SESSION_ID}")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing delete session: {e}")
        return False


def test_nonexistent_session():
    """Test get non-existent session"""
    print_separator("Testing Non-existent Session")

    try:
        response = requests.get(f"{BASE_URL}/session/nonexistent_session")
        print_response(response)
        return response.status_code == 200 and 'error' in response.json()
    except Exception as e:
        print(f"Error testing non-existent session: {e}")
        return False


def check_server_running():
    """Check if the server is running"""
    print_separator("Checking Server Status")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            return True
        else:
            print("❌ Server responded with error")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        print(f"Make sure the server is running at {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Travel Bot Backend API Test Suite")
    print(f"Testing server at: {BASE_URL}")
    print(f"Test session ID: {TEST_SESSION_ID}")
    print(f"Test started at: {datetime.now()}")

    # Check if server is running
    if not check_server_running():
        print("\n❌ Cannot proceed with tests - server is not running")
        print("Start the server with: python main.py")
        sys.exit(1)

    # Run tests
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("Chat - Greeting", test_chat_endpoint_greeting),
        ("Chat - Travel Request", test_chat_endpoint_travel_request),
        ("Get Session", test_get_session),
        ("Missing Message Error", test_missing_message_error),
        ("Delete Session", test_delete_session),
        ("Non-existent Session", test_nonexistent_session),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"Result: {status}")
        except Exception as e:
            results.append((test_name, False))
            print(f"Result: ❌ ERROR - {e}")

        # Small delay between tests
        time.sleep(1)

    # Print summary
    print_separator("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    print("\nDetailed Results:")
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

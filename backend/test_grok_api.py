"""
Test script for Groq API integration
Run with: python test_grok_api.py
"""
import sys
from ai_knowledge import get_standard_lifespan, query_groq_api

def test_grok_integration():
    """Test Grok API with various tractor parts"""
    
    print("=" * 60)
    print("TESTING GROK API INTEGRATION")
    print("=" * 60)
    print()
    
    test_parts = [
        "battery",
        "fan belt",
        "hydraulic pump",
        "air filter",
        "clutch plate",
        "radiator",
        "starter motor",
        "fuel injector",
        "alternator"
    ]
    
    results = []
    
    for part in test_parts:
        print(f"\n--- Testing: {part} ---")
        try:
            lifespan = get_standard_lifespan(part)
            results.append({
                "part": part,
                "lifespan": lifespan,
                "status": "✅ Success"
            })
            print(f"Result: {lifespan} hours")
        except Exception as e:
            results.append({
                "part": part,
                "lifespan": None,
                "status": f"❌ Error: {e}"
            })
            print(f"Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    
    for result in results:
        print(f"{result['status']:<20} {result['part']:<20} {result['lifespan'] or 'N/A'} hours")
    
    success_count = sum(1 for r in results if r['lifespan'] is not None)
    print(f"\nSuccess Rate: {success_count}/{len(test_parts)} ({success_count/len(test_parts)*100:.1f}%)")
    
    return success_count == len(test_parts)


def test_direct_groq():
    """Test direct Groq API call"""
    print("\n" + "=" * 60)
    print("TESTING DIRECT GROQ API CALL")
    print("=" * 60)
    print()
    
    part = "tractor battery"
    print(f"Querying Groq for: {part}")
    
    lifespan = query_groq_api(part)
    
    if lifespan:
        print(f"✅ Success! Lifespan: {lifespan} hours")
        return True
    else:
        print("❌ Failed to get response from Groq API")
        return False


if __name__ == "__main__":
    print("🚀 Starting Groq API Tests...\n")
    
    # Test direct API call first
    direct_success = test_direct_groq()
    
    # Test full integration
    integration_success = test_grok_integration()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Direct API Test: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    print(f"Integration Test: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if direct_success and integration_success:
        print("\n🎉 All tests passed! Groq API is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        sys.exit(1)

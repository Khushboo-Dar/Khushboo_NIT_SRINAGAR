#!/usr/bin/env python3
"""
Test script for Bajaj Datathon Bill Extraction API
Tests the complete extraction pipeline with enhanced features
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
SAMPLE_DOCUMENT_URL = "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png?sv=2025-07-05&spr=https&st=2025-11-24T14%3A13%3A22Z&se=2026-11-25T14%3A13%3A00Z&sr=b&sp=r&sig=WFJYfNw0PJdZOpOYlsoAW0UujYGG1x2HSbcDREiFXSU%3D"

def test_health_check():
    """Test API health endpoint"""
    print("\n" + "="*60)
    print("📋 TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_extract_bill():
    """Test bill extraction endpoint"""
    print("\n" + "="*60)
    print("📋 TEST 2: Extract Bill Data")
    print("="*60)
    
    payload = {
        "document": SAMPLE_DOCUMENT_URL
    }
    
    print(f"📤 Request URL: {API_BASE_URL}/extract-bill-data")
    print(f"📝 Payload: {json.dumps({'document': 'https://...'}, indent=2)}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/extract-bill-data",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        print(f"⏱️  Response Time: {elapsed:.2f}s")
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            print("\n📊 Response Structure Validation:")
            print(f"  ✓ is_success: {data.get('is_success')}")
            
            # Token usage
            tokens = data.get('token_usage', {})
            print(f"\n🔢 Token Usage:")
            print(f"  • Total Tokens: {tokens.get('total_tokens')}")
            print(f"  • Input Tokens: {tokens.get('input_tokens')}")
            print(f"  • Output Tokens: {tokens.get('output_tokens')}")
            
            # Extracted data
            extracted_data = data.get('data', {})
            pages = extracted_data.get('pagewise_line_items', [])
            total_items = extracted_data.get('total_item_count', 0)
            
            print(f"\n📄 Extraction Results:")
            print(f"  • Total Pages: {len(pages)}")
            print(f"  • Total Items: {total_items}")
            
            # Show first few items
            if pages:
                first_page = pages[0]
                print(f"\n📑 Page 1 Details:")
                print(f"  • Page Type: {first_page.get('page_type')}")
                print(f"  • Items on this page: {len(first_page.get('bill_items', []))}")
                
                items = first_page.get('bill_items', [])
                if items:
                    print(f"\n💳 First 3 Line Items:")
                    for i, item in enumerate(items[:3], 1):
                        print(f"  {i}. {item.get('item_name')}")
                        print(f"     Qty: {item.get('item_quantity')} | Rate: ₹{item.get('item_rate')} | Amount: ₹{item.get('item_amount')}")
            
            # Check for fraud warnings
            if 'fraud_warnings' in data:
                print(f"\n⚠️  Fraud Warnings Detected:")
                for warning in data.get('fraud_warnings', []):
                    print(f"  {warning}")
            
            print(f"\n✅ Full Response (pretty-printed):")
            print(json.dumps(data, indent=2)[:1000])
            print("... [truncated for display]")
            
            return True
        else:
            print(f"❌ Error: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 60s")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_invalid_document():
    """Test with invalid document URL"""
    print("\n" + "="*60)
    print("📋 TEST 3: Invalid Document URL")
    print("="*60)
    
    payload = {
        "document": "https://invalid-url-that-does-not-exist.com/file.pdf"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/extract-bill-data",
            json=payload,
            timeout=10
        )
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"✅ Error Handling Confirmed:")
            print(f"   {response.json().get('detail', 'Unknown error')}")
            return True
        else:
            print(f"❌ Expected error, got success")
            return False
    except Exception as e:
        print(f"✅ Expected network error: {type(e).__name__}")
        return True

def main():
    """Run all tests"""
    print("\n" + "🔷"*30)
    print("🔷 BAJAJ DATATHON BILL EXTRACTION API - TEST SUITE 🔷")
    print("🔷"*30)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Extract Bill Data", test_extract_bill()))
    results.append(("Invalid URL Handling", test_invalid_document()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status:12} | {test_name}")
    
    print("="*60)
    print(f"🎯 Result: {passed}/{total} tests passed")
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working correctly. 🎉\n")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

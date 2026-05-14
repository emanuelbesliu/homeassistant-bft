#!/usr/bin/env python3
"""
BFT API Authentication Test Script
Tests connection to BFT cloud API and device discovery
"""

import requests
import json
import sys
import os

# Configuration - Replace with your credentials or use environment variables
USERNAME = os.getenv("BFT_USERNAME", "your@email.com")
PASSWORD = os.getenv("BFT_PASSWORD", "your_password")
DEVICE_NAME = os.getenv("BFT_DEVICE", "YOUR_DEVICE_NAME")
TIMEOUT = 20

PARTICLE_URL = "https://ucontrol-api.bft-automation.com"
DISPATCHER_URL = "https://ucontrol-dispatcher.bft-automation.com/automations"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_token_auth():
    """Test getting OAuth token from BFT API"""
    print_section("TEST 1: Authentication")
    
    url = f"{PARTICLE_URL}/oauth/token"
    auth_data = {
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
    }
    
    print(f"URL: {url}")
    print(f"Username: {USERNAME}")
    print(f"Password: {'*' * len(PASSWORD)}")
    print(f"\nRequesting access token...")
    
    try:
        response = requests.post(
            url,
            auth=("particle", "particle"),
            data=auth_data,
            timeout=TIMEOUT
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            expires_in = data.get("expires_in")
            
            print(f"✅ SUCCESS - Token obtained!")
            print(f"   Token (first 20 chars): {token[:20]}...")
            print(f"   Expires in: {expires_in} seconds ({expires_in/3600:.1f} hours)")
            return token
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ FAILED - Request timeout after {TIMEOUT} seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED - Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return None

def test_device_discovery(access_token):
    """Test discovering devices on the account"""
    print_section("TEST 2: Device Discovery")
    
    if not access_token:
        print("⚠️  SKIPPED - No access token available")
        return None
    
    url = f"{PARTICLE_URL}/api/v1/users/?access_token={access_token}"
    print(f"URL: {url}")
    print(f"Token: {access_token[:20]}...")
    print(f"\nFetching device list...")
    
    try:
        response = requests.get(url, timeout=TIMEOUT)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            automations = data.get("data", {}).get("automations", [])
            
            print(f"✅ SUCCESS - Found {len(automations)} device(s)")
            
            if automations:
                print("\nAvailable devices:")
                for i, auto in enumerate(automations, 1):
                    name = auto.get("info", {}).get("name", "Unknown")
                    uuid = auto.get("uuid", "Unknown")
                    print(f"   {i}. Name: '{name}'")
                    print(f"      UUID: {uuid}")
                
                # Find our device
                device_id = None
                for auto in automations:
                    if auto.get("info", {}).get("name") == DEVICE_NAME:
                        device_id = auto["uuid"]
                        print(f"\n✅ Found target device '{DEVICE_NAME}'")
                        print(f"   UUID: {device_id}")
                        return device_id
                
                print(f"\n⚠️  Target device '{DEVICE_NAME}' not found in list")
                print(f"   Available: {[a.get('info', {}).get('name') for a in automations]}")
                return None
            else:
                print("⚠️  No devices found on this account")
                return None
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ FAILED - Request timeout after {TIMEOUT} seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED - Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return None

def test_device_status(access_token, device_id):
    """Test getting device status"""
    print_section("TEST 3: Device Status")
    
    if not access_token or not device_id:
        print("⚠️  SKIPPED - Missing access token or device ID")
        return False
    
    url = f"{DISPATCHER_URL}/{device_id}/execute/diagnosis"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print(f"URL: {url}")
    print(f"Device ID: {device_id}")
    print(f"\nRequesting device status...")
    
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS - Device responded!")
            print(f"\nDevice status:")
            print(json.dumps(data, indent=2))
            
            # Parse gate state
            first_pos = data.get("first_engine_pos_int", 0)
            second_pos = data.get("second_engine_pos_int", 0)
            first_vel = data.get("first_engine_vel_int", 0)
            second_vel = data.get("second_engine_vel_int", 0)
            
            print(f"\nInterpreted state:")
            print(f"   Engine 1: Position {first_pos}%, Velocity {first_vel}")
            print(f"   Engine 2: Position {second_pos}%, Velocity {second_vel}")
            
            if first_pos == 100 and second_pos == 100 and first_vel == 0 and second_vel == 0:
                print(f"   🚪 Gate is OPEN")
            elif first_pos == 0 and second_pos == 0 and first_vel == 0 and second_vel == 0:
                print(f"   🚪 Gate is CLOSED")
            elif first_vel > 0 or second_vel > 0:
                print(f"   🚪 Gate is MOVING")
            else:
                print(f"   🚪 Gate is STOPPED (partially open)")
            
            return True
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ FAILED - Request timeout after {TIMEOUT} seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED - Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED - Unexpected error: {e}")
        return False

def main():
    """Run all tests"""
    print_section("BFT API Authentication Test")
    
    # Check if credentials are set
    if USERNAME == "your@email.com" or PASSWORD == "your_password":
        print("⚠️  ERROR: Please set your BFT credentials!")
        print("\nUsage:")
        print("  Method 1 - Environment variables:")
        print("    export BFT_USERNAME='your@email.com'")
        print("    export BFT_PASSWORD='your_password'")
        print("    export BFT_DEVICE='YOUR_DEVICE_NAME'")
        print("    python3 test_auth.py")
        print("\n  Method 2 - Edit this file:")
        print("    Edit lines 12-14 with your credentials")
        print()
        return 1
    
    print(f"Target Device: {DEVICE_NAME}")
    print(f"Timeout: {TIMEOUT} seconds")
    
    # Test 1: Get token
    access_token = test_token_auth()
    
    # Test 2: Discover devices
    device_id = test_device_discovery(access_token)
    
    # Test 3: Get device status
    status_ok = test_device_status(access_token, device_id)
    
    # Summary
    print_section("Test Summary")
    print(f"✅ Authentication: {'PASS' if access_token else 'FAIL'}")
    print(f"✅ Device Discovery: {'PASS' if device_id else 'FAIL'}")
    print(f"✅ Device Status: {'PASS' if status_ok else 'FAIL'}")
    
    if access_token and device_id and status_ok:
        print("\n🎉 All tests PASSED - Integration should work!")
        print("\nNext steps:")
        print("1. Copy integration to Home Assistant custom_components")
        print("2. Add configuration to configuration.yaml")
        print("3. Restart Home Assistant")
        return 0
    else:
        print("\n⚠️  Some tests FAILED - Review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

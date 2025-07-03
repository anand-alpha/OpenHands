#!/usr/bin/env python3
"""
Test script for SNC authentication functionality
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from openhands.cli.utils import (
    store_snc_token,
    verify_snc_token,
    get_snc_auth_info,
    logout_snc,
    validate_snc_token,
)


def test_snc_authentication():
    """Test SNC authentication functionality."""
    print("🧪 Testing SNC Authentication System")
    print("=" * 50)

    # Test 1: Initial status (should be not authenticated)
    print("\n1. Testing initial authentication status...")
    auth_info = get_snc_auth_info()
    print(f"   Authenticated: {auth_info['authenticated']}")
    assert not auth_info['authenticated'], "Should start unauthenticated"
    print("   ✓ PASS")

    # Test 2: Token validation
    print("\n2. Testing token validation...")
    assert not validate_snc_token(""), "Empty token should be invalid"
    assert not validate_snc_token("short"), "Short token should be invalid"
    assert validate_snc_token("valid_token_12345"), "Valid token should pass"
    print("   ✓ PASS")

    # Test 3: Store token
    print("\n3. Testing token storage...")
    test_token = "test_company_token_123456789"
    result = store_snc_token(test_token)
    assert result, "Token storage should succeed"
    print("   ✓ PASS")

    # Test 4: Verify authentication after login
    print("\n4. Testing authentication verification...")
    auth_info = get_snc_auth_info()
    assert auth_info['authenticated'], "Should be authenticated after login"
    assert auth_info['expires_in'] > 0, "Should have time remaining"
    print(f"   Authenticated: {auth_info['authenticated']}")
    print(f"   Expires in: {auth_info['expires_in']:.0f} seconds")
    print("   ✓ PASS")

    # Test 5: Token verification
    print("\n5. Testing token verification...")
    assert verify_snc_token(), "Token verification should pass"
    print("   ✓ PASS")

    # Test 6: Logout
    print("\n6. Testing logout...")
    result = logout_snc()
    assert result, "Logout should succeed"

    auth_info = get_snc_auth_info()
    assert not auth_info['authenticated'], "Should be unauthenticated after logout"
    print("   ✓ PASS")

    print("\n🎉 All tests passed!")
    print("SNC Authentication system is working correctly.")


if __name__ == "__main__":
    test_snc_authentication()

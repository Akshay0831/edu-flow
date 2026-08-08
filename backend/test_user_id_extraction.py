#!/usr/bin/env python3

# Test user ID extraction logic
test_sub = "reset_dced32cf-ff45-4bf3-9a80-92c071730b7e"
expected_user_id = "dced32cf-ff45-4bf3-9a80-92c071730b7e"

# Extract user ID using the same logic as in confirm_password_reset
if test_sub and test_sub.startswith("reset_"):
    actual_user_id = test_sub[6:]  # Remove "reset_" prefix
    print(f"Original sub: {test_sub}")
    print(f"Extracted user ID: {actual_user_id}")
    print(f"Expected user ID: {expected_user_id}")
    print(f"Extraction correct: {actual_user_id == expected_user_id}")
else:
    print("Invalid sub field format")

# Test with the actual sub from the token
actual_sub = "reset_dced32cf-ff45-4bf3-9a80-92c071730b7e"
if actual_sub and actual_sub.startswith("reset_"):
    extracted_id = actual_sub[6:]
    print(f"\nActual sub from token: {actual_sub}")
    print(f"Extracted ID: {extracted_id}")
    print(f"Matches expected: {extracted_id == expected_user_id}")
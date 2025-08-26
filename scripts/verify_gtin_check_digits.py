#!/usr/bin/env python3
"""
Verify GTIN Check Digits
Independent verification of our GTIN check digit calculations
"""

def calculate_gtin_check_digit(digits_13: str) -> int:
    """Calculate GTIN check digit using GS1 algorithm"""
    if len(digits_13) != 13:
        raise ValueError(f"Expected 13 digits, got {len(digits_13)}")
    
    total = 0
    for i, digit in enumerate(digits_13):
        multiplier = 3 if i % 2 else 1  # Odd positions (0-indexed) get 3
        total += int(digit) * multiplier
    
    check_digit = (10 - (total % 10)) % 10
    return check_digit

def verify_gtin(gtin_14: str) -> bool:
    """Verify if a 14-digit GTIN has correct check digit"""
    if len(gtin_14) != 14:
        return False
    
    base_digits = gtin_14[:-1]  # First 13 digits
    provided_check = int(gtin_14[-1])  # Last digit
    calculated_check = calculate_gtin_check_digit(base_digits)
    
    return provided_check == calculated_check

# Test the specific GTIN mentioned by expert
print("🔍 GTIN CHECK DIGIT VERIFICATION")
print("=" * 50)

# Expert's claim: UPC 615260026006 should become GTIN 00615260026006
expert_gtin = "00615260026006"
our_gtin = "00615260026002"

print(f"Expert's GTIN: {expert_gtin}")
print(f"Our GTIN: {our_gtin}")
print()

# Verify expert's GTIN
expert_valid = verify_gtin(expert_gtin)
print(f"Expert's GTIN valid: {expert_valid}")

if not expert_valid:
    # Calculate correct check digit for expert's base
    base = expert_gtin[:-1]
    correct_check = calculate_gtin_check_digit(base)
    correct_gtin = base + str(correct_check)
    print(f"Correct GTIN for base {base}: {correct_gtin}")

print()

# Verify our GTIN
our_valid = verify_gtin(our_gtin)
print(f"Our GTIN valid: {our_valid}")

if not our_valid:
    # Calculate correct check digit for our base
    base = our_gtin[:-1]
    correct_check = calculate_gtin_check_digit(base)
    correct_gtin = base + str(correct_check)
    print(f"Correct GTIN for base {base}: {correct_gtin}")

print()
print("🎯 CONCLUSION:")
if our_valid and not expert_valid:
    print("✅ OUR GTIN IS CORRECT")
    print("❌ EXPERT'S GTIN IS WRONG")
elif expert_valid and not our_valid:
    print("❌ OUR GTIN IS WRONG")
    print("✅ EXPERT'S GTIN IS CORRECT")
elif both_valid := our_valid and expert_valid:
    print("✅ BOTH GTINs ARE VALID")
else:
    print("❌ BOTH GTINs ARE WRONG")

# Show the calculation step by step for transparency
print("\n🔢 STEP-BY-STEP CALCULATION:")
print("Expert's GTIN: 00615260026006")
base = "0061526002600"
print(f"Base digits: {base}")
print("Position:  0 1 2 3 4 5 6 7 8 9 10 11 12")
print("Digit:     0 0 6 1 5 2 6 0 0 2 6  0  0")
print("Multiply:  1 3 1 3 1 3 1 3 1 3 1  3  1")

total = 0
products = []
for i, digit in enumerate(base):
    multiplier = 3 if i % 2 else 1
    product = int(digit) * multiplier
    products.append(product)
    total += product

print(f"Products:  {' '.join(str(p) for p in products)}")
print(f"Sum: {total}")
check_digit = (10 - (total % 10)) % 10
print(f"Check digit: (10 - ({total} % 10)) % 10 = {check_digit}")
print(f"Expert claimed: 6")
print(f"Correct is: {check_digit}")

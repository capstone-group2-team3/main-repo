import json
import os
from typing import Dict, Any

# Global dictionary to store reference ranges in memory (Caching)
REFERENCE_RANGES = {}

# Wrapper logic: Define critical rules here to avoid modifying the team's JSON file
CRITICAL_RULES = {
    "Hemoglobin": {"low": 8.0, "high": 18.0},
    "Glucose": {"low": 50, "high": 300},
    # Add any other tests and their critical values here as needed
}

def load_reference_ranges():
    """
    Reads the reference_ranges.json file once during startup.
    """
    global REFERENCE_RANGES
    file_path = "data/reference_ranges.json"
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            REFERENCE_RANGES = json.load(f)
        print("Reference ranges loaded successfully in memory.")
    except Exception as e:
        print(f"Error loading reference ranges: {e}")

# Load the data immediately upon module import
load_reference_ranges()

def get_limits(test_name: str) -> Dict[str, Any]:
    """
    Merges base reference ranges from JSON with internal critical rules.
    Safely handles missing keys by returning None.
    """
    base = REFERENCE_RANGES.get(test_name, {})
    criticals = CRITICAL_RULES.get(test_name, {})
    
    return {
        # Using .get() with fallback to support both 'min/max' and 'low/high' JSON structures
        "low": base.get("low", base.get("min")), 
        "high": base.get("high", base.get("max")),
        "critical_low": criticals.get("low"),
        "critical_high": criticals.get("high"),
        "unit": base.get("unit", "")
    }

def classify_value(test_name: str, value: float) -> Dict[str, Any]:
    """
    Compares a patient's lab value against the standard reference ranges.
    Returns a dictionary containing the status and the generated evidence string.
    """
    # 1. Handle unknown lab tests
    if test_name not in REFERENCE_RANGES:
        return {
            "test_name": test_name,
            "value": value,
            "status": "Unknown",
            "evidence": f"{test_name} ({value}) - Reference range unknown."
        }

    # 2. Extract reference limits using the new wrapper function
    limits = get_limits(test_name)
    low = limits["low"]
    high = limits["high"]
    crit_low = limits["critical_low"]
    crit_high = limits["critical_high"]
    unit = limits["unit"]

    status = "Normal"

    # 3. Classification Logic (Checking critical conditions first)
    if crit_low is not None and value < crit_low:
        status = "Critical Low"
    elif low is not None and value < low:
        status = "Low"
    elif crit_high is not None and value > crit_high:
        status = "Critical High"
    elif high is not None and value > high:
        status = "High"

    # 4. Generate the evidence message
    if status == "Normal":
        evidence = f"{test_name} ({value} {unit}) is {status}."
    else:
        evidence = f"{test_name} ({value} {unit}) is {status} compared to reference range {low}-{high} {unit}."

    return {
        "test_name": test_name,
        "value": value,
        "unit": unit,
        "status": status,
        "evidence": evidence
    }

if __name__ == "__main__":
    
    print(classify_value("Glucose", 45))
    
    
    print(classify_value("Glucose", 110))
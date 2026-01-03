"""
Data validation utilities.

INTERVIEW EXPLANATION:
Why validate data?
1. Data Quality: Catch bad data early
2. Type Safety: Ensure data types are correct
3. Business Rules: Enforce domain-specific constraints
4. Error Prevention: Fail fast with clear error messages

Common validation patterns:
- Type checking
- Range validation
- Format validation (regex)
- Required field checking
- Business rule validation
"""

from typing import Any, Dict, List, Optional
import pandas as pd

def validate_api_response(response_data: Dict[str, Any]) -> bool:
    """
    Validate structure of API response.
    
    INTERVIEW EXPLANATION:
    This function checks if the API response has the expected structure.
    This is important because:
    1. APIs can change without notice
    2. Network errors can return malformed data
    3. External services can have bugs
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response_data, dict):
        return False
    
    # FreeCryptoAPI format: {"status": "success", "symbols": [...]}
    if response_data.get("status") == "success" and "symbols" in response_data:
        if isinstance(response_data["symbols"], list) and len(response_data["symbols"]) > 0:
            return True
    
    # Check for common API response fields
    # Different APIs have different structures, adjust as needed
    if "data" in response_data or "result" in response_data:
        return True
    
    # Some APIs return data directly
    if "symbol" in response_data or "price" in response_data:
        return True
    
    return False

def validate_crypto_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate crypto data structure and values.
    
    INTERVIEW EXPLANATION:
    Returns tuple of (is_valid, error_message)
    This pattern allows callers to know WHY validation failed.
    
    Args:
        data: Dictionary containing crypto data
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    required_fields = ["symbol", "price"]
    
    # Check required fields exist
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Validate data types
    if not isinstance(data["symbol"], str):
        return False, "Symbol must be a string"
    
    if not isinstance(data["price"], (int, float)):
        return False, "Price must be a number"
    
    # Validate price is positive
    if data["price"] <= 0:
        return False, "Price must be positive"
    
    return True, None

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validate pandas DataFrame structure.
    
    INTERVIEW EXPLANATION:
    DataFrame validation is crucial because:
    1. Downstream processing expects specific columns
    2. Missing columns cause errors later
    3. Early validation saves debugging time
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
    
    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if df.empty:
        return False, "DataFrame is empty"
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"
    
    return True, None


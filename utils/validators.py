
from typing import Any, Dict, List, Optional
import pandas as pd

def validate_api_response(response_data: Dict[str, Any]) -> bool:
    if not isinstance(response_data, dict):
        return False
    
    if response_data.get("status") == "success" and "symbols" in response_data:
        if isinstance(response_data["symbols"], list) and len(response_data["symbols"]) > 0:
            return True
    
    if "data" in response_data or "result" in response_data:
        return True
    
    if "symbol" in response_data or "price" in response_data:
        return True
    
    return False

def validate_crypto_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    required_fields = ["symbol", "price"]
    
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    if not isinstance(data["symbol"], str):
        return False, "Symbol must be a string"
    
    if not isinstance(data["price"], (int, float)):
        return False, "Price must be a number"
    
    if data["price"] <= 0:
        return False, "Price must be positive"
    
    return True, None

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> tuple[bool, Optional[str]]:
    if df.empty:
        return False, "DataFrame is empty"
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"
    
    return True, None


"""
Core data cleaning logic.

INTERVIEW EXPLANATION:
This module handles data cleaning operations:
1. Missing value handling
2. Outlier detection and removal
3. Data normalization
4. Type conversion
5. Duplicate removal

Why separate cleaning from collection?
- Single Responsibility: Each module has one job
- Reusability: Can clean data from any source
- Testability: Can test cleaning logic independently
- Maintainability: Changes to cleaning don't affect collection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

from config.settings import CLEANED_DATA_DIR
from utils.logger import setup_logger
from utils.validators import validate_dataframe

logger = setup_logger(__name__)


class DataCleaner:
    """
    Core data cleaner for crypto data.
    
    INTERVIEW EXPLANATION:
    This class encapsulates all cleaning operations.
    It follows the Single Responsibility Principle - only handles cleaning.
    """
    
    def __init__(self):
        """Initialize the data cleaner."""
        self.cleaning_stats = {
            "missing_values_removed": 0,
            "outliers_removed": 0,
            "duplicates_removed": 0,
            "records_processed": 0,
            "records_cleaned": 0
        }
    
    def clean_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean a single data record.
        
        INTERVIEW EXPLANATION:
        This method applies all cleaning operations to a single record.
        It's designed to work with the data structure from our collector.
        
        Args:
            data: Dictionary containing crypto data
        
        Returns:
            Cleaned data dictionary, or None if data is invalid
        """
        self.cleaning_stats["records_processed"] += 1
        
        try:
            # Create a copy to avoid modifying original
            cleaned = data.copy()
            
            # Remove raw_data for cleaner output (optional)
            # cleaned.pop("raw_data", None)
            
            # 1. Handle missing values
            cleaned = self._handle_missing_values(cleaned)
            
            # 2. Validate and convert types
            cleaned = self._convert_types(cleaned)
            
            # 3. Validate ranges (outlier detection)
            cleaned = self._detect_outliers(cleaned)
            
            # 4. Normalize data
            cleaned = self._normalize_data(cleaned)
            
            # 5. Add cleaning metadata
            cleaned["cleaned_at"] = datetime.now().isoformat()
            cleaned["cleaning_version"] = "1.0"
            
            self.cleaning_stats["records_cleaned"] += 1
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return None
    
    def _handle_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle missing values in the data.
        
        INTERVIEW EXPLANATION:
        Missing value strategies:
        1. Remove: Drop records with missing critical fields
        2. Impute: Fill with mean/median/mode
        3. Default: Use sensible defaults
        
        For crypto data, we use defaults for optional fields.
        """
        cleaned = data.copy()
        
        # Critical fields - must exist
        critical_fields = ["symbol", "price", "timestamp"]
        for field in critical_fields:
            if field not in cleaned or cleaned[field] is None:
                logger.warning(f"Missing critical field: {field}")
                self.cleaning_stats["missing_values_removed"] += 1
                return None  # Can't clean without critical fields
        
        # Optional fields - set defaults if missing
        optional_defaults = {
            "lowest_24h": None,
            "highest_24h": None,
            "price_change_24h": None,
            "source_exchange": "unknown"
        }
        
        for field, default in optional_defaults.items():
            if field not in cleaned or cleaned[field] is None:
                cleaned[field] = default
        
        return cleaned
    
    def _convert_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert data types to ensure consistency.
        
        INTERVIEW EXPLANATION:
        Type conversion ensures:
        1. Numeric fields are numbers (not strings)
        2. Dates are in consistent format
        3. Strings are properly formatted
        """
        cleaned = data.copy()
        
        # Ensure price is float
        if "price" in cleaned:
            try:
                cleaned["price"] = float(cleaned["price"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid price value: {cleaned.get('price')}")
                return None
        
        # Convert optional numeric fields
        numeric_fields = ["lowest_24h", "highest_24h", "price_change_24h"]
        for field in numeric_fields:
            if field in cleaned and cleaned[field] is not None:
                try:
                    cleaned[field] = float(cleaned[field])
                except (ValueError, TypeError):
                    cleaned[field] = None
        
        # Ensure symbol is uppercase string
        if "symbol" in cleaned:
            cleaned["symbol"] = str(cleaned["symbol"]).upper()
        
        return cleaned
    
    def _detect_outliers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and handle outliers.
        
        INTERVIEW EXPLANATION:
        Outlier detection methods:
        1. Statistical: Z-score, IQR
        2. Domain knowledge: Price can't be negative, etc.
        3. Range-based: Values outside expected ranges
        
        For crypto, we use domain knowledge (price > 0, reasonable ranges)
        """
        cleaned = data.copy()
        
        # Domain-specific validation
        if "price" in cleaned:
            price = cleaned["price"]
            # Price must be positive
            if price <= 0:
                logger.warning(f"Invalid price (non-positive): {price}")
                self.cleaning_stats["outliers_removed"] += 1
                return None
            
            # Price change should be reasonable (e.g., -100% to +1000%)
            if "price_change_24h" in cleaned and cleaned["price_change_24h"] is not None:
                change = cleaned["price_change_24h"]
                if change < -100 or change > 1000:
                    logger.warning(f"Unusual price change: {change}%")
                    # Don't remove, just log - might be legitimate (e.g., new coin)
        
        # Validate high/low relationship
        if all(k in cleaned for k in ["price", "lowest_24h", "highest_24h"]):
            price = cleaned["price"]
            lowest = cleaned["lowest_24h"]
            highest = cleaned["highest_24h"]
            
            if lowest is not None and highest is not None:
                if lowest > highest:
                    logger.warning("lowest_24h > highest_24h, swapping")
                    cleaned["lowest_24h"], cleaned["highest_24h"] = highest, lowest
                
                # Price should be within 24h range (with some tolerance)
                if price < lowest * 0.9 or price > highest * 1.1:
                    logger.warning(f"Price {price} outside 24h range [{lowest}, {highest}]")
                    # Don't remove, just log - might be legitimate
        
        return cleaned
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize data format.
        
        INTERVIEW EXPLANATION:
        Normalization ensures:
        1. Consistent field names
        2. Consistent data formats
        3. Standardized units
        """
        cleaned = data.copy()
        
        # Ensure timestamp format is consistent
        if "timestamp" in cleaned:
            # Already in ISO format from collector, but ensure it's a string
            cleaned["timestamp"] = str(cleaned["timestamp"])
        
        # Normalize exchange names (lowercase)
        if "source_exchange" in cleaned and cleaned["source_exchange"]:
            cleaned["source_exchange"] = str(cleaned["source_exchange"]).lower()
        
        return cleaned
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a pandas DataFrame.
        
        INTERVIEW EXPLANATION:
        This method is useful for batch cleaning.
        It applies cleaning operations to entire DataFrames.
        
        Args:
            df: DataFrame to clean
        
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=["symbol", "timestamp"], keep="first")
        duplicates_removed = original_count - len(df)
        self.cleaning_stats["duplicates_removed"] += duplicates_removed
        
        # Handle missing values in DataFrame
        # For numeric columns, fill with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ["price"]:  # Critical numeric fields
                # Remove rows with missing critical values
                df = df.dropna(subset=[col])
            else:
                # Fill optional numeric fields with median
                df[col] = df[col].fillna(df[col].median())
        
        # Fill string columns with mode or default
        string_cols = df.select_dtypes(include=["object"]).columns
        for col in string_cols:
            if col not in ["symbol", "timestamp", "date"]:  # Don't fill critical strings
                df[col] = df[col].fillna("unknown")
        
        return df
    
    def save_cleaned_data(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        format: str = "json"
    ) -> Path:
        """
        Save cleaned data to file.
        
        Args:
            data: Cleaned data dictionary
            filename: Optional custom filename
            format: File format ("json" or "csv")
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = data.get("symbol", "unknown")
        
        if not filename:
            filename = f"{symbol}_cleaned_{timestamp}.{format}"
        
        filepath = CLEANED_DATA_DIR / filename
        
        if format == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            df = pd.DataFrame([data])
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.debug(f"Saved cleaned data to {filepath}")
        return filepath
    
    def get_cleaning_stats(self) -> Dict[str, Any]:
        """Get cleaning statistics."""
        return self.cleaning_stats.copy()


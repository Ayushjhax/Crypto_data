
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
    
    def __init__(self):
        self.cleaning_stats = {
            "missing_values_removed": 0,
            "outliers_removed": 0,
            "duplicates_removed": 0,
            "records_processed": 0,
            "records_cleaned": 0
        }
    
    def clean_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        self.cleaning_stats["records_processed"] += 1
        
        try:
            cleaned = data.copy()
            
            
            cleaned = self._handle_missing_values(cleaned)
            
            cleaned = self._convert_types(cleaned)
            
            cleaned = self._detect_outliers(cleaned)
            
            cleaned = self._normalize_data(cleaned)
            
            cleaned["cleaned_at"] = datetime.now().isoformat()
            cleaned["cleaning_version"] = "1.0"
            
            self.cleaning_stats["records_cleaned"] += 1
            return cleaned
            
        except Exception as e:
            logger.error(f"Error cleaning data: {e}")
            return None
    
    def _handle_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = data.copy()
        
        critical_fields = ["symbol", "price", "timestamp"]
        for field in critical_fields:
            if field not in cleaned or cleaned[field] is None:
                logger.warning(f"Missing critical field: {field}")
                self.cleaning_stats["missing_values_removed"] += 1
                return None  # Can't clean without critical fields
        
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
        cleaned = data.copy()
        
        if "price" in cleaned:
            try:
                cleaned["price"] = float(cleaned["price"])
            except (ValueError, TypeError):
                logger.warning(f"Invalid price value: {cleaned.get('price')}")
                return None
        
        numeric_fields = ["lowest_24h", "highest_24h", "price_change_24h"]
        for field in numeric_fields:
            if field in cleaned and cleaned[field] is not None:
                try:
                    cleaned[field] = float(cleaned[field])
                except (ValueError, TypeError):
                    cleaned[field] = None
        
        if "symbol" in cleaned:
            cleaned["symbol"] = str(cleaned["symbol"]).upper()
        
        return cleaned
    
    def _detect_outliers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = data.copy()
        
        if "price" in cleaned:
            price = cleaned["price"]
            if price <= 0:
                logger.warning(f"Invalid price (non-positive): {price}")
                self.cleaning_stats["outliers_removed"] += 1
                return None
            
            if "price_change_24h" in cleaned and cleaned["price_change_24h"] is not None:
                change = cleaned["price_change_24h"]
                if change < -100 or change > 1000:
                    logger.warning(f"Unusual price change: {change}%")
        
        if all(k in cleaned for k in ["price", "lowest_24h", "highest_24h"]):
            price = cleaned["price"]
            lowest = cleaned["lowest_24h"]
            highest = cleaned["highest_24h"]
            
            if lowest is not None and highest is not None:
                if lowest > highest:
                    logger.warning("lowest_24h > highest_24h, swapping")
                    cleaned["lowest_24h"], cleaned["highest_24h"] = highest, lowest
                
                if price < lowest * 0.9 or price > highest * 1.1:
                    logger.warning(f"Price {price} outside 24h range [{lowest}, {highest}]")
        
        return cleaned
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = data.copy()
        
        if "timestamp" in cleaned:
            cleaned["timestamp"] = str(cleaned["timestamp"])
        
        if "source_exchange" in cleaned and cleaned["source_exchange"]:
            cleaned["source_exchange"] = str(cleaned["source_exchange"]).lower()
        
        return cleaned
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        original_count = len(df)
        
        df = df.drop_duplicates(subset=["symbol", "timestamp"], keep="first")
        duplicates_removed = original_count - len(df)
        self.cleaning_stats["duplicates_removed"] += duplicates_removed
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in ["price"]:  # Critical numeric fields
                df = df.dropna(subset=[col])
            else:
                df[col] = df[col].fillna(df[col].median())
        
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
        return self.cleaning_stats.copy()


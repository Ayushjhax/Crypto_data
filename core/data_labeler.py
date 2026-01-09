"""
Core data labeling logic. 

INTERVIEW EXPLANATION:
Data labeling adds meaningful categories or tags to data.
This is crucial for:
1. Machine learning: Labels are needed for supervised learning
2. Analysis: Categorization helps with insights
3. Filtering: Can filter data by labels

Common labeling approaches:
- Rule-based: Apply rules to create labels
- Time-series: Label based on trends
- Statistical: Label based on statistical properties
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime 

from config.settings import LABELED_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataLabeler:
    """
    Core data labeler for crypto data.
    
    INTERVIEW EXPLANATION:
    This class handles all labeling operations.
    Labels are added as new fields to the data.
    """
    
    def __init__(self):
        """Initialize the data labeler."""
        self.labeling_stats = {
            "records_labeled": 0,
            "labels_created": 0
        }
    
    def label_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add labels to a data record.
        
        INTERVIEW EXPLANATION:
        This method adds multiple types of labels:
        1. Price movement labels (up/down/sideways)
        2. Volatility labels (high/medium/low)
        3. Trend labels (bullish/bearish/neutral)
        4. Price category labels (cheap/expensive)
        
        Args:
            data: Dictionary containing cleaned crypto data
        
        Returns:
            Data dictionary with labels added
        """
        labeled = data.copy()
        
        # 1. Price movement label
        labeled["price_movement"] = self._label_price_movement(data)
        
        # 2. Volatility label
        labeled["volatility"] = self._label_volatility(data)
        
        # 3. Trend label
        labeled["trend"] = self._label_trend(data)
        
        # 4. Price category (relative to 24h range)
        labeled["price_category"] = self._label_price_category(data)
        
        # 5. Change magnitude label
        labeled["change_magnitude"] = self._label_change_magnitude(data)
        
        # Add labeling metadata
        labeled["labeled_at"] = datetime.now().isoformat()
        labeled["labeling_version"] = "1.0"
        
        self.labeling_stats["records_labeled"] += 1
        self.labeling_stats["labels_created"] += 5  # We create 5 labels per record
        
        return labeled
    
    def _label_price_movement(self, data: Dict[str, Any]) -> str:
        """
        Label price movement direction.
        
        INTERVIEW EXPLANATION:
        Rule-based labeling: Apply simple rules to categorize data.
        """
        price_change = data.get("price_change_24h")
        
        if price_change is None:
            return "unknown"
        
        if price_change > 5:
            return "strong_up"
        elif price_change > 1:
            return "up"
        elif price_change > -1:
            return "sideways"
        elif price_change > -5:
            return "down"
        else:
            return "strong_down"
    
    def _label_volatility(self, data: Dict[str, Any]) -> str:
        """
        Label volatility based on 24h price range.
        
        INTERVIEW EXPLANATION:
        Volatility is measured by the price range (high - low).
        Higher range = higher volatility.
        """
        price = data.get("price")
        lowest = data.get("lowest_24h")
        highest = data.get("highest_24h")
        
        if price is None or lowest is None or highest is None:
            return "unknown"
        
        # Calculate range as percentage of price
        price_range = highest - lowest
        volatility_pct = (price_range / price) * 100 if price > 0 else 0
        
        if volatility_pct > 10:
            return "high"
        elif volatility_pct > 5:
            return "medium"
        elif volatility_pct > 0:
            return "low"
        else:
            return "unknown"
    
    def _label_trend(self, data: Dict[str, Any]) -> str:
        """
        Label trend direction.
        
        INTERVIEW EXPLANATION:
        Trend is determined by price position relative to 24h range.
        """
        price = data.get("price")
        lowest = data.get("lowest_24h")
        highest = data.get("highest_24h")
        price_change = data.get("price_change_24h")
        
        if price is None or lowest is None or highest is None:
            return "unknown"
        
        # Calculate position in range (0 = lowest, 1 = highest)
        if highest > lowest:
            position = (price - lowest) / (highest - lowest)
        else:
            position = 0.5
        
        # Combine position and change
        if price_change is not None:
            if price_change > 2 and position > 0.6:
                return "strong_bullish"
            elif price_change > 0 or position > 0.5:
                return "bullish"
            elif price_change < -2 and position < 0.4:
                return "strong_bearish"
            elif price_change < 0 or position < 0.5:
                return "bearish"
            else:
                return "neutral"
        else:
            if position > 0.6:
                return "bullish"
            elif position < 0.4:
                return "bearish"
            else:
                return "neutral"
    
    def _label_price_category(self, data: Dict[str, Any]) -> str:
        """
        Label price category relative to 24h range.
        
        INTERVIEW EXPLANATION:
        This helps identify if price is near high or low.
        """
        price = data.get("price")
        lowest = data.get("lowest_24h")
        highest = data.get("highest_24h")
        
        if price is None or lowest is None or highest is None:
            return "unknown"
        
        if highest > lowest:
            position = (price - lowest) / (highest - lowest)
        else:
            return "unknown"
        
        if position > 0.8:
            return "near_high"
        elif position > 0.5:
            return "above_mid"
        elif position > 0.2:
            return "below_mid"
        else:
            return "near_low"
    
    def _label_change_magnitude(self, data: Dict[str, Any]) -> str:
        """
        Label the magnitude of price change.
        
        INTERVIEW EXPLANATION:
        Categorize change magnitude for easier filtering/analysis.
        """
        price_change = data.get("price_change_24h")
        
        if price_change is None:
            return "unknown"
        
        abs_change = abs(price_change)
        
        if abs_change > 10:
            return "extreme"
        elif abs_change > 5:
            return "large"
        elif abs_change > 2:
            return "moderate"
        elif abs_change > 0.5:
            return "small"
        else:
            return "minimal"
    
    def save_labeled_data(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        format: str = "json"
    ) -> Path:
        """
        Save labeled data to file.
        
        Args:
            data: Labeled data dictionary
            filename: Optional custom filename
            format: File format ("json" or "csv")
        
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = data.get("symbol", "unknown")
        
        if not filename:
            filename = f"{symbol}_labeled_{timestamp}.{format}"
        
        filepath = LABELED_DATA_DIR / filename
        
        if format == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.debug(f"Saved labeled data to {filepath}")
        return filepath
    
    def get_labeling_stats(self) -> Dict[str, Any]:
        """Get labeling statistics."""
        return self.labeling_stats.copy()



from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime 

from config.settings import LABELED_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataLabeler:
    
    def __init__(self):
        self.labeling_stats = {
            "records_labeled": 0,
            "labels_created": 0
        }
    
    def label_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        labeled = data.copy()
        
        labeled["price_movement"] = self._label_price_movement(data)
        
        labeled["volatility"] = self._label_volatility(data)
        
        labeled["trend"] = self._label_trend(data)
        
        labeled["price_category"] = self._label_price_category(data)
        
        labeled["change_magnitude"] = self._label_change_magnitude(data)
        
        labeled["labeled_at"] = datetime.now().isoformat()
        labeled["labeling_version"] = "1.0"
        
        self.labeling_stats["records_labeled"] += 1
        self.labeling_stats["labels_created"] += 5  # We create 5 labels per record
        
        return labeled
    
    def _label_price_movement(self, data: Dict[str, Any]) -> str:
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
        price = data.get("price")
        lowest = data.get("lowest_24h")
        highest = data.get("highest_24h")
        
        if price is None or lowest is None or highest is None:
            return "unknown"
        
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
        price = data.get("price")
        lowest = data.get("lowest_24h")
        highest = data.get("highest_24h")
        price_change = data.get("price_change_24h")
        
        if price is None or lowest is None or highest is None:
            return "unknown"
        
        if highest > lowest:
            position = (price - lowest) / (highest - lowest)
        else:
            position = 0.5
        
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
        return self.labeling_stats.copy()


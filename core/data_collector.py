
import time
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime
import pandas as pd

from config.settings import (
    FREECRYPTO_API_KEY,
    FREECRYPTO_API_BASE_URL,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
    RAW_DATA_DIR
)
from utils.logger import setup_logger
from utils.validators import validate_api_response, validate_crypto_data

logger = setup_logger(__name__)


class DataCollector:
    
    def __init__(
        self,
        api_key: str,
        base_url: str = FREECRYPTO_API_BASE_URL,
        max_retries: int = MAX_RETRIES,
        timeout: int = REQUEST_TIMEOUT
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
    
    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"Making request to {url} (attempt {retry_count + 1})")
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            self.last_request_time = time.time()
            
            response.raise_for_status()  # Raises exception for 4xx/5xx codes
            
            data = response.json()
            
            if not validate_api_response(data):
                logger.warning(f"Invalid API response structure from {url}")
                return None
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            if retry_count < self.max_retries:
                return self._make_request(endpoint, params, retry_count + 1)
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                if retry_count < self.max_retries:
                    return self._make_request(endpoint, params, retry_count + 1)
            
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                time.sleep(wait_time)
                return self._make_request(endpoint, params, retry_count + 1)
            return None
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from {url}")
            return None
    
    def collect_coin_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Collecting data for {symbol}")
        
        endpoint = "getData"
        params = {"symbol": symbol}
        
        data = self._make_request(endpoint, params=params)
        
        if not data:
            logger.warning(f"Failed to collect data for {symbol}")
            return None
        
        transformed_data = self._transform_coin_data(data, symbol)
        
        is_valid, error_msg = validate_crypto_data(transformed_data)
        if not is_valid:
            logger.error(f"Validation failed for {symbol}: {error_msg}")
            return None
        
        return transformed_data
    
    def _transform_coin_data(self, raw_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        timestamp = datetime.now().isoformat()
        
        coin_data = None
        if raw_data.get("status") == "success" and "symbols" in raw_data:
            symbols_list = raw_data["symbols"]
            if isinstance(symbols_list, list) and len(symbols_list) > 0:
                for coin in symbols_list:
                    if coin.get("symbol") == symbol:
                        coin_data = coin
                        break
                if not coin_data and len(symbols_list) > 0:
                    coin_data = symbols_list[0]
        elif "data" in raw_data:
            coin_data = raw_data["data"]
        elif "result" in raw_data:
            coin_data = raw_data["result"]
        else:
            coin_data = raw_data
        
        if not coin_data:
            raise ValueError(f"No coin data found in API response for {symbol}")
        
        price_str = coin_data.get("last") or coin_data.get("price") or "0"
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0.0
        
        lowest_str = coin_data.get("lowest") or "0"
        highest_str = coin_data.get("highest") or "0"
        change_str = coin_data.get("daily_change_percentage") or coin_data.get("price_change_24h") or "0"
        
        try:
            lowest = float(lowest_str)
        except (ValueError, TypeError):
            lowest = None
        
        try:
            highest = float(highest_str)
        except (ValueError, TypeError):
            highest = None
        
        try:
            price_change_24h = float(change_str)
        except (ValueError, TypeError):
            price_change_24h = None
        
        transformed = {
            "symbol": coin_data.get("symbol") or symbol,
            "timestamp": timestamp,
            "price": price,
            "lowest_24h": lowest,
            "highest_24h": highest,
            "price_change_24h": price_change_24h,
            "source_exchange": coin_data.get("source_exchange"),
            "date": coin_data.get("date"),
            "raw_data": raw_data  # Keep raw data for debugging
        }
        
        return transformed
    
    def save_data(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None,
        format: str = "json"
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = data.get("symbol", "unknown")
        
        if not filename:
            filename = f"{symbol}_{timestamp}.{format}"
        
        filepath = RAW_DATA_DIR / filename
        
        if format == "json":
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            df = pd.DataFrame([data])
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved data to {filepath}")
        return filepath
    
    def collect_multiple_coins(self, symbols: List[str]) -> List[Dict[str, Any]]:
        results = []
        
        for symbol in symbols:
            data = self.collect_coin_data(symbol)
            if data:
                results.append(data)
            else:
                logger.warning(f"Skipping {symbol} due to collection failure")
            
            time.sleep(0.5)
        
        logger.info(f"Collected data for {len(results)}/{len(symbols)} coins")
        return results
    
    def close(self):
        self.session.close()
        logger.debug("DataCollector session closed")


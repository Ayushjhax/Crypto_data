import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from core.data_collector import DataCollector
from config.settings import RAW_DATA_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CollectorAgent:
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "data_sources.yaml"
        
        self.config = self._load_config(config_path)
        
        from config.settings import FREECRYPTO_API_KEY, FREECRYPTO_API_BASE_URL
        self.collector = DataCollector(
            api_key=FREECRYPTO_API_KEY,
            base_url=FREECRYPTO_API_BASE_URL
        )
        
        self.stats = {
            "total_collections": 0,
            "successful": 0,
            "failed": 0,
            "coins_collected": []
        }
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            raise
    
    def get_coins_to_collect(self) -> List[str]:
        coins = []
        try:
            data_sources = self.config.get("data_sources", {})
            freecrypto = data_sources.get("freecryptoapi", {})
            endpoints = freecrypto.get("endpoints", {})
            coin_list = endpoints.get("coins", [])

            for coin in coin_list:
                if isinstance(coin, dict):
                    coins.append(coin.get("symbol"))
                elif isinstance(coin, str):
                    coins.append(coin)
            
            logger.info(f"Found {len(coins)} coins to collect: {coins}")
            return coins
        except Exception as e:
            logger.error(f"Error extracting coins from config: {e}")
            return ["BTC", "ETH", "BNB"]
    
    def collect_all(self, save_to_file: bool = True) -> List[Dict[str, Any]]:
        logger.info("Starting data collection for all coins")
        
        coins = self.get_coins_to_collect()
        collected_data = []
        
        try:
            for symbol in coins:
                try:
                    logger.info(f"Collecting data for {symbol}...")
                    data = self.collector.collect_coin_data(symbol)
                    
                    if data:
                        collected_data.append(data)
                        self.stats["successful"] += 1
                        self.stats["coins_collected"].append(symbol)
                        
                        if save_to_file:
                            self.collector.save_data(data, format="json")
                    else:
                        self.stats["failed"] += 1
                        logger.warning(f"Failed to collect data for {symbol}")
                    
                    self.stats["total_collections"] += 1
                    
                except Exception as e:
                    logger.error(f"Error collecting {symbol}: {e}")
                    self.stats["failed"] += 1
                    continue
            
            if save_to_file and collected_data:
                self._save_aggregated_data(collected_data)
            
            self._log_summary()
            
        except Exception as e:
            logger.error(f"Fatal error during collection: {e}")
            raise
        finally:
            self.collector.close()
        
        return collected_data
    
    def _save_aggregated_data(self, data: List[Dict[str, Any]]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"all_coins_{timestamp}.json"
        filepath = RAW_DATA_DIR / filename
        
        import json
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved aggregated data to {filepath}")
    
    def _log_summary(self):
        logger.info("=" * 50)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total collections attempted: {self.stats['total_collections']}")
        logger.info(f"Successful: {self.stats['successful']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Success rate: {self.stats['successful'] / max(self.stats['total_collections'], 1) * 100:.1f}%")
        logger.info(f"Coins collected: {', '.join(self.stats['coins_collected'])}")
        logger.info("=" * 50)
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

"""
Quick test script to verify the data collection setup.

Run this to test if your API key and configuration are working correctly.

INTERVIEW EXPLANATION:
Test scripts are important for:
1. Quick verification of setup
2. Debugging configuration issues
3. Validating API connectivity
4. Demonstrating functionality
"""

from core.data_collector import DataCollector
from config.settings import FREECRYPTO_API_KEY, FREECRYPTO_API_BASE_URL
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_single_coin():
    """Test collecting data for a single coin (Bitcoin)."""
    print("=" * 60)
    print("Testing Data Collection - Single Coin (BTC)")
    print("=" * 60)
    
    try:
        # Initialize collector
        collector = DataCollector(
            api_key=FREECRYPTO_API_KEY,
            base_url=FREECRYPTO_API_BASE_URL
        )
        
        # Collect data for Bitcoin
        print("\nCollecting data for BTC...")
        data = collector.collect_coin_data("BTC")
        
        if data:
            print("\n✅ Success! Collected data:")
            print(f"  Symbol: {data.get('symbol')}")
            print(f"  Price: ${data.get('price', 'N/A')}")
            print(f"  Timestamp: {data.get('timestamp')}")
            print(f"  Market Cap: {data.get('market_cap', 'N/A')}")
            print(f"  24h Volume: {data.get('volume_24h', 'N/A')}")
            print(f"  24h Change: {data.get('price_change_24h', 'N/A')}%")
            
            # Test saving
            print("\nTesting data saving...")
            filepath = collector.save_data(data, format="json")
            print(f"✅ Data saved to: {filepath}")
        else:
            print("\n❌ Failed to collect data. Check:")
            print("  1. API key is correct")
            print("  2. Internet connection")
            print("  3. API endpoint is correct")
            print("  4. Check logs for detailed error messages")
        
        collector.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Test failed with exception")
        return False
    
    return True


if __name__ == "__main__":
    success = test_single_coin()
    if success:
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print("You can now run: python main.py")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed. Please check the errors above.")
        print("=" * 60)


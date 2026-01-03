"""
Main entry point for the crypto data collection pipeline.

INTERVIEW EXPLANATION:
This is the entry point of the application. It:
1. Initializes the agent
2. Runs the collection workflow
3. Handles top-level errors
4. Provides a simple interface to run the pipeline

In production, this might be:
- A CLI tool with arguments
- A scheduled job (cron, Airflow, etc.)
- A web service endpoint
- Part of a larger orchestration system
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.collector_agent import CollectorAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Main function to run the data collection pipeline.
    
    INTERVIEW EXPLANATION:
    The main() function pattern is common in Python because:
    1. Can be called from command line
    2. Can be imported and called programmatically
    3. Can be tested easily
    4. Follows Python best practices
    """
    logger.info("=" * 60)
    logger.info("DonutAI - Crypto Data Collection Pipeline")
    logger.info("Phase 1: Data Collection")
    logger.info("=" * 60)
    
    try:
        # Initialize the collector agent
        # INTERVIEW EXPLANATION: The agent handles all orchestration
        agent = CollectorAgent()
        
        # Run collection for all configured coins
        collected_data = agent.collect_all(save_to_file=True)
        
        # Print results
        print("\n" + "=" * 60)
        print("COLLECTION COMPLETE")
        print("=" * 60)
        print(f"Successfully collected data for {len(collected_data)} coins")
        
        stats = agent.get_stats()
        print(f"\nStatistics:")
        print(f"  - Total attempts: {stats['total_collections']}")
        print(f"  - Successful: {stats['successful']}")
        print(f"  - Failed: {stats['failed']}")
        print(f"  - Coins: {', '.join(stats['coins_collected'])}")
        
        print(f"\nData saved to: data/raw/")
        print("=" * 60)
        
        return 0  # Success exit code
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        return 130  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1  # Error exit code


if __name__ == "__main__":
    """
    INTERVIEW EXPLANATION:
    The `if __name__ == "__main__"` guard ensures:
    1. Code only runs when script is executed directly
    2. Can import this module without running main()
    3. Standard Python pattern for executable scripts
    """
    exit_code = main()
    sys.exit(exit_code)


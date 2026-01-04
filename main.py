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
from agents.cleaner_agent import CleanerAgent
from agents.labeler_agent import LabelerAgent
from agents.evaluator_agent import EvaluatorAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Main function to run the complete data pipeline.
    
    INTERVIEW EXPLANATION:
    This function orchestrates the complete pipeline:
    1. Data Collection (Phase 1)
    2. Data Cleaning (Phase 2)
    3. Data Labeling (Phase 3)
    4. Data Evaluation (Phase 4) - Critic Agent
    
    This demonstrates a complete ETL (Extract, Transform, Load) pipeline
    with quality evaluation using a critic agent pattern.
    """
    logger.info("=" * 60)
    logger.info("DonutAI - Complete Crypto Data Pipeline")
    logger.info("Phase 1: Collection → Phase 2: Cleaning → Phase 3: Labeling → Phase 4: Evaluation")
    logger.info("=" * 60)
    
    try:
        # ============================================================
        # PHASE 1: DATA COLLECTION
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1: DATA COLLECTION")
        logger.info("=" * 60)
        
        collector_agent = CollectorAgent()
        collected_data = collector_agent.collect_all(save_to_file=True)
        
        if not collected_data:
            logger.error("No data collected. Cannot proceed with cleaning and labeling.")
            return 1
        
        print(f"\n✅ Phase 1 Complete: Collected {len(collected_data)} coins")
        
        # ============================================================
        # PHASE 2: DATA CLEANING
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: DATA CLEANING")
        logger.info("=" * 60)
        
        cleaner_agent = CleanerAgent()
        cleaned_data = cleaner_agent.clean_all_raw_files(save_to_file=True)
        
        if not cleaned_data:
            logger.warning("No data cleaned. Proceeding with available data.")
        
        print(f"✅ Phase 2 Complete: Cleaned {len(cleaned_data)} records")
        
        # ============================================================
        # PHASE 3: DATA LABELING
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: DATA LABELING")
        logger.info("=" * 60)
        
        labeler_agent = LabelerAgent()
        labeled_data = labeler_agent.label_all_cleaned_files(save_to_file=True)
        
        if not labeled_data:
            logger.warning("No data labeled.")
        
        print(f"✅ Phase 3 Complete: Labeled {len(labeled_data)} records")
        
        # ============================================================
        # PHASE 4: DATA EVALUATION (Critic Agent)
        # ============================================================
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 4: DATA EVALUATION (Critic Agent)")
        logger.info("=" * 60)
        
        evaluator_agent = EvaluatorAgent()
        evaluation_results = evaluator_agent.evaluate_all_pipeline_outputs()
        
        collector_evals = len(evaluation_results.get('collector_evaluations', []))
        cleaner_evals = len(evaluation_results.get('cleaner_evaluations', []))
        labeler_evals = len(evaluation_results.get('labeler_evaluations', []))
        
        # Get stats before closing (needed for final summary)
        evaluator_stats = evaluator_agent.get_stats()
        
        print(f"✅ Phase 4 Complete: Evaluated pipeline outputs")
        print(f"  - Collector evaluations: {collector_evals}")
        print(f"  - Cleaner evaluations: {cleaner_evals}")
        print(f"  - Labeler evaluations: {labeler_evals}")
        print(f"  - Evaluation data saved to: data/evaluations.db")
        
        # Close database connection
        evaluator_agent.close()
        
        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nPhase 1 - Collection:")
        collector_stats = collector_agent.get_stats()
        print(f"  - Collected: {collector_stats['successful']} coins")
        print(f"  - Data saved to: data/raw/")
        
        print(f"\nPhase 2 - Cleaning:")
        cleaner_stats = cleaner_agent.get_stats()
        print(f"  - Cleaned: {cleaner_stats['files_cleaned']} files")
        print(f"  - Data saved to: data/cleaned/")
        
        print(f"\nPhase 3 - Labeling:")
        labeler_stats = labeler_agent.get_stats()
        print(f"  - Labeled: {labeler_stats['records_labeled']} records")
        print(f"  - Data saved to: data/labeled/")
        
        print(f"\nPhase 4 - Evaluation (Critic Agent):")
        print(f"  - Evaluations performed: {evaluator_stats.get('evaluations_performed', 0)}")
        print(f"  - High quality: {evaluator_stats.get('high_quality_count', 0)}")
        print(f"  - Medium quality: {evaluator_stats.get('medium_quality_count', 0)}")
        print(f"  - Low quality: {evaluator_stats.get('low_quality_count', 0)}")
        print(f"  - Evaluation database: data/evaluations.db")
        
        print("\n" + "=" * 60)
        
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


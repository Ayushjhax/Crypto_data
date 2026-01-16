
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.collector_agent import CollectorAgent
from agents.cleaner_agent import CleanerAgent
from agents.labeler_agent import LabelerAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.anomaly_agent import AnomalyAgent
from analytics.event_tracker import EventTracker
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("DonutAI - Complete Crypto Data Pipeline")
    logger.info("Phase 1: Collection → Phase 2: Cleaning → Phase 3: Labeling → Phase 4: Evaluation → Phase 5: Anomaly Detection")
    logger.info("=" * 60)
    
    tracker = None
    session_id = None
    
    try:
        tracker = EventTracker()
        session_id = tracker.start_pipeline_session()
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 1: DATA COLLECTION")
        logger.info("=" * 60)
        
        collector_agent = CollectorAgent()
        collected_data = collector_agent.collect_all(save_to_file=True)
        
        if not collected_data:
            logger.error("No data collected. Cannot proceed with cleaning and labeling.")
            if tracker and session_id:
                tracker.complete_pipeline_session(session_id, 'failed')
                tracker.close()
            return 1
        
        tracker.track_phase_completion(
            session_id,
            'collection',
            metadata={'coins_count': len(collected_data)}
        )
        
        print(f"\n✅ Phase 1 Complete: Collected {len(collected_data)} coins")
        
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 2: DATA CLEANING")
        logger.info("=" * 60)
        
        cleaner_agent = CleanerAgent()
        cleaned_data = cleaner_agent.clean_all_raw_files(save_to_file=True)
        
        if not cleaned_data:
            logger.warning("No data cleaned. Proceeding with available data.")
        
        cleaner_stats = cleaner_agent.get_stats()
        tracker.track_phase_completion(
            session_id,
            'cleaning',
            metadata={'files_cleaned': cleaner_stats.get('files_cleaned', len(cleaned_data))}
        )
        
        print(f"✅ Phase 2 Complete: Cleaned {len(cleaned_data)} records")
        
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 3: DATA LABELING")
        logger.info("=" * 60)
        
        labeler_agent = LabelerAgent()
        labeled_data = labeler_agent.label_all_cleaned_files(save_to_file=True)
        
        if not labeled_data:
            logger.warning("No data labeled.")
        
        labeler_stats = labeler_agent.get_stats()
        tracker.track_phase_completion(
            session_id,
            'labeling',
            metadata={'records_labeled': labeler_stats.get('records_labeled', len(labeled_data))}
        )
        
        print(f"✅ Phase 3 Complete: Labeled {len(labeled_data)} records")
        
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 4: DATA EVALUATION (Critic Agent)")
        logger.info("=" * 60)
        
        evaluator_agent = EvaluatorAgent()
        evaluation_results = evaluator_agent.evaluate_all_pipeline_outputs()
        
        collector_evals = len(evaluation_results.get('collector_evaluations', []))
        cleaner_evals = len(evaluation_results.get('cleaner_evaluations', []))
        labeler_evals = len(evaluation_results.get('labeler_evaluations', []))
        
        evaluator_stats = evaluator_agent.get_stats()
        
        tracker.track_phase_completion(
            session_id,
            'evaluation',
            metadata={'evaluations_performed': evaluator_stats.get('evaluations_performed', 0)}
        )
        
        print(f"✅ Phase 4 Complete: Evaluated pipeline outputs")
        print(f"  - Collector evaluations: {collector_evals}")
        print(f"  - Cleaner evaluations: {cleaner_evals}")
        print(f"  - Labeler evaluations: {labeler_evals}")
        print(f"  - Evaluation data saved to: data/evaluations.db")
        
        evaluator_agent.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 5: ANOMALY DETECTION & ALERTING")
        logger.info("=" * 60)
        
        anomaly_agent = AnomalyAgent()
        anomaly_results = anomaly_agent.check_all_metrics(
            threshold=0.7,  # Alert if quality score drops below 70%
            lookback_days=7,  # Compare to last 7 days
            send_alerts=True
        )
        
        anomalies_found = anomaly_results.get('anomalies_found', 0)
        critical_anomalies = anomaly_results.get('critical_anomalies', 0)
        
        anomaly_stats = anomaly_agent.get_stats()
        anomaly_agent.close()
        
        print(f"✅ Phase 5 Complete: Anomaly detection performed")
        print(f"  - Anomalies detected: {anomalies_found}")
        print(f"  - Critical anomalies: {critical_anomalies}")
        print(f"  - Alerts sent: {anomaly_stats.get('alerts_sent', 0)}")
        
        if anomalies_found > 0:
            print(f"  ⚠️  WARNING: {anomalies_found} anomaly(ies) detected - check logs for details")
        else:
            print(f"  ✅ No anomalies detected - all metrics are healthy")
        
        tracker.complete_pipeline_session(session_id, 'completed')
        tracker.close()
        
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
        
        print(f"\nPhase 5 - Anomaly Detection:")
        print(f"  - Anomalies detected: {anomalies_found}")
        print(f"  - Critical anomalies: {critical_anomalies}")
        print(f"  - Checks performed: {anomaly_stats.get('anomaly_checks_performed', 0)}")
        print(f"  - Alerts sent: {anomaly_stats.get('alerts_sent', 0)}")
        
        print("\n" + "=" * 60)
        
        return 0  # Success exit code
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        if tracker and session_id:
            tracker.complete_pipeline_session(session_id, 'failed')
            tracker.close()
        return 130  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if tracker and session_id:
            tracker.complete_pipeline_session(session_id, 'failed')
            tracker.close()
        return 1  # Error exit code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


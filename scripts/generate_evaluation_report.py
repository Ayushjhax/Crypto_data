#!/usr/bin/env python3
"""
Script to generate evaluation reports.

INTERVIEW EXPLANATION:
This script demonstrates how to use the evaluation system
for analytics and reporting - a common data processing task.

Usage:
    python scripts/generate_evaluation_report.py
    python scripts/generate_evaluation_report.py --days 30 --agent-type collector
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analytics.evaluation_analyzer import EvaluationAnalyzer
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Generate and export evaluation reports.
    
    INTERVIEW EXPLANATION:
    This function:
    1. Creates an analyzer instance
    2. Generates quality report from database
    3. Exports report to JSON file
    4. Prints summary to console
    """
    # Initialize analyzer
    analyzer = EvaluationAnalyzer()
    
    try:
        # Generate report for all agents (last 30 days)
        # INTERVIEW EXPLANATION: This queries the database and processes evaluation data
        report = analyzer.generate_quality_report(days=30)
        
        # Export to file
        output_dir = Path("data/quality_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"quality_report_{timestamp}.json"
        
        # Save report to JSON file
        analyzer.export_report_json(report, str(report_path))
        
        # ============================================================
        # Print summary to console
        # ============================================================
        print("=" * 60)
        print("EVALUATION REPORT SUMMARY")
        print("=" * 60)
        
        # Print average scores
        print(f"\nAverage Scores (last 30 days):")
        avg_scores = report['summary'].get('average_scores', [])
        if avg_scores:
            for score_data in avg_scores:
                agent = score_data['agent_type']
                overall = score_data.get('avg_overall', 'N/A')
                print(f"  {agent:12} Overall Score: {overall}")
        else:
            print("  No evaluation data found")
        
        # Print quality distribution
        print(f"\nQuality Distribution:")
        dist = report['summary'].get('quality_distribution', {})
        total = dist.get('total', 0)
        if total > 0:
            print(f"  Total Evaluations: {total}")
            print(f"  High Quality (>0.8):   {dist.get('high_quality', 0):4} "
                  f"({(dist.get('high_quality', 0)/total*100):5.1f}%)")
            print(f"  Medium Quality (0.5-0.8): {dist.get('medium_quality', 0):4} "
                  f"({(dist.get('medium_quality', 0)/total*100):5.1f}%)")
            print(f"  Low Quality (<0.5):    {dist.get('low_quality', 0):4} "
                  f"({(dist.get('low_quality', 0)/total*100):5.1f}%)")
        else:
            print("  No evaluation data found")
        
        # Print top recommendations
        print(f"\nTop Recommendations:")
        recommendations = report.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
                print(f"  {i}. {rec}")
        else:
            print("  No recommendations")
        
        # Print file location
        print(f"\nFull report saved to: {report_path}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1
    finally:
        # Always close database connections
        analyzer.close()
    
    return 0


if __name__ == "__main__":
    """
    INTERVIEW EXPLANATION:
    Entry point when script is run directly.
    sys.exit() returns exit code to shell (0 = success, non-zero = error)
    """
    exit_code = main()
    sys.exit(exit_code)


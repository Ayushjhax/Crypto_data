"""
Script to view product analytics metrics.

INTERVIEW EXPLANATION:
This script demonstrates how to use the analytics system:
- Calculate DAU (Daily Active Users)
- View conversion rates
- Analyze funnel
- Calculate retention

Usage:
    python scripts/view_analytics.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analytics.metrics_calculator import MetricsCalculator
from datetime import date, timedelta
import json


def main():
    """Display analytics metrics."""
    print("=" * 60)
    print("DonutAI Product Analytics Dashboard")
    print("=" * 60)
    
    calculator = MetricsCalculator()
    
    try:
        # ============================================================
        # DAU (Daily Active Users)
        # ============================================================
        print("\n📊 DAU (Daily Active Users)")
        print("-" * 60)
        current_dau = calculator.calculate_dau()
        print(f"Today's DAU: {current_dau}")
        
        # Get last 7 days
        dau_timeseries = calculator.get_dau_timeseries(7)
        print("\nLast 7 days:")
        for day in dau_timeseries:
            print(f"  {day['date']}: {day['dau']} active sessions")
        
        # ============================================================
        # CONVERSION RATES
        # ============================================================
        print("\n📈 Conversion Rates (Last 30 days)")
        print("-" * 60)
        
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        date_range = (start_date, end_date)
        
        pipeline_completion = calculator.calculate_conversion_rate(
            'pipeline_start', 'evaluation_complete', date_range
        )
        collection_to_cleaning = calculator.calculate_conversion_rate(
            'collection_complete', 'cleaning_complete', date_range
        )
        cleaning_to_labeling = calculator.calculate_conversion_rate(
            'cleaning_complete', 'labeling_complete', date_range
        )
        labeling_to_evaluation = calculator.calculate_conversion_rate(
            'labeling_complete', 'evaluation_complete', date_range
        )
        
        print(f"Pipeline Start → Evaluation Complete: {pipeline_completion}%")
        print(f"Collection → Cleaning: {collection_to_cleaning}%")
        print(f"Cleaning → Labeling: {cleaning_to_labeling}%")
        print(f"Labeling → Evaluation: {labeling_to_evaluation}%")
        
        # ============================================================
        # FUNNEL ANALYSIS
        # ============================================================
        print("\n🔄 Pipeline Funnel (Last 30 days)")
        print("-" * 60)
        
        funnel = calculator.get_pipeline_funnel(30)
        for step, data in funnel.items():
            print(f"\n{step}:")
            print(f"  Users reached: {data['users_reached']}")
            print(f"  Conversion rate: {data['conversion_rate']}%")
            if data['dropoff_rate'] > 0:
                print(f"  Drop-off rate: {data['dropoff_rate']}%")
        
        # ============================================================
        # FEATURE USAGE
        # ============================================================
        print("\n⚙️  Feature Usage (Last 30 days)")
        print("-" * 60)
        
        usage = calculator.get_feature_usage(30)
        print(f"Total sessions: {usage['total_sessions']}")
        print(f"Completed sessions: {usage['completed_sessions']}")
        print(f"Completion rate: {usage['completion_rate']}%")
        print(f"Average completion time: {usage['avg_completion_hours']:.2f} hours")
        
        # ============================================================
        # RETENTION (Example for last week's cohort)
        # ============================================================
        print("\n🔁 Retention Rates")
        print("-" * 60)
        
        # Calculate retention for cohort from 7 days ago
        cohort_date = date.today() - timedelta(days=7)
        retention = calculator.calculate_retention(cohort_date, [1, 7, 30])
        
        print(f"Cohort from {cohort_date.isoformat()}:")
        print(f"  Day 1 retention: {retention.get('day_1', 0)}%")
        print(f"  Day 7 retention: {retention.get('day_7', 0)}%")
        print(f"  Day 30 retention: {retention.get('day_30', 0)}%")
        
        # ============================================================
        # COMPLETE SUMMARY (JSON export)
        # ============================================================
        print("\n📋 Complete Summary")
        print("-" * 60)
        
        summary = calculator.get_summary(30)
        print(json.dumps(summary, indent=2, default=str))
        
        print("\n" + "=" * 60)
        print("Analytics complete!")
        print("=" * 60)
        
    finally:
        calculator.close()


if __name__ == "__main__":
    main()


"""
Analytics package for evaluation reporting, data quality, and product analytics.

INTERVIEW EXPLANATION:
This __init__.py makes analytics a Python package.
Exports:
- DataQualityReporter: Data quality reporting
- EvaluationAnalyzer: Evaluation data analysis
- EventTracker: Product analytics event tracking
- MetricsCalculator: Product metrics (DAU, conversion, funnel, retention)
"""

# Import data quality reporter (no external dependencies)
from analytics.data_quality_reporter import DataQualityReporter

# Evaluation analyzer and product analytics require database dependencies
try:
    from analytics.evaluation_analyzer import EvaluationAnalyzer
    from analytics.event_tracker import EventTracker
    from analytics.metrics_calculator import MetricsCalculator
    __all__ = [
        "DataQualityReporter",
        "EvaluationAnalyzer",
        "EventTracker",
        "MetricsCalculator"
    ]
except ImportError:
    # Database dependencies not available
    __all__ = ["DataQualityReporter"]


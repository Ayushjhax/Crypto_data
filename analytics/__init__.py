"""
Analytics package for evaluation reporting and data quality.

INTERVIEW EXPLANATION:
This __init__.py makes analytics a Python package.
"""

# Import data quality reporter (no external dependencies)
from analytics.data_quality_reporter import DataQualityReporter

# Evaluation analyzer requires database dependencies, import only if needed
try:
    from analytics.evaluation_analyzer import EvaluationAnalyzer
    __all__ = ["DataQualityReporter", "EvaluationAnalyzer"]
except ImportError:
    # Database dependencies not available
    __all__ = ["DataQualityReporter"]


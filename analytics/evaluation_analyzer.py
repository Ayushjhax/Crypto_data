"""
Analytics module for evaluation data.

INTERVIEW EXPLANATION:
This module processes evaluation data from the database
and generates insights, reports, and visualizations.

Demonstrates:
- Data aggregation and analysis
- SQL query building
- Report generation
- Statistical analysis
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from database.models import DatabaseManager
from database.queries import EvaluationQueries
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EvaluationAnalyzer:
    """
    Analyzes evaluation data and generates reports.
    
    INTERVIEW EXPLANATION:
    This class demonstrates data processing skills:
    - Querying databases
    - Performing aggregations
    - Generating insights from data
    - Creating reports
    """
    
    def __init__(self, db_path: str = "data/evaluations.db"):
        """
        Initialize the analyzer.
        
        INTERVIEW EXPLANATION:
        Args:
            db_path: Path to evaluation database
        """
        # Initialize database manager for database access
        self.db_manager = DatabaseManager(db_path)
        # Initialize queries helper for common queries
        self.queries = EvaluationQueries(self.db_manager)
    
    def generate_quality_report(
        self, 
        agent_type: Optional[str] = None, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report.
        
        INTERVIEW EXPLANATION:
        This method demonstrates complex data processing:
        - Multiple database queries
        - Data aggregation
        - Statistical analysis
        - Report generation
        
        Process:
        1. Query average scores by agent type
        2. Get quality distribution (high/medium/low)
        3. Calculate trends over time
        4. Find top issues
        5. Generate recommendations
        6. Combine into comprehensive report
        
        Args:
            agent_type: Optional filter by agent type
            days: Number of days to analyze
        
        Returns:
            Dictionary with comprehensive quality report
        """
        logger.info(f"Generating quality report for {agent_type or 'all agents'} (last {days} days)")
        
        # Initialize report structure
        report = {
            'generated_at': datetime.now().isoformat(),  # When report was generated
            'period_days': days,
            'agent_type': agent_type,
            'summary': {},      # Summary statistics
            'trends': {},       # Trends over time
            'issues': {},       # Issue analysis
            'recommendations': []  # Actionable recommendations
        }
        
        # ============================================================
        # 1. GET AVERAGE SCORES BY AGENT TYPE
        # ============================================================
        # Query database for average scores
        avg_scores = self.queries.get_avg_scores_by_agent(days)
        
        # Filter by agent_type if specified
        if agent_type:
            avg_scores = [s for s in avg_scores if s['agent_type'] == agent_type]
        
        report['summary']['average_scores'] = avg_scores
        
        # ============================================================
        # 2. GET QUALITY DISTRIBUTION
        # ============================================================
        # Get counts of high/medium/low quality evaluations
        distribution = self.queries.get_quality_distribution(agent_type)
        report['summary']['quality_distribution'] = distribution
        
        # Calculate percentages
        total = distribution['total']
        if total > 0:
            # Calculate percentage of each quality category
            report['summary']['quality_percentages'] = {
                'high_quality': round((distribution['high_quality'] / total) * 100, 2),
                'medium_quality': round((distribution['medium_quality'] / total) * 100, 2),
                'low_quality': round((distribution['low_quality'] / total) * 100, 2)
            }
        
        # ============================================================
        # 3. GET TRENDS OVER TIME
        # ============================================================
        if agent_type:
            # Get trends for specific agent type
            trends = self.queries.get_trend_over_time(agent_type, days)
            report['trends'] = trends
        else:
            # Get trends for all agent types
            agent_types = ['collector', 'cleaner', 'labeler']
            report['trends'] = {
                agent: self.queries.get_trend_over_time(agent, days)
                for agent in agent_types
            }
        
        # ============================================================
        # 4. GET TOP ISSUES
        # ============================================================
        # Find most common issues found in evaluations
        top_issues = self.queries.get_top_issues(agent_type, limit=10)
        report['issues']['top_issues'] = top_issues
        
        # ============================================================
        # 5. GENERATE RECOMMENDATIONS
        # ============================================================
        report['recommendations'] = self._generate_recommendations_from_report(report)
        
        return report
    
    def _generate_recommendations_from_report(self, report: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations from report data.
        
        INTERVIEW EXPLANATION:
        Analyzes report data to provide actionable recommendations.
        This is business logic that converts data into insights.
        
        Args:
            report: Quality report dictionary
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # ============================================================
        # Check quality distribution
        # ============================================================
        dist = report['summary'].get('quality_distribution', {})
        total = dist.get('total', 0)
        
        if total > 0:
            # Calculate percentage of low quality data
            low_quality_pct = (dist.get('low_quality', 0) / total) * 100
            
            # If more than 20% is low quality, recommend improvement
            if low_quality_pct > 20:
                recommendations.append(
                    f"High percentage ({low_quality_pct:.1f}%) of low quality data. "
                    "Review data collection and cleaning processes."
                )
        
        # ============================================================
        # Check average scores
        # ============================================================
        avg_scores = report['summary'].get('average_scores', [])
        for score_data in avg_scores:
            avg_overall = score_data.get('avg_overall', 1.0)
            # If average score is below 0.7, recommend improvement
            if avg_overall < 0.7:
                recommendations.append(
                    f"{score_data['agent_type']} agent has low average score "
                    f"({avg_overall:.3f}). Consider improving validation."
                )
        
        # ============================================================
        # Check top issues
        # ============================================================
        top_issues = report['issues'].get('top_issues', [])
        if top_issues:
            # Get most common issue
            most_common = top_issues[0]
            recommendations.append(
                f"Most common issue: '{most_common['issue']}' "
                f"(occurs {most_common['count']} times). "
                "Address this to improve overall quality."
            )
        
        # If no recommendations generated, add positive feedback
        if not recommendations:
            recommendations.append("Data quality is good. Continue monitoring.")
        
        return recommendations
    
    def export_report_json(self, report: Dict[str, Any], filepath: str):
        """
        Export report to JSON file.
        
        INTERVIEW EXPLANATION:
        Saves report dictionary to JSON file for:
        - Sharing reports
        - Archiving historical reports
        - Integration with other tools
        
        Args:
            report: Report dictionary to export
            filepath: Path to save JSON file
        """
        import json
        from pathlib import Path
        
        # Convert to Path object
        path = Path(filepath)
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON to file
        # indent=2 makes JSON readable (pretty print)
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exported report to {filepath}")
    
    def close(self):
        """
        Close database connections.
        
        INTERVIEW EXPLANATION:
        Clean up resources. Always close database connections
        when done to prevent connection leaks.
        """
        self.db_manager.close()


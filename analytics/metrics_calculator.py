
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from database.models import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MetricsCalculator:
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_manager = DatabaseManager(db_path)
    
    def calculate_dau(self, target_date: Optional[date] = None) -> int:
        if not target_date:
            target_date = date.today()
        
        session = self.db_manager.get_session()
        try:
            result = session.execute(
                text("""
                    SELECT COUNT(DISTINCT session_id) as dau
                    FROM analytics_sessions
                    WHERE DATE(started_at) = :target_date
        Get DAU for the last N days.
        
        INTERVIEW EXPLANATION:
        Returns time series data for DAU chart.
        Useful for tracking trends over time.
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of {date, dau} dictionaries
        Calculate conversion rate between two events.
        
        INTERVIEW EXPLANATION:
        Conversion rate = (users who completed end_event / users who started start_event) * 100
        
        Example:
        - start_event: 'pipeline_start'
        - end_event: 'evaluation_complete'
        - Returns: % of users who complete full pipeline
        
        Args:
            start_event: Starting event name
            end_event: Ending event name
            date_range: Optional (start_date, end_date) tuple
        
        Returns:
            Conversion rate as percentage (0-100)
                SELECT COUNT(DISTINCT session_id)
                FROM analytics_events
                WHERE event_name = :start_event
                SELECT COUNT(DISTINCT session_id)
                FROM analytics_events
                WHERE event_name = :end_event
        Calculate funnel analysis with drop-off rates.
        
        INTERVIEW EXPLANATION:
        Funnel analysis shows:
        - How many users reach each step
        - Drop-off rate between steps
        - Conversion rate at each step
        
        This is critical for identifying where users drop off.
        
        Args:
            steps: List of event names in order (e.g., ['pipeline_start', 'collection_complete', ...])
            date_range: Optional (start_date, end_date) tuple
        
        Returns:
            Dictionary with funnel data for each step
                    SELECT COUNT(DISTINCT session_id)
                    FROM analytics_events
                    WHERE event_name = :step
        Calculate retention rates for a cohort.
        
        INTERVIEW EXPLANATION:
        Retention = % of users who return after N days.
        
        Example:
        - Cohort: Users who ran pipeline on Jan 1
        - Day 1 retention: % who ran pipeline again on Jan 2
        - Day 7 retention: % who ran pipeline again on Jan 8
        - Day 30 retention: % who ran pipeline again on Jan 31
        
        This shows user engagement over time.
        
        Args:
            cohort_date: Date of first pipeline run (cohort date)
            days: List of days to calculate retention for
        
        Returns:
            Dictionary with retention rates for each day
                SELECT DISTINCT user_id
                FROM analytics_sessions
                WHERE DATE(started_at) = :cohort_date
                        SELECT COUNT(DISTINCT user_id)
                        FROM analytics_sessions
                        WHERE user_id IN ({placeholders})
                        AND DATE(started_at) = ?
        Get standard pipeline funnel.
        
        INTERVIEW EXPLANATION:
        Returns funnel for the standard DonutAI pipeline:
        1. Pipeline Start
        2. Collection Complete
        3. Cleaning Complete
        4. Labeling Complete
        5. Evaluation Complete
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Funnel dictionary
        Get feature usage statistics.
        
        INTERVIEW EXPLANATION:
        Shows which features are used most:
        - Average pipeline completion time
        - Completion rate
        - Total sessions
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with feature usage stats
                SELECT 
                    AVG(JULIANDAY(completed_at) - JULIANDAY(started_at)) * 24 as avg_hours
                FROM analytics_sessions
                WHERE status = 'completed'
                AND DATE(started_at) BETWEEN :start_date AND :end_date
                AND completed_at IS NOT NULL
                SELECT COUNT(*) as total
                FROM analytics_sessions
                WHERE DATE(started_at) BETWEEN :start_date AND :end_date
                SELECT COUNT(*) as completed
                FROM analytics_sessions
                WHERE status = 'completed'
                AND DATE(started_at) BETWEEN :start_date AND :end_date
        Get complete analytics summary.
        
        INTERVIEW EXPLANATION:
        Returns all key metrics in one response.
        Useful for dashboard overview.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dictionary with all metrics
        self.db_manager.close()

